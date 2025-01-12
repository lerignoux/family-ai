import { ComfyUIClient } from './comfy/client';
import type { Prompt } from './comfy/types';

interface textToSpeechCallback {
  (audioBlob: Blob): void;
}

export function textToSpeech(
  text: string,
  language: string,
  callback: textToSpeechCallback
) {
  const params: any = { sentence: text };
  if (language !== null) {
    if (language != 'en') {
      console.log('Only english tts is supported');
    } else {
      params.language = language;
    }
  }

  const requestOptions = {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params),
  };
  // fetch('http://localhost:5174/tts', requestOptions)
  fetch('https://ai.shanghai.laurent.erignoux.fr:9443/tts', requestOptions)
    .then((response) => response.blob())
    .then((audioBlob) => {
      console.log('Audio fetched');
      callback(audioBlob);
    });
}

interface queryAiCallback {
  (response: string): void;
}

export function queryAi(
  prompt: string,
  model: string,
  callback: queryAiCallback
) {
  const requestOptions = {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      model: model,
      prompt: prompt,
      format: 'json',
      stream: false,
    }),
  };
  // fetch('http://localhost:5175/chat', requestOptions)
  fetch('https://ai.shanghai.laurent.erignoux.fr:9443/ollama', requestOptions)
    .then((response) => response.json())
    .then((data) => {
      console.log(`Ai answer: "${data.response}"`);
      callback(data.response);
    });
}

interface speechToTextCallback {
  (response: string): void;
}

export function speechToText(blob: Blob, callback: speechToTextCallback) {
  const formData = new FormData();
  formData.append('file', blob, 'audio.ogg');
  formData.append('type', 'ogg');

  const requestOptions = {
    method: 'POST',
    body: formData,
  };
  //fetch('http://localhost:5176/uploadfile', requestOptions)
  fetch('https://ai.shanghai.laurent.erignoux.fr:9443/stt', requestOptions)
    .then((response) => response.json())
    .then((data) => {
      console.log(`Decoded: ${data.result}`);
      callback(data.result);
    })
    .catch((error) => {
      console.log(error);
    });
}

export function translateString(
  prompt: string,
  language_src: string,
  language_dst: string,
  callback: queryAiCallback
) {
  const params = new URLSearchParams({
    sentence: prompt,
    from_code: language_src,
    to_code: language_dst,
  }).toString();
  const requestOptions = {
    method: 'POST',
    headers: { 'content-type': 'application/x-www-form-urlencoded' },
    body: JSON.stringify({}),
  };
  //fetch('http://localhost:5175/chat', requestOptions)
  fetch(
    'https://ai.shanghai.laurent.erignoux.fr:9443/translate?' + params,
    requestOptions
  )
    .then((response) => response.json())
    .then((data) => {
      console.log(`Ai answer: "${data.result}"`);
      callback(data.result);
    });
}

interface queryImageCallback {
  (image: any): void;
}

export async function queryImage(
  prompt: string,
  model: string,
  callback: queryImageCallback
) {
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
  const serverAddress = 'ai.shanghai.laurent.erignoux.fr:9443/comfy';
  const clientId = 'baadbabe-b00b-4206-9420-deadd00d1337';
  const client = new ComfyUIClient(serverAddress, clientId);

  // Connect to server
  await client.connect();

  // Generate images
  const images = await client.getImages(promptData);

  // Disconnect
  await client.disconnect();

  callback(images['9'][0].blob);
}
