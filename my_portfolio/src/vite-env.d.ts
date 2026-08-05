/// <reference types="vite/client" />

interface Window {
  tracknode?: {
    track?: (eventName: string, payload?: Record<string, string>) => void;
  };
}
