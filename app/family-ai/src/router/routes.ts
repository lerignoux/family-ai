import { RouteRecordRaw } from 'vue-router';

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    component: () => import('layouts/MainLayout.vue'),
    children: [
      { path: '', component: () => import('pages/AssistantPage.vue') },
    ],
  },
  {
    path: '/assistant',
    component: () => import('layouts/MainLayout.vue'),
    children: [
      { path: '', component: () => import('pages/AssistantPage.vue') },
    ],
  },
  {
    path: '/translator',
    component: () => import('layouts/MainLayout.vue'),
    children: [
      { path: '', component: () => import('pages/TranslatorPage.vue') },
    ],
  },
  {
    path: '/painter',
    component: () => import('layouts/MainLayout.vue'),
    children: [{ path: '', component: () => import('pages/PainterPage.vue') }],
  },
  {
    path: '/story_teller',
    component: () => import('layouts/MainLayout.vue'),
    children: [
      { path: '', component: () => import('pages/StoryTellerPage.vue') },
    ],
  },
  // Always leave this as last one,
  // but you can also remove it
  {
    path: '/:catchAll(.*)*',
    component: () => import('pages/ErrorNotFound.vue'),
  },
];

export default routes;
