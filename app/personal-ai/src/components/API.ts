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

export function queryImage(
  prompt: string,
  model: string,
  callback: queryImageCallback
) {
  const requestOptions = {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({}),
  };
  fetch('https://comfy.shanghai.laurent.erignoux.fr:9443', requestOptions)
    .then((response) => response.json())
    .then((data) => {
      console.log(`Ai answer: "${data.response}"`);
      callback(data.response);
    });
}
