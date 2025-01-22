<script setup lang="ts">
import { ref } from 'vue';
import { speechToText, textToImage } from '../components/API';

const userInput = ref('a cosmonaut riding a horse on the moon.');
const model = ref('epicrealismXL_v5Ultimate.safetensors');
const models = ref([
  { label: 'Epic Realism', value: 'epicrealismXL_v5Ultimate.safetensors' },
  { label: 'Flux Dev', value: 'flux1-dev-fp8_comfy.safetensors' },
]);
const imageUrl = ref('');

const querying = ref(false);
const recording = ref(false);

var audioRecorder: MediaRecorder;
var audioDevice = navigator.mediaDevices.getUserMedia({ audio: true });
audioDevice.then((stream) => {
  audioRecorder = new MediaRecorder(stream);
  audioRecorder.ondataavailable = handleUserStream;
});

function recordAudio() {
  recording.value = true;
  querying.value = true;
  audioRecorder.start();
}

function stopAudio() {
  audioRecorder.stop();
  recording.value = false;
}

async function handleUserStream(event: BlobEvent) {
  console.log('Audio data available.');
  const text = await speechToText(event.data);
  userInput.value = text;
  await handleUserQuery(text, model.value);
}

function handleUserInput() {
  querying.value = true;
  handleUserQuery(userInput.value, model.value);
}

async function handleUserQuery(query: string, model: string) {
  const image = await textToImage(query, model);
  querying.value = false;
  imageUrl.value = URL.createObjectURL(image);
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

    <div class="painting-actions">
      <div class="chat-action" @mousedown="recordAudio" @mouseup="stopAudio">
        <q-btn
          id="recordButton"
          round
          :color="recording ? 'secondary' : 'primary'"
          :loading="querying"
          :disable="querying && !recording"
          icon="mic"
          size="xl"
        />
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
        :loading="querying"
        :disable="recording || querying"
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

.painting-box {
  align-self: stretch;
  width: 100%;
  min-width: 200px;
}
</style>
