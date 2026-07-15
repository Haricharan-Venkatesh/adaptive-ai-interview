"use client";

import { createContext, useContext, useCallback, useSyncExternalStore, type ReactNode } from "react";

type Theme = "light" | "dark";

interface ThemeContextType {
  theme: Theme;
  toggleTheme: () => void;
}

const ThemeContext = createContext<ThemeContextType | null>(null);

// ── External store for theme ────────────────────────────────────────────────
// This avoids calling setState inside useEffect (react-hooks/set-state-in-effect).

let currentTheme: Theme = "dark";
const listeners = new Set<() => void>();

function getThemeSnapshot(): Theme {
  return currentTheme;
}

function getServerSnapshot(): Theme {
  return "dark";
}

function subscribeToTheme(callback: () => void): () => void {
  listeners.add(callback);
  return () => listeners.delete(callback);
}

function setThemeValue(next: Theme) {
  currentTheme = next;
  if (typeof window !== "undefined") {
    localStorage.setItem("theme", next);
    document.documentElement.classList.toggle("dark", next === "dark");
  }
  listeners.forEach((cb) => cb());
}

// Initialize on first client load
if (typeof window !== "undefined") {
  const stored = localStorage.getItem("theme") as Theme | null;
  const preferred =
    stored ??
    (window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");
  currentTheme = preferred;
  document.documentElement.classList.toggle("dark", preferred === "dark");
}

// ── Provider ─────────────────────────────────────────────────────────────────

export function ThemeProvider({ children }: { children: ReactNode }) {
  const theme = useSyncExternalStore(subscribeToTheme, getThemeSnapshot, getServerSnapshot);

  const toggleTheme = useCallback(() => {
    setThemeValue(theme === "dark" ? "light" : "dark");
  }, [theme]);

  return (
    <ThemeContext.Provider value={{ theme, toggleTheme }}>
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme(): ThemeContextType {
  const ctx = useContext(ThemeContext);
  if (!ctx) throw new Error("useTheme must be used within ThemeProvider");
  return ctx;
}
