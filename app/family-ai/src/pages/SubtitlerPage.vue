<script setup lang="ts">
import { inject, ref, onMounted, watch } from 'vue';
import { generateSubtitles } from '../components/api/tts';
import { saveUserSelection, getPageSelection } from '../utils/localStorage';
import { logger } from '../utils/logger';

const bus = inject<any>('bus');
const selectedFile = ref<File | null>(null);
const language = ref({ label: 'English', value: 'en' });
const embedSubtitles = ref(true);
const processing = ref(false);
const progressMessage = ref('');
const downloadUrl = ref('');
const fileName = ref('');

const languages = ref([
  { label: 'English', value: 'en' },
  { label: 'French', value: 'fr' },
  { label: 'Chinese', value: 'zh' },
  { label: 'Spanish', value: 'es' },
  { label: 'Japanese', value: 'jp' },
]);

const supportedVideoTypes = [
  '.mp3',
  '.mp4',
  '.avi',
  '.mov',
  '.wmv',
  '.flv',
  '.3gp',
  '.ogg',
];

onMounted(() => {
  // Load saved language selection
  const savedSelections = getPageSelection('subtitler');
  if (savedSelections.language) {
    language.value = savedSelections.language;
  }
  if (savedSelections.embedSubtitles !== undefined) {
    embedSubtitles.value = savedSelections.embedSubtitles;
  }
});

// Watch for language changes and save to localStorage
watch(language, (newLanguage) => {
  if (newLanguage) {
    saveUserSelection('subtitler', 'language', newLanguage);
  }
});

watch(embedSubtitles, (newValue) => {
  saveUserSelection('subtitler', 'embedSubtitles', newValue);
});

function handleFileSelect(file: File | null) {
  if (!file) {
    selectedFile.value = null;
    fileName.value = '';
    return;
  }

  const fileExtension = '.' + file.name.split('.').pop()?.toLowerCase();

  if (supportedVideoTypes.includes(fileExtension)) {
    selectedFile.value = file;
    fileName.value = file.name;
    logger.debug(`Selected file: ${file.name}`);
  } else {
    selectedFile.value = null;
    fileName.value = '';
    bus.emit('show-notification', {
      type: 'negative',
      message: `Unsupported file type. Supported types: ${supportedVideoTypes.join(
        ', '
      )}`,
      timeout: 5000,
    });
  }
}

async function generateSubtitlesForVideo() {
  if (!selectedFile.value) {
    bus.emit('show-notification', {
      type: 'negative',
      message: 'Please select a video file first',
      timeout: 3000,
    });
    return;
  }

  try {
    processing.value = true;
    progressMessage.value = 'Processing video and generating subtitles...';

    logger.debug(
      `Generating subtitles for ${selectedFile.value.name} in ${language.value.label}`
    );

    const result = await generateSubtitles(
      selectedFile.value,
      language.value.value,
      embedSubtitles.value
    );

    // Create download URL
    if (downloadUrl.value) {
      URL.revokeObjectURL(downloadUrl.value);
    }

    downloadUrl.value = URL.createObjectURL(result);

    // Determine file extension based on embed option
    const originalName = selectedFile.value.name;
    const nameWithoutExt = originalName.substring(
      0,
      originalName.lastIndexOf('.')
    );
    const extension = embedSubtitles.value
      ? originalName.substring(originalName.lastIndexOf('.'))
      : '.srt';
    fileName.value = `${nameWithoutExt}_subtitles${extension}`;

    progressMessage.value = 'Subtitles generated successfully!';

    bus.emit('show-notification', {
      type: 'positive',
      message: `Subtitles generated for ${selectedFile.value.name}`,
      timeout: 3000,
    });
  } catch (error) {
    logger.error('Error generating subtitles:', error);
    bus.emit('show-notification', {
      type: 'negative',
      message: `Failed to generate subtitles: ${error}`,
      timeout: 5000,
    });
    progressMessage.value = 'Error generating subtitles';
  } finally {
    processing.value = false;
  }
}

function downloadResult() {
  if (downloadUrl.value) {
    const link = document.createElement('a');
    link.href = downloadUrl.value;
    link.download = fileName.value;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }
}

function clearFile() {
  selectedFile.value = null;
  fileName.value = '';
  if (downloadUrl.value) {
    URL.revokeObjectURL(downloadUrl.value);
    downloadUrl.value = '';
  }
  progressMessage.value = '';
}
</script>

<template>
  <div class="subtitler col wrap justify-start items-center">
    <div class="subtitler-options row items-start wrap">
      <div class="col-grow-xs col-md">
        <q-select
          standout="bg-grey-9 text-white"
          dark
          text-color="white"
          v-model="language"
          :options="languages"
          label="Language:"
        >
          <template v-slot:append>
            <q-avatar icon="mdi-translate" text-color="white" />
          </template>
        </q-select>
      </div>

      <div class="col-grow-xs col-md">
        <q-toggle
          v-model="embedSubtitles"
          label="Embed subtitles in video"
          color="primary"
          dark
        />
      </div>
    </div>

    <div class="subtitler-actions row items-center wrap">
      <div class="file-upload-section col-grow">
        <q-file
          v-model="selectedFile"
          @update:model-value="handleFileSelect"
          label="Select video/audio file"
          filled
          dark
          accept="*"
          :disable="processing"
        >
          <template v-slot:prepend>
            <q-icon name="mdi-video" />
          </template>
        </q-file>
      </div>

      <div class="col-auto">
        <q-btn
          @click="generateSubtitlesForVideo"
          :loading="processing"
          :disable="!selectedFile || processing"
          color="primary"
          icon="mdi-subtitles"
          round
          size="l"
          class="q-mr-md"
        />

        <q-btn
          @click="clearFile"
          :disable="processing"
          color="grey"
          icon="mdi-delete"
          round
          size="l"
        />
      </div>
    </div>

    <div class="progress-section" v-if="processing || progressMessage">
      <q-linear-progress
        :indeterminate="processing"
        color="primary"
        class="q-mb-md"
      />
    </div>

    <div class="download-section" v-if="downloadUrl">
      <q-card dark class="q-pa-md">
        <q-card-section>
          <div class="text-h6">Subtitles Ready!</div>
          <div class="text-body2">{{ fileName }}</div>
          <q-btn
            @click="downloadResult"
            color="primary"
            icon="mdi-download"
            label="Download video"
            size="l"
            class="q-mt-md"
          />
        </q-card-section>
      </q-card>
    </div>
  </div>
</template>

<style>
.subtitler {
  margin-left: 20px;
  margin-right: 20px;
  height: 100%;
}

.subtitler-options {
  gap: 20px;
  margin-bottom: 20px;
  .q-field__native span {
    color: white;
  }
}

.subtitler-actions {
  gap: 10px;
  margin-bottom: 10px;
}

.file-upload-section {
  width: 100%;
  max-width: 500px;
}

.progress-section {
  width: 100%;
  margin-bottom: 20px;
}

.download-section {
  width: 100%;
  margin-bottom: 20px;
}
</style>
