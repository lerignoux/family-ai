<script setup lang="ts">
import { ref } from 'vue';
import { speechToText, textToText, textToSpeech } from '../components/API';
import { playAudio } from '../components/utils';

const userInput = ref('Who are you');
const model = ref('gemma:7b');
const models = ref([
  { label: 'Gemma', value: 'gemma:7b' },
  { label: 'Phi', value: 'phi' },
  { label: 'Lamma2 (Uncensonred)', value: 'llama2-uncensored:7b' },
  { label: 'Deep Seek', value: 'deepseek-llm:7b-chat-q8_0' },
]);
const chat = ref([
  {
    name: 'Ai',
    avatar: 'src/assets/assistant_head_small_black.png',
    status: 'sent',
    stamp: 'now',
    text: ['Hello what can I do for you ?'],
  },
]);
const autoRead = ref(true);
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
  recording.value = false;
  audioRecorder.stop();
}

async function handleUserStream(event: BlobEvent) {
  console.log('Audio data available.');
  const text = await speechToText(event.data);
  userInput.value = text;
  await handleUserQuery(text);
}

function handleUserInput() {
  querying.value = true;
  handleUserQuery(userInput.value);
}

async function handleUserQuery(query: string) {
  if (query == '') {
    console.log('Empty user query, skipping.');
  }
  console.log(query);
  chat.value.push({
    name: 'user',
    avatar: 'https://cdn.quasar.dev/img/avatar2.jpg',
    stamp: 'Now',
    text: [query],
    status: 'sending',
  });
  const response = await textToText(query, model.value);
  chat.value.push({
    name: 'Ai',
    avatar: 'src/assets/assistant_head_small_black.png',
    stamp: 'Now',
    text: [response],
    status: 'sent',
  });
  querying.value = false;
  userInput.value = '';
  if (autoRead.value) {
    const audio = await textToSpeech(response, 'en');
    playAudio(audio);
  }
}
</script>

<template>
  <div class="assistant">
    <div class="chat-options">
      <q-select
        standout
        v-model="model"
        emit-value
        :options="models"
        label="Model:"
      >
        <template v-slot:append>
          <q-avatar icon="mdi-data-matrix" text-color="white"/>
        </template>
      </q-select>
      <q-item tag="label" class="bg-grey-10" v-ripple>
        <q-checkbox
          left-label
          v-model="autoRead"
          checked-icon="mic"
          unchecked-icon="keyboard"
          label="Auto play audio"
          indeterminate-icon="help"
        />
      </q-item>
    </div>

    <div class="chat">
      <q-chat-message
        v-for="(msg, i) in chat"
        :name="msg.name"
        :avatar="msg.avatar"
        :stamp="msg.stamp"
        :sent="msg.status === 'sent'"
        :key="i"
        :text="msg.text"
        text-html
      >
      </q-chat-message>
    </div>

    <div class="chat-actions">
      <div
        class="chat-action"
        @touchstart="recordAudio"
        @touchend="stopAudio"
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
          size="xl"
        />
      </div>
      <q-input
        class="chat-box chat-action"
        outlined
        v-model="userInput"
        label="Query Ai"
        v-on:keyup.enter="handleUserInput"
      />
      <q-btn
        class="chat-action"
        @click="handleUserInput"
        :loading="querying"
        :disable="recording || querying"
        id="queryButton"
        round
        color="primary"
        icon="message"
        size="xl"
      />
    </div>
  </div>
</template>

<style>
.assistant {
  width: 80%;
  height: 100%;
  max-height: 100%;
  margin-left: 10%;
  margin-right: 10%;
  display: flex;
  flex-direction: column;
  padding: 6px;
}

.chat-options {
  display: flex;
  flex-direction: row;
  align-items: center;
  flex-wrap: no-wrap;
  justify-content: space-around;
  gap: 20px;
}

.chat-actions {
  display: flex;
  flex-direction: row;
  align-items: center;
  flex-wrap: no-wrap;
  justify-content: space-around;
  gap: 20px;
  height: 72px;
}

.chat {
  display: flex;
  flex-direction: column;
  padding: 10px;
  flex-grow: 1;
  max-height: 50%;
  overflow-y: auto;
}

.chat-box {
  width: 100%;
  min-width: 200px;
}
</style>
