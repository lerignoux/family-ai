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

    const startJson = await startResponse.json().catch((err) => {
      logger.error(
        { err },
        'Unable to parse JSON response when starting subtitle task.'
      );
      throw new Error('Unable to parse subtitle task start response.');
    });

    task_id = startJson.task_id;
    if (!task_id) {
      logger.error({ startJson }, 'Subtitle task started without task_id.');
      throw new Error('Subtitle service did not return a task id.');
    }

    logger.info({ task_id }, 'Subtitle task accepted, starting polling.');

    // 2. Polling Loop
    while (true) {
      let statusResponse: Response;
      try {
        statusResponse = await fetch(`${baseUrl}/stt/status/${task_id}`);
      } catch (err) {
        logger.error({ err, task_id }, 'Network error while checking subtitle status.');
        throw new Error('Network error while checking subtitle status.');
      }

      const contentType = statusResponse.headers.get('content-type') || '';

      // If backend returns the final file, it will NOT be JSON.
      if (statusResponse.ok && !contentType.includes('application/json')) {
        logger.info({ task_id }, 'Subtitle generation completed, returning file blob.');
        return await statusResponse.blob();
      }

      if (!statusResponse.ok) {
        const errorText = await statusResponse.text().catch(() => '');
        logger.error(
          {
            task_id,
            status: statusResponse.status,
            statusText: statusResponse.statusText,
            body: errorText,
          },
          'Subtitle status endpoint returned an error.'
        );
        throw new Error(
          `Subtitle status request failed (HTTP ${statusResponse.status} ${statusResponse.statusText})`
        );
      }

      const data = await statusResponse.json().catch((err) => {
        logger.error(
          { err, task_id },
          'Unable to parse JSON response from subtitle status endpoint.'
        );
        throw new Error('Unable to parse subtitle status response.');
      });

      if (data.status === 'failed') {
        logger.error({ task_id, error: data.error }, 'Subtitle task reported failure.');
        throw new Error(
          `Subtitle generation failed: ${data.error || 'Unknown error from subtitle service.'}`
        );
      }

      logger.debug({ task_id, status: data.status }, 'Subtitle task still processing.');

      // Wait 5 seconds before next check
      await new Promise((resolve) => setTimeout(resolve, 5000));
    }
  } catch (err: any) {
    logger.error(
      { err, task_id },
      'Error generating subtitles (client-side wrapper caught exception).'
    );
    throw err;
  }
}
