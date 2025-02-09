import pino from 'pino';

const logger = pino({
  level: 'info',
});

export async function textToText(prompt: string, model: string) {
  logger.info(`Request text generation for "${prompt}"".`);
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
  const rawResponse = await fetch(
    `${process.env.API_SCHEME}://${process.env.API_URL}:${process.env.OLLAMA_PORT}/ollama/chat`,
    requestOptions
  );
  const jsonResponse = await rawResponse.json();
  const data = jsonResponse.response;
  console.debug(`Ai answer: "${data}"`);
  return data;
}

export async function textToStory(
  prompt: string,
  model: string,
  chapter_count: number
) {
  logger.info(`Request story generation for "${prompt}".`);
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
  const rawResponse = await fetch(
    `${process.env.API_SCHEME}://${process.env.API_URL}:${process.env.OLLAMA_PORT}/ollama/story`,
    requestOptions
  );
  const jsonResponse = await rawResponse.json();
  const data = jsonResponse.response;
  logger.debug(`Ai story: "${data}"`);
  return data;
}
