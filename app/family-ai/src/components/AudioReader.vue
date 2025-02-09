<template>
  <q-item v-ripple>
    <q-checkbox
      left-label
      color="white"
      v-model="autoRead"
      checked-icon="volume_up"
      unchecked-icon="volume_off"
      indeterminate-icon="help"
    />
    <q-tooltip> Auto play audio after generation </q-tooltip>
  </q-item>
</template>

<script setup lang="ts">
import { inject, ref } from 'vue';
import { textToSpeech } from './api/tts';

const autoRead = ref(true);
const bus = inject<any>('bus');

function playAudio(audioBlob: Blob) {
  const objectURL = URL.createObjectURL(audioBlob);
  const newAudioURL = objectURL;
  const w = new Audio();
  w.src = newAudioURL;
  w.play();
}

async function readText(text: string, language = 'en') {
  if (language != 'en') {
    language = `${language}-${language}`;
  }
  const audio = await textToSpeech(text, language);
  playAudio(audio);
}

bus.on('read-text', (text: string) => {
  console.log('event fetched' + text);
  if (autoRead.value) {
    readText(text);
  }
});
</script>
