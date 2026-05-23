/**
 * 共用 auth state — token 存 localStorage；其他 module 透過 getToken() 拿。
 *
 * Phase 1 簡化（不接 Zustand / Redux）：
 * - token 寫入 localStorage 後，整個 app 透過 getToken() 讀取
 * - 變動時觸發 listener（用於 App.tsx 重渲染決定顯示 Login 或 tabs）
 */
const TOKEN_KEY = "aeos.expert_token";
const EXPERT_KEY = "aeos.expert_profile";

export interface ExpertProfile {
  id: string;
  email: string;
  name: string;
  role: string;
  tenant_id: string | null;
}

type Listener = () => void;
const listeners = new Set<Listener>();

export function getToken(): string | null {
  try {
    return window.localStorage.getItem(TOKEN_KEY);
  } catch {
    return null;
  }
}

export function getStoredExpert(): ExpertProfile | null {
  try {
    const raw = window.localStorage.getItem(EXPERT_KEY);
    if (!raw) return null;
    return JSON.parse(raw) as ExpertProfile;
  } catch {
    return null;
  }
}

export function setSession(token: string, expert: ExpertProfile): void {
  try {
    window.localStorage.setItem(TOKEN_KEY, token);
    window.localStorage.setItem(EXPERT_KEY, JSON.stringify(expert));
  } catch {
    /* localStorage unavailable */
  }
  notify();
}

export function clearSession(): void {
  try {
    window.localStorage.removeItem(TOKEN_KEY);
    window.localStorage.removeItem(EXPERT_KEY);
  } catch {
    /* localStorage unavailable */
  }
  notify();
}

export function subscribe(fn: Listener): () => void {
  listeners.add(fn);
  return () => {
    listeners.delete(fn);
  };
}

function notify(): void {
  for (const fn of listeners) {
    try {
      fn();
    } catch {
      /* listener error - ignore */
    }
  }
}

export function authHeader(): Record<string, string> {
  const token = getToken();
  return token ? { authorization: `Bearer ${token}` } : {};
}
