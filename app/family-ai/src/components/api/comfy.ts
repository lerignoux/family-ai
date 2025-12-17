import pino from 'pino';

import { ComfyUIClient } from './comfy/client';
import type { Prompt } from './comfy/types';

const logger = pino({
  level: 'info',
});

export interface ComfyModel {
  name: string;
  value: string;
  description: string;
}

export async function getAvailableModels(): Promise<ComfyModel[]> {
  logger.info('Fetching available models from Ollama');
  const models = [
    {
      name: 'Z Image',
      value: 'z-image-turbo-fp8-e4m3fn.safetensors',
      description: 'Z image model for realist pictures.',
    },
    {
      name: 'Dreamshaper',
      value: 'dreamshaperXL_v21TurboDPMSDE.safetensors',
      description: 'a model trained on fantasy.',
    },
    {
      name: 'Epicrealism',
      value: 'epicrealismXL_v5Ultimate.safetensors',
      description: 'a realist model.',
    },
    {
      name: 'Flux Dev',
      value: 'flux1-dev-fp8.safetensors',
      description: 'A model good with embedded Text',
    },
  ];
  logger.debug(`Available models: ${JSON.stringify(models)}`);
  return models;
}

export async function textToImage(
  prompt: string,
  model: string,
  template = 'z_image_turbo'
) {
  logger.info(`Requested image generation for: "${prompt}"`);
  const workflowTemplate = await import(`./comfy/workflows/${template}.json`);
  // Access the JSON data via the 'default' export
  const promptData: Prompt = workflowTemplate.default;

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

  // Create client
  const serverAddress = `${process.env.COMFY_URL}`;
  const clientId = process.env.COMFY_CLIENT_ID || '';
  const client = new ComfyUIClient(
    serverAddress,
    clientId,
    process.env.API_SCHEME
  );

  // Connect to server
  await client.connect();

  // Generate images
  const images = await client.getImages(promptData);

  // Disconnect
  await client.disconnect();

  return images['9'][0].blob;
}
