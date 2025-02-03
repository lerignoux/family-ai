<script setup lang="ts">
import { ref } from 'vue';
import { textToStory, speechToText, textToImage } from '../components/API';

import { jsPDF } from 'jspdf';

interface StoryPage {
  text: string;
  illustration: string;
  pageNumber: number;
}
type StoryBook = StoryPage[];

const userInput = ref(
  'a little kid day in the wood playing with his animals friends.'
);

const autoRead = ref(true);
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
    illustrationTemplate: 'An oniric and colorful painting of ',
  },
  {
    label: 'Oil painting',
    illustrationTemplate:
      'oil painting, heavy strokes, paint dripping, stunning masterpiece, Leonid Afremov details of ',
  },
  {
    label: 'Chinese painting',
    illustrationTemplate:
      'Traditional chinese painting style asian chinese culture beautiful chinese ink of ',
  },
  {
    label: 'Scary',
    illustrationTemplate: 'A black and white scary painting of ',
  },
]);
const style = ref({
  label: 'Oniric',
  illustrationTemplate: 'An oniric and colorful painting of ',
});
const rawStory = ref('');
const storyIndex = ref(0);
const formattedStory = ref<StoryBook>([]);

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

function handleUserInput() {
  querying.value = true;
  handleUserQuery(userInput.value);
}

async function handleUserQuery(query: string) {
  if (query == '') {
    console.log('Empty user query, skipping.');
  }

  formattedStory.value = [];
  storyIndex.value = 0;

  const story = await textToStory(query, model.value.value, storyLength.value);
  if (story == undefined) {
    console.log('Empty story returned.');
    querying.value = false;
    return;
  }
  if (story.title != undefined) {
    const pageCount = storyLength.value;
    var i: number;
    for (i = 0; i < pageCount; i++) {
      const chapterKey = `chapter ${i}`;
      const illustrationRequest =
        style.value.illustrationTemplate + story[chapterKey];
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
    console.log('Cutting the raw story in pages;');

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
    console.log('Empty page content, skipping.');
    return;
  } else {
    console.log(`Generating page content for "${pageContent}"`);
  }

  const illustrationRequest = style.value.illustrationTemplate + pageContent;
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
  doc.textWithLink('personal AI', 67, 100, {
    url: 'https://github.com/lerignoux/personal-ai',
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

      <div class="col-grow-xs col-md">
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
    </div>

    <div class="story-actions row items-center wrap">
      <div class="col-auto" @mousedown="recordAudio" @mouseup="stopAudio">
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
          :disable="recording || querying"
          id="queryButton"
          round
          color="primary"
          icon="message"
          size="l"
        />
      </div>

      <div class="col-auto">
        <q-btn
          class="download-pdf"
          color="primary"
          icon="mdi-file-download"
          label="PDF"
          @click="saveStoryPdf"
          :disable="querying"
        />
      </div>
    </div>

    <div class="story-content row items-center">
      <div class="col">
        <q-carousel
          v-model="storyIndex"
          transition-prev="slide-right"
          transition-next="slide-left"
          animated
          navigation
          control-color="primary"
          swipeable
          padding
          arrows
          class="shadow-2"
        >
          <q-carousel-slide
            v-for="(storyPage, index) in formattedStory"
            :key="index"
            :name="index"
            class="column no-wrap"
            draggable="false"
          >
            <div
              class="row fit justify-start items-center q-col-gutter no-wrap"
            >
              <q-img
                class="rounded-borders full-height"
                ratio="1"
                src="src/assets/page-background.png"
              >
                <div class="absolute-full text-subtitle2 flex flex-center">
                  <div class="story-text">
                    {{ storyPage.text }}
                  </div>
                </div>
              </q-img>
              <q-img
                class="rounded-borders full-height"
                ratio="1/1"
                :src="storyPage.illustration"
              >
              </q-img>
            </div>
          </q-carousel-slide>
          <template v-slot:navigation-icon="{ onClick, index }">
            <q-btn @click="onClick">
              <q-avatar size="56px" square>
                <img :src="formattedStory[index].illustration" />
              </q-avatar>
            </q-btn>
          </template>
        </q-carousel>
      </div>
    </div>
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
  padding: 12px;
}
</style>
