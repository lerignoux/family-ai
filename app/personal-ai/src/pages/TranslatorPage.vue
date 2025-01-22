<script setup lang="ts">
import { ref } from 'vue';
import { translateText, textToSpeech, speechToText } from '../components/API';
import { playAudio } from '../components/utils';

const userInput = ref('Who are you');
const aiTranslation = ref('');
const language_src = ref('en');
const language_dst = ref('fr');
const languages = ref([
  { label: 'English', value: 'en' },
  { label: 'French', value: 'fr' },
  { label: 'Chinese', value: 'zh' },
  { label: 'Spanish', value: 'es' },
  { label: 'Japanese', value: 'jp' },
]);
const autoRead = ref(false);
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
  await handleUserQuery(text);
}

async function handleUserInput() {
  querying.value = true;
  await handleUserQuery(userInput.value);
}

async function handleUserQuery(query: string) {
  const translated = await translateText(
    query,
    language_src.value,
    language_dst.value
  );
  aiTranslation.value = translated;
  querying.value = false;
  if (autoRead.value) {
    let language = 'en';
    if (language_dst.value != 'en') {
      language = `${language_dst.value}-${language_dst.value}`;
    }
    const audio = await textToSpeech(translated, language);
    playAudio(audio);
  }
}
</script>

<template>
  <div class="translator">
    <div class="translate-options">
      <q-select
        standout
        v-model="language_src"
        emit-value
        :options="languages"
        dense
        label="From:"
      >
        <template v-slot:append>
          <q-avatar>
            <img src="ai_logo.png" />
          </q-avatar>
        </template>
      </q-select>
      <q-select
        standout
        v-model="language_dst"
        emit-value
        :options="languages"
        dense
        label="To:"
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
      <div class="q-pa-md translate-source" style="width: 400px">
        <q-input
          v-model="userInput"
          v-on:keyup.enter="handleUserInput"
          filled
          type="textarea"
          hint="Your input"
        />
      </div>

      <div class="translate-actions">
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
        <q-btn
          class="translate-action"
          @click="handleUserInput"
          :loading="querying"
          :disable="recording || querying"
          id="queryButton"
          round
          color="primary"
          icon="forward"
          size="xl"
        />
      </div>

      <div class="q-pa-md translate-result" style="width: 400px">
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
  align-items: center;
  justify-content: center;
}

.translate-source {
  min-width: 200px;
}

.translate-result {
  min-width: 200px;
}
</style>
