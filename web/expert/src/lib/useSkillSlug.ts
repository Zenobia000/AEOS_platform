/**
 * useSkillSlug — 與 URL `?skill_slug=` 同步的 React hook.
 *
 * CR-0001 §9 #7. 設計：deep-link 支援 + 全頁狀態（top-level 一處持有）。
 */
import { useCallback, useEffect, useState } from "react";

const QUERY_KEY = "skill_slug";
const DEFAULT_SLUG = "_all_";

function readFromUrl(): string {
  if (typeof window === "undefined") return DEFAULT_SLUG;
  const params = new URLSearchParams(window.location.search);
  return params.get(QUERY_KEY) ?? DEFAULT_SLUG;
}

function writeToUrl(slug: string): void {
  if (typeof window === "undefined") return;
  const url = new URL(window.location.href);
  if (slug === DEFAULT_SLUG) {
    url.searchParams.delete(QUERY_KEY);
  } else {
    url.searchParams.set(QUERY_KEY, slug);
  }
  window.history.replaceState({}, "", url.toString());
}

export function useSkillSlug(): [string, (slug: string) => void] {
  const [slug, setSlugState] = useState<string>(readFromUrl);

  // popstate 同步（瀏覽器前進後退）
  useEffect(() => {
    const handler = () => setSlugState(readFromUrl());
    window.addEventListener("popstate", handler);
    return () => window.removeEventListener("popstate", handler);
  }, []);

  const setSlug = useCallback((next: string) => {
    setSlugState(next);
    writeToUrl(next);
  }, []);

  return [slug, setSlug];
}

export { DEFAULT_SLUG, QUERY_KEY };
