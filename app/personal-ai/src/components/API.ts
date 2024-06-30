interface textToSpeechCallback {
  (audioBlob: Blob): void;
}

export function textToSpeech(text: string, callback: textToSpeechCallback) {
  const requestOptions = {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ sentence: text }),
  };
  fetch('http://localhost:5174/tts', requestOptions)
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
  fetch('http://localhost:5175/chat', requestOptions)
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
  fetch('http://localhost:5176/uploadfile', requestOptions)
    .then((response) => response.json())
    .then((data) => {
      console.log(`Decoded: ${data.result}`);
      callback(data.result);
    });
}

export function translate(
  prompt: string,
  language: String,
  callback: queryAiCallback
) {
  const requestOptions = {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      source: 'auto',
      target: language,
      format: 'text',
      q: prompt,
      alternatives: 1,
      api_key: '',
    }),
  };
  fetch('http://localhost:5175/chat', requestOptions)
    .then((response) => response.json())
    .then((data) => {
      console.log(`Ai answer: "${data.response}"`);
      callback(data.response);
    });
}

interface queryImageCallback {
  (image: any): void;
}

export function queryImage(
  prompt: string,
  model: string,
  callback: queryImageCallback
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
  fetch('http://localhost:8188/chat', requestOptions)
    .then((response) => response.json())
    .then((data) => {
      console.log(`Ai answer: "${data.response}"`);
      callback(data.response);
    });
}
