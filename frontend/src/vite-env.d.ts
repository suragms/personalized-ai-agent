/// <reference types="vite/client" />

interface ImportMetaEnv {
  /** Backend origin, e.g. https://agent-backend.onrender.com. Empty = same-origin. */
  readonly VITE_API_BASE?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
