import pino from 'pino';

// Create a centralized logger instance
export const logger = pino({
  browser: {
    write: {
      info: (...args: any[]) => console.log(...args),
      warn: (...args: any[]) => console.warn(...args),
      error: (...args: any[]) => console.error(...args),
      debug: (...args: any[]) => console.debug(...args),
      trace: (...args: any[]) => console.trace(...args),
      fatal: (...args: any[]) => console.error(...args),
    },
  },
  level: process.env.NODE_ENV === 'development' ? 'debug' : 'info',
  // Add timestamp and log level to console output
  transport: {
    target: 'pino-pretty',
    options: {
      colorize: true,
      translateTime: 'SYS:standard',
      ignore: 'pid,hostname',
    },
  },
});

// Export the logger as default for backward compatibility
export default logger;
