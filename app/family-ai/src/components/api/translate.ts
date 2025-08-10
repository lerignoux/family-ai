import pino from 'pino';

const logger = pino({
  level: 'info',
});

export interface TranslationProgress {
  type:
    | 'speech_to_text'
    | 'translation'
    | 'text_to_speech'
    | 'complete'
    | 'error';
  message: string;
  progress?: number;
  data?: any;
  transcribedText?: string;
  translatedText?: string;
}

export interface TranslationStreamOptions {
  onProgress?: (progress: TranslationProgress) => void;
  onComplete?: (result: Blob) => void;
  onError?: (error: string) => void;
}

export async function translateText(
  prompt: string,
  language_src: string,
  language_dst: string
) {
  logger.info(`Requested ${language_dst} translation of "${prompt}"`);
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
  const rawResponse = await fetch(
    `${process.env.API_SCHEME}://${process.env.API_URL}:${process.env.TRANSLATE_PORT}/translate?${params}`,
    requestOptions
  );
  const jsonResponse = await rawResponse.json();
  const data = jsonResponse.result;
  logger.debug(`Ai translated: "${data}"`);
  return data;
}

export async function translateAudio(
  blob: Blob,
  language_src: string,
  language_dst: string
) {
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

  const formData = new FormData();
  formData.append('file', blob, filename);
  formData.append('type', audioType);

  // Build URL with language parameters as query string
  const params = new URLSearchParams({
    from_code: language_src,
    to_code: language_dst,
  }).toString();

  const requestOptions = {
    method: 'POST',
    body: formData,
  };

  const url = `${process.env.API_SCHEME}://${process.env.API_URL}:${process.env.TRANSLATE_PORT}/translate_audio?${params}`;

  const rawResponse = await fetch(url, requestOptions);
  const blobResponse = await rawResponse.blob();
  logger.debug('Translated Audio returned.');
  return blobResponse;
}

export async function translateAudioStream(
  blob: Blob,
  language_src: string,
  language_dst: string,
  options: TranslationStreamOptions = {}
): Promise<WebSocket> {
  // Determine file extension and type based on blob MIME type
  let audioType = 'ogg';

  if (blob.type.includes('webm')) {
    audioType = 'webm';
  } else if (blob.type.includes('ogg')) {
    audioType = 'ogg';
  }

  // Create WebSocket connection
  const params = new URLSearchParams({
    from_code: language_src,
    to_code: language_dst,
    type: audioType,
  }).toString();

  const scheme = process.env.API_SCHEME === 'https' ? 'wss' : 'ws';
  const wsUrl = `${scheme}://${process.env.API_URL}:${process.env.TRANSLATE_PORT}/translate_audio_stream?${params}`;
  const ws = new WebSocket(wsUrl);

  ws.onopen = () => {
    logger.debug('WebSocket connection opened for translation streaming');
    ws.send(blob);
  };

  ws.onmessage = (event) => {
    try {
      const progress: TranslationProgress = JSON.parse(event.data);
      logger.debug('Translation progress:', progress);

      if (options.onProgress) {
        options.onProgress(progress);
      }

      if (progress.type === 'complete' && progress.data && options.onComplete) {
        // Convert base64 data back to blob
        const binaryString = atob(progress.data);
        const bytes = new Uint8Array(binaryString.length);
        for (let i = 0; i < binaryString.length; i++) {
          bytes[i] = binaryString.charCodeAt(i);
        }
        const resultBlob = new Blob([bytes], { type: 'audio/ogg' });
        options.onComplete(resultBlob);
      }
    } catch (error) {
      logger.error('Error parsing WebSocket message:', error);
      if (options.onError) {
        options.onError('Failed to parse server response');
      }
    }
  };

  ws.onerror = (error) => {
    logger.error('WebSocket error:', error);
    if (options.onError) {
      options.onError('WebSocket connection error');
    }
  };

  ws.onclose = (event) => {
    logger.debug('WebSocket connection closed:', event.code, event.reason);
    if (event.code !== 1000 && options.onError) {
      options.onError(`Connection closed: ${event.reason || 'Unknown reason'}`);
    }
  };

  return ws;
}
