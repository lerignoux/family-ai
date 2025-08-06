// Local storage utility for persisting user selections
export interface UserSelections {
  assistant?: {
    model?: string;
  };
  translator?: {
    language_src?: { label: string; value: string };
    language_dst?: { label: string; value: string };
  };
  painter?: {
    model?: string;
  };
  storyTeller?: {
    model?: string;
    storyLength?: number;
    style?: { 
      label: string; 
      illustrationTemplateSuffix?: string; 
      illustrationTemplatePrefix?: string;
    };
  };
}

const STORAGE_KEY = 'family-ai-user-selections';

export function saveUserSelection(page: keyof UserSelections, key: string, value: any): void {
  try {
    const existing = getUserSelections();
    if (!existing[page]) {
      existing[page] = {};
    }
    (existing[page] as any)[key] = value;
    localStorage.setItem(STORAGE_KEY, JSON.stringify(existing));
  } catch (error) {
    console.error('Error saving user selection:', error);
  }
}

export function getUserSelections(): UserSelections {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    return stored ? JSON.parse(stored) : {};
  } catch (error) {
    console.error('Error reading user selections:', error);
    return {};
  }
}

export function getPageSelection(page: keyof UserSelections): any {
  const selections = getUserSelections();
  return selections[page] || {};
}

export function clearUserSelections(): void {
  try {
    localStorage.removeItem(STORAGE_KEY);
  } catch (error) {
    console.error('Error clearing user selections:', error);
  }
} 