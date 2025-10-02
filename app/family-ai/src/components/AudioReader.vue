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
  <q-btn
    :loading="isPlaying"
    :disable="isPlaying || !lastAudio"
    @click="replayAudio"
    round
    color="primary"
    icon="replay"
    size="sm"
  >
    <q-tooltip>Replay audio</q-tooltip>
  </q-btn>
</template>

<script setup lang="ts">
import { inject, ref } from 'vue';
import { textToSpeech } from './api/tts';

const autoRead = ref(true);
const isPlaying = ref(false);
const lastAudio = ref<Blob | null>(null);
const lastLanguage = ref('');
const bus = inject<any>('bus');

function playAudio(audioBlob: Blob) {
  const objectURL = URL.createObjectURL(audioBlob);
  const newAudioURL = objectURL;
  const w = new Audio();
  w.src = newAudioURL;
  w.play();
}

function replayAudio() {
  if (isPlaying.value) return;
  if (!lastAudio.value) return;
  playAudio(lastAudio.value);
}

async function readText(text: string, language = 'en') {
  const audio = await textToSpeech(text, language);
  lastAudio.value = audio;
  lastLanguage.value = language;
  playAudio(audio);
}

bus.on('read-text', (text: string, language = 'en') => {
  console.log(`read-text event fetched: ${text} in ${language}`);
  if (autoRead.value) {
    readText(text, language);
  }
});
</script>
