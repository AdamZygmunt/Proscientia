import React from "react";
import { FiSun, FiMoon } from "react-icons/fi";
import { motion, AnimatePresence } from "framer-motion";
import { logout } from "../utils/axiosInstance";

type TopbarProps = {
  title: string;
  subtitle?: string;
};

const Topbar: React.FC<TopbarProps> = ({ title, subtitle }) => {
  const [isDark, setIsDark] = React.useState<boolean>(() => {
    if (typeof window === "undefined") return true;
    const stored = localStorage.getItem("theme");
    // domyślnie ciemny motyw
    return stored ? stored === "dark" : true;
  });

  React.useEffect(() => {
    if (typeof document === "undefined") return;

    const root = document.documentElement;

    if (isDark) {
      root.classList.add("dark");
      localStorage.setItem("theme", "dark");
    } else {
      root.classList.remove("dark");
      localStorage.setItem("theme", "light");
    }

    // Powiadom Sidebar o zmianie motywu (dla logo)
    window.dispatchEvent(
      new CustomEvent("proscientia-theme-change", {
        detail: { isDark },
      })
    );
  }, [isDark]);

  const toggleTheme = () => setIsDark((prev) => !prev);

  return (
    <header className="sticky top-0 z-20 border-b border-zinc-300/70 bg-zinc-300 dark:border-zinc-800/70 dark:bg-zinc-900/95 backdrop-blur-md">
      <div className="flex justify-between px-4 py-3">
        {/* Tytuł po lewej */}
        <div className="flex flex-col text-left">
          <h1 className="text-sm sm:text-base font-semibold tracking-tight text-zinc-900 dark:text-zinc-50">
            {title}
          </h1>
          {subtitle && (
            <p className="text-xs text-zinc-600 dark:text-zinc-400">
              {subtitle}
            </p>
          )}
        </div>

        {/* Prawa strona: theme toggle + logout */}
        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={toggleTheme}
            className="relative flex h-9 w-9 items-center justify-center rounded-full border border-zinc-600/80 hover:border-orange-400/90 transition-colors bg-transparent"
            aria-label={isDark ? "Przełącz na jasny motyw" : "Przełącz na ciemny motyw"}
          >
            <AnimatePresence mode="wait" initial={false}>
              {isDark ? (
                <motion.span
                  key="moon"
                  initial={{ scale: 0.6, rotate: -45, opacity: 0 }}
                  animate={{ scale: 1, rotate: 0, opacity: 1 }}
                  exit={{ scale: 0.6, rotate: 45, opacity: 0 }}
                  transition={{ duration: 0.25 }}
                >
                  <FiMoon className="text-zinc-100" />
                </motion.span>
              ) : (
                <motion.span
                  key="sun"
                  initial={{ scale: 0.6, rotate: 45, opacity: 0 }}
                  animate={{ scale: 1, rotate: 0, opacity: 1 }}
                  exit={{ scale: 0.6, rotate: -45, opacity: 0 }}
                  transition={{ duration: 0.25 }}
                >
                  <FiSun className="text-amber-500" />
                </motion.span>
              )}
            </AnimatePresence>
          </button>

          <button
            type="button"
            onClick={logout}
            className="btn-gradient-primary px-4 py-2 text-xs sm:text-sm"
          >
            Wyloguj
          </button>
        </div>
      </div>
    </header>
  );
};

export default Topbar;
