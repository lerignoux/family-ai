<script setup lang="ts">
import { inject, ref, onMounted, watch } from 'vue';
import {
  translateAudioStream,
  translateTextStream,
  type TranslationProgress,
} from '../components/api/translate';

import VoiceInput from '../components/VoiceInput.vue';
import { saveUserSelection, getPageSelection } from '../utils/localStorage';
import { logger } from '../utils/logger';

const bus = inject<any>('bus');
const userInput = ref('Who are you');
const aiTranslation = ref('');
const language_src = ref({ label: 'English', value: 'en' });
const language_dst = ref({ label: 'French', value: 'fr' });
const languages = ref([
  { label: 'English', value: 'en' },
  { label: 'French', value: 'fr' },
  { label: 'Chinese', value: 'zh' },
  { label: 'Spanish', value: 'es' },
  { label: 'Japanese', value: 'jp' },
]);
const querying = ref(false);
const audioTranslating = ref(false);
const translationProgress = ref<TranslationProgress | null>(null);
const translationPhase = ref<string>('');
const progressPercentage = ref(0);

onMounted(() => {
  // Load saved language selections
  const savedSelections = getPageSelection('translator');
  if (savedSelections.language_src) {
    language_src.value = savedSelections.language_src;
  }
  if (savedSelections.language_dst) {
    language_dst.value = savedSelections.language_dst;
  }
});

// Watch for language changes and save to localStorage
watch(language_src, (newLanguage) => {
  if (newLanguage) {
    saveUserSelection('translator', 'language_src', newLanguage);
  }
});

watch(language_dst, (newLanguage) => {
  if (newLanguage) {
    saveUserSelection('translator', 'language_dst', newLanguage);
  }
});

async function handleAudioTranslation(blob: Blob) {
  try {
    audioTranslating.value = true;
    translationProgress.value = null;
    translationPhase.value = '';
    progressPercentage.value = 0;

    logger.debug('Processing audio for translation...');

    // Use WebSocket streaming for real-time progress
    await translateAudioStream(
      blob,
      language_src.value.value,
      language_dst.value.value,
      {
        onProgress: (progress: TranslationProgress) => {
          translationProgress.value = progress;

          switch (progress.type) {
            case 'speech_to_text':
              translationPhase.value = 'Converting speech to text...';
              progressPercentage.value = progress.progress || 25;
              // Update user input with transcribed text
              if (progress.transcribedText) {
                userInput.value = progress.transcribedText;
              }
              break;
            case 'translation':
              translationPhase.value = 'Translating text...';
              progressPercentage.value = progress.progress || 50;
              // Update translated content with translated text
              if (progress.translatedText) {
                aiTranslation.value = progress.translatedText;
              }
              break;
            case 'text_to_speech':
              translationPhase.value = 'Converting to speech...';
              progressPercentage.value = progress.progress || 75;
              break;
            case 'complete':
              translationPhase.value = 'Translation complete!';
              progressPercentage.value = 100;
              break;
            case 'error':
              translationPhase.value = 'Error occurred';
              progressPercentage.value = 0;
              break;
          }
        },
        onComplete: async (resultBlob: Blob) => {
          try {
            const audioUrl = URL.createObjectURL(resultBlob);
            const audio = new Audio(audioUrl);

            audio.onended = () => {
              URL.revokeObjectURL(audioUrl); // Clean up the URL
            };

            await audio.play();
            logger.debug('Playing translated audio');

            // Reset the translation state
            audioTranslating.value = false;
            translationProgress.value = null;
            translationPhase.value = '';
            progressPercentage.value = 0;

            bus.emit('show-notification', {
              type: 'positive',
              message: `Audio translated from ${language_src.value.label} to ${language_dst.value.label}`,
              timeout: 3000,
            });
          } catch (error) {
            logger.error('Error playing translated audio:', error);
            bus.emit('show-notification', {
              type: 'negative',
              message: 'Error playing translated audio',
              timeout: 5000,
            });
          }
        },
        onError: (error: string) => {
          logger.error('WebSocket translation error:', error);
          bus.emit('show-notification', {
            type: 'negative',
            message: `Translation failed: ${error}`,
            timeout: 5000,
          });

          // Reset state on error
          audioTranslating.value = false;
          translationProgress.value = null;
          translationPhase.value = '';
          progressPercentage.value = 0;
        },
      }
    );
  } catch (error) {
    logger.error('Error setting up audio translation:', error);

    bus.emit('show-notification', {
      type: 'negative',
      message: 'Audio translation failed.',
      timeout: 5000,
    });

    // Reset state on error
    audioTranslating.value = false;
    translationProgress.value = null;
    translationPhase.value = '';
    progressPercentage.value = 0;
  } finally {
    // Don't set audioTranslating to false here - let the WebSocket handle completion
  }
}

async function handleUserInput() {
  querying.value = true;
  await handleUserQuery(userInput.value);
}

async function handleUserQuery(query: string) {
  logger.debug(
    `Requesting translation ${language_src.value.value}-> ${language_dst.value.value}.`
  );

  try {
    querying.value = true;

    await translateTextStream(
      query,
      language_src.value.value,
      language_dst.value.value,
      {
        onProgress: (progress: TranslationProgress) => {
          if (progress.translatedText) {
            aiTranslation.value = progress.translatedText;
          }
        },
        onComplete: async () => {
          try {
            bus.emit(
              'read-text',
              aiTranslation.value,
              language_dst.value.value
            );

            bus.emit('show-notification', {
              type: 'positive',
              message: `Text translated from ${language_src.value.label} to ${language_dst.value.value}`,
              timeout: 3000,
            });
          } catch (error) {
            logger.error('Error playing translated audio:', error);
            bus.emit('show-notification', {
              type: 'negative',
              message: 'Error playing translated audio',
              timeout: 5000,
            });
          } finally {
            querying.value = false;
          }
        },
        onError: (error: string) => {
          logger.error('WebSocket text translation error:', error);
          bus.emit('show-notification', {
            type: 'negative',
            message: `Text translation failed: ${error}`,
            timeout: 5000,
          });
          querying.value = false;
        },
      }
    );
  } catch (error) {
    logger.error('Error setting up text translation:', error);
    bus.emit('show-notification', {
      type: 'negative',
      message: 'Text translation failed.',
      timeout: 5000,
    });
    querying.value = false;
  }
}

async function invertLanguages() {
  var tmp = language_src.value;
  language_src.value = language_dst.value;
  language_dst.value = tmp;
}
</script>

<template>
  <div class="translator col wrap justify-start items-center">
    <div class="translate-options row items-start wrap">
      <div class="col-grow-xs col-md">
        <q-select
          standout="bg-grey-9 text-white"
          dark
          text-color="white"
          v-model="language_src"
          :options="languages"
          label="From:"
        >
          <template v-slot:append>
            <q-avatar icon="mdi-translate" text-color="white" />
          </template>
        </q-select>
      </div>
      <div class="translate-actions invert-languages">
        <q-btn
          class="translate-action"
          @click="invertLanguages"
          id="invertButton"
          round
          color="primary"
          icon="mdi-swap-horizontal"
          size="s"
        />
      </div>
      <div class="col-grow-xs col-md">
        <q-select
          standout="bg-grey-9 text-white"
          v-model="language_dst"
          :options="languages"
          label="To:"
        >
          <template v-slot:append>
            <q-avatar icon="mdi-translate" text-color="white" />
          </template>
        </q-select>
      </div>
    </div>

    <div class="translate row items-center wrap">
      <div class="translate-input col-grow">
        <q-input
          v-model="userInput"
          v-on:keyup.enter="handleUserInput"
          filled
          type="textarea"
          hint="Your input"
        />
      </div>

      <div class="translate-actions col-auto justify-start items-center">
        <q-btn
          class="translate-action"
          @click="handleUserInput"
          :loading="querying"
          :disable="querying"
          id="queryButton"
          round
          color="primary"
          icon="forward"
          size="l"
        />
      </div>

      <div class="translate-content col-grow">
        <q-input
          v-model="aiTranslation"
          filled
          type="textarea"
          hint="Ai translation"
          readonly
        />
      </div>
    </div>

    <VoiceInput :custom-handler="handleAudioTranslation" />
  </div>
</template>

<style>
.translator {
  margin-left: 20px;
  margin-right: 20px;
  height: 100%;
}

.translate-options {
  gap: 20px;
  margin-bottom: 20px;
  .q-field__native span {
    color: white;
  }
}

.translate-actions {
  gap: 10px;
  .translate-action {
    margin-top: 10px;
    margin-bottom: 20px;
  }
}

.translate {
  gap: 20px;
  padding: 10px;
  display: flex;
  flex-direction: row;
  align-items: center;
  justify-content: center;
}

.translate-input {
  min-width: 200px;
}

.translate-content {
  min-width: 200px;
}
</style>
