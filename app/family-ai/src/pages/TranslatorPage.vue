<script setup lang="ts">
import { inject, ref, onMounted, watch } from 'vue';
import { translateText, translateAudio } from '../components/api/translate';
import { speechToText } from '../components/api/tts';
import VoiceInput from '../components/VoiceInput.vue';
import { saveUserSelection, getPageSelection } from '../utils/localStorage';
import pino from 'pino';

const logger = pino({
  level: 'info',
});

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

async function recordCallback(text: string) {
  userInput.value = text;
  handleUserInput();
}

async function handleAudioTranslation(blob: Blob) {
  try {
    audioTranslating.value = true;
    logger.debug('Processing audio for translation...');

    // Call translateAudio directly with the audio blob
    const translatedAudioBlob = await translateAudio(
      blob,
      language_src.value.value,
      language_dst.value.value
    );

    // Play the translated audio
    const audioUrl = URL.createObjectURL(translatedAudioBlob);
    const audio = new Audio(audioUrl);

    audio.onended = () => {
      URL.revokeObjectURL(audioUrl); // Clean up the URL
    };

    await audio.play();
    logger.debug('Playing translated audio');

    // Show success notification
    bus.emit('show-notification', {
      type: 'positive',
      message: `Audio translated from ${language_src.value.label} to ${language_dst.value.label}`,
      timeout: 3000,
    });
  } catch (error) {
    logger.error('Error processing audio translation:', error);

    // Show error notification
    bus.emit('show-notification', {
      type: 'negative',
      message: 'Audio translation failed. Falling back to text translation.',
      timeout: 5000,
    });

    // Fallback to speech-to-text if audio translation fails
    const text = await speechToText(blob);
    userInput.value = text;
    handleUserInput();
  } finally {
    audioTranslating.value = false;
  }
}

async function handleUserInput() {
  querying.value = true;
  await handleUserQuery(userInput.value);
}

async function handleUserQuery(query: string) {
  logger.debug(
    `Requesting translation ${language_src.value.value}-> ${language_src.value.value}.`
  );
  const translated = await translateText(
    query,
    language_src.value.value,
    language_dst.value.value
  );
  aiTranslation.value = translated;
  querying.value = false;
  bus.emit('read-text', translated, language_dst.value.value);
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
