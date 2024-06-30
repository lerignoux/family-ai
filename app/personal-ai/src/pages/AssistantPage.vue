<script setup lang="ts">
import { ref } from 'vue';
import { queryAi, textToSpeech, speechToText } from '../components/API';
import { playAudio } from '../components/utils';

const userInput = ref('Who are you');
const model = ref('gemma:7b');
const models = ref([
  { label: 'Gemma', value: 'gemma:7b' },
  { label: 'Phi', value: 'phi' },
  { label: 'Lamma2 (Uncensonred)', value: 'llama2-uncensored:7b' },
]);
const chat = ref([
  {
    name: 'Ai',
    avatar: 'ai.png',
    status: 'sent',
    stamp: 'now',
    text: ['Hello what can I do for you ?'],
  },
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
  chat.value.push({
    name: 'Ai',
    avatar: 'ai.png',
    stamp: 'Now',
    text: [response],
    status: 'sent',
  });
  if (autoRead.value) {
    textToSpeech(response, playAudio);
  }
}

function handleUserQuery(query: string, model: string) {
  chat.value.push({
    name: 'user',
    avatar: 'https://cdn.quasar.dev/img/avatar2.jpg',
    stamp: 'Now',
    text: [query],
    status: 'sending',
  });
  queryAi(query, model, handleAiAnswer);
}

function handleSpeechToText(text: string) {
  handleUserQuery(text, model.value);
}

function handleUserInput() {
  handleUserQuery(userInput.value, model.value);
  userInput.value = '';
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
        dense
        label="Model:"
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
      <div class="chat-action" @mousedown="recordAudio" @mouseup="stopAudio">
        <q-btn id="recordButton" round color="primary" icon="mic" size="xl" />
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
  margin-left: 10%;
  margin-right: 10%;
  display: flex;
  flex-direction: column;
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
}

.chat {
  padding: 10px;
}

.chat-box {
  align-self: stretch;
  width: 100%;
}
</style>
