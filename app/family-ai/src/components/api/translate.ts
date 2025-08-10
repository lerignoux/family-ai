import pino from 'pino';

const logger = pino({
  level: 'info',
});

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
