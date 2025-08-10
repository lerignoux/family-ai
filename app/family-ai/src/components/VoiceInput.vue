<template>
  <q-page-sticky
    position="bottom-right"
    :offset="[18, 18]"
    @touchstart.prevent="handleTouchStart"
    @touchend.prevent="handleTouchEnd"
    @mousedown="recordAudio"
    @mouseup="stopAudio"
  >
    <q-btn
      fab
      id="recordButton"
      :color="recording ? 'secondary' : 'primary'"
      :loading="recording"
      :icon="recordIcon"
    />
  </q-page-sticky>
</template>

<script setup lang="ts">
/**
 * VoiceInput Component
 *
 * A voice recording component that supports both default speech-to-text processing
 * and custom audio handling via props.
 *
 * Usage:
 * - Default: <VoiceInput @record-available="handleText" />
 * - Custom: <VoiceInput :custom-handler="handleAudioBlob" />
 *
 * @emits record-available - Emitted when text is available (default mode only)
 * @prop customHandler - Optional custom function to handle audio blobs
 */
import { ref } from 'vue';
import { speechToText } from './api/tts';

/**
 * Props for VoiceInput component
 */
interface Props {
  /**
   * Custom handler function for processing audio blobs.
   * If provided, this will be called instead of the default speech-to-text processing.
   * The function receives the audio blob and should return a Promise.
   */
  customHandler?: (blob: Blob) => Promise<void>;
}

const props = withDefaults(defineProps<Props>(), {
  customHandler: undefined,
});

const emit = defineEmits<{
  'record-available': [text: string];
}>();

var audioRecorder: MediaRecorder;
const recording = ref(false);
const recordIcon = ref('perm_camera_mic');
const isMobile = ref(false);

// Check if device is mobile
if ('ontouchstart' in window || navigator.maxTouchPoints > 0) {
  isMobile.value = true;
}

async function requestAudioDevice() {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({
      audio: {
        sampleRate: 48000,
        channelCount: 1,
        echoCancellation: true,
        noiseSuppression: true,
        autoGainControl: true,
      },
    });

    // Configure MediaRecorder with Opus codec for optimal compression
    const options: MediaRecorderOptions = {};

    // Try different Opus MIME types in order of preference
    const opusTypes = [
      'audio/ogg; codecs=opus',
      'audio/webm; codecs=opus',
      'audio/ogg',
      'audio/webm',
    ];

    for (const mimeType of opusTypes) {
      if (MediaRecorder.isTypeSupported(mimeType)) {
        options.mimeType = mimeType;
        console.log(`Using MIME type: ${mimeType}`);
        break;
      }
    }

    // Set bitrate for compression (32kbps for voice is usually sufficient)
    if (options.mimeType) {
      options.audioBitsPerSecond = 32000;
    }

    audioRecorder = new MediaRecorder(stream, options);
    audioRecorder.ondataavailable = handleUserStream;
    recordIcon.value = 'mic';
    return true;
  } catch (error) {
    console.error('Error accessing microphone:', error);
    recordIcon.value = 'mic_off';
    return false;
  }
}

async function recordAudio() {
  if (!audioRecorder) {
    const success = await requestAudioDevice();
    if (!success) return;
  }

  try {
    console.log('recording.');
    recording.value = true;
    audioRecorder.start();
  } catch (error) {
    console.error('Error starting recording:', error);
    recording.value = false;
  }
}

function stopAudio() {
  if (audioRecorder && audioRecorder.state === 'recording') {
    console.log('end recording.');
    audioRecorder.stop();
  }
}

async function handleTouchStart(event: TouchEvent) {
  event.preventDefault();
  if (isMobile.value) {
    await recordAudio();
  }
}

function handleTouchEnd(event: TouchEvent) {
  event.preventDefault();
  if (isMobile.value) {
    stopAudio();
  }
}

async function handleUserStream(event: BlobEvent) {
  console.log('Audio data available.');

  try {
    if (props.customHandler) {
      await props.customHandler(event.data);
    } else {
      const text = await speechToText(event.data);
      emit('record-available', text);
    }
  } catch (error) {
    console.error('Error processing audio:', error);
  } finally {
    recording.value = false;
  }
}
</script>
