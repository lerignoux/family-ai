import pino from 'pino';

const logger = pino({
  level: 'info',
});

export async function textToSpeech(text: string, language: string) {
  if (text == '') {
    logger.warn('Unable to generate speech from an empty text.');
  } else {
    logger.info(`Requested tts for "${text}".`);
  }
  const params: any = { sentence: text };
  if (language !== null) {
    params.language = language;
  }
  const requestOptions = {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params),
  };
  const rawResponse = await fetch(
    `${process.env.API_SCHEME}://${process.env.API_URL}:${process.env.TTS_PORT}/tts`,
    requestOptions
  );
  const blobResponse = await rawResponse.blob();
  logger.debug('TTS Audio returned.');
  return blobResponse;
}

export async function speechToText(blob: Blob, language = null) {
  logger.debug('Requested text from audio input.');

  const formData = new FormData();
  if (language) {
    formData.append('language', language);
  }

  // Determine file extension and type based on blob MIME type
  let filename = 'audio.ogg';
  let audioType = 'ogg';

  if (blob.type.includes('webm')) {
    filename = 'audio.webm';
    audioType = 'webm';
  } else if (blob.type.includes('ogg')) {
    filename = 'audio.ogg';
    audioType = 'ogg';
  }

  formData.append('file', blob, filename);
  formData.append('type', audioType);

  const requestOptions = {
    method: 'POST',
    body: formData,
  };
  const rawResponse = await fetch(
    `${process.env.API_SCHEME}://${process.env.API_URL}:${process.env.TTS_PORT}/stt`,
    requestOptions
  );
  const jsonResponse = await rawResponse.json();
  const data = jsonResponse.result;
  logger.info(`Text decoded from audio: "${data}"`);
  return data;
}

export async function generateSubtitles(
  file: File,
  language: string,
  integration: string | null = null
) {
  const formData = new FormData();
  formData.append('file', file);

  const params = new URLSearchParams({
    language,
    integration: integration || '',
  });
  const baseUrl = `${process.env.API_SCHEME}://${process.env.API_URL}:${process.env.TTS_PORT}`;

  const startResponse = await fetch(`${baseUrl}/stt/subtitles?${params}`, {
    method: 'POST',
    body: formData,
  });
  const { task_id } = await startResponse.json();

  // 2. Polling Loop
  while (true) {
    const statusResponse = await fetch(`${baseUrl}/stt/status/${task_id}`);

    if (
      statusResponse.ok &&
      statusResponse.headers.get('content-type') !== 'application/json'
    ) {
      return await statusResponse.blob();
    }

    const data = await statusResponse.json();
    if (data.status === 'failed') throw new Error(data.error);

    // Wait 5 seconds before next check
    await new Promise((resolve) => setTimeout(resolve, 5000));
  }
}
