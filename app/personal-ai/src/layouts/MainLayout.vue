<template>
  <q-layout view="hHh lpR fFf">
    <q-header elevated>
      <q-toolbar>
        <q-btn
          flat
          dense
          round
          icon="menu"
          aria-label="Menu"
          @click="toggleLeftDrawer"
        />
        <q-toolbar-title>
          <q-avatar>
            <img src="https://cdn.quasar.dev/logo-v2/svg/logo-mono-white.svg" />
          </q-avatar>
          Personal Ai Hub
        </q-toolbar-title>
        <AudioReader ref="audioReader" />
      </q-toolbar>
    </q-header>

    <q-drawer v-model="leftDrawerOpen" show-if-above bordered>
      <q-list>
        <q-item-label header> Pages </q-item-label>

        <PageLink
          v-for="link in pageLinksList"
          :key="link.title"
          v-bind="link"
        />
        <q-separator />
        <q-item-label header> Powered by: </q-item-label>
        <EssentialLink
          v-for="link in refLinksList"
          :key="link.title"
          v-bind="link"
        />
      </q-list>
    </q-drawer>

    <q-page-container>
      <router-view />
    </q-page-container>
  </q-layout>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import EssentialLink, { ExternalLinkProps } from 'components/ExternalLink.vue';
import PageLink, { PageLinkProps } from 'components/PageLink.vue';
import AudioReader from 'components/AudioReader.vue';

defineOptions({
  name: 'MainLayout',
});

const pageLinksList: PageLinkProps[] = [
  {
    title: 'Assistant',
    caption: 'How can I assist you today ?',
    icon: 'support_agent',
    link: 'assistant',
  },
  {
    title: 'Translator',
    caption: 'What do you want translated ?',
    icon: 'translate',
    link: 'translator',
  },
  {
    title: 'Painter',
    caption: 'Can I paint something for you ?',
    icon: 'palette',
    link: 'painter',
  },
  {
    title: 'StoryTeller',
    caption: "Let's create a little story.",
    icon: 'escalator_warning',
    link: 'story_teller',
  },
];
const refLinksList: ExternalLinkProps[] = [
  {
    title: 'Argos translate',
    caption: 'argosopentech.com',
    icon: 'img:icons/argos.png',
    link: 'https://www.argosopentech.com/',
  },
  {
    title: 'Comfy',
    caption: 'comfy.org',
    icon: 'img:icons/comfy.png',
    link: 'https://docs.comfy.org',
  },
  {
    title: 'CoquiTTS',
    caption: 'docs.coqui.ai',
    icon: 'img:icons/coquitts.png',
    link: 'https://docs.coqui.ai/en/dev/models/xtts.html',
  },
  {
    title: 'Kokoro-82M',
    caption: 'huggingface.co/hexgrad/Kokoro-82M',
    icon: 'img:icons/hexgrad.png',
    link: 'https://huggingface.co/hexgrad/Kokoro-82M',
  },
  {
    title: 'Ollama',
    caption: 'ollama.com',
    icon: 'img:icons/ollama.png',
    link: 'https://ollama.com/',
  },
  {
    title: 'Quasar',
    caption: 'quasar.dev',
    icon: 'img:icons/quasar.png',
    link: 'https://quasar.dev',
  },
  {
    title: 'Whisper',
    caption: 'openai.com/index/whisper',
    icon: 'img:icons/openai.svg#icon-1',
    link: 'https://openai.com/index/whisper/',
  },
];

const leftDrawerOpen = ref(false);

function toggleLeftDrawer() {
  leftDrawerOpen.value = !leftDrawerOpen.value;
}
</script>
