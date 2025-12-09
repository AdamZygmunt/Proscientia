import React from "react";
import Topbar from "./Topbar";
import Sidebar from "./Sidebar";

type MainLayoutProps = {
  title: string;
  subtitle?: string;
  children: React.ReactNode;
};

const MainLayout: React.FC<MainLayoutProps> = ({
  title,
  subtitle,
  children,
}) => {
  return (
    <div className="min-h-screen bg-zinc-300/90 text-zinc-800 dark:bg-zinc-800 dark:text-zinc-100">
      {/* Sidebar przyklejony do lewej */}
      <Sidebar />

      {/* Prawa część – gradient na CAŁEJ wysokości, kolumna: topbar + main */}
      <div
        className="ml-64 min-h-screen flex flex-col
        bg-[radial-gradient(circle_at_top_left,_rgba(255,184,108,0.25),transparent_40%),radial-gradient(circle_at_bottom_right,_rgba(255,152,67,0.3),transparent_60%)]
        dark:bg-[radial-gradient(circle_at_top_left,_rgba(255,138,0,0.18),transparent_40%),radial-gradient(circle_at_bottom_right,_rgba(255,90,0,0.24),transparent_60%)]"
      >
        <Topbar title={title} subtitle={subtitle} />

        {/* main wypełnia resztę, żeby gradient leciał do samego dołu */}
        <main className="flex-1 px-6 pb-6 pt-4">
          <div className="space-y-6">{children}</div>
        </main>
      </div>
    </div>
  );
};

export default MainLayout;
