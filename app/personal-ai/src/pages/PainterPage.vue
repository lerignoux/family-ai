<script setup lang="ts">
import { ref } from 'vue';
import { speechToText, textToImage } from '../components/API';

const userInput = ref('a cosmonaut riding a horse on the moon.');
const model = ref({
  label: 'Epic Realism',
  value: 'epicrealismXL_v5Ultimate.safetensors',
});
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
  await handleUserQuery(text, model.value.value);
}

function handleUserInput() {
  querying.value = true;
  handleUserQuery(userInput.value, model.value.value);
}

async function handleUserQuery(query: string, model: string) {
  const image = await textToImage(query, model);
  querying.value = false;
  imageUrl.value = URL.createObjectURL(image);
}
</script>

<template>
  <div class="painting col wrap justify-start items-center">
    <div class="painting-options row items-start wrap">
      <div class="col-grow-xs col-md">
        <q-select
          v-model="model"
          standout="bg-grey-9 text-white"
          dark
          text-color="white"
          :options="models"
          label="Model:"
        >
          <template v-slot:append>
            <q-avatar icon="mdi-data-matrix" text-color="white" />
          </template>
        </q-select>
      </div>
    </div>

    <div class="painting-actions row items-center wrap">
      <div
        class="painting-action col-auto"
        @mousedown="recordAudio"
        @mouseup="stopAudio"
      >
        <q-btn
          id="recordButton"
          round
          :color="recording ? 'secondary' : 'primary'"
          :loading="querying"
          :disable="querying && !recording"
          icon="mic"
          size="l"
        />
      </div>

      <div class="painting-input col-grow">
        <q-input
          class="painting-box painting-action"
          outlined
          v-model="userInput"
          label="Create an image of:"
          v-on:keyup.enter="handleUserInput"
        />
      </div>

      <div class="col-auto">
        <q-btn
          class="painting-action"
          @click="handleUserInput"
          :loading="querying"
          :disable="recording || querying"
          id="queryButton"
          round
          color="primary"
          icon="message"
          size="l"
        />
      </div>

      <div class="painting-result col-grow">
        <q-responsive :ratio="1" style="min-height: 200px; min-width: 200px">
          <q-img :src="imageUrl" spinner-color="white" />
        </q-responsive>
      </div>
    </div>
  </div>
</template>

<style>
.painting {
  margin-left: 20px;
  margin-right: 20px;
  height: 100%;
}

.painting-options {
  gap: 20px;
  margin-bottom: 20px;
  .q-field__native span {
    color: white;
  }
}

.painting-input {
  min-width: 100px;
}

.painting-actions {
  gap: 10px;
  margin-bottom: 10px;
}

.painting-result {
}
</style>
