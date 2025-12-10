# Utilities

This directory contains utility functions and helpers used across the application.

## Logger

The centralized logger utility provides consistent logging across all pages and components.

### Basic Usage

```typescript
import { logger } from '../utils/logger';

// Basic logging
logger.info('This is an info message');
logger.warn('This is a warning message');
logger.error('This is an error message');
logger.debug('This is a debug message');

// With context
logger.info('User action completed', { userId: 123, action: 'login' });
```

### Configuration

The logger automatically adjusts its level based on the environment:
- **Development**: `debug` level (shows all logs)
- **Production**: `info` level (shows info, warn, and error only)

### Benefits

1. **Consistency**: All pages use the same logging format and configuration
2. **Centralized Control**: Easy to change logging behavior across the entire app
3. **Environment Awareness**: Automatically adjusts logging level based on environment
4. **Utility Functions**: Pre-built functions for common logging patterns
5. **Type Safety**: Full TypeScript support with proper typing

### Migration from Individual Loggers

If you have existing code with individual pino instances:

**Before:**
```typescript
import pino from 'pino';
const logger = pino({ level: 'info' });
logger.info('Message');
```

**After:**
```typescript
import { logger } from '../utils/logger';
logger.info('Message');
```

The centralized logger maintains the same API, so existing code will work without changes.
