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

export interface StoryResult {
  title: string;
  [key: string]: string;
}

export interface StoryProgress {
  status: string;
  current_chapter?: number;
  chapter_count?: number;
  title?: string;
  summary?: string;
  chapters?: Record<string, string>;
}

export async function textToStory(
  prompt: string,
  model: string,
  chapter_count: number,
  onProgress?: (progress: StoryProgress) => void
): Promise<StoryResult> {
  logger.info(`Request story generation for "${prompt}".`);

  // Start the story generation
  const response = await fetch(
    `${process.env.API_SCHEME}://${process.env.API_URL}:${process.env.OLLAMA_PORT}/ollama/story`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        model: model,
        subject: prompt,
        format: 'json',
        stream: false,
        chapter_count: chapter_count,
      }),
    }
  );

  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }

  const { story_id } = await response.json();

  // Connect to WebSocket for progress updates
  const ws = new WebSocket(
    `${process.env.API_SCHEME === 'https' ? 'wss' : 'ws'}://${
      process.env.API_URL
    }:${process.env.OLLAMA_PORT}/ollama/ws/story/${story_id}`
  );

  return new Promise<StoryResult>((resolve, reject) => {
    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data.toString());

        if (onProgress) {
          onProgress({
            status: data.status,
            current_chapter: data.current_chapter,
            chapter_count: data.chapter_count,
            title: data.title,
            summary: data.summary,
            chapters: data.chapters,
          });
        }

        if (data.status === 'complete') {
          ws.close();
          resolve({
            title: data.title,
            ...data.chapters,
          });
        } else if (data.status === 'error') {
          ws.close();
          reject(new Error(data.error || 'Story generation failed'));
        }
      } catch (error) {
        ws.close();
        reject(error);
      }
    };

    ws.onerror = (error) => {
      ws.close();
      reject(error);
    };

    ws.onclose = () => {
      // Handle unexpected closure
      if (!ws.CLOSED) {
        reject(new Error('WebSocket connection closed unexpectedly'));
      }
    };
  });
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
        name: `${model.name} (${model.value})`,
      };
    }
    return model;
  });

  logger.debug(`Available models: ${JSON.stringify(processedModels)}`);
  return processedModels;
}
