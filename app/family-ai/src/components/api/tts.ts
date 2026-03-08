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

  logger.info(
    { language, integration },
    'Starting subtitle generation request.'
  );

  let task_id: string | undefined;

  try {
    const startResponse = await fetch(`${baseUrl}/stt/subtitles?${params}`, {
      method: 'POST',
      body: formData,
    });

    if (!startResponse.ok) {
      const errorText = await startResponse.text().catch(() => '');
      logger.error(
        {
          status: startResponse.status,
          statusText: startResponse.statusText,
          body: errorText,
        },
        'Failed to start subtitle generation task.'
      );
      throw new Error(
        `Failed to start subtitle generation (HTTP ${startResponse.status} ${startResponse.statusText})`
      );
    }

    const requestJson = await startResponse.json().catch((err) => {
      logger.error(
        { err },
        'Unable to parse JSON response when starting subtitle task.'
      );
      throw new Error('Unable to parse subtitle task start response.');
    });

    task_id = requestJson.task_id;
    if (!task_id) {
      logger.error({ requestJson }, 'Subtitle task started without task_id.');
      throw new Error('Subtitle service did not return a task id.');
    }

    logger.info(
      { task_id },
      'Subtitle task accepted, connecting via WebSocket.'
    );

    // Wait for completion
    const ws = new WebSocket(
      `${process.env.API_SCHEME === 'https' ? 'wss' : 'ws'}://${
        process.env.API_URL
      }:${process.env.TTS_PORT}/stt/ws/${task_id}`
    );

    const data = await new Promise<{
      status: string;
      error?: string;
      message?: string;
    }>((resolve, reject) => {
      ws.onmessage = (event) => {
        try {
          const msg = JSON.parse(event.data.toString()) as {
            status: string;
            error?: string;
            message?: string;
          };

          if (msg.status === 'complete') {
            ws.close();
            resolve(msg);
          } else if (msg.status === 'error') {
            ws.close();
            reject(
              new Error(
                msg.error || msg.message || 'Subtitle generation failed'
              )
            );
          } else {
            logger.debug(
              { task_id, status: msg.status },
              'Subtitle task progress.'
            );
          }
        } catch (err) {
          logger.error({ err, task_id }, 'Invalid WebSocket message.');
          ws.close();
          reject(new Error('Invalid WebSocket message from subtitle service.'));
        }
      };

      ws.onerror = (err) => {
        logger.error(
          { err, task_id },
          'WebSocket error while waiting for subtitles.'
        );
        ws.close();
        reject(new Error('WebSocket error while waiting for subtitles.'));
      };

      ws.onclose = (event) => {
        if (event.code !== 1000 && !event.wasClean) {
          const msg =
            event.reason ||
            `WebSocket closed unexpectedly (code ${event.code})`;
          logger.error({ task_id, code: event.code }, msg);
          reject(new Error(msg));
        }
      };
    });

    if (data.status !== 'complete') {
      throw new Error(`Unexpected subtitle status: ${data.status}`);
    }

    // Fetch the result file
    logger.info({ task_id }, 'Subtitle generation completed, fetching file.');
    const fileResponse = await fetch(`${baseUrl}/stt/status/${task_id}`);
    if (!fileResponse.ok) {
      const errorText = await fileResponse.text().catch(() => '');
      logger.error(
        {
          task_id,
          status: fileResponse.status,
          statusText: fileResponse.statusText,
          body: errorText,
        },
        'Failed to fetch subtitle file after completion.'
      );
      throw new Error(
        `Failed to fetch subtitle file (HTTP ${fileResponse.status} ${fileResponse.statusText})`
      );
    }
    return await fileResponse.blob();
  } catch (err: any) {
    logger.error(
      { err, task_id },
      'Error generating subtitles (client-side wrapper caught exception).'
    );
    throw err;
  }
}
