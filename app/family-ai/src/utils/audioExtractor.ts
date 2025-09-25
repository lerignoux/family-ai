import { FFmpeg } from '@ffmpeg/ffmpeg';
import type { LogEvent } from '@ffmpeg/ffmpeg/dist/esm/types';
import { fetchFile, toBlobURL } from '@ffmpeg/util';
import { logger } from './logger';

// const baseURL = 'https://cdn.jsdelivr.net/npm/@ffmpeg/core-mt@0.12.10/dist/esm';
const baseURL = '/node_modules/@ffmpeg/core-mt/dist/esm';
class AudioExtractor {
  private ffmpeg: any = null;
  private isLoaded = false;
  private isLoading = false;

  async initialize(): Promise<void> {
    if (this.isLoaded || this.isLoading) return;

    try {
      this.isLoading = true;
      this.ffmpeg = new FFmpeg();
      this.ffmpeg.on('log', ({ message: msg }: LogEvent) => {
        console.log(msg);
        logger.info(msg);
      });
      logger.debug('Loading FFmpeg...');

      await this.ffmpeg.load({
        coreURL: await toBlobURL(
          `${baseURL}/ffmpeg-core.js`,
          'text/javascript'
        ),
        wasmURL: await toBlobURL(
          `${baseURL}/ffmpeg-core.wasm`,
          'application/wasm'
        ),
        workerURL: await toBlobURL(
          `${baseURL}/ffmpeg-core.worker.js`,
          'text/javascript'
        ),
        classWorkerURL: await toBlobURL(
          '/node_modules/@ffmpeg/ffmpeg/dist/esm/worker.js',
          'text/javascript'
        ),
      });

      this.isLoaded = true;
      this.isLoading = false;
      logger.debug('FFmpeg loaded successfully');
    } catch (error) {
      this.isLoading = false;
      logger.error('Failed to load FFmpeg:', error);
      throw new Error(
        'Failed to initialize audio extractor. FFmpeg WASM files could not be loaded properly.'
      );
    }
  }

  async extractAudioFromVideo(videoFile: File): Promise<File> {
    if (!this.ffmpeg || !this.isLoaded) {
      await this.initialize();
    }

    if (!this.ffmpeg) {
      throw new Error('FFmpeg not initialized');
    }

    try {
      const inputFileName = 'input_video';
      const outputFileName = 'output_audio.mp3';

      logger.debug(`Extracting audio from ${videoFile.name}...`);

      // Write the video file to FFmpeg's virtual file system
      await this.ffmpeg.writeFile(inputFileName, await fetchFile(videoFile));

      // Extract audio using FFmpeg with more compatible settings
      await this.ffmpeg.exec([
        '-i',
        inputFileName,
        '-vn', // No video
        '-acodec',
        'libmp3lame', // Use libmp3lame encoder
        '-ab',
        '128k', // Audio bitrate
        '-ar',
        '44100', // Sample rate
        '-ac',
        '2', // Stereo
        '-y', // Overwrite output file
        outputFileName,
      ]);

      // Read the output file
      const data = await this.ffmpeg.readFile(outputFileName);

      // Create a new File object with the extracted audio
      const audioBlob = new Blob([data], { type: 'audio/mp3' });
      const audioFileName = videoFile.name.replace(/\.[^/.]+$/, '.mp3');

      // Clean up temporary files
      try {
        await this.ffmpeg.deleteFile(inputFileName);
        await this.ffmpeg.deleteFile(outputFileName);
      } catch (cleanupError) {
        logger.warn('Failed to cleanup temporary files:', cleanupError);
      }

      logger.debug(`Audio extracted successfully: ${audioFileName}`);
      return new File([audioBlob], audioFileName, { type: 'audio/mp3' });
    } catch (error) {
      logger.error('Error extracting audio:', error);
      throw new Error(`Failed to extract audio: ${error}`);
    }
  }

  async cleanup(): Promise<void> {
    if (this.ffmpeg && this.isLoaded) {
      try {
        await this.ffmpeg.terminate();
        this.ffmpeg = null;
        this.isLoaded = false;
        this.isLoading = false;
        logger.debug('FFmpeg cleaned up');
      } catch (error) {
        logger.error('Error cleaning up FFmpeg:', error);
      }
    }
  }
}

// Export a singleton instance
export const audioExtractor = new AudioExtractor();
