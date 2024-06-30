<template>
  <router-view />
</template>

<script setup lang="ts">
// Should be in the quasar config file
import { useQuasar } from 'quasar';
const $q = useQuasar();
$q.dark.set(true);

defineOptions({
  name: 'App',
});
</script>
