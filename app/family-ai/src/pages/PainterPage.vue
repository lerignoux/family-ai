<script setup lang="ts">
import { ref, onMounted, watch } from 'vue';
import { textToImage } from '../components/api/comfy';
import { getAvailableModels, type ComfyModel } from '../components/api/comfy';
import voiceInput from '../components/VoiceInput.vue';
import { saveUserSelection, getPageSelection } from '../utils/localStorage';
import { logger } from '../utils/logger';

const userInput = ref('');
const model = ref('');
const models = ref<ComfyModel[]>([]);
const loading = ref(true);
const imageUrl = ref('');
const querying = ref(false);
const recording = ref(false);

onMounted(async () => {
  try {
    loading.value = true;
    const availableModels = await getAvailableModels();
    models.value = availableModels;

    // Load saved model selection
    const savedSelections = getPageSelection('painter');
    if (
      savedSelections.model &&
      availableModels.some((m) => m.value === savedSelections.model)
    ) {
      model.value = savedSelections.model;
    } else if (availableModels.length > 0) {
      model.value = availableModels[0].value;
    }
  } catch (error) {
    logger.error('Error loading models:', error);
  } finally {
    loading.value = false;
  }
});

// Watch for model changes and save to localStorage
watch(model, (newModel) => {
  if (newModel) {
    saveUserSelection('painter', 'model', newModel);
  }
});

async function recordCallback(text: string) {
  userInput.value = text;
  handleUserInput();
}

function handleUserInput() {
  querying.value = true;
  handleUserQuery(userInput.value, model.value);
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
          :options="models"
          :option-label="(model) => model.name"
          :option-value="(model) => model.value"
          label="Model"
          :loading="loading"
          :disable="loading"
          class="q-mb-md"
          emit-value
          map-options
        />
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
