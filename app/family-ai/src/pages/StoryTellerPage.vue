<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue';
import { jsPDF } from 'jspdf';
import assistantHeadPng from '../assets/assistant_head_black.png';
import pageBackgroundPng from '../assets/page-background.png';
import { textToImage, freeComfyMemory } from '../components/api/comfy';
import ComfyClientManager from 'src/components/api/comfy/manager';

// Initialize the manager (if not already done)
ComfyClientManager.init(
  `${process.env.COMFY_URL}`,
  process.env.COMFY_CLIENT_ID || '',
  process.env.API_SCHEME
);
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
  /** jsPDF format for addImage; from Blob.type (ComfyUI may return JPEG). */
  pdfImageFormat: 'PNG' | 'JPEG' | 'WEBP';
  /** True until the chapter image has been generated. */
  illustrationPending?: boolean;
}
type StoryBook = StoryPage[];

function pdfImageFormatFromBlobType(blobType: string): 'PNG' | 'JPEG' | 'WEBP' {
  const t = blobType.toLowerCase();
  if (t.includes('jpeg') || t.includes('jpg')) return 'JPEG';
  if (t.includes('webp')) return 'WEBP';
  return 'PNG';
}

const userInput = ref(
  'a little kid day in the wood playing with his animals friends.'
);

const model = ref('');
const models = ref<OllamaModel[]>([]);
const initializing = ref(true);
const loading = ref(0);
const modelIllustration = ref({
  label: 'Flux 2 Klein',
  value: 'flux-2-klein-9b-fp8.safetensors',
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

const sortedFormattedStory = computed(() =>
  [...formattedStory.value].sort((a, b) => a.pageNumber - b.pageNumber)
);

const canSaveStoryPdf = computed(
  () =>
    sortedFormattedStory.value.length > 0 &&
    !sortedFormattedStory.value.some((p) => p.illustrationPending)
);

/** 1-based page numbers; avoids duplicate Comfy jobs when WS skips chapter steps. */
const illustrationJobsStarted = ref(new Set<number>());

/** Story batch: free VRAM once after LLM is done and all illustration jobs finished. */
const storyLlmFinished = ref(false);
const storyVramFreed = ref(false);
const pendingStoryIllustrations = ref(0);

const illustrationQueue = ref<{ chapter: number; content: string }[]>([]);
const isProcessingQueue = ref(false);

async function processIllustrationQueue() {
  if (isProcessingQueue.value) return;
  isProcessingQueue.value = true;
  while (illustrationQueue.value.length > 0) {
    const job = illustrationQueue.value.shift();
    if (job) {
      try {
        await generateIllustration(job.chapter, job.content);
      } catch (err) {
        console.error(
          `Failed to process illustration for chapter ${job.chapter}:`,
          err
        );
      }
    }
  }
  isProcessingQueue.value = false;
}

function maybeFreeComfyAfterStoryBatch(): void {
  if (!storyLlmFinished.value || storyVramFreed.value) return;
  if (pendingStoryIllustrations.value > 0) return;
  storyVramFreed.value = true;
  void freeComfyMemory().catch((e) => {
    logger.warn('freeComfyMemory after story batch failed:', e);
  });
}

function pageNumberFromChapterKey(chapterKey: string): number | null {
  const m = /^chapter (\d+)$/i.exec(chapterKey);
  if (!m) return null;
  return Number(m[1]) + 1;
}

/**
 * Add or update carousel pages as soon as chapter text arrives (before images).
 * Keeps one row per pageNumber; refreshes text if the backend sends revisions.
 */
function syncStoryPagesFromChapters(
  chapters: Record<string, string> | undefined
) {
  if (!chapters) return;
  for (const [chapterKey, text] of Object.entries(chapters)) {
    const pageNumber = pageNumberFromChapterKey(chapterKey);
    if (pageNumber === null) continue;
    const pages = formattedStory.value;
    const idx = pages.findIndex((p) => p.pageNumber === pageNumber);
    if (idx >= 0) {
      const prev = pages[idx];
      pages[idx] = {
        ...prev,
        text,
        ...(prev.illustrationPending
          ? {
              illustration: pageBackgroundPng,
              pdfImageFormat: 'PNG' as const,
              illustrationPending: true,
            }
          : {}),
      };
    } else {
      pages.push({
        text,
        illustration: pageBackgroundPng,
        pageNumber,
        pdfImageFormat: 'PNG',
        illustrationPending: true,
      });
    }
  }
  const sorted = [...formattedStory.value].sort(
    (a, b) => a.pageNumber - b.pageNumber
  );
  if (sorted.length > 0) {
    storyIndex.value = sorted.length - 1;
  }
}

function startIllustrationsFromProgress(progress: StoryProgress) {
  if (!progress.chapters) return;
  syncStoryPagesFromChapters(progress.chapters);
  const entries = Object.entries(progress.chapters).filter(([key]) =>
    /^chapter \d+$/i.test(key)
  );
  entries.sort(([a], [b]) => {
    const na = pageNumberFromChapterKey(a) ?? 0;
    const nb = pageNumberFromChapterKey(b) ?? 0;
    return na - nb;
  });
  entries.forEach(([chapterKey, text]) => {
    const pageNumber = pageNumberFromChapterKey(chapterKey);
    if (pageNumber === null) return;
    if (illustrationJobsStarted.value.has(pageNumber)) return;
    illustrationJobsStarted.value.add(pageNumber);
    illustrationQueue.value.push({ chapter: pageNumber, content: text });
  });
  processIllustrationQueue();
}

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
  pendingStoryIllustrations.value += 1;
  loading.value += 1;
  try {
    const s = style.value;
    const prompt = `${
      s.illustrationTemplatePrefix ?? ''
    }Create an illustration for the following chapter:\n\n${content}${
      s.illustrationTemplateSuffix ?? ''
    }`;
    const result = await textToImage(
      prompt,
      modelIllustration.value.value,
      'flux_2_klein',
      false
    );

    function applyIllustration(
      src: string,
      fmt: 'PNG' | 'JPEG' | 'WEBP'
    ): void {
      const idx = formattedStory.value.findIndex(
        (p) => p.pageNumber === chapter
      );
      if (idx >= 0) {
        const prev = formattedStory.value[idx];
        if (prev.illustration.startsWith('blob:')) {
          URL.revokeObjectURL(prev.illustration);
        }
        formattedStory.value[idx] = {
          ...prev,
          text: content,
          illustration: src,
          pdfImageFormat: fmt,
          illustrationPending: false,
        };
      } else {
        formattedStory.value.push({
          text: content,
          illustration: src,
          pageNumber: chapter,
          pdfImageFormat: fmt,
          illustrationPending: false,
        });
      }
    }

    if (result instanceof Blob) {
      const pdfFmt = pdfImageFormatFromBlobType(result.type);
      applyIllustration(URL.createObjectURL(result), pdfFmt);
      const reader = new FileReader();
      reader.onload = () => {
        if (typeof reader.result === 'string') {
          illustrations.value[chapter] = reader.result;
        }
      };
      reader.readAsDataURL(result);
    } else {
      applyIllustration(result, 'PNG');
      illustrations.value[chapter] = result;
    }
  } catch (err) {
    illustrationJobsStarted.value.delete(chapter);
    const failedIdx = formattedStory.value.findIndex(
      (p) => p.pageNumber === chapter
    );
    if (failedIdx >= 0) {
      formattedStory.value[failedIdx] = {
        ...formattedStory.value[failedIdx],
        illustrationPending: false,
      };
    }
    logger.error(`Failed to generate illustration for ${chapter}:`, err);
    $q.notify({
      type: 'warning',
      message: `Failed to generate illustration for ${chapter}`,
      timeout: 6000,
    });
  } finally {
    loading.value -= 1;
    pendingStoryIllustrations.value -= 1;
    maybeFreeComfyAfterStoryBatch();
  }
};

const generateStory = async () => {
  if (!userInput.value || !model.value) {
    querying.value = false;
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
  formattedStory.value = [];
  illustrationJobsStarted.value = new Set();
  illustrations.value = {};
  error.value = null;
  storyLlmFinished.value = false;
  storyVramFreed.value = false;
  pendingStoryIllustrations.value = 0;

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
          startIllustrationsFromProgress(progress);
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
    storyLlmFinished.value = true;
    maybeFreeComfyAfterStoryBatch();
    loading.value -= 1;
    querying.value = false;
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
  const doc = new jsPDF();
  const marginX = 24;
  const marginBottom = 15;
  const pageWidth = doc.internal.pageSize.getWidth();
  const maxTextWidth = pageWidth - 2 * marginX;
  /** Top margin when continuing wrapped text on a new page (no illustration). */
  const continuationTop = 22;

  function contentBottomMm(): number {
    return doc.internal.pageSize.getHeight() - marginBottom;
  }

  /** Line spacing in mm for the current font size (jsPDF uses pt for font size). */
  function lineHeightMm(fontSizePt: number, leading = 1.35): number {
    return fontSizePt * leading * (25.4 / 72);
  }

  /**
   * Draws text wrapped to maxTextWidth; adds pages when needed.
   * Returns the baseline Y directly below the last line (for stacking blocks).
   */
  function drawWrappedText(
    text: string,
    startX: number,
    startY: number,
    fontSizePt: number,
    leading = 1.35
  ): number {
    const raw = String(text ?? '').trim();
    const payload = raw.length ? raw : ' ';
    doc.setFontSize(fontSizePt);
    const lh = lineHeightMm(fontSizePt, leading);
    const lines = doc.splitTextToSize(payload, maxTextWidth);
    let y = startY;
    for (const line of lines) {
      if (y + lh > contentBottomMm()) {
        doc.addPage();
        y = continuationTop;
      }
      doc.text(line, startX, y);
      y += lh;
    }
    return y;
  }

  doc.addImage(assistantHeadPng, 'PNG', 84, 24, 40, 40);

  doc.setFont('helvetica', 'bold');
  doc.setTextColor(0.8, 0.3, 0.3);
  let y = drawWrappedText(capitalize(userInput.value), marginX, 78, 24);

  doc.setFont('helvetica', 'normal');
  doc.setTextColor(0, 0, 0);
  let lineY = y + 10;
  const lhSubtitle = lineHeightMm(18);
  if (lineY + lhSubtitle > contentBottomMm()) {
    doc.addPage();
    lineY = continuationTop;
  }
  doc.setFontSize(18);
  const prefix = 'Story created by ';
  doc.text(prefix, marginX, lineY);
  let xAfter = marginX + doc.getTextWidth(prefix);
  doc.setTextColor(0.2, 0.2, 1);
  doc.textWithLink('Family Ai', xAfter, lineY, {
    url: 'https://github.com/lerignoux/family-ai',
  });
  xAfter += doc.getTextWidth('Family Ai');
  doc.setTextColor(0, 0, 0);
  doc.text(' assistant.', xAfter, lineY);
  y = lineY + lhSubtitle;

  doc.setFontSize(14);
  y = drawWrappedText(
    `* Text generated using ${model.value}`,
    marginX,
    y + 6,
    14
  );
  y = drawWrappedText(
    `* Illustrations generated using ${modelIllustration.value.label}`,
    marginX,
    y + 4,
    14
  );

  const imgX = marginX;
  const imgY = 24;
  const imgSize = 160;
  const textGapBelowImage = 10;
  const bodyFontPt = 11;

  doc.setTextColor(0, 0, 0);
  doc.setFont('helvetica', 'normal');
  sortedFormattedStory.value.forEach((page: StoryPage) => {
    doc.addPage();
    doc.addImage(
      page.illustration,
      page.pdfImageFormat,
      imgX,
      imgY,
      imgSize,
      imgSize
    );
    const textStartY = imgY + imgSize + textGapBelowImage;
    drawWrappedText(page.text, marginX, textStartY, bodyFontPt);
  });
  doc.save('personal_ai_story.pdf');
}

onMounted(async () => {
  await ComfyClientManager.connect();
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
              v-for="(storyPage, index) in sortedFormattedStory"
              :key="storyPage.pageNumber"
              :name="index"
              class="row no-wrap items-stretch"
              draggable="false"
            >
              <q-img
                style="width: 45%; min-width: 150px"
                class="rounded-borders full-height"
                :src="pageBackgroundPng"
              >
                <div
                  class="absolute-full text-subtitle2 flex flex-center"
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
                class="rounded-borders full-height relative-position"
                :src="storyPage.illustration"
              >
                <div
                  v-if="storyPage.illustrationPending === true"
                  class="absolute-full flex flex-center"
                  style="background: rgba(0, 0, 0, 0.35)"
                >
                  <q-spinner color="primary" size="48px" />
                </div>
              </q-img>
            </q-carousel-slide>
            <template v-slot:navigation-icon="{ onClick, index }">
              <q-btn @click="onClick">
                <q-avatar size="56px" square>
                  <img :src="sortedFormattedStory[index].illustration" />
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
        :disable="querying || !canSaveStoryPdf"
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
