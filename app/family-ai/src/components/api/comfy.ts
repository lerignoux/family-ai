import pino from 'pino';
import ComfyClientManager from './comfy/manager';
import type { Prompt } from './comfy/types';

const logger = pino({
  level: 'info',
});

// Initialize the manager (call this once at app startup)
ComfyClientManager.init(
  `${process.env.COMFY_URL}`,
  process.env.COMFY_CLIENT_ID || '',
  process.env.API_SCHEME
);

export interface ComfyModel {
  name: string;
  value: string;
  description: string;
}

export async function getAvailableModels(): Promise<ComfyModel[]> {
  const models = [
    {
      name: 'Z Image',
      value: 'z-image-turbo-fp8-e4m3fn.safetensors',
      description: 'Z image model for realist pictures.',
    },
    {
      name: 'Flux 2 Klein',
      value: 'flux-2-klein-9b-fp8.safetensors',
      description: 'A model good with embedded Text',
    },
  ];
  logger.debug(`Available models: ${JSON.stringify(models)}`);
  return models;
}

export async function textToImage(
  prompt: string,
  model: string,
  template = 'flux_2_klein',
  clearVram = true
) {
  logger.info(`Requested image generation for: "${prompt}"`);
  const workflowTemplate = await import(`./comfy/workflows/${template}.json`);
  // Access the JSON data via the 'default' export
  const promptData: Prompt = workflowTemplate.default;

  if (template == 'flux_2_klein') {
    promptData['76'].inputs.value = prompt;
    promptData['75:73'].inputs.noise_seed = Math.random();
    promptData['75:70'].inputs.unet_name = model;
  }
  if (template == 'z_image_turbo') {
    promptData['34:27'].inputs.text = prompt;
    promptData['34:3'].inputs.seed = Math.random();
    promptData['34:28'].inputs.unet_name = model;
  }
  if (template == 'simple') {
    promptData['6'].inputs.text = prompt;
    promptData['3'].inputs.seed = Math.random();
    promptData['4'].inputs.ckpt_name = model;
  }

  // Reuse the existing WebSocket connection
  const client = ComfyClientManager.getClient();
  const images = await client.getImages(promptData, clearVram);

  return images['9'][0].blob;
}

/**
 * Unloads models and frees VRAM on ComfyUI (`POST /api/free`).
 * Call once after a batch (e.g. story illustrations) when using `textToImage(..., clearVram=false)` per job.
 * Single-request flows (e.g. Painter) default `clearVram=true` on `textToImage` and free after each image.
 */
export async function freeComfyMemory(): Promise<void> {
  const serverAddress = `${process.env.COMFY_URL}`;
  const scheme = process.env.API_SCHEME ?? 'http';
  const res = await fetch(`${scheme}://${serverAddress}/api/free`, {
    method: 'POST',
    headers: {
      Accept: 'application/json',
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      unload_models: true,
      free_memory: true,
    }),
  });
  if (!res.ok) {
    logger.warn(`freeComfyMemory: HTTP ${res.status}`);
  }
}
