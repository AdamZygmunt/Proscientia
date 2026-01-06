import React from "react";
import { motion } from "framer-motion";
import {
  FiFileText,
  FiUploadCloud,
  FiTrash2,
  FiDownload,
  FiPlay,
  FiAlertCircle,
  FiRefreshCw,
} from "react-icons/fi";
import {
  FaFilePdf,
  FaFileWord,
  FaFileAlt,
  FaFileCode,
} from "react-icons/fa";
import MainLayout from "../components/MainLayout";
import axiosInstance from "../utils/axiosInstance";

type DocumentItem = {
  id: number;
  title?: string;
  source?: string;
  description?: string;
  content_type?: string;
  uploaded_by_email?: string | null;
  file_url?: string | null;
  mock_stream?: string | null;
  mock_version_date?: string | null;
  mock_filename?: string | null;
  created_at?: string;
  updated_at?: string;
};

type SummaryArtifact = {
  id: number;
  title?: string;
  artifact_type?: string;
  file_url?: string | null;
  file?: string | null;
  document?: {
    id: number;
    title?: string;
  } | null;
  document_id?: number | null;
  metadata?: any;
  created_at?: string;
};

type TabKey = "files" | "summaries" | "manage";

const ALLOWED_EXTENSIONS = [
  "pdf",
  "txt",
  "json",
  "jsonl",
  "yaml",
  "yml",
  "xml",
  "doc",
  "docx",
];

function getFileExtension(name?: string | null): string {
  if (!name) return "";
  const parts = name.split(".");
  if (parts.length < 2) return "";
  return parts[parts.length - 1].toLowerCase();
}

function getFileIcon(ext: string) {
  if (ext === "pdf") return <FaFilePdf className="text-red-400" />;
  if (ext === "doc" || ext === "docx")
    return <FaFileWord className="text-blue-400" />;
  if (["json", "jsonl", "yaml", "yml", "xml"].includes(ext))
    return <FaFileCode className="text-emerald-400" />;
  return <FaFileAlt className="text-slate-300" />;
}

const AISummary: React.FC = () => {
  const [activeTab, setActiveTab] = React.useState<TabKey>("files");

  const [documents, setDocuments] = React.useState<DocumentItem[]>([]);
  const [documentsLoading, setDocumentsLoading] = React.useState<boolean>(true);

  const [summaries, setSummaries] = React.useState<SummaryArtifact[]>([]);
  const [summariesLoading, setSummariesLoading] = React.useState<boolean>(true);

  const [triggeringDocId, setTriggeringDocId] = React.useState<number | null>(
    null
  );
  const [erpMesReportLoading, setErpMesReportLoading] =
    React.useState<boolean>(false);

  const [uploadQueue, setUploadQueue] = React.useState<File[]>([]);
  const [uploading, setUploading] = React.useState<boolean>(false);
  const [localError, setLocalError] = React.useState<string | null>(null);

  const loadDocuments = React.useCallback(async () => {
    setDocumentsLoading(true);
    try {
      const res = await axiosInstance.get<DocumentItem[]>("/documents/");
      setDocuments(res.data || []);
    } catch {
      setDocuments([]);
    } finally {
      setDocumentsLoading(false);
    }
  }, []);

  const loadSummaries = React.useCallback(async () => {
    setSummariesLoading(true);
    try {
      const res = await axiosInstance.get<SummaryArtifact[]>(
        "/agents/artifacts/",
        {
          params: { type: "summary" },
        }
      );
      setSummaries(res.data || []);
    } catch {
      setSummaries([]);
    } finally {
      setSummariesLoading(false);
    }
  }, []);

  React.useEffect(() => {
    let mounted = true;
    (async () => {
      if (!mounted) return;
      await Promise.all([loadDocuments(), loadSummaries()]);
    })();
    return () => {
      mounted = false;
    };
  }, [loadDocuments, loadSummaries]);

  const docs = documents || [];
  const serverDocs = docs.filter(
    (d) => d.source && d.source !== "USER_UPLOAD"
  );
  const userDocs = docs.filter((d) => d.source === "USER_UPLOAD");
  const userDocsCount = userDocs.length;

  const groupedSummaries = React.useMemo(() => {
    const groups: {
      key: string;
      documentId: number | null;
      documentTitle: string;
      artifacts: SummaryArtifact[];
    }[] = [];

    const byKey: Record<
      string,
      {
        documentId: number | null;
        documentTitle: string;
        artifacts: SummaryArtifact[];
      }
    > = {};

    for (const art of summaries) {
      const nestedDoc = art.document as any;
      const docId =
        nestedDoc?.id ?? art.document_id ?? null;

      const docTitle =
        nestedDoc?.title ??
        art.metadata?.document_title ??
        "Nieznany dokument";

      const key = docId ? `doc-${docId}` : `nodoc-${art.id}`;

      if (!byKey[key]) {
        byKey[key] = {
          documentId: docId,
          documentTitle: docTitle,
          artifacts: [],
        };
      }
      byKey[key].artifacts.push(art);
    }

    for (const [key, value] of Object.entries(byKey)) {
      groups.push({
        key,
        documentId: value.documentId,
        documentTitle: value.documentTitle,
        artifacts: value.artifacts,
      });
    }

    // najnowsze na górze
    groups.sort((a, b) => {
      const aCreated = a.artifacts[0]?.created_at
        ? new Date(a.artifacts[0].created_at!).getTime()
        : 0;
      const bCreated = b.artifacts[0]?.created_at
        ? new Date(b.artifacts[0].created_at!).getTime()
        : 0;
      return bCreated - aCreated;
    });

    return groups;
  }, [summaries]);

  const handleTriggerSummary = async (docId: number) => {
    setLocalError(null);
    setTriggeringDocId(docId);
    try {
      await axiosInstance.post(`/agents/summarize/${docId}/`);
      await loadSummaries();
    } catch (err: any) {
      if (err.response?.data?.detail) {
        setLocalError(err.response.data.detail);
      } else if (err.isApiError) {
        setLocalError(err.message || "Błąd podczas uruchamiania streszczenia.");
      } else {
        setLocalError("Nie udało się uruchomić streszczenia.");
      }
    } finally {
      setTriggeringDocId(null);
    }
  };

  const handleGenerateErpMesReport = async () => {
    setLocalError(null);
    setErpMesReportLoading(true);
    try {
      await axiosInstance.post("/agents/erp-mes/latest-report/");
      await loadSummaries();
    } catch (err: any) {
      if (err.response?.data?.detail) {
        setLocalError(err.response.data.detail);
      } else if (err.isApiError) {
        setLocalError(
          err.message || "Błąd podczas generowania raportu ERP/MES."
        );
      } else {
        setLocalError("Nie udało się wygenerować raportu ERP/MES.");
      }
    } finally {
      setErpMesReportLoading(false);
    }
  };

    const handleDownloadUrl = (url?: string | null) => {
    if (!url) {
        setLocalError("Ten plik nie jest jeszcze dostępny do pobrania.");
        return;
    }
    // wymuszenie pobierania
    const link = document.createElement("a");
    link.href = url;
    link.target = "_blank";
    link.rel = "noopener noreferrer";
    link.download = ""; // pozwala przeglądarce potraktować to jako "download"
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    };

  const handleDeleteSummary = async (artifactId: number) => {
    setLocalError(null);
    try {
      await axiosInstance.delete(`/agents/artifacts/${artifactId}/`);
      await loadSummaries();
    } catch (err: any) {
      if (err.response?.data?.detail) {
        setLocalError(err.response.data.detail);
      } else if (err.isApiError) {
        setLocalError(
          err.message || "Nie udało się usunąć streszczenia."
        );
      } else {
        setLocalError("Nie udało się usunąć streszczenia.");
      }
    }
  };

  const handleFilesSelected = (files: FileList | null) => {
    if (!files || files.length === 0) return;
    setLocalError(null);

    const incoming = Array.from(files);

    const filtered = incoming.filter((file) => {
      const ext = getFileExtension(file.name);
      if (!ALLOWED_EXTENSIONS.includes(ext)) {
        return false;
      }
      return true;
    });

    if (filtered.length === 0) {
      setLocalError(
        "Żaden z wybranych plików nie ma dozwolonego rozszerzenia."
      );
      return;
    }

    // unikamy duplikatów po nazwie
    setUploadQueue((prev) => {
      const existingNames = new Set(prev.map((f) => f.name));
      const toAdd = filtered.filter((f) => !existingNames.has(f.name));
      return [...prev, ...toAdd];
    });
  };

  const handleUploadDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    handleFilesSelected(e.dataTransfer.files);
  };

  const handleUploadDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const handleRemoveFromQueue = (name: string) => {
    setUploadQueue((prev) => prev.filter((f) => f.name !== name));
  };

  const handleUploadAll = async () => {
    setLocalError(null);
    if (uploadQueue.length === 0) return;

    if (userDocsCount + uploadQueue.length > 5) {
      setLocalError(
        `Możesz mieć maksymalnie 5 własnych plików. Obecnie masz ${userDocsCount}, a chcesz dodać ${uploadQueue.length}.`
      );
      return;
    }

    setUploading(true);
    try {
      for (const file of uploadQueue) {
        const formData = new FormData();
        formData.append("file", file);

        await axiosInstance.post("/documents/upload/", formData);
      }

      setUploadQueue([]);
      await loadDocuments();
    } catch (err: any) {
      if (err.response?.data?.detail) {
        setLocalError(err.response.data.detail);
      } else if (err.isApiError) {
        setLocalError(err.message || "Błąd podczas uploadu plików.");
      } else {
        setLocalError("Nie udało się wgrać plików.");
      }
    } finally {
      setUploading(false);
    }
  };

  const handleDeleteDocument = async (docId: number) => {
    setLocalError(null);
    try {
        await axiosInstance.delete(`/documents/${docId}/`);
        await loadDocuments();
    } catch (err: any) {
        if (err.response?.data?.detail) {
        setLocalError(err.response.data.detail);
        } else if (err.isApiError) {
        setLocalError(err.message || "Nie udało się usunąć pliku.");
        } else {
        setLocalError("Nie udało się usunąć pliku.");
        }
    }
    };

  const renderDocumentTile = (
    doc: DocumentItem,
    opts: {
        mode: "trigger" | "download";
        canDelete?: boolean;
    }
    ) => {
    const ext =
        getFileExtension(doc.mock_filename || doc.title || "") ||
        getFileExtension(doc.file_url || "");
    const icon = getFileIcon(ext);
    const isTriggerMode = opts.mode === "trigger";
    const isBusy = isTriggerMode && triggeringDocId === doc.id;

    const handleClick = () => {
        if (isTriggerMode) {
        handleTriggerSummary(doc.id);
        } else {
        handleDownloadUrl(doc.file_url);
        }
    };

    const showDelete = opts.canDelete === true && doc.source === "USER_UPLOAD";


    return (
        <div
        key={doc.id}
        className="group flex flex-col rounded-xl border border-zinc-700/60 bg-zinc-900/80 px-3 py-3 hover:border-orange-400/80 hover:bg-zinc-900 transition-colors"
        >
        <div className="flex items-start justify-between gap-2">
            <button
            type="button"
            onClick={handleClick}
            className="flex flex-1 flex-col items-start gap-2 text-left"
            >
            <div className="flex items-center gap-2">
                <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-zinc-800/80">
                {icon}
                </div>
                <div className="flex flex-col">
                <span className="text-xs font-medium text-slate-100 truncate max-w-[200px]">
                    {doc.title || doc.mock_filename || `Dokument #${doc.id}`}
                </span>
                <span className="text-[0.65rem] text-slate-400">
                    {doc.source === "USER_UPLOAD"
                    ? "Mój plik"
                    : doc.source || "Mock"}
                </span>
                </div>
            </div>
            <div className="mt-1 flex w-full items-center justify-between text-[0.7rem] text-slate-400">
                {isTriggerMode ? (
                <>
                    <span className="flex items-center gap-1">
                    <FiFileText className="inline-block" />
                    Streszczaj
                    </span>
                    <span className="flex items-center gap-1 text-orange-400 group-hover:text-orange-300">
                    {isBusy ? "Uruchamianie..." : "Start"}
                    <FiPlay className="inline-block" />
                    </span>
                </>
                ) : (
                <>
                    <span className="flex items-center gap-1">
                    <FiDownload className="inline-block" />
                    Pobierz
                    </span>
                    <span className="text-slate-500">
                    {ext ? ext.toUpperCase() : ""}
                    </span>
                </>
                )}
            </div>
            </button>

            {showDelete && (
            <button
                type="button"
                onClick={() => handleDeleteDocument(doc.id)}
                className="ml-2 mt-1 inline-flex h-7 w-7 items-center justify-center rounded-md border border-red-500/70 text-red-400 hover:bg-red-500/10 text-xs"
                title="Usuń plik"
            >
                <FiTrash2 />
            </button>
            )}
        </div>
        </div>
    );
    };

  const renderUploadQueue = () => {
    if (uploadQueue.length === 0) {
      return (
        <p className="text-xs text-slate-400">
          Brak plików w kolejce. Dodaj pliki przez kliknięcie lub drag & drop.
        </p>
      );
    }

    return (
      <ul className="mt-2 space-y-1 max-h-40 overflow-y-auto pr-1">
        {uploadQueue.map((file) => {
          const ext = getFileExtension(file.name);
          const icon = getFileIcon(ext);

          return (
            <li
              key={file.name}
              className="flex items-center justify-between gap-2 rounded-lg bg-zinc-900/70 px-2 py-1 text-xs"
            >
              <div className="flex items-center gap-2">
                <div className="flex h-7 w-7 items-center justify-center rounded-md bg-zinc-800/80">
                  {icon}
                </div>
                <div className="flex flex-col">
                  <span className="truncate max-w-[200px] text-slate-100">
                    {file.name}
                  </span>
                  <span className="text-[0.65rem] text-slate-500">
                    {(file.size / 1024).toFixed(1)} KB
                  </span>
                </div>
              </div>
              <button
                type="button"
                onClick={() => handleRemoveFromQueue(file.name)}
                className="inline-flex items-center justify-center rounded-md border border-red-500/60 px-2 py-1 text-[0.65rem] text-red-400 hover:bg-red-500/10"
              >
                <FiTrash2 className="mr-1" />
                Usuń
              </button>
            </li>
          );
        })}
      </ul>
    );
  };

  const renderTabButtons = () => (
    <div className="mb-4 flex flex-wrap gap-2 text-xs">
      <button
        type="button"
        onClick={() => setActiveTab("files")}
        className={`rounded-full px-3 py-1 border ${
          activeTab === "files"
            ? "border-orange-400 bg-orange-500/10 text-orange-300"
            : "border-zinc-600 bg-zinc-900 text-slate-200 hover:border-orange-400/80"
        }`}
      >
        Pliki
      </button>
      <button
        type="button"
        onClick={() => setActiveTab("summaries")}
        className={`rounded-full px-3 py-1 border ${
          activeTab === "summaries"
            ? "border-orange-400 bg-orange-500/10 text-orange-300"
            : "border-zinc-600 bg-zinc-900 text-slate-200 hover:border-orange-400/80"
        }`}
      >
        Streszczenia
      </button>
      <button
        type="button"
        onClick={() => setActiveTab("manage")}
        className={`rounded-full px-3 py-1 border ${
          activeTab === "manage"
            ? "border-orange-400 bg-orange-500/10 text-orange-300"
            : "border-zinc-600 bg-zinc-900 text-slate-200 hover:border-orange-400/80"
        }`}
      >
        Pobierz / Dodaj
      </button>
    </div>
  );

  const renderFilesTab = () => (
    <div className="grid gap-4 md:grid-cols-2">
      <motion.div
        initial={{ opacity: 0, y: 6 }}
        animate={{ opacity: 1, y: 0 }}
        className="card-surface p-4 flex flex-col gap-2 rounded-2xl border border-zinc-300/30 dark:border-zinc-800/80 bg-zinc-200/70 dark:bg-zinc-900/60"
      >
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-sm font-semibold text-slate-100">
              Dostępne pliki (serwer ERP/MES)
            </h2>
            <p className="text-[0.7rem] text-slate-400">
              Dokumenty z mock ERP/MES i inne przykładowe pliki serwerowe.
            </p>
          </div>
          <button
            type="button"
            onClick={handleGenerateErpMesReport}
            disabled={erpMesReportLoading}
            className="inline-flex items-center gap-1 rounded-full border border-emerald-500/70 px-3 py-1 text-[0.7rem] text-emerald-300 hover:bg-emerald-500/10 disabled:opacity-60"
          >
            {erpMesReportLoading ? (
              <>
                <FiRefreshCw className="animate-spin" />
                Generowanie...
              </>
            ) : (
              <>
                <FiPlay />
                Raport ERP/MES
              </>
            )}
          </button>
        </div>

        {documentsLoading ? (
          <p className="mt-4 text-xs text-slate-400">Ładowanie dokumentów...</p>
        ) : serverDocs.length === 0 ? (
          <p className="mt-4 text-xs text-slate-400">
            Brak plików z mock ERP/MES.
          </p>
        ) : (
          <div className="mt-3 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2">
            {serverDocs.map((doc) =>
              renderDocumentTile(doc, { mode: "trigger", canDelete: false })
            )}
          </div>
        )}
      </motion.div>

      <motion.div
        initial={{ opacity: 0, y: 6 }}
        animate={{ opacity: 1, y: 0 }}
        className="card-surface p-4 flex flex-col gap-2 rounded-2xl border border-zinc-300/30 dark:border-zinc-800/80 bg-zinc-200/70 dark:bg-zinc-900/60"
      >
        <h2 className="text-sm font-semibold text-slate-100">
          Moje pliki (do streszczania)
        </h2>
        <p className="text-[0.7rem] text-slate-400">
          Własne dokumenty wgrane przez Ciebie – maksymalnie 5 na użytkownika.
        </p>
        <p className="mt-1 text-[0.7rem] text-slate-500">
          Aktualnie: {userDocsCount} / 5 plików.
        </p>

        {documentsLoading ? (
          <p className="mt-4 text-xs text-slate-400">Ładowanie...</p>
        ) : userDocs.length === 0 ? (
          <p className="mt-4 text-xs text-slate-400">
            Nie masz jeszcze żadnych własnych plików. Dodaj je w zakładce{" "}
            <span className="font-semibold">Pobierz / Dodaj</span>.
          </p>
        ) : (
          <div className="mt-3 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2">
            {userDocs.map((doc) =>
                renderDocumentTile(doc, { mode: "trigger", canDelete: true })
            )}
          </div>
        )}
      </motion.div>
    </div>
  );

  const renderSummariesTab = () => (
    <motion.div
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      className="card-surface p-4 flex flex-col gap-3 rounded-2xl border border-zinc-300/30 dark:border-zinc-800/80 bg-zinc-200/70 dark:bg-zinc-900/60"
    >
      <h2 className="text-sm font-semibold text-slate-100">Streszczenia</h2>
      <p className="text-[0.7rem] text-slate-400">
        Zgrupowane według dokumentu. Maksymalnie 3 streszczenia na dokument
        (limit wymuszany po stronie backendu).
      </p>

      {summariesLoading ? (
        <p className="mt-2 text-xs text-slate-400">Ładowanie streszczeń...</p>
      ) : groupedSummaries.length === 0 ? (
        <p className="mt-2 text-xs text-slate-400">
          Nie masz jeszcze żadnych streszczeń. Uruchom agenta dla wybranego
          pliku w zakładce <span className="font-semibold">Pliki</span>.
        </p>
      ) : (
        <div className="mt-3 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          {groupedSummaries.map((group) => {
            const docTitle = group.documentTitle;
            const artifacts = group.artifacts;

            return (
              <div
                key={group.key}
                className="flex flex-col rounded-xl border border-zinc-700/70 bg-zinc-900/80 px-3 py-3"
              >
                <div className="flex items-center gap-2 mb-2">
                  <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-zinc-800/80">
                    <FiFileText className="text-orange-300" />
                  </div>
                  <div className="flex flex-col">
                    <span className="text-xs font-semibold text-slate-100 truncate max-w-[210px]">
                      {docTitle}
                    </span>
                    <span className="text-[0.65rem] text-slate-500">
                      {artifacts.length} streszczeń
                    </span>
                  </div>
                </div>

                {artifacts.length === 0 ? (
                  <p className="text-[0.7rem] text-slate-500">
                    No summaries available.
                  </p>
                ) : (
                  <ul className="space-y-1">
                    {artifacts.map((art) => {
                      const fileUrl =
                        art.file_url || (art.file as string | undefined);
                      const created =
                        art.created_at &&
                        !Number.isNaN(new Date(art.created_at).getTime())
                          ? new Date(
                              art.created_at
                            ).toLocaleString("pl-PL", {
                              dateStyle: "short",
                              timeStyle: "short",
                            })
                          : "";

                      return (
                        <li
                          key={art.id}
                          className="flex items-center justify-between rounded-lg bg-zinc-900 px-2 py-1 text-[0.7rem]"
                        >
                          <div className="flex flex-col">
                            <span className="text-slate-100 truncate max-w-[180px]">
                              {art.title || "Streszczenie"}
                            </span>
                            {created && (
                              <span className="text-[0.6rem] text-slate-500">
                                {created}
                              </span>
                            )}
                          </div>
                          <div className="flex items-center gap-1">
                            <button
                              type="button"
                              onClick={() => handleDownloadUrl(fileUrl)}
                              className="inline-flex items-center justify-center rounded-md border border-emerald-500/70 px-2 py-1 text-[0.7rem] text-emerald-300 hover:bg-emerald-500/10"
                            >
                              <FiDownload className="mr-1" />
                              Pobierz
                            </button>
                            <button
                              type="button"
                              onClick={() => handleDeleteSummary(art.id)}
                              className="inline-flex items-center justify-center rounded-md border border-red-500/70 px-2 py-1 text-[0.7rem] text-red-400 hover:bg-red-500/10"
                            >
                              <FiTrash2 />
                            </button>
                          </div>
                        </li>
                      );
                    })}
                  </ul>
                )}
              </div>
            );
          })}
        </div>
      )}
    </motion.div>
  );

  const renderManageTab = () => (
    <div className="grid gap-4 md:grid-cols-2">
      <motion.div
        initial={{ opacity: 0, y: 6 }}
        animate={{ opacity: 1, y: 0 }}
        className="card-surface p-4 flex flex-col gap-2 rounded-2xl border border-zinc-300/30 dark:border-zinc-800/80 bg-zinc-200/70 dark:bg-zinc-900/60"
      >
        <h2 className="text-sm font-semibold text-slate-100">
          Pobierz istniejące pliki
        </h2>
        <p className="text-[0.7rem] text-slate-400">
          Kliknij kafelek, aby pobrać dokument źródłowy. W zależności od
          źródła plik może być już pobrany z mocka (ERP/MES).
        </p>

        {documentsLoading ? (
          <p className="mt-4 text-xs text-slate-400">Ładowanie...</p>
        ) : docs.length === 0 ? (
          <p className="mt-4 text-xs text-slate-400">
            Brak dokumentów w systemie.
          </p>
        ) : (
          <div className="mt-3 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2">
            {docs.map((doc) =>
                renderDocumentTile(doc, {
                    mode: "download",
                    canDelete: doc.source === "USER_UPLOAD",
                })
            )}
          </div>
        )}
      </motion.div>

      <motion.div
        initial={{ opacity: 0, y: 6 }}
        animate={{ opacity: 1, y: 0 }}
        className="card-surface p-4 flex flex-col gap-2 rounded-2xl border border-zinc-300/30 dark:border-zinc-800/80 bg-zinc-200/70 dark:bg-zinc-900/60"
      >
        <h2 className="text-sm font-semibold text-slate-100">
          Dodaj nowe pliki
        </h2>
        <p className="text-[0.7rem] text-slate-400">
          Dozwolone rozszerzenia:{" "}
          <span className="font-mono">
            {ALLOWED_EXTENSIONS.join(", ")}
          </span>
          . Maksymalnie 5 plików użytkownika w systemie.
        </p>
        <p className="text-[0.7rem] text-slate-500">
          Aktualnie masz{" "}
          <span className="font-semibold">{userDocsCount}</span> / 5
          własnych plików.
        </p>

        <div
          onDrop={handleUploadDrop}
          onDragOver={handleUploadDragOver}
          className="mt-3 flex flex-col items-center justify-center rounded-xl border border-dashed border-zinc-600 bg-zinc-900/70 px-4 py-6 text-center cursor-pointer hover:border-orange-400/80"
          onClick={() => {
            const input = document.getElementById(
              "ai-summary-file-input"
            ) as HTMLInputElement | null;
            if (input) {
              input.click();
            }
          }}
        >
          <FiUploadCloud className="mb-2 text-xl text-orange-300" />
          <p className="text-xs text-slate-200">
            Przeciągnij pliki tutaj lub kliknij, aby je wybrać
          </p>
          <p className="mt-1 text-[0.65rem] text-slate-500">
            Pliki nie zostaną wgrane od razu – najpierw pojawią się w liście
            poniżej, potem kliknij <span className="font-semibold">Upload</span>.
          </p>
          <input
            id="ai-summary-file-input"
            type="file"
            multiple
            className="hidden"
            accept={ALLOWED_EXTENSIONS.map((ext) => "." + ext).join(",")}
            onChange={(e) => handleFilesSelected(e.target.files)}
          />
        </div>

        <div className="mt-3">
          {renderUploadQueue()}
        </div>

        <div className="mt-3 flex items-center justify-between">
          <p className="text-[0.7rem] text-slate-500">
            Po wgraniu pliki pojawią się w zakładkach{" "}
            <span className="font-semibold">Pliki</span> oraz{" "}
            <span className="font-semibold">Pobierz / Dodaj</span>.
          </p>
          <button
            type="button"
            onClick={handleUploadAll}
            disabled={uploading || uploadQueue.length === 0}
            className="inline-flex items-center gap-1 rounded-full border border-orange-500/80 bg-orange-500/10 px-3 py-1 text-[0.75rem] text-orange-200 hover:bg-orange-500/20 disabled:opacity-60"
          >
            {uploading ? "Wgrywanie..." : "Upload"}
          </button>
        </div>
      </motion.div>
    </div>
  );

  return (
    <MainLayout
      title="Agent streszczeń"
      subtitle="Zarządzaj dokumentami, uruchamiaj streszczenia agentowe i pobieraj wygenerowane raporty."
    >
      <div className="space-y-4">
        {renderTabButtons()}

        {localError && (
          <div className="flex items-start gap-2 rounded-lg border border-red-500/70 bg-red-950/40 px-3 py-2 text-xs text-red-200">
            <FiAlertCircle className="mt-[2px]" />
            <p>{localError}</p>
          </div>
        )}

        {activeTab === "files" && renderFilesTab()}
        {activeTab === "summaries" && renderSummariesTab()}
        {activeTab === "manage" && renderManageTab()}
      </div>
    </MainLayout>
  );
};

export default AISummary;
