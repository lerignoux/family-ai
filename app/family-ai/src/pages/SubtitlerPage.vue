<script setup lang="ts">
import { inject, ref, onMounted, watch } from 'vue';

import { generateSubtitles } from '../components/api/tts';
import { saveUserSelection, getPageSelection } from '../utils/localStorage';
import { logger } from '../utils/logger';
// Avoid importing ffmpeg utilities at module scope to prevent SSR issues

const bus = inject<any>('bus');
const selectedFile = ref<File | null>(null);
const language = ref({ label: 'English', value: 'en' });
const embedSubtitles = ref(true);
const processing = ref(false);
const progressMessage = ref('');
const downloadUrl = ref('');
const fileName = ref('');
const MAX_DIRECT_UPLOAD_BYTES = 20 * 1024 * 1024; // 20 MB

let ffmpeg: any = null;
let ffmpegUtils: {
  fetchFile: (i: Blob | File | string) => Promise<Uint8Array>;
  toBlobURL: (u: string, t: string) => Promise<string>;
} | null = null;
const loaded = ref(false);
async function ensureFfmpegLoaded() {
  if (loaded.value) return;
  try {
    progressMessage.value = 'Loading media tools...';
    console.log('Loading media tools...');
    if (typeof window === 'undefined') {
      // Avoid throwing during SSR/pre-render; quietly skip loading
      return;
    }
    if (!ffmpeg) {
      const mod = await import('@ffmpeg/ffmpeg');
      const FFmpegCtor = (mod as any).FFmpeg;
      ffmpeg = new FFmpegCtor();
      // Optional: ffmpeg.on('log', ({ message }: { message: string }) => console.log('[ffmpeg]', message));
    }
    if (!ffmpegUtils) {
      const utilMod = await import('@ffmpeg/util');
      ffmpegUtils = {
        fetchFile: utilMod.fetchFile,
        toBlobURL: utilMod.toBlobURL,
      };
    }
    // Load FFmpeg core from local public assets and use a dedicated local worker
    const baseURL = '/ffmpeg';

    const coreURL = await ffmpegUtils.toBlobURL(
      `${baseURL}/ffmpeg-core.js`,
      'text/javascript'
    );
    const wasmURL = await ffmpegUtils.toBlobURL(
      `${baseURL}/ffmpeg-core.wasm`,
      'application/wasm'
    );
    const workerURL = await ffmpegUtils.toBlobURL(
      `${baseURL}/worker.js`,
      'text/javascript'
    );
    console.log('ffmpeg loading');
    await ffmpeg.load({ coreURL, wasmURL, workerURL });
    console.log('ffmpeg loaded');
    loaded.value = true;
  } catch (e) {
    console.log('ffmpeg not loaded');
    console.error('Failed to load ffmpeg:', e);
    progressMessage.value = 'Failed to load media tools';
    bus.emit('show-notification', {
      type: 'negative',
      message:
        'Failed to load media tools. Please check your connection and try again.',
      timeout: 5000,
    });
    throw e;
  }
}

async function extractAudioMp3(inputFile: File): Promise<File> {
  console.log('Extracting audio from video...');
  await ensureFfmpegLoaded();

  console.log('ffmpeg loaded');
  const baseName =
    inputFile.name.substring(0, inputFile.name.lastIndexOf('.')) ||
    inputFile.name;
  const inputName = 'input_video';
  const outputName = 'output_audio.mp3';

  // Write the input file into ffmpeg FS
  if (!ffmpegUtils) {
    const utilMod = await import('@ffmpeg/util');
    ffmpegUtils = {
      fetchFile: utilMod.fetchFile,
      toBlobURL: utilMod.toBlobURL,
    };
  }
  await ffmpeg.writeFile(inputName, await ffmpegUtils.fetchFile(inputFile));

  // -vn: no video, -acodec libmp3lame to mp3, bitrate 192k (tweakable)
  await ffmpeg.exec([
    '-i',
    inputName,
    '-vn',
    '-acodec',
    'libmp3lame',
    '-b:a',
    '192k',
    outputName,
  ]);

  const data = (await ffmpeg.readFile(outputName)) as Uint8Array;
  const copy = new Uint8Array(data.length);
  copy.set(data);
  const blob = new Blob([copy.buffer as ArrayBuffer], { type: 'audio/mpeg' });
  return new File([blob], `${baseName}.mp3`, { type: 'audio/mpeg' });
}

const languages = ref([
  { label: 'English', value: 'en' },
  { label: 'French', value: 'fr' },
  { label: 'Chinese', value: 'zh' },
  { label: 'Spanish', value: 'es' },
  { label: 'Japanese', value: 'jp' },
]);

const supportedVideoTypes = [
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
    progressMessage.value = 'Preparing media...';

    logger.debug(
      `Generating subtitles for ${selectedFile.value.name} in ${language.value.label}`
    );

    // Decide whether to convert to audio-only based on size
    let uploadFile: File = selectedFile.value;
    let effectiveEmbed = embedSubtitles.value;
    if (selectedFile.value.size > MAX_DIRECT_UPLOAD_BYTES) {
      progressMessage.value = 'Extracting audio from video (mp3)...';
      uploadFile = await extractAudioMp3(selectedFile.value);
      // When sending audio-only, disable embedding on server side
      effectiveEmbed = false;
    }

    progressMessage.value = 'Uploading and generating subtitles...';
    const result = await generateSubtitles(
      uploadFile,
      language.value.value,
      effectiveEmbed
    );

    // Create download URL
    if (downloadUrl.value) {
      URL.revokeObjectURL(downloadUrl.value);
    }

    downloadUrl.value = URL.createObjectURL(result);

    // Determine file extension based on embed option
    const originalName = uploadFile.name;
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
          label="Select video file"
          filled
          dark
          accept="video/*"
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
