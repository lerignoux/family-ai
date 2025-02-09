<script setup lang="ts">
import { ref } from 'vue';
import { jsPDF } from 'jspdf';
import { textToImage } from '../components/api/comfy';
import { textToStory } from '../components/api/llm';
import voiceInput from '../components/VoiceInput.vue';
import pino from 'pino';

const logger = pino({
  level: 'info',
});

interface StoryPage {
  text: string;
  illustration: string;
  pageNumber: number;
}
type StoryBook = StoryPage[];

const userInput = ref(
  'a little kid day in the wood playing with his animals friends.'
);

const model = ref({
  label: 'Mistral',
  value: 'mistral',
  description: 'European Mistral model.',
  type: 'local',
});
const models = ref([
  {
    label: 'Mistral',
    value: 'mistral',
    description: 'European Mistral model.',
    type: 'local',
  },
  {
    label: 'Mistral API',
    value: 'mistral-large-latest',
    description: 'European Mistral model, non free.',
    type: 'api',
  },
  {
    label: 'Llama 3.1',
    value: 'llama3.1',
    description: '"Open source" llama 3.1 model created by meta.',
    type: 'local',
  },
]);
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
const style = ref({
  label: 'Oniric',
  illustrationTemplatePrefix:
    ', colorful and oniric painting style, beautiful, dream.',
  illustrationTemplateSuffix: undefined,
});
const rawStory = ref('');
const storyIndex = ref(0);
const formattedStory = ref<StoryBook>([]);

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
    logger.debug('Empty user query, skipping.');
  }

  formattedStory.value = [];
  storyIndex.value = 0;

  const story = await textToStory(query, model.value.value, storyLength.value);
  if (story == undefined) {
    logger.warn('Empty story returned.');
    querying.value = false;
    return;
  }
  if (story.title != undefined) {
    const pageCount = storyLength.value;
    var i: number;
    for (i = 0; i < pageCount; i++) {
      const chapterKey = `chapter ${i}`;
      var illustrationRequest = story[chapterKey];
      if (style.value.illustrationTemplatePrefix !== undefined) {
        illustrationRequest =
          style.value.illustrationTemplatePrefix + illustrationRequest;
      }
      if (style.value.illustrationTemplateSuffix !== undefined) {
        illustrationRequest =
          illustrationRequest + style.value.illustrationTemplateSuffix;
      }
      const pageIllustration = await textToImage(
        illustrationRequest,
        modelIllustration.value.value
      );
      formattedStory.value.push({
        text: story[chapterKey],
        illustration: URL.createObjectURL(pageIllustration),
        pageNumber: i,
      });
    }
  } else {
    rawStory.value = story;
    logger.debug('Cutting the raw story in pages;');

    let index = 0;
    for (const pageContent of story.split('.')) {
      await formatRawPageContent(pageContent, index);
      index += 1;
    }
  }
  querying.value = false;
}

async function formatRawPageContent(pageContent: string, pageNumber: number) {
  if (pageContent.trim() == '' || pageContent.trim().length < 12) {
    logger.warn('Empty page content, skipping.');
    return;
  } else {
    logger.info(`Generating page content for "${pageContent}"`);
  }

  var illustrationRequest = pageContent;
  if (style.value.illustrationTemplatePrefix !== undefined) {
    illustrationRequest =
      style.value.illustrationTemplatePrefix + illustrationRequest;
  }
  if (style.value.illustrationTemplateSuffix !== undefined) {
    illustrationRequest =
      illustrationRequest + style.value.illustrationTemplateSuffix;
  }

  const pageIllustration = await textToImage(
    illustrationRequest,
    modelIllustration.value.value
  );
  formattedStory.value.push({
    text: pageContent,
    illustration: URL.createObjectURL(pageIllustration),
    pageNumber: pageNumber,
  });
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
  doc.text(
    `* Text generated using ${model.value.label}`,
    26,
    110,
    titleOptions
  );
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

      <div class="col-grow-xs col-md">
        <q-select
          standout="bg-grey-9 text-white"
          v-model="model"
          :options="models"
          label="Story creation model:"
        >
          <template v-slot:append>
            <q-avatar icon="style" text-color="white" />
          </template>
        </q-select>
      </div>

      <div class="col-grow-s col-md">
        <q-input
          v-model.number="storyLength"
          type="number"
          standout="bg-grey-9 text-white"
          label="story length"
        />
      </div>
    </div>

    <div class="story-actions row items-center wrap">
      <div class="story-input col-grow">
        <q-input
          class="story-input"
          outlined
          v-model="userInput"
          label="Create a story about:"
          v-on:keyup.enter="handleUserInput"
        />
      </div>

      <div class="col-auto">
        <q-btn
          class="story-action"
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
      </div>
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
