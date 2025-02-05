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
      icon="mic"
    />
  </q-page-sticky>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { speechToText } from '../components/API';

const emit = defineEmits<{
  'record-available': [text: string];
}>();

var audioRecorder: MediaRecorder;

var audioDevice = navigator.mediaDevices.getUserMedia({ audio: true });
audioDevice.then((stream) => {
  audioRecorder = new MediaRecorder(stream);
  audioRecorder.ondataavailable = handleUserStream;
});
const recording = ref(false);

function recordAudio() {
  console.log('recording.');
  recording.value = true;
  audioRecorder.start();
}

function stopAudio() {
  console.log('end recording.');
  audioRecorder.stop();
}

async function handleUserStream(event: BlobEvent) {
  console.log('Audio data available.');
  const text = await speechToText(event.data);
  emit('record-available', text);
  recording.value = false;
}
</script>
