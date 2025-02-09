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
