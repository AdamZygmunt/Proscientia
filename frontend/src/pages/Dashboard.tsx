import React from "react";
import { motion } from "framer-motion";
import MainLayout from "../components/MainLayout";
import axiosInstance from "../utils/axiosInstance";

type ErpMesSnapshot = {
  id: number;
  stream: "erp" | "mes" | string;
  version_date: string;
  is_latest?: boolean;
  files?: unknown[] | null;
};

type DocumentItem = {
  id: number;
  title?: string;
  source?: string;
  is_mock_doc?: boolean;
  is_mock_erp_mes?: boolean;
  created_at?: string;
};

const formatDate = (dateStr?: string) => {
  if (!dateStr) return "–";
  const d = new Date(dateStr);
  if (Number.isNaN(d.getTime())) return dateStr;
  return d.toLocaleDateString("pl-PL");
};

const Dashboard: React.FC = () => {
  const [snapshots, setSnapshots] = React.useState<ErpMesSnapshot[] | null>(null);
  const [snapshotsLoading, setSnapshotsLoading] = React.useState(true);

  const [documents, setDocuments] = React.useState<DocumentItem[] | null>(null);
  const [documentsLoading, setDocumentsLoading] = React.useState(true);

  const [syncLoading, setSyncLoading] = React.useState(false);

  const loadAllData = React.useCallback(async () => {
    setSnapshotsLoading(true);
    setDocumentsLoading(true);
    try {
      const [snapRes, docRes] = await Promise.all([
        axiosInstance.get<ErpMesSnapshot[]>("/erp-mes/snapshots/"),
        axiosInstance.get<DocumentItem[]>("/documents/"),
      ]);

      setSnapshots(snapRes.data || []);
      setDocuments(docRes.data || []);

      console.log("Loaded snapshots:", snapRes.data);
      console.log("Loaded documents:", docRes.data);
    } catch {
      // Błędy złapie GlobalErrorDialog z axiosInstance,
      // tutaj tylko czyścimy dane, żeby pokazać "brak informacji".
      setSnapshots([]);
      setDocuments([]);
    } finally {
      setSnapshotsLoading(false);
      setDocumentsLoading(false);
    }
  }, []);

  React.useEffect(() => {
    let isMounted = true;

    (async () => {
      if (!isMounted) return;
      await loadAllData();
    })();

    return () => {
      isMounted = false;
    };
  }, [loadAllData]);

  const handleSyncClick = async () => {
    setSyncLoading(true);
    try {
      // ręczne wywołanie synchronizacji z mock ERP/MES
      await axiosInstance.post("/erp-mes/snapshots/sync/");
      // po udanej synchronizacji odśwież dane na dashboardzie
      await loadAllData();
    } catch {
      // błąd pokaże GlobalErrorDialog
    } finally {
      setSyncLoading(false);
    }
  };

  const erpSnapshots = (snapshots || []).filter((s) => s.stream === "erp");
  const mesSnapshots = (snapshots || []).filter((s) => s.stream === "mes");

  const latestErp =
    erpSnapshots.find((s) => s.is_latest) ||
    (erpSnapshots.length > 0 ? erpSnapshots[erpSnapshots.length - 1] : undefined);

  const latestMes =
    mesSnapshots.find((s) => s.is_latest) ||
    (mesSnapshots.length > 0 ? mesSnapshots[mesSnapshots.length - 1] : undefined);

  const totalErpFiles = erpSnapshots.reduce(
    (sum, s: any) => sum + (s.files_count ?? 0),
    0
  );
  const totalMesFiles = mesSnapshots.reduce(
    (sum, s: any) => sum + (s.files_count ?? 0),
    0
  );


  const docs = documents || [];
  const totalDocs = docs.length;
  const mockErpDocs = docs.filter((d) => d.is_mock_erp_mes).length;
  const mockOtherDocs = docs.filter((d) => d.is_mock_doc && !d.is_mock_erp_mes).length;
  const userDocs = totalDocs - mockErpDocs - mockOtherDocs;
  const latestDoc = docs[0];

  const renderSkeletonCard = () => (
    <div className="card-surface min-h-[160px] rounded-2xl border border-zinc-300/30 dark:border-zinc-800/70 bg-zinc-200/70 dark:bg-zinc-900/60 animate-pulse">
      <div className="h-5 w-1/3 rounded bg-zinc-300/70 dark:bg-zinc-700/80 mb-3" />
      <div className="space-y-2">
        <div className="h-3 w-2/3 rounded bg-zinc-300/70 dark:bg-zinc-700/80" />
        <div className="h-3 w-1/2 rounded bg-zinc-300/70 dark:bg-zinc-700/80" />
        <div className="h-3 w-1/4 rounded bg-zinc-300/70 dark:bg-zinc-700/80" />
      </div>
    </div>
  );

  return (
    <MainLayout
      title="Proscientia Dashboard"
      subtitle="Podgląd agentów AI, danych ERP/MES i dokumentów."
    >
      {/* Karta powitalna */}
      <motion.section
        className="card-surface p-6 rounded-2xl border border-zinc-300/30 dark:border-zinc-800/80 bg-zinc-200/70 dark:bg-zinc-900/60"
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.35 }}
      >
        <h2 className="text-2xl font-semibold mb-3 text-orange-500 dark:text-orange-400">Witaj w panelu Proscientia</h2>
        <p className="text-md text-zinc-800 dark:text-zinc-400 text-justify">
          To jest główna strona aplikacji – szybki podgląd danych ERP/MES,
          dokumentów oraz (docelowo) aktywności agentów AI. Szczegółowe operacje,
          takie jak generowanie streszczeń, testów czy zapytania DocSearch,
          będą dostępne w dedykowanych zakładkach.
        </p>
      </motion.section>

      {/* Główna siatka kafelków */}
      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-3 mt-4">
        {/* ERP/MES */}
        <motion.div
          className="card-surface min-h-[160px] rounded-2xl border border-zinc-300/30 dark:border-zinc-800/80 bg-zinc-200/80 dark:bg-zinc-900/60 p-5"
          initial={{ opacity: 0, y: 18 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, delay: 0.05 }}
        >
          {snapshotsLoading ? (
            renderSkeletonCard()
          ) : (
            <>
              <div className="flex items-center justify-between mb-2 gap-3">
                <h3 className="text-xl font-semibold text-orange-500 dark:text-orange-400">Snapshoty ERP/MES</h3>
                <motion.button
                  type="button"
                  onClick={handleSyncClick}
                  disabled={syncLoading || snapshotsLoading}
                  whileTap={{ scale: syncLoading ? 1 : 0.97 }}
                  className="btn-gradient-primary px-3 py-1.5 text-xs font-medium disabled:opacity-60 disabled:cursor-not-allowed whitespace-nowrap min-h-[2rem]"
                >
                  {syncLoading ? "Synchronizuję..." : "Synchronizuj z mock ERP/MES"}
                </motion.button>
              </div>
              {snapshots && snapshots.length > 0 ? (
                <div className="space-y-5 mt-8 text-md text-justify text-zinc-900 dark:text-zinc-300">
                  <div className="flex justify-between">
                    <span className="font-medium">Liczba snapshotów ERP:</span>
                    <span className="text-orange-500 dark:text-orange-400">{erpSnapshots.length}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="font-medium">Liczba snapshotów MES:</span>
                    <span className="text-orange-500 dark:text-orange-400">{mesSnapshots.length}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="font-medium">Łącznie plików ERP:</span>
                    <span className="text-orange-500 dark:text-orange-400">{totalErpFiles}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="font-medium">Łącznie plików MES:</span>
                    <span className="text-orange-500 dark:text-orange-400">{totalMesFiles}</span>
                  </div>
                  <div className="mt-2 border-t border-zinc-300/40 dark:border-zinc-700/60 pt-2 space-y-2 text-right">
                    <p className="mt-3 text-sm text-zinc-800 dark:text-zinc-400">
                      Ostatni snapshot ERP:{" "}
                      <span className="font-medium text-orange-500 dark:text-orange-400">
                        {latestErp ? formatDate(latestErp.version_date) : "brak danych"}
                      </span>
                    </p>
                    <p className="text-sm text-zinc-800 dark:text-zinc-400">
                      Ostatni snapshot MES:{" "}
                      <span className="font-medium text-orange-500 dark:text-orange-400">
                        {latestMes ? formatDate(latestMes.version_date) : "brak danych"}
                      </span>
                    </p>
                  </div>
                </div>
              ) : (
                <p className="text-sm text-center my-[3.5rem] text-zinc-800 dark:text-zinc-400">
                  Brak informacji o snapshotach ERP/MES. Upewnij się, że wykonano
                  synchronizację z systemem mock.
                </p>
              )}
            </>
          )}
        </motion.div>

        {/* Dokumenty */}
        <motion.div
          className="card-surface min-h-[160px] rounded-2xl border border-zinc-300/30 dark:border-zinc-800/80 bg-zinc-200/80 dark:bg-zinc-900/60 p-5"
          initial={{ opacity: 0, y: 18 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, delay: 0.1 }}
        >
          {documentsLoading ? (
            renderSkeletonCard()
          ) : (
            <>
              <h3 className="text-xl font-semibold mb-3 text-orange-500 dark:text-orange-400">Dokumenty w systemie</h3>
              {totalDocs > 0 ? (
                <div className="space-y-3 text-sm text-justify text-zinc-900 dark:text-zinc-300">
                  <div className="flex justify-between">
                    <span className="font-medium">Łącznie dokumentów:</span>
                    <span>{totalDocs}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="font-medium">Z ERP/MES (mock):</span>
                    <span>{mockErpDocs}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="font-medium">Inne dokumenty mock:</span>
                    <span>{mockOtherDocs}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="font-medium">Uploady użytkowników:</span>
                    <span>{userDocs}</span>
                  </div>
                  <div className="mt-2 border-t border-zinc-300/40 dark:border-zinc-700/60 pt-2 space-y-1">
                    <p className="text-[11px] text-zinc-800 dark:text-zinc-400">
                      Ostatnio dodany:{" "}
                      <span className="font-medium">
                        {latestDoc?.title || "brak tytułu / brak danych"}
                      </span>
                    </p>
                    {latestDoc?.created_at && (
                      <p className="text-[11px] text-zinc-800 dark:text-zinc-400">
                        Data dodania:{" "}
                        <span className="font-medium">
                          {formatDate(latestDoc.created_at)}
                        </span>
                      </p>
                    )}
                  </div>
                </div>
              ) : (
                <p className="text-sm text-center my-[25%] text-zinc-800 dark:text-zinc-400">
                  Brak dokumentów w systemie. Dodaj pierwszy dokument lub
                  zsynchronizuj pliki z ERP/MES.
                </p>
              )}
            </>
          )}
        </motion.div>

        {/* Agenci AI – placeholder na przyszłe statystyki */}
        <motion.div
          className="card-surface min-h-[160px] rounded-2xl border border-zinc-300/30 dark:border-zinc-800/80 bg-zinc-200/80 dark:bg-zinc-900/60 p-5"
          initial={{ opacity: 0, y: 18 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, delay: 0.15 }}
        >
          <h3 className="text-xl font-semibold mb-3 text-orange-500 dark:text-orange-400">Agenci AI (podgląd)</h3>
          <p className="text-sm text-zinc-800 dark:text-zinc-400 mb-3 text-justify">
            Moduł agentów (streszczenia, testy wiedzy, DocSearch) jest w trakcie
            wdrażania. W tym miejscu pojawi się podgląd liczby zadań w toku,
            zakończonych oraz podstawowe statystyki skuteczności.
          </p>
          <div className="grid grid-cols-3 gap-2 text-center text-[11px] text-zinc-900 dark:text-zinc-200 mt-12">
            <div className="rounded-xl bg-zinc-400/30 dark:bg-zinc-800/70 px-2 py-2">
              <div className="text-xs font-semibold text-orange-500 dark:text-orange-400 mb-1">W toku</div>
              <div className="text-lg font-bold">0</div>
            </div>
            <div className="rounded-xl bg-zinc-400/30 dark:bg-zinc-800/70 px-2 py-2">
              <div className="text-xs font-semibold text-orange-500 dark:text-orange-400 mb-1">Zakończone</div>
              <div className="text-lg font-bold">0</div>
            </div>
            <div className="rounded-xl bg-zinc-400/30 dark:bg-zinc-800/70 px-2 py-2">
              <div className="text-xs font-semibold text-orange-500 dark:text-orange-400 mb-1">Błędy</div>
              <div className="text-lg font-bold">0</div>
            </div>
          </div>
        </motion.div>
      </section>
    </MainLayout>
  );
};

export default Dashboard;
