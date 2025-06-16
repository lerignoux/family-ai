<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { textToImage } from '../components/api/comfy';
import { getAvailableModels, type OllamaModel } from '../components/api/llm';
import voiceInput from '../components/VoiceInput.vue';
import pino from 'pino';

const logger = pino({
  level: 'info',
});

const userInput = ref('');
const model = ref({
  label: '',
  value: '',
  description: '',
  type: 'local',
});
const models = ref<{ label: string; value: string; description: string; type: string }[]>([]);
const loading = ref(true);
const imageUrl = ref('');
const querying = ref(false);
const recording = ref(false);

onMounted(async () => {
  try {
    const availableModels = await getAvailableModels();
    models.value = availableModels.map((m: OllamaModel) => ({
      label: m.name,
      value: m.value,
      description: m.description,
      type: m.type
    }));
    if (models.value.length > 0) {
      model.value = models.value[0];
    }
  } catch (error) {
    logger.error('Failed to fetch models:', error);
  } finally {
    loading.value = false;
  }
});

async function recordCallback(text: string) {
  userInput.value = text;
  handleUserInput();
}

function handleUserInput() {
  querying.value = true;
  handleUserQuery(userInput.value, model.value.value);
}

async function handleUserQuery(query: string, model: string) {
  logger.debug(`Requesting image creation using ${model}.`);
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
          :loading="loading"
          :disable="loading"
        >
          <template v-slot:append>
            <q-avatar icon="mdi-data-matrix" text-color="white" />
          </template>
        </q-select>
      </div>
    </div>

    <div class="painting-actions row items-center wrap">
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

    <voiceInput @record-available="recordCallback" />
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
  background-color: #212121;
}
</style>
