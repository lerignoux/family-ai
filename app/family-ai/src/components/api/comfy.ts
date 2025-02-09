import pino from 'pino';

import { ComfyUIClient } from './comfy/client';
import type { Prompt } from './comfy/types';

const logger = pino({
  level: 'info',
});

export async function textToImage(prompt: string, model: string) {
  logger.info(`Requested image generation for: "${prompt}"`);
  const promptData: Prompt = {
    '3': {
      class_type: 'KSampler',
      inputs: {
        cfg: 8,
        denoise: 1,
        latent_image: ['5', 0],
        model: ['4', 0],
        negative: ['7', 0],
        positive: ['6', 0],
        sampler_name: 'euler',
        scheduler: 'normal',
        seed: Math.random(),
        steps: 20,
      },
    },
    '4': {
      class_type: 'CheckpointLoaderSimple',
      inputs: {
        ckpt_name: model,
      },
    },
    '5': {
      class_type: 'EmptyLatentImage',
      inputs: {
        batch_size: 1,
        height: 512,
        width: 512,
      },
    },
    '6': {
      class_type: 'CLIPTextEncode',
      inputs: {
        clip: ['4', 1],
        text: prompt,
      },
    },
    '7': {
      class_type: 'CLIPTextEncode',
      inputs: {
        clip: ['4', 1],
        text: 'bad hands',
      },
    },
    '8': {
      class_type: 'VAEDecode',
      inputs: {
        samples: ['3', 0],
        vae: ['4', 2],
      },
    },
    '9': {
      class_type: 'SaveImage',
      inputs: {
        filename_prefix: 'ComfyUI',
        images: ['8', 0],
      },
    },
  };

  // Set the text prompt for our positive CLIPTextEncode
  promptData['6'].inputs.text = prompt;

  // Set the seed for our KSampler node
  promptData['3'].inputs.seed = Math.random();

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
