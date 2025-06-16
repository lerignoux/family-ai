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

export interface OllamaModel {
  name: string;
  value: string;
  description: string;
  type: 'local' | 'api';
}

export async function getAvailableModels(): Promise<OllamaModel[]> {
  logger.info('Fetching available models from Ollama');
  const rawResponse = await fetch(
    `${process.env.API_SCHEME}://${process.env.API_URL}:${process.env.OLLAMA_PORT}/ollama/models`
  );
  const models = await rawResponse.json();

  // Count occurrences of each model name
  const nameCounts = new Map<string, number>();
  models.forEach((model: OllamaModel) => {
    nameCounts.set(model.name, (nameCounts.get(model.name) || 0) + 1);
  });

  // Add model ID in brackets for duplicate names
  const processedModels = models.map((model: OllamaModel) => {
    if ((nameCounts.get(model.name) ?? 0) > 1) {
      return {
        ...model,
        name: `${model.name} (${model.value})`
      };
    }
    return model;
  });

  logger.debug(`Available models: ${JSON.stringify(processedModels)}`);
  return processedModels;
}
