// comfyClientManager.ts
import { ComfyUIClient } from './client';

class ComfyClientManager {
  private static instance: ComfyUIClient;
  private static serverAddress: string;
  private static clientId: string;
  private static scheme: string;

  public static init(
    serverAddress: string,
    clientId: string,
    scheme = 'https'
  ) {
    this.serverAddress = serverAddress;
    this.clientId = clientId;
    this.scheme = scheme;
  }

  public static getClient(): ComfyUIClient {
    if (!this.instance) {
      this.instance = new ComfyUIClient(
        this.serverAddress,
        this.clientId,
        this.scheme
      );
    }
    return this.instance;
  }

  public static async connect(): Promise<void> {
    if (!this.instance) {
      this.instance = this.getClient();
    }
    await this.instance.connect();
  }

  public static async disconnect(): Promise<void> {
    if (this.instance) {
      await this.instance.disconnect();
      this.instance = undefined as any;
    }
  }
}

export default ComfyClientManager;
