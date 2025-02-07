<script setup lang="ts">
import { inject, ref } from 'vue';
import { translateText } from '../components/API';
import voiceInput from '../components/VoiceInput.vue';

const bus = inject<any>('bus');
const userInput = ref('Who are you');
const aiTranslation = ref('');
const language_src = ref({ label: 'English', value: 'en' });
const language_dst = ref({ label: 'French', value: 'fr' });
const languages = ref([
  { label: 'English', value: 'en' },
  { label: 'French', value: 'fr' },
  { label: 'Chinese', value: 'zh' },
  { label: 'Spanish', value: 'es' },
  { label: 'Japanese', value: 'jp' },
]);
const querying = ref(false);

async function recordCallback(text: string) {
  userInput.value = text;
  handleUserInput();
}

async function handleUserInput() {
  querying.value = true;
  await handleUserQuery(userInput.value);
}

async function handleUserQuery(query: string) {
  const translated = await translateText(
    query,
    language_src.value.value,
    language_dst.value.value
  );
  aiTranslation.value = translated;
  querying.value = false;
  bus.emit('read-text', translated);
}
</script>

<template>
  <div class="translator col wrap justify-start items-center">
    <div class="translate-options row items-start wrap">
      <div class="col-grow-xs col-md">
        <q-select
          standout="bg-grey-9 text-white"
          dark
          text-color="white"
          v-model="language_src"
          :options="languages"
          label="From:"
        >
          <template v-slot:append>
            <q-avatar icon="mdi-translate" text-color="white" />
          </template>
        </q-select>
      </div>

      <div class="col-grow-xs col-md">
        <q-select
          standout="bg-grey-9 text-white"
          v-model="language_dst"
          :options="languages"
          label="To:"
        >
          <template v-slot:append>
            <q-avatar icon="mdi-translate" text-color="white" />
          </template>
        </q-select>
      </div>
    </div>

    <div class="translate row items-center wrap">
      <div class="translate-input col-grow">
        <q-input
          v-model="userInput"
          v-on:keyup.enter="handleUserInput"
          filled
          type="textarea"
          hint="Your input"
        />
      </div>

      <div class="translate-actions col-auto justify-start items-center">
        <q-btn
          class="translate-action"
          @click="handleUserInput"
          :loading="querying"
          :disable="querying"
          id="queryButton"
          round
          color="primary"
          icon="forward"
          size="l"
        />
      </div>

      <div class="translate-content col-grow">
        <q-input
          v-model="aiTranslation"
          filled
          type="textarea"
          hint="Ai translation"
          readonly
        />
      </div>
    </div>

    <voiceInput @record-available="recordCallback" />
  </div>
</template>

<style>
.translator {
  margin-left: 20px;
  margin-right: 20px;
  height: 100%;
}

.translate-options {
  gap: 20px;
  margin-bottom: 20px;
  .q-field__native span {
    color: white;
  }
}

.translate-actions {
  gap: 10px;
  .translate-action {
    margin-top: 10px;
    margin-bottom: 20px;
  }
}

.translate {
  gap: 20px;
  padding: 10px;
  display: flex;
  flex-direction: row;
  align-items: center;
  justify-content: center;
}

.translate-input {
  min-width: 200px;
}

.translate-content {
  min-width: 200px;
}
</style>
