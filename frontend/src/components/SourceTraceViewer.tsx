import { useCallback, useEffect, useMemo, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { fetchEquipmentList, type Equipment } from "../api/equipment";
import { fetchRepositories, type GitRepository } from "../api/repositories";
import {
  buildTraceReportRequest,
  buildTraceSelectionRequest,
  fetchTraceReport,
  fetchTraceSelection,
  getRepositorySelectionState,
  mapSourceTraceErrorMessage,
  type SourceTraceReportForm,
  type SourceTraceSelectionForm,
} from "../api/sourceTrace";
import LongRunningTaskPanel from "./LongRunningTaskPanel";
import { copyTextToClipboard } from "../utils/clipboardUtils";
import "./SourceTraceViewer.css";

interface SourceTraceViewerProps {
  equipmentVersion: number;
}

type TraceMode = "report" | "selection";

type ResultState =
  | {
      mode: "report";
      equipmentName: string;
      repositoryName?: string;
      filePath?: string;
      functionName: string;
      content: string;
    }
  | {
      mode: "selection";
      equipmentName: string;
      repositoryName?: string;
      filePath: string;
      startLine: number;
      endLine: number;
      enclosingSymbol?: string;
      content: string;
    };

const EMPTY_REPORT_FORM: SourceTraceReportForm = {
  equipmentId: 0,
  filePath: "",
  functionName: "",
};

const EMPTY_SELECTION_FORM: SourceTraceSelectionForm = {
  equipmentId: 0,
  repositoryId: undefined,
  filePath: "",
  startLine: 1,
  endLine: 1,
  selectedCode: "",
  enclosingSymbol: "",
};

function getEquipmentName(equipmentList: Equipment[], equipmentId: number): string {
  return equipmentList.find((item) => item.id === equipmentId)?.name || `장비 #${equipmentId}`;
}

function getRepositoryName(repositories: GitRepository[], repositoryId?: number): string | undefined {
  if (!repositoryId) return undefined;
  return repositories.find((item) => item.id === repositoryId)?.name;
}

function MarkdownResult({ content }: { content: string }) {
  return (
    <div className="st-markdown">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          a: ({ ...props }) => (
            <a {...props} target="_blank" rel="noreferrer" />
          ),
          code: ({ className, children, ...props }) => {
            const isInline = !className;
            if (isInline) {
              return (
                <code className="st-inline-code" {...props}>
                  {children}
                </code>
              );
            }
            return (
              <code className={className} {...props}>
                {children}
              </code>
            );
          },
          pre: ({ children }) => <pre className="st-code-block">{children}</pre>,
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
}

export default function SourceTraceViewer({ equipmentVersion }: SourceTraceViewerProps) {
  const [mode, setMode] = useState<TraceMode>("report");
  const [equipmentList, setEquipmentList] = useState<Equipment[]>([]);
  const [repositories, setRepositories] = useState<GitRepository[]>([]);
  const [loadingEquipment, setLoadingEquipment] = useState(false);
  const [loadingRepositories, setLoadingRepositories] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [copyMessage, setCopyMessage] = useState<string | null>(null);
  const [result, setResult] = useState<ResultState | null>(null);
  const [reportForm, setReportForm] = useState<SourceTraceReportForm>(EMPTY_REPORT_FORM);
  const [selectionForm, setSelectionForm] = useState<SourceTraceSelectionForm>(EMPTY_SELECTION_FORM);

  const activeEquipmentId = mode === "report" ? reportForm.equipmentId : selectionForm.equipmentId;
  const repositoryState = useMemo(
    () => getRepositorySelectionState(repositories),
    [repositories],
  );

  const loadEquipment = useCallback(async () => {
    setLoadingEquipment(true);
    try {
      const data = await fetchEquipmentList();
      setEquipmentList(data);
      if (data.length === 1) {
        const onlyId = data[0].id;
        setReportForm((current) => ({ ...current, equipmentId: current.equipmentId || onlyId }));
        setSelectionForm((current) => ({
          ...current,
          equipmentId: current.equipmentId || onlyId,
        }));
      }
    } catch {
      setEquipmentList([]);
    } finally {
      setLoadingEquipment(false);
    }
  }, []);

  useEffect(() => {
    void loadEquipment();
  }, [equipmentVersion, loadEquipment]);

  useEffect(() => {
    if (!activeEquipmentId) {
      setRepositories([]);
      setSelectionForm((current) => ({ ...current, repositoryId: undefined }));
      return;
    }

    let cancelled = false;
    setLoadingRepositories(true);
    void fetchRepositories(activeEquipmentId)
      .then((data) => {
        if (cancelled) return;
        setRepositories(data);
        setSelectionForm((current) => {
          const currentRepo = current.repositoryId;
          if (current.equipmentId !== activeEquipmentId) return current;
          if (data.length === 1) {
            return { ...current, repositoryId: data[0].id };
          }
          if (currentRepo && data.some((repo) => repo.id === currentRepo)) {
            return current;
          }
          return { ...current, repositoryId: undefined };
        });
      })
      .catch(() => {
        if (cancelled) return;
        setRepositories([]);
        setSelectionForm((current) => ({ ...current, repositoryId: undefined }));
      })
      .finally(() => {
        if (!cancelled) setLoadingRepositories(false);
      });

    return () => {
      cancelled = true;
    };
  }, [activeEquipmentId]);

  useEffect(() => {
    if (!copyMessage) return;
    const timer = window.setTimeout(() => setCopyMessage(null), 2500);
    return () => window.clearTimeout(timer);
  }, [copyMessage]);

  const handleResetReport = () => {
    setReportForm((current) => ({
      ...EMPTY_REPORT_FORM,
      equipmentId: current.equipmentId,
    }));
    setResult(null);
    setError(null);
  };

  const handleResetSelection = () => {
    setSelectionForm((current) => ({
      ...EMPTY_SELECTION_FORM,
      equipmentId: current.equipmentId,
      repositoryId:
        repositoryState.hasSingleRepository && repositories[0] ? repositories[0].id : undefined,
    }));
    setResult(null);
    setError(null);
  };

  const handleCopyResult = async () => {
    if (!result?.content) return;
    const copied = await copyTextToClipboard(result.content);
    setCopyMessage(copied ? "결과를 클립보드에 복사했습니다." : "결과를 복사하지 못했습니다.");
  };

  const submitReport = async () => {
    if (!reportForm.equipmentId) {
      setError("장비를 선택해주세요.");
      return;
    }
    if (!reportForm.functionName.trim()) {
      setError("함수명을 입력해주세요.");
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const response = await fetchTraceReport(buildTraceReportRequest(reportForm));
      setResult({
        mode: "report",
        equipmentName: getEquipmentName(equipmentList, reportForm.equipmentId),
        filePath: reportForm.filePath.trim() || undefined,
        functionName: reportForm.functionName.trim(),
        content: response.content,
      });
    } catch (err) {
      setError(mapSourceTraceErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  const submitSelection = async () => {
    if (!selectionForm.equipmentId) {
      setError("장비를 선택해주세요.");
      return;
    }
    if (!selectionForm.filePath.trim()) {
      setError("소스 파일 경로를 확인해주세요.");
      return;
    }
    if (repositoryState.requiresExplicitChoice && !selectionForm.repositoryId) {
      setError("Repository를 특정할 수 없습니다.");
      return;
    }
    if (!Number.isInteger(selectionForm.startLine) || selectionForm.startLine < 1) {
      setError("시작 Line을 확인해주세요.");
      return;
    }
    if (!Number.isInteger(selectionForm.endLine) || selectionForm.endLine < selectionForm.startLine) {
      setError("종료 Line을 확인해주세요.");
      return;
    }
    if (!selectionForm.selectedCode.trim()) {
      setError("선택 코드를 입력해주세요.");
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const response = await fetchTraceSelection(buildTraceSelectionRequest(selectionForm));
      setResult({
        mode: "selection",
        equipmentName: getEquipmentName(equipmentList, selectionForm.equipmentId),
        repositoryName: getRepositoryName(repositories, selectionForm.repositoryId),
        filePath: selectionForm.filePath.trim(),
        startLine: selectionForm.startLine,
        endLine: selectionForm.endLine,
        enclosingSymbol: selectionForm.enclosingSymbol.trim() || undefined,
        content: response.content,
      });
    } catch (err) {
      setError(mapSourceTraceErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  const hasNoEquipment = !loadingEquipment && equipmentList.length === 0;
  const reportRepositoryNote =
    repositories.length <= 1
      ? repositories[0]?.name || "장비 기준 자동 판정"
      : "여러 Repository가 등록되어 있습니다. 함수 조회는 file path 기준으로 backend가 자동 판정합니다.";

  return (
    <div className="st-viewer">
      <header className="st-header">
        <h1>Source Trace 조회</h1>
        <p className="st-intro">
          IDE Extension을 사용할 수 없는 환경에서도 장비와 소스 정보를 직접 입력하여 함수 변경
          이력과 선택 코드 변경 근거를 조회할 수 있습니다.
        </p>
      </header>

      {hasNoEquipment && (
        <div className="st-banner st-banner-info" role="status">
          등록된 장비가 없습니다. 장비 관리에서 장비를 먼저 등록해주세요.
        </div>
      )}

      <section className="st-mode-switch" aria-label="조회 방식 선택">
        <button
          type="button"
          className={mode === "report" ? "active" : ""}
          onClick={() => {
            setMode("report");
            setError(null);
          }}
        >
          함수 변경 이력 조회
        </button>
        <button
          type="button"
          className={mode === "selection" ? "active" : ""}
          onClick={() => {
            setMode("selection");
            setError(null);
          }}
        >
          선택 코드 변경 근거 조회
        </button>
      </section>

      {mode === "report" ? (
        <section className="st-card">
          <div className="st-grid">
            <label>
              장비 <span className="st-required">*</span>
              <select
                value={reportForm.equipmentId || ""}
                onChange={(e) =>
                  setReportForm((current) => ({
                    ...current,
                    equipmentId: e.target.value ? Number(e.target.value) : 0,
                  }))
                }
                disabled={loading || loadingEquipment}
              >
                <option value="">선택</option>
                {equipmentList.map((item) => (
                  <option key={item.id} value={item.id}>
                    {item.name} (ID: {item.id})
                  </option>
                ))}
              </select>
            </label>

            <div className="st-readonly-field">
              <span className="st-label">Repository</span>
              <div className="st-readonly-value">{loadingRepositories ? "불러오는 중..." : reportRepositoryNote}</div>
            </div>

            <label className="st-span-2">
              소스 파일 경로
              <input
                type="text"
                value={reportForm.filePath}
                onChange={(e) =>
                  setReportForm((current) => ({ ...current, filePath: e.target.value }))
                }
                placeholder="예: src/fare/file_save_mgt.c"
                disabled={loading}
              />
              <span className="st-help">Git Repository 기준 상대 경로. 정확도를 위해 입력을 권장합니다.</span>
            </label>

            <label className="st-span-2">
              함수명 <span className="st-required">*</span>
              <input
                type="text"
                value={reportForm.functionName}
                onChange={(e) =>
                  setReportForm((current) => ({ ...current, functionName: e.target.value }))
                }
                placeholder="예: file_close_init"
                disabled={loading}
              />
            </label>
          </div>

          <div className="st-actions">
            <button type="button" className="st-primary-btn" onClick={() => void submitReport()} disabled={loading}>
              변경 이력 조회
            </button>
            <button type="button" className="st-secondary-btn" onClick={handleResetReport} disabled={loading}>
              입력 초기화
            </button>
          </div>
        </section>
      ) : (
        <section className="st-card">
          <div className="st-grid">
            <label>
              장비 <span className="st-required">*</span>
              <select
                value={selectionForm.equipmentId || ""}
                onChange={(e) =>
                  setSelectionForm((current) => ({
                    ...current,
                    equipmentId: e.target.value ? Number(e.target.value) : 0,
                  }))
                }
                disabled={loading || loadingEquipment}
              >
                <option value="">선택</option>
                {equipmentList.map((item) => (
                  <option key={item.id} value={item.id}>
                    {item.name} (ID: {item.id})
                  </option>
                ))}
              </select>
            </label>

            <label>
              Repository
              <select
                value={selectionForm.repositoryId || ""}
                onChange={(e) =>
                  setSelectionForm((current) => ({
                    ...current,
                    repositoryId: e.target.value ? Number(e.target.value) : undefined,
                  }))
                }
                disabled={loading || loadingRepositories || repositories.length <= 1}
              >
                <option value="">
                  {repositories.length <= 1 ? "자동 선택" : "선택"}
                </option>
                {repositories.map((item) => (
                  <option key={item.id} value={item.id}>
                    {item.name}
                  </option>
                ))}
              </select>
              <span className="st-help">
                {repositories.length > 1
                  ? "여러 Repository가 등록된 경우 선택 결과를 정확히 맞추기 위해 사용합니다."
                  : "Repository가 1개면 자동으로 사용합니다."}
              </span>
            </label>

            <label className="st-span-2">
              소스 파일 경로 <span className="st-required">*</span>
              <input
                type="text"
                value={selectionForm.filePath}
                onChange={(e) =>
                  setSelectionForm((current) => ({ ...current, filePath: e.target.value }))
                }
                placeholder="예: src/fare/file_save_mgt.c"
                disabled={loading}
              />
              <span className="st-help">Git Repository 기준 상대 경로</span>
            </label>

            <label>
              시작 Line <span className="st-required">*</span>
              <input
                type="number"
                min={1}
                value={selectionForm.startLine}
                onChange={(e) =>
                  setSelectionForm((current) => ({
                    ...current,
                    startLine: Number(e.target.value || 0),
                  }))
                }
                disabled={loading}
              />
            </label>

            <label>
              종료 Line <span className="st-required">*</span>
              <input
                type="number"
                min={1}
                value={selectionForm.endLine}
                onChange={(e) =>
                  setSelectionForm((current) => ({
                    ...current,
                    endLine: Number(e.target.value || 0),
                  }))
                }
                disabled={loading}
              />
              <span className="st-help">Line 번호는 1부터 시작합니다.</span>
            </label>

            <label className="st-span-2">
              포함 함수명
              <input
                type="text"
                value={selectionForm.enclosingSymbol}
                onChange={(e) =>
                  setSelectionForm((current) => ({
                    ...current,
                    enclosingSymbol: e.target.value,
                  }))
                }
                placeholder="예: file_close_init"
                disabled={loading}
              />
            </label>

            <label className="st-span-2">
              선택 코드 <span className="st-required">*</span>
              <textarea
                rows={8}
                value={selectionForm.selectedCode}
                onChange={(e) =>
                  setSelectionForm((current) => ({
                    ...current,
                    selectedCode: e.target.value,
                  }))
                }
                placeholder="선택한 코드 내용을 붙여넣으세요."
                disabled={loading}
              />
            </label>
          </div>

          <div className="st-actions">
            <button type="button" className="st-primary-btn" onClick={() => void submitSelection()} disabled={loading}>
              변경 근거 조회
            </button>
            <button type="button" className="st-secondary-btn" onClick={handleResetSelection} disabled={loading}>
              입력 초기화
            </button>
          </div>
        </section>
      )}

      <LongRunningTaskPanel
        active={loading}
        title="조회 중..."
        description="Backend 결과를 가져오고 있습니다. 중복 요청은 잠시만 기다려 주세요."
      />

      {error && (
        <div className="st-banner st-banner-error" role="alert">
          {error}
        </div>
      )}

      {result && (
        <section className="st-result">
          <div className="st-result-head">
            <div>
              <h2>조회 결과</h2>
              <dl className="st-result-meta">
                <div>
                  <dt>장비</dt>
                  <dd>{result.equipmentName}</dd>
                </div>
                {result.repositoryName && (
                  <div>
                    <dt>Repository</dt>
                    <dd>{result.repositoryName}</dd>
                  </div>
                )}
                {result.filePath && (
                  <div className="st-meta-wide">
                    <dt>파일</dt>
                    <dd>{result.filePath}</dd>
                  </div>
                )}
                {result.mode === "report" ? (
                  <div>
                    <dt>함수</dt>
                    <dd>{result.functionName}</dd>
                  </div>
                ) : (
                  <>
                    <div>
                      <dt>Line</dt>
                      <dd>
                        {result.startLine} - {result.endLine}
                      </dd>
                    </div>
                    {result.enclosingSymbol && (
                      <div>
                        <dt>포함 함수</dt>
                        <dd>{result.enclosingSymbol}</dd>
                      </div>
                    )}
                  </>
                )}
              </dl>
            </div>

            <div className="st-result-actions">
              <button type="button" className="st-secondary-btn" onClick={() => void handleCopyResult()}>
                결과 복사
              </button>
              {copyMessage && <span className="st-copy-message">{copyMessage}</span>}
            </div>
          </div>

          <div className="st-result-body">
            <MarkdownResult content={result.content} />
          </div>
        </section>
      )}
    </div>
  );
}
