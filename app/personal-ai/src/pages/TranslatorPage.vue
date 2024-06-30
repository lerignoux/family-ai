<script setup lang="ts">
import { ref } from 'vue';
import { translate, textToSpeech, speechToText } from '../components/API';
import { playAudio } from '../components/utils';

const userInput = ref('Who are you');
const aiTranslation = ref('');
const model = ref('mistral:7b');
const models = ref([
  { label: 'Mistral', value: 'mistral:7b' },
  { label: 'Gemma', value: 'gemma:7b' },
  { label: 'Phi', value: 'phi' },
  { label: 'Lamma2 (Uncensonred)', value: 'llama2-uncensored:7b' },
]);
const language = ref('English');
const languages = ref([
  { label: 'English', value: 'en' },
  { label: 'French', value: 'fr' },
  { label: 'Chinese', value: 'zh' },
  { label: 'Spanish', value: 'es' },
  { label: 'Japanese', value: 'jp' },
]);
const autoRead = ref(true);

var audioRecorder: MediaRecorder;
var audioDevice = navigator.mediaDevices.getUserMedia({ audio: true });
audioDevice.then((stream) => {
  audioRecorder = new MediaRecorder(stream);
  audioRecorder.ondataavailable = (event: BlobEvent) => {
    console.log('Audio data available.');
    speechToText(event.data, handleSpeechToText);
  };
});

function recordAudio() {
  audioRecorder.start();
}

function stopAudio() {
  audioRecorder.stop();
}

function handleAiAnswer(response: string) {
  console.log(`Ai answered "${response}"`);
  aiTranslation.value = response;
  if (autoRead.value) {
    textToSpeech(response, playAudio);
  }
}

function translate(text: string, language: string, model: string) {
  translate(text, language, handleAiAnswer);
}

function translateInput() {
  translate(userInput.value, language.value, model.value);
}

function handleSpeechToText(text: string) {
  userInput.value = text;
  translate(text, language.value, model.value);
}
</script>

<template>
  <div class="translator">
    <div class="translate-options">
      <q-select
        standout
        v-model="model"
        emit-value
        :options="models"
        dense
        label="Model:"
      >
        <template v-slot:append>
          <q-avatar>
            <img src="ai_logo.png" />
          </q-avatar>
        </template>
      </q-select>
      <q-select
        standout
        v-model="language"
        emit-value
        :options="languages"
        dense
        label="Language:"
      >
        <template v-slot:append>
          <q-avatar>
            <img src="ai_logo.png" />
          </q-avatar>
        </template>
      </q-select>
      <q-checkbox
        left-label
        v-model="autoRead"
        checked-icon="mic"
        unchecked-icon="keyboard"
        label="Auto play audio"
        indeterminate-icon="help"
      />
    </div>

    <div class="translate">
      <div class="q-pa-md" style="max-width: 600px">
        <q-input
          v-model="userInput"
          v-on:keyup.enter="translateInput"
          filled
          type="textarea"
          hint="Your input"
        />
      </div>
      <div class="translate-actions">
        <div class="chat-action" @mousedown="recordAudio" @mouseup="stopAudio">
          <q-btn id="recordButton" round color="primary" icon="mic" size="xl" />
        </div>
        <q-btn
          class="translate-action"
          @click="translateInput"
          id="queryButton"
          round
          color="primary"
          icon="forward"
          size="xl"
        />
      </div>
      <div class="q-pa-md" style="max-width: 600px">
        <q-input
          v-model="aiTranslation"
          filled
          type="textarea"
          hint="Ai translation"
          readonly
        />
      </div>
    </div>
  </div>
</template>

<style>
.translator {
  width: 80%;
  height: 100%;
  margin-left: 10%;
  margin-right: 10%;
  display: flex;
  flex-direction: column;
}

.translate-options {
  display: flex;
  flex-direction: row;
  align-items: center;
  flex-wrap: no-wrap;
  justify-content: space-around;
  gap: 20px;
}

.translate-actions {
  display: flex;
  flex-direction: column;
  align-items: center;
  flex-wrap: no-wrap;
  justify-content: space-around;
  gap: 20px;
}

.translate {
  padding: 10px;
  display: flex;
  flex-direction: row;
  flex-wrap: no-wrap;
  align-items: center;
  justify-content: center;

  text-area {
    background-color: $grey-5;
    min-width: 50%;
    min-height: 50%;
  }
}
</style>
