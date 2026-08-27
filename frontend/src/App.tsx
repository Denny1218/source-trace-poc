import { useCallback, useEffect, useRef, useState } from "react";
import Dashboard from "./components/Dashboard";
import EquipmentManager from "./components/EquipmentManager";
import EvidenceLinkViewer from "./components/EvidenceLinkViewer";
import GitHistory from "./components/GitHistory";
import PptCacheViewer from "./components/PptCacheViewer";
import SourceTraceViewer from "./components/SourceTraceViewer";
import type { TabWorkStatus } from "./types/tabWork";
import "./App.css";

type PublicTab = "dashboard" | "equipment" | "history" | "ppt-cache" | "source-trace";
type HiddenTab = "evidence-dev";
type Tab = PublicTab | HiddenTab;

const TAB_LABELS: Record<Tab, string> = {
  dashboard: "시스템 상태",
  equipment: "장비 관리",
  history: "Git 변경 이력",
  "ppt-cache": "변경내역서 분석",
  "source-trace": "Source Trace 조회",
  "evidence-dev": "Evidence Link 검증",
};

function workBadge(status: TabWorkStatus): string {
  if (status === "running") return " ●";
  if (status === "success") return " ✓";
  if (status === "error") return " !";
  return "";
}

const PUBLIC_TABS: PublicTab[] = ["dashboard", "equipment", "history", "ppt-cache", "source-trace"];

function tabFromHash(hash: string): HiddenTab | null {
  if (hash === "#evidence-dev") return "evidence-dev";
  return null;
}

function App() {
  const [tab, setTab] = useState<Tab>(tabFromHash(window.location.hash) ?? "dashboard");
  const [equipmentVersion, setEquipmentVersion] = useState(0);
  const [historyWork, setHistoryWork] = useState<TabWorkStatus>("idle");
  const [pptWork, setPptWork] = useState<TabWorkStatus>("idle");
  const [toast, setToast] = useState<{
    tab: Tab;
    message: string;
    type: "success" | "error";
  } | null>(null);
  const tabRef = useRef<Tab>(tab);

  useEffect(() => {
    tabRef.current = tab;
  }, [tab]);

  useEffect(() => {
    const syncHashTab = () => {
      const hiddenTab = tabFromHash(window.location.hash);
      if (hiddenTab) {
        setTab(hiddenTab);
      }
    };
    window.addEventListener("hashchange", syncHashTab);
    return () => window.removeEventListener("hashchange", syncHashTab);
  }, []);

  const refreshEquipmentList = useCallback(() => {
    setEquipmentVersion((version) => version + 1);
  }, []);

  const notifyIfBackground = useCallback(
    (targetTab: Tab, status: TabWorkStatus, message?: string) => {
      if (status !== "success" && status !== "error") return;
      if (tabRef.current === targetTab) return;
      const fallback =
        status === "success"
          ? `${TAB_LABELS[targetTab]} 작업이 완료되었습니다.`
          : `${TAB_LABELS[targetTab]} 작업에 실패했습니다.`;
      setToast({
        tab: targetTab,
        message: message ?? fallback,
        type: status === "success" ? "success" : "error",
      });
    },
    [],
  );

  const handlePublicTabChange = useCallback((nextTab: PublicTab) => {
    if (window.location.hash === "#evidence-dev") {
      window.history.replaceState(null, "", `${window.location.pathname}${window.location.search}`);
    }
    setTab(nextTab);
  }, []);

  const handleHistoryWork = useCallback(
    (status: TabWorkStatus, message?: string) => {
      setHistoryWork(status);
      notifyIfBackground("history", status, message);
      if ((status === "success" || status === "error") && tabRef.current === "history") {
        window.setTimeout(() => setHistoryWork("idle"), 4000);
      }
    },
    [notifyIfBackground],
  );

  const handlePptWork = useCallback(
    (status: TabWorkStatus, message?: string) => {
      setPptWork(status);
      notifyIfBackground("ppt-cache", status, message);
      if ((status === "success" || status === "error") && tabRef.current === "ppt-cache") {
        window.setTimeout(() => setPptWork("idle"), 4000);
      }
    },
    [notifyIfBackground],
  );

  useEffect(() => {
    if (!toast) return;
    const timer = window.setTimeout(() => setToast(null), 6000);
    return () => window.clearTimeout(timer);
  }, [toast]);

  return (
    <div className="app">
      <header className="app-header">
        <div className="brand">
          <img
            src="/static/brand/logo_web_header.png"
            srcSet="/static/brand/logo_web_header.png 1x, /static/brand/logo_web_header_2x.png 2x"
            alt="ATEC Mobility"
            className="brand-logo"
          />
        </div>
        <nav className="app-nav">
          {PUBLIC_TABS.map((key) => (
            <button
              key={key}
              type="button"
              className={tab === key ? "active" : ""}
              onClick={() => handlePublicTabChange(key)}
            >
              {TAB_LABELS[key]}
              {key === "history" ? workBadge(historyWork) : ""}
              {key === "ppt-cache" ? workBadge(pptWork) : ""}
            </button>
          ))}
        </nav>
      </header>
      {toast && (
        <div className={`app-toast ${toast.type}`} role="status">
          {toast.message}
          <button type="button" className="app-toast-dismiss" onClick={() => setToast(null)}>
            닫기
          </button>
        </div>
      )}
      <main>
        <div className="tab-panel" hidden={tab !== "dashboard"}>
          <Dashboard />
        </div>
        <div className="tab-panel" hidden={tab !== "equipment"}>
          <EquipmentManager onEquipmentChange={refreshEquipmentList} />
        </div>
        <div className="tab-panel" hidden={tab !== "history"}>
          <GitHistory
            equipmentVersion={equipmentVersion}
            onWorkStatusChange={handleHistoryWork}
          />
        </div>
        <div className="tab-panel" hidden={tab !== "ppt-cache"}>
          <PptCacheViewer
            equipmentVersion={equipmentVersion}
            onWorkStatusChange={handlePptWork}
          />
        </div>
        <div className="tab-panel" hidden={tab !== "source-trace"}>
          <SourceTraceViewer equipmentVersion={equipmentVersion} />
        </div>
        <div className="tab-panel" hidden={tab !== "evidence-dev"}>
          <EvidenceLinkViewer equipmentVersion={equipmentVersion} />
        </div>
      </main>
    </div>
  );
}

export default App;
