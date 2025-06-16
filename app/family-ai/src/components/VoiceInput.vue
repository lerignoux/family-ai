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
import { ref } from 'vue';
import { speechToText } from './api/tts';

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
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    audioRecorder = new MediaRecorder(stream);
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
    const text = await speechToText(event.data);
    emit('record-available', text);
  } catch (error) {
    console.error('Error processing audio:', error);
  } finally {
    recording.value = false;
  }
}
</script>
