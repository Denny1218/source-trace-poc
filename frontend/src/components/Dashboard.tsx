import { useCallback, useEffect, useState } from "react";
import { fetchHealth, type HealthStatus } from "../api/health";
import "./Dashboard.css";

function statusClass(value: string): string {
  if (value === "ok" || value === "available") return "status-ok";
  if (value === "error" || value === "unavailable" || value === "degraded")
    return "status-error";
  return "status-unknown";
}

function labelFor(key: keyof HealthStatus): string {
  const labels: Record<keyof HealthStatus, string> = {
    status: "Backend 연결 상태",
    database: "Database 상태",
    git: "Git 사용 가능 여부",
    ollama: "Ollama 연결 상태",
  };
  return labels[key];
}

export default function Dashboard() {
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [backendConnected, setBackendConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const loadHealth = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchHealth();
      setHealth(data);
      setBackendConnected(true);
    } catch (err) {
      setBackendConnected(false);
      setHealth(null);
      setError(err instanceof Error ? err.message : "연결 실패");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadHealth();
    const interval = setInterval(loadHealth, 30000);
    return () => clearInterval(interval);
  }, [loadHealth]);

  const displayItems: { key: string; label: string; value: string }[] = [
    {
      key: "backend",
      label: "Backend 연결 상태",
      value: backendConnected ? "ok" : "error",
    },
    ...(health
      ? (["database", "git", "ollama"] as const).map((key) => ({
          key,
          label: labelFor(key),
          value: health[key],
        }))
      : [
          { key: "database", label: "Database 상태", value: "unknown" },
          { key: "git", label: "Git 사용 가능 여부", value: "unknown" },
          { key: "ollama", label: "Ollama 연결 상태", value: "unknown" },
        ]),
  ];

  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <h1>장비 소스 변경 이력 추적</h1>
        <p className="subtitle">AI 기반 장비 소스 변경 이력 추적 및 유지보수 지원 POC</p>
      </header>

      <section className="status-card">
        <div className="status-card-header">
          <h2>시스템 상태</h2>
          <button type="button" onClick={loadHealth} disabled={loading}>
            {loading ? "확인 중..." : "새로고침"}
          </button>
        </div>

        {error && (
          <div className="error-banner">
            Backend에 연결할 수 없습니다. FastAPI 서버(포트 8010)가 실행 중인지 확인하세요.
            <br />
            <span className="error-detail">{error}</span>
          </div>
        )}

        <ul className="status-list">
          {displayItems.map((item) => (
            <li key={item.key} className="status-item">
              <span className="status-label">{item.label}</span>
              <span className={`status-value ${statusClass(item.value)}`}>
                {item.value}
              </span>
            </li>
          ))}
        </ul>
      </section>
    </div>
  );
}
