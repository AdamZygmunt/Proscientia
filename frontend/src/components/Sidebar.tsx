import React from "react";
import { NavLink } from "react-router-dom";
import {
  FiGrid,
  FiFileText,
  FiCheckSquare,
  FiSearch,
  FiLogOut,
  FiUser,
} from "react-icons/fi";
import axiosInstance, { logout } from "../utils/axiosInstance";
import logoDark from "../assets/logo-transparent-white.png";
import logoLight from "../assets/logo-transparent.png";

type SidebarProps = {
  userName?: string;
  userEmail?: string;
};

const navItems = [
  { to: "/", label: "Dashboard", icon: FiGrid },
  { to: "/summaries", label: "Streszczenia", icon: FiFileText },
  { to: "/tests", label: "Testy", icon: FiCheckSquare },
  { to: "/docsearch", label: "DocSearch", icon: FiSearch },
];

const Sidebar: React.FC<SidebarProps> = ({
  userName = "Użytkownik systemu",
  userEmail = "user@example.com",
}) => {
  const [isDark, setIsDark] = React.useState<boolean>(() => {
    if (typeof document === "undefined") return true;
    return document.documentElement.classList.contains("dark");
  });

  const [displayName, setDisplayName] = React.useState<string>(userName);
  const [displayEmail, setDisplayEmail] = React.useState<string>(userEmail);

  // nasłuchujemy na globalny event z Topbara, żeby przełączać logo
  React.useEffect(() => {
    const handler = (event: Event) => {
      if (typeof document === "undefined") return;
      setIsDark(document.documentElement.classList.contains("dark"));
    };

    window.addEventListener("proscientia-theme-change", handler);
    // inicjalne ustawienie
    handler(new Event("init"));

    return () => window.removeEventListener("proscientia-theme-change", handler);
  }, []);

  React.useEffect(() => {
    let isMounted = true;

    const fetchMe = async () => {
      try {
        const response = await axiosInstance.get("/users/auth/me/");
        const data = response.data as {
          email: string;
          first_name?: string;
          last_name?: string;
        };

        // console.log(data);

        if (!isMounted) return;

        const first = (data.first_name || "").trim();
        const last = (data.last_name || "").trim();
        const fullName =
          (first || last) ? `${first} ${last}`.trim() : "Użytkownik systemu";

        setDisplayName(fullName);
        setDisplayEmail(data.email || "user@example.com");
      } catch {
        // błędy obsłuży interceptor (401 -> refresh/logout),
        // tutaj świadomie nic nie robimy, żeby nie spamować konsoli
      }
    };

    fetchMe();

    return () => {
      isMounted = false;
    };
  }, []);

  const Logo = isDark ? logoDark : logoLight;

  return (
    <aside className="fixed left-0 top-0 flex h-screen w-64 flex-col border-r border-zinc-300/70 bg-gradient-to-b from-zinc-300 via-zinc-200 to-zinc-100 dark:border-zinc-800/80 dark:from-zinc-900 dark:via-zinc-900 dark:to-zinc-800">
      {/* Logo */}
      <div className="flex items-center gap-2 px-6 pt-0 pb-6 border-b border-zinc-300/70 dark:border-zinc-700/70">
        <div className="w-40 h-10 shrink-0">
          <img src={Logo} alt="Proscientia" className="w-full h-auto" />
        </div>
      </div>

      {/* Menu */}
      <nav className="flex-1 px-3 pt-3 pb-2 space-y-1 overflow-y-auto">
        {navItems.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === "/"}
              className={({ isActive }) =>
                [
                  "group flex items-center gap-3 rounded-xl px-3 py-2 text-sm transition-colors",
                  isActive
                    ? "bg-zinc-400 text-zinc-900 dark:bg-zinc-800/85 dark:text-zinc-50"
                    : "text-zinc-700 hover:bg-zinc-300/70 hover:text-zinc-900 dark:text-zinc-400 dark:hover:bg-zinc-900/70 dark:hover:text-zinc-50",
                ].join(" ")
              }
            >
              {({ isActive }) => (
                <>
                  <span
                    className={[
                      "flex h-8 w-8 items-center justify-center rounded-lg border text-base transition-colors",
                      isActive
                        ? "border-orange-500 bg-zinc-200 text-orange-500 dark:border-orange-500 dark:bg-zinc-900 dark:text-orange-300"
                        : "border-zinc-400 bg-zinc-200 text-zinc-500 group-hover:border-orange-500 group-hover:text-orange-500 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-400 dark:group-hover:border-orange-500 dark:group-hover:text-orange-300",
                    ].join(" ")}
                  >
                    <Icon />
                  </span>
                  <span className="font-medium">
                    {item.label}
                  </span>
                </>
              )}
            </NavLink>
          );
        })}
      </nav>

      {/* Stopka – przyklejona do dołu */}
      <div className="border-t border-zinc-300/70 dark:border-zinc-700/70 px-3 py-3 flex items-center justify-between gap-2">
        <div className="flex items-center gap-2 min-w-0">
          <div className="flex h-9 w-9 items-center justify-center rounded-full bg-zinc-300/95 text-orange-500 dark:bg-zinc-700 dark:text-orange-400">
            <FiUser />
          </div>
          <div className="flex flex-col leading-tight min-w-0">
            <span className="text-xs font-semibold truncate">
              {displayName}
            </span>
            <span className="text-[11px] text-zinc-600 dark:text-zinc-400 truncate max-w-[140px]">
              {displayEmail}
            </span>
          </div>
        </div>

        <button
          type="button"
          onClick={logout}
          className="btn-icon bg-zinc-300/95 dark:bg-zinc-700/50 hover:bg-zinc-500/70 dark:hover:bg-zinc-800/20"
          aria-label="Wyloguj"
        >
          <FiLogOut className="text-zinc-800 dark:text-zinc-100" />
        </button>
      </div>
    </aside>
  );
};

export default Sidebar;
