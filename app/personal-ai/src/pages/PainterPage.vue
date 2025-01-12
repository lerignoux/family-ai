<script setup lang="ts">
import { ref } from 'vue';
import { speechToText, queryImage } from '../components/API';

const userInput = ref('a cosmonaut riding a horse on the moon.');
const model = ref('epicrealismXL_v5Ultimate.safetensors');
const models = ref([
  { label: 'Epic Realism', value: 'epicrealismXL_v5Ultimate.safetensors' },
  { label: 'Flux Dev', value: 'flux1-dev-fp8_comfy.safetensors' },
]);
const imageUrl = ref('');

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

function handleAiAnswer(image: any) {
  console.log(`Ai generated an image: ${image}`);
  imageUrl.value = URL.createObjectURL(image);
}

async function handleUserQuery(query: string, model: string) {
  await queryImage(query, model, handleAiAnswer);
}

function handleSpeechToText(text: string) {
  userInput.value = text;
  handleUserQuery(text, model.value);
}

function handleUserInput() {
  handleUserQuery(userInput.value, model.value);
}
</script>

<template>
  <div class="painting">
    <div class="painting-options">
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
    </div>

    <div class="painting"></div>
    <div class="painting-actions">
      <div class="chat-action" @mousedown="recordAudio" @mouseup="stopAudio">
        <q-btn id="recordButton" round color="primary" icon="mic" size="xl" />
      </div>
      <q-input
        class="painting-box painting-action"
        outlined
        v-model="userInput"
        label="Query Ai"
        v-on:keyup.enter="handleUserInput"
      />
      <q-btn
        class="painting-action"
        @click="handleUserInput"
        id="queryButton"
        round
        color="primary"
        icon="message"
        size="xl"
      />
      <q-img
        :src="imageUrl"
        spinner-color="white"
        style="height: 512px; max-width: 512px"
      />
    </div>
  </div>
</template>

<style>
.painting {
  width: 80%;
  height: 100%;
  margin-left: 10%;
  margin-right: 10%;
  display: flex;
  flex-direction: column;
}

.painting-options {
  display: flex;
  flex-direction: row;
  align-items: center;
  flex-wrap: no-wrap;
  justify-content: space-around;
  gap: 20px;
}

.painting-actions {
  display: flex;
  flex-direction: row;
  align-items: center;
  flex-wrap: no-wrap;
  justify-content: space-around;
  gap: 20px;
}

.painting {
  padding: 10px;
}
</style>
