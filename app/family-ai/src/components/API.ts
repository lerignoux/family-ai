import { ComfyUIClient } from './comfy/client';
import type { Prompt } from './comfy/types';

export async function textToText(prompt: string, model: string) {
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
  const rawResponse = await fetch(
    'https://ai.shanghai.laurent.erignoux.fr:9443/ollama/chat',
    requestOptions
  );
  const jsonResponse = await rawResponse.json();
  const data = jsonResponse.response;
  console.log(`Ai answer: "${data}"`);
  return data;
}

export async function textToStory(prompt: string, model: string, chapter_count: number) {
  const requestOptions = {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      model: model,
      subject: prompt,
      format: 'json',
      stream: false,
      chapter_count: chapter_count,
    }),
  };
  // fetch('http://localhost:5175/story', requestOptions)
  const rawResponse = await fetch(
    'https://ai.shanghai.laurent.erignoux.fr:9443/ollama/story',
    requestOptions
  );
  const jsonResponse = await rawResponse.json();
  const data = jsonResponse.response;
  console.log(`Ai story: "${data}"`);
  return data;
}

export async function textToSpeech(text: string, language: string) {
  if (text == '') {
    console.log('Unable to generate speech from an empty text.');
  }
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
  const rawResponse = await fetch(
    'https://ai.shanghai.laurent.erignoux.fr:9443/tts',
    requestOptions
  );
  const blobResponse = await rawResponse.blob();
  console.log('Audio fetched');
  return blobResponse;
}

export async function speechToText(blob: Blob) {
  const formData = new FormData();
  formData.append('file', blob, 'audio.ogg');
  formData.append('type', 'ogg');

  const requestOptions = {
    method: 'POST',
    body: formData,
  };
  //fetch('http://localhost:5176/uploadfile', requestOptions)
  const rawResponse = await fetch(
    'https://ai.shanghai.laurent.erignoux.fr:9443/stt',
    requestOptions
  );
  const jsonResponse = await rawResponse.json();
  const data = jsonResponse.result;
  console.log(`Decoded: ${data}`);
  return data;
}

export async function translateText(
  prompt: string,
  language_src: string,
  language_dst: string
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
  const rawResponse = await fetch(
    'https://ai.shanghai.laurent.erignoux.fr:9443/translate?' + params,
    requestOptions
  );
  const jsonResponse = await rawResponse.json();
  const data = jsonResponse.result;
  console.log(`Ai translated: "${data}"`);
  return data;
}

export async function textToImage(prompt: string, model: string) {
  console.log(`Requested image generation from prompt: ${prompt}`);
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

  return images['9'][0].blob;
}
