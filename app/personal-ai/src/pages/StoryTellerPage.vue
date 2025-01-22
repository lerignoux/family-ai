<script setup lang="ts">
import { ref } from 'vue';
import { textToText, speechToText, textToImage } from '../components/API';

interface StoryPage {
  text: string;
  summary: string;
  illustration: string;
  pageNumber: number;
}
type StoryBook = StoryPage[];

const userInput = ref(
  'a little kid day in the wood playing with his animals friends.'
);
const promptTemplate = ref(
  'Please create a kid story of {pageCount} sentences around the following subject: '
);
const summaryTemplate = ref(
  'Please create a summary in a short sentence of the following text: '
);
const modelStory = ref('phi');
const modelIllustration = ref('epicrealismXL_v5Ultimate.safetensors');
const styles = ref([
  {
    label: 'Oniric',
    illustrationTemplate: 'An oniric and colorful painting of ',
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
const pageCount = ref(2);
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

  const request =
    promptTemplate.value.replace('{pageCount}', pageCount.value.toString()) +
    query;
  const story = await textToText(request, modelStory.value);
  rawStory.value = story;
  console.log('Cutting the story in pages;');

  let index = 0;
  for (const pageContent of story.split('.')) {
    await generatePageContent(pageContent, index);
    index += 1;
  }

  querying.value = false;
}

async function generatePageContent(pageContent: string, pageNumber: number) {
  if (pageContent.trim() == '' || pageContent.trim().length < 12) {
    console.log('Empty page content, skipping.');
    return;
  } else {
    console.log(`Generating page content for "${pageContent}"`);
  }

  const request = summaryTemplate.value + pageContent;
  const pageSummary = await textToText(request, modelStory.value);
  const illustrationRequest = style.value.illustrationTemplate + pageSummary;
  const pageIllustration = await textToImage(
    illustrationRequest,
    modelIllustration.value
  );
  formattedStory.value.push({
    text: pageContent,
    illustration: URL.createObjectURL(pageIllustration),
    pageNumber: pageNumber,
    summary: pageSummary,
  });
}
</script>

<template>
  <div class="story">
    <div class="story-options">
      <q-select
        standout
        v-model="style"
        emit-value
        :options="styles"
        dense
        label="Model:"
      >
        <template v-slot:append>
          <q-avatar>
            <img src="ai_logo.png" />
          </q-avatar>
        </template>
      </q-select>
    </div>

    <div class="story-actions">
      <div class="chat-action" @mousedown="recordAudio" @mouseup="stopAudio">
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
        class="painting-box painting-action"
        outlined
        v-model="userInput"
        label="Query Ai"
        v-on:keyup.enter="handleUserInput"
      />
      <q-btn
        class="painting-action"
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
        <div class="row fit justify-start items-center q-col-gutter no-wrap">
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
</template>

<style>
.story {
  width: 80%;
  height: 100%;
  margin-left: 10%;
  margin-right: 10%;
  display: flex;
  flex-direction: column;
}

.story-options {
  display: flex;
  flex-direction: row;
  align-items: center;
  flex-wrap: no-wrap;
  justify-content: space-around;
  gap: 20px;
}

.story-actions {
  display: flex;
  flex-direction: row;
  align-items: center;
  flex-wrap: no-wrap;
  justify-content: space-around;
  gap: 20px;
  margin: 12px;
}

.story-box {
  align-self: stretch;
  width: 100%;
  min-width: 200px;
}

.story-text {
  color: black;
  padding: 12px;
}
</style>
