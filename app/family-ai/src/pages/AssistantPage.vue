<script setup lang="ts">
import { inject, ref } from 'vue';
import { textToText } from '../components/api/llm';
import voiceInput from '../components/VoiceInput.vue';
import pino from 'pino';

const logger = pino({
  level: 'info',
});

const bus = inject<any>('bus');
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
const querying = ref(false);

async function recordCallback(text: string) {
  userInput.value = text;
  handleUserInput();
}

function handleUserInput() {
  querying.value = true;
  handleUserQuery(userInput.value);
}

async function handleUserQuery(query: string) {
  if (query == '') {
    logger.warn('Empty user query, skipping request.');
  }
  logger.warn(`Asking ${model.value} Ai for ${query}.`);
  chat.value.push({
    name: 'user',
    avatar: 'https://cdn.quasar.dev/img/avatar2.jpg',
    stamp: 'Now',
    text: [query],
    status: 'sending',
  });
  try {
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
    bus.emit('read-text', response);
  } catch (e) {
    querying.value = false;
    throw e;
  }
}
</script>

<template>
  <div class="assistant col wrap justify-start items-center">
    <div class="chat-options row items-start wrap">
      <div class="col-grow-xs col-md">
        <q-select
          standout="bg-grey-9 text-white"
          dark
          text-color="white"
          v-model="model"
          emit-value
          :options="models"
          label="Model:"
        >
          <template v-slot:append>
            <q-avatar icon="mdi-data-matrix" text-color="white" />
          </template>
        </q-select>
      </div>
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

    <div class="chat-actions row items-center wrap">
      <div class="chat-input col-grow">
        <q-input
          class="chat-box chat-action"
          outlined
          v-model="userInput"
          label="Query Ai"
          v-on:keyup.enter="handleUserInput"
        />
      </div>

      <div class="col-auto">
        <q-btn
          class="chat-action"
          @click="handleUserInput"
          :loading="querying"
          :disable="querying"
          id="queryButton"
          round
          color="primary"
          icon="message"
          size="l"
        />
      </div>

      <voiceInput @record-available="recordCallback" />
    </div>
  </div>
</template>

<style>
.assistant {
  margin-left: 20px;
  margin-right: 20px;
  height: 100%;
}

.chat-options {
  gap: 20px;
  margin-bottom: 20px;
  .q-field__native span {
    color: white;
  }
}

.chat-actions {
  gap: 10px;
  margin-bottom: 10px;
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
