import { useState, useEffect } from 'react'
import proscientiaLogo from "./assets/logo-transparent-white.png"
import './App.css'
import {  Routes, Route, Navigate, Outlet} from "react-router-dom";
import { setApiErrorHandler, getAccessToken } from "./utils/axiosInstance";
import GlobalErrorDialog from "./components/GlobalErrorDialog";
import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import AISummary from './pages/AISummary';

function ProtectedRoute() {
  const isAuthed =
    !!getAccessToken() || !!localStorage.getItem("accessToken");

  if (!isAuthed) {
    return <Navigate to="/login" replace />;
  }

  return <Outlet />;
}

function App() {
  const [globalError, setGlobalError] = useState<string | null>(null);

  useEffect(() => {
    setApiErrorHandler((message: string) => {
      setGlobalError(message);
    });
  }, []);

  return (
    <>
      <Routes>
        {/* Publiczna trasa: login */}
        <Route path="/login" element={<Login />} />

        {/* Chronione trasy */}
        <Route element={<ProtectedRoute />}>
          <Route path="/" element={<Dashboard />} />
          <Route path="/summaries" element={<AISummary />} />
        </Route>

        {/* fallback */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>

      <GlobalErrorDialog
        message={globalError}
        onClose={() => setGlobalError(null)}
      />
    </>
  );
}

export default App;