<script setup lang="ts">
import { ref, onMounted, watch } from 'vue';
import { jsPDF } from 'jspdf';
import { textToImage } from '../components/api/comfy';
import {
  textToStory,
  getAvailableModels,
  type OllamaModel,
  type StoryResult,
  type StoryProgress,
} from '../components/api/llm';
import voiceInput from '../components/VoiceInput.vue';
import { saveUserSelection, getPageSelection } from '../utils/localStorage';
import { logger } from '../utils/logger';
import { useQuasar } from 'quasar';

interface StoryPage {
  text: string;
  illustration: string;
  pageNumber: number;
}
type StoryBook = StoryPage[];

const userInput = ref(
  'a little kid day in the wood playing with his animals friends.'
);

const model = ref('');
const models = ref<OllamaModel[]>([]);
const initializing = ref(true);
const loading = ref(0);
const modelIllustration = ref({
  label: 'EpicRealism XL',
  value: 'epicrealismXL_v5Ultimate.safetensors',
});
const storyLength = ref(4);
const styles = ref([
  {
    label: 'Oniric',
    illustrationTemplateSuffix:
      ', colorful and oniric painting style, beautiful, dream.',
  },
  {
    label: 'Oil painting',
    illustrationTemplateSuffix:
      ', oil painting style, heavy strokes, paint dripping, stunning masterpiece, Leonid Afremov details.',
  },
  {
    label: 'Chinese painting',
    illustrationTemplateSuffix:
      ', traditional chinese painting style, asian, chinese culture, beautiful, chinese ink.',
  },
  {
    label: 'Crayon drawing',
    illustrationTemplateSuffix:
      ', color crayon drawing style with pen visible mark, beautiful, colorful.',
  },
  {
    label: 'Scary',
    illustrationTemplatePrefix: 'A black and white scary painting of ',
  },
]);
const style = ref<{
  label: string;
  illustrationTemplateSuffix?: string;
  illustrationTemplatePrefix?: string;
}>({
  label: 'Oniric',
  illustrationTemplateSuffix:
    ', colorful and oniric painting style, beautiful, dream.',
});
const storyIndex = ref(0);
const formattedStory = ref<StoryBook>([]);

const querying = ref(false);

const storyText = ref<string>('');
const storyResult = ref<StoryResult | null>(null);
const illustrations = ref<Record<string, string>>({});
const error = ref<string | null>(null);
const $q = useQuasar();

const formatStoryText = (result: StoryResult): string => {
  const chapters = Object.entries(result)
    .filter(([key]) => key !== 'title')
    .map(([chapter, content]) => `${chapter}\n${content}`)
    .join('\n\n');
  return `${result.title}\n\n${chapters}`;
};

const generateIllustration = async (chapter: number, content: string) => {
  loading.value += 1;
  try {
    const prompt = `Create an illustration for the following chapter:\n\n${content}`;
    const result = await textToImage(
      prompt,
      modelIllustration.value.value,
      'simple'
    );
    if (result instanceof Blob) {
      const reader = new FileReader();
      reader.onload = () => {
        if (typeof reader.result === 'string') {
          illustrations.value[chapter] = reader.result;

          formattedStory.value.push({
            text: content,
            illustration: URL.createObjectURL(result),
            pageNumber: chapter,
          });
        }
      };
      reader.readAsDataURL(result);
    } else {
      illustrations.value[chapter] = result;
    }
  } catch (err) {
    logger.error(`Failed to generate illustration for ${chapter}:`, err);
    $q.notify({
      type: 'warning',
      message: `Failed to generate illustration for ${chapter}`,
      timeout: 6000,
    });
  } finally {
    loading.value -= 1;
  }
};

const generateStory = async () => {
  if (!userInput.value || !model.value) {
    $q.notify({
      type: 'negative',
      message: 'Please enter a prompt and select a model',
      timeout: 6000,
    });
    return;
  }

  loading.value += 1;
  storyText.value = '';
  storyResult.value = null;
  illustrations.value = {};
  error.value = null;

  try {
    const result = await textToStory(
      userInput.value,
      model.value,
      storyLength.value,
      (progress: StoryProgress) => {
        // Update progress
        if (progress.status === 'initializing') {
          storyText.value = 'Initializing story...';
        } else if (
          progress.status === 'generating_chapters' ||
          progress.status === 'complete'
        ) {
          storyText.value = `Polishing chapter ${progress.current_chapter} of ${progress.chapter_count}...`;
          if (progress.current_chapter) {
            var chapterName = `chapter ${progress.current_chapter - 1}`;
            if (progress.chapters && progress.chapters[chapterName])
              generateIllustration(
                progress.current_chapter,
                progress.chapters[chapterName]
              );
          }
          if (
            progress.status === 'complete' &&
            progress.chapters &&
            progress.title
          ) {
            const tempResult: StoryResult = {
              title: progress.title,
              ...progress.chapters,
            };
            storyText.value = formatStoryText(tempResult);
            storyResult.value = tempResult;
          }
        }
      }
    );

    storyText.value = formatStoryText(result);
    storyResult.value = result;
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'An error occurred';
    $q.notify({
      type: 'negative',
      message: error.value,
      timeout: 6000,
    });
  } finally {
    loading.value -= 1;
  }
};

async function recordCallback(text: string) {
  userInput.value = text;
  handleUserInput();
}

function handleUserInput() {
  querying.value = true;
  generateStory();
}

function capitalize(text: string) {
  return String(text).charAt(0).toUpperCase() + String(text).slice(1);
}

async function saveStoryPdf() {
  // Default export is a4 paper, portrait, using millimeters for units
  const doc = new jsPDF();

  const titleOptions = {
    maxWidth: 160,
  };

  const textOptions = {
    maxWidth: 160,
  };

  doc.addImage('src/assets/assistant_head_black.png', 'PNG', 84, 24, 40, 40);
  doc.setTextColor(0.8, 0.3, 0.3);
  doc.setFontSize(24);
  doc.setFont('undefined', 'bold');
  doc.text(capitalize(userInput.value), 24, 80, titleOptions);

  doc.setFont('undefined', 'undefined');
  doc.setFontSize(18);
  doc.text('Story created by', 24, 100, titleOptions);
  doc.setTextColor('#3333ff');
  doc.textWithLink('Family Ai', 67, 100, {
    url: 'https://github.com/lerignoux/family-ai',
  });
  doc.setTextColor(0.0);
  doc.text('assistant.', 98, 100, titleOptions);
  doc.setFontSize(16);
  doc.text(`* Text generated using ${model.value}`, 26, 110, titleOptions);
  doc.text(
    `* Illustrations generated using ${modelIllustration.value.label}`,
    26,
    120,
    titleOptions
  );

  doc.setTextColor(0.0);
  doc.setFontSize(16);
  formattedStory.value.forEach((page: StoryPage) => {
    doc.addPage();
    doc.text(page.text, 24, 200, textOptions);
    doc.addImage(page.illustration, 'PNG', 24, 24, 160, 160);
  });
  doc.save('personal_ai_story.pdf');
}

onMounted(async () => {
  try {
    const availableModels = await getAvailableModels();
    models.value = availableModels;

    // Load saved selections
    const savedSelections = getPageSelection('storyTeller');

    // Load saved model selection
    if (
      savedSelections.model &&
      availableModels.some((m) => m.value === savedSelections.model)
    ) {
      model.value = savedSelections.model;
    } else if (availableModels.length > 0) {
      model.value = availableModels[0].value;
    }

    // Load saved story length
    if (
      savedSelections.storyLength &&
      savedSelections.storyLength >= 1 &&
      savedSelections.storyLength <= 10
    ) {
      storyLength.value = savedSelections.storyLength;
    }

    // Load saved style
    if (savedSelections.style) {
      const savedStyle = styles.value.find(
        (s) => s.label === savedSelections.style.label
      );
      if (savedStyle) {
        style.value = savedStyle;
      }
    }
  } catch (error) {
    logger.error('Failed to fetch available models:', error);
    $q.notify({
      type: 'negative',
      message: 'Failed to fetch available models',
      timeout: 6000,
    });
  } finally {
    initializing.value = false;
  }
});

// Watch for changes and save to localStorage
watch(model, (newModel) => {
  if (newModel) {
    saveUserSelection('storyTeller', 'model', newModel);
  }
});

watch(storyLength, (newLength) => {
  if (newLength >= 1 && newLength <= 10) {
    saveUserSelection('storyTeller', 'storyLength', newLength);
  }
});

watch(
  style,
  (newStyle) => {
    if (newStyle) {
      saveUserSelection('storyTeller', 'style', newStyle);
    }
  },
  { deep: true }
);
</script>

<template>
  <div class="story col wrap justify-start items-center">
    <div class="story-options row items-start wrap">
      <div class="col-grow-xs col-md">
        <q-select
          standout="bg-grey-9 text-white"
          dark
          text-color="white"
          v-model="style"
          emit-value
          :options="styles"
          label="Style:"
        >
          <template v-slot:append>
            <q-avatar icon="style" text-color="white" />
          </template>
        </q-select>
      </div>
      <div class="col-12 col-md-6">
        <q-select
          standout="bg-grey-9 text-white"
          dark
          text-color="white"
          v-model="model"
          :options="models"
          :option-label="(model) => model.name"
          :option-value="(model) => model.value"
          label="Model"
          :loading="initializing"
          :disable="initializing"
          class="q-mb-md"
          emit-value
          map-options
        >
          <template v-slot:append>
            <q-avatar icon="mdi-data-matrix" text-color="white" />
          </template>
        </q-select>
      </div>
      <div class="col-grow-s col-md">
        <q-input
          v-model.number="storyLength"
          type="number"
          standout="bg-grey-9 text-white"
          label="Number of Chapters"
          :min="1"
          :max="10"
          :disable="initializing"
        />
      </div>
    </div>
    <div class="story-actions row items-center wrap">
      <div class="col-grow-l col-md">
        <q-input
          class="story-input"
          outlined
          v-model="userInput"
          label="Create a story about:"
          v-on:keyup.enter="handleUserInput"
        />
      </div>
      <div class="col-xxs">
        <q-btn
          color="primary"
          label="Generate Story"
          @click="generateStory"
          :loading="loading > 0"
          :disable="loading > 0"
        />
      </div>
    </div>

    <div class="story-content row items-center">
      <div class="col">
        <q-responsive :ratio="2">
          <q-carousel
            v-model="storyIndex"
            transition-prev="slide-right"
            transition-next="slide-left"
            animated
            navigation
            control-color="primary"
            swipeable
            padding
            class="shadow-2"
          >
            <q-carousel-slide
              v-for="(storyPage, index) in formattedStory"
              :key="index"
              :name="index"
              class="column wrap"
              draggable="false"
            >
              <q-img
                style="width: 45%; min-width: 150px"
                class="rounded-borders full-height"
                src="src/assets/page-background.png"
              >
                <div
                  class="absolute-full text-subtitle2 flex flex-center;"
                  style="overflow-y: scroll"
                >
                  <div
                    class="story-text"
                    style="min-height: 150px; min-width: 150px"
                  >
                    {{ storyPage.text }}
                  </div>
                </div>
              </q-img>
              <q-img
                style="width: 45%; min-width: 150px"
                class="rounded-borders full-height"
                :src="storyPage.illustration"
              >
              </q-img>
            </q-carousel-slide>
            <template v-slot:navigation-icon="{ onClick, index }">
              <q-btn @click="onClick">
                <q-avatar size="56px" square>
                  <img :src="formattedStory[index].illustration" />
                </q-avatar>
              </q-btn>
            </template>
          </q-carousel>
        </q-responsive>
      </div>
    </div>
    <div class="pdf-download">
      <q-btn
        class="download-pdf"
        color="primary"
        icon="mdi-file-download"
        @click="saveStoryPdf"
        :disable="querying || formattedStory.length == 0"
        padding="none"
      />
      <q-tooltip> Download story PDF </q-tooltip>
    </div>
    <voiceInput @record-available="recordCallback" />
  </div>
</template>

<style>
.story {
  margin-left: 20px;
  margin-right: 20px;
  height: 100%;
}

.story-options {
  gap: 20px;
  margin-bottom: 20px;
  .q-field__native span {
    color: white;
  }
}

.story-actions {
  gap: 10px;
  margin-bottom: 10px;
}

.story-input {
  min-width: 100px;
}

.download-pdf {
  min-width: 98px;
  font-size: 15px;
}

.story-content {
  width: 100%;
  min-width: 400px;
}

.story-text {
  color: black;
}

.pdf-download {
  position: relative;
  margin-top: -50%;
  float: right;
}
</style>
