<template>
  <q-page-sticky
    position="bottom-right"
    :offset="[18, 18]"
    @touchstart="recordAudio"
    @touchend="stopAudio"
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

function requestAudioDevice() {
  var audioDevice = navigator.mediaDevices.getUserMedia({ audio: true });
  audioDevice.then((stream) => {
    audioRecorder = new MediaRecorder(stream);
    audioRecorder.ondataavailable = handleUserStream;
    recordIcon.value = 'mic';
  });
}

function recordAudio() {
  if (!audioRecorder) {
    requestAudioDevice();
    return;
  }
  console.log('recording.');
  recording.value = true;
  audioRecorder.start();
}

function stopAudio() {
  if (audioRecorder !== undefined) {
    console.log('end recording.');
    audioRecorder.stop();
  }
}

async function handleUserStream(event: BlobEvent) {
  console.log('Audio data available.');
  const text = await speechToText(event.data);
  emit('record-available', text);
  recording.value = false;
}
</script>
