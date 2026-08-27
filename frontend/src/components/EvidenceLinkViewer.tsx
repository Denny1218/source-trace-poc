import { useCallback, useEffect, useMemo, useState } from "react";
import { fetchAnalysis, type AnalysisResponse, type EvidenceRefItem } from "../api/analysis";
import { fetchEquipmentList, type Equipment } from "../api/equipment";
import {
  fetchEvidence,
  type EvidenceLinkItem,
  type EvidenceResponse,
  type MatchReasonItem,
  type QueryMatchReasonItem,
} from "../api/evidence";
import type { ChangeItemCandidate, SourceFunctionItem } from "../api/pptCache";
import { formatCommitDate, shortenHash } from "./DiffViewer";
import LongRunningTaskPanel from "./LongRunningTaskPanel";
import "./EvidenceLinkViewer.css";

interface EvidenceLinkViewerProps {
  equipmentVersion: number;
}

const PRIMARY_REASON_TYPES = new Set([
  "same_function_exact",
  "csr_exact",
  "same_file_path",
  "same_file_basename",
  "commit_message_change_title",
]);

const FIELD_LABELS: Record<string, string> = {
  change_title: "변경내역서 제목",
  to_be: "To-Be",
  as_is: "As-Is",
  business_background: "업무 배경",
  current_status: "현황",
  csr_no: "CSR",
  source_function: "변경내역서 소스/함수",
  file_name: "문서명",
  raw_text: "원문",
  commit_message: "Commit 메시지",
  git_file_path: "Git 파일 경로",
  selected_code: "선택 코드",
  request_file_path: "요청 파일",
  path_scope: "검색 범위 경로",
};

const GENERIC_PATH_SUMMARY_SKIP = new Set([
  "src",
  "source",
  "lib",
  "common",
  "include",
  "inc",
  "proc",
  "app",
  "device",
  "card",
  "fare",
  "util",
  "utils",
  "api",
  "test",
  "tests",
]);

function formatSourceFunctions(entries: SourceFunctionItem[]): string {
  if (!entries.length) return "—";
  return entries
    .map((sf) => {
      const path = sf.file_path?.trim() || "(path 없음)";
      const funcs = (sf.functions || []).join(", ");
      return funcs ? `${path} · ${funcs}` : path;
    })
    .join(" / ");
}

function formatQueryMatchSummary(reasons: QueryMatchReasonItem[] | undefined): string {
  if (!reasons?.length) return "—";
  const core = reasons.filter((r) => r.strength !== "weak");
  const pick = (core.length ? core : reasons).slice(0, 2);
  return pick.map((r) => `${r.keyword} · ${FIELD_LABELS[r.field] || r.field}`).join(" / ");
}

function summarizeQueryMatches(reasons: QueryMatchReasonItem[] | undefined): string[] {
  if (!reasons?.length) return [];
  const lines: string[] = [];
  const seen = new Set<string>();

  const add = (line: string) => {
    if (seen.has(line)) return;
    seen.add(line);
    lines.push(line);
  };

  for (const r of reasons) {
    if (r.strength === "weak") continue;
    if (GENERIC_PATH_SUMMARY_SKIP.has(r.keyword.toLowerCase())) continue;
    if (r.field === "path_scope") continue;
    if (r.field === "selected_code" || (r.keyword.includes("_") && r.field === "source_function")) {
      add(`요청 함수 ${r.keyword} 일치`);
      continue;
    }
    if (r.field === "request_file_path" || r.field === "git_file_path") {
      add(`요청 파일 ${r.keyword} 일치`);
      continue;
    }
    if (r.field === "source_function") {
      add(`변경내역서 소스/함수 항목에 ${r.keyword} 존재`);
      continue;
    }
    if (r.field === "change_title") {
      add(`변경내역서 제목에 ${r.keyword} 포함`);
      continue;
    }
    if (r.field === "commit_message") {
      add(`Commit 메시지에 ${r.keyword} 포함`);
      continue;
    }
    add(`${r.keyword} — ${FIELD_LABELS[r.field] || r.field}`);
  }
  return lines.slice(0, 4);
}

function summarizeLinkMatches(reasons: MatchReasonItem[]): string[] {
  const lines: string[] = [];
  const byType = new Map(reasons.map((r) => [r.type, r]));

  const file = byType.get("same_file_path") || byType.get("same_file_basename");
  if (file) {
    const name = file.git_value || file.change_item_value || "";
    lines.push(name ? `같은 파일: ${name}` : "같은 파일 일치");
  }
  const fn = byType.get("same_function_exact");
  if (fn) {
    const name = fn.git_value || fn.change_item_value || "";
    lines.push(name ? `같은 함수: ${name}` : "같은 함수 일치");
  }
  const csr = byType.get("csr_exact");
  if (csr) {
    const name = csr.git_value || csr.change_item_value || "";
    lines.push(name ? `CSR 일치: ${name}` : "CSR 일치");
  }
  const title = byType.get("commit_message_change_title") || byType.get("diff_change_title");
  if (title) {
    const tip = title.git_value || title.change_item_value || "";
    lines.push(tip ? `관련 Diff/제목 키워드: ${tip}` : "Commit 메시지 ↔ 변경 제목 연결");
  }
  const diffSrc = byType.get("diff_source_function");
  if (diffSrc && lines.length < 3) {
    const tip = diffSrc.git_value || diffSrc.change_item_value || "";
    lines.push(tip ? `Diff 소스/함수: ${tip}` : "Diff ↔ 소스/함수 연결");
  }
  if (!lines.length && reasons.length) {
    const primary = reasons.filter((r) => PRIMARY_REASON_TYPES.has(r.type));
    for (const r of (primary.length ? primary : reasons).slice(0, 3)) {
      lines.push(r.type.replace(/_/g, " "));
    }
  }
  return lines.slice(0, 4);
}

function QueryMatchView({
  level,
  reasons,
}: {
  level?: string;
  score?: number;
  reasons?: QueryMatchReasonItem[];
}) {
  const [open, setOpen] = useState(false);
  const lv = level || "없음";
  const summary = summarizeQueryMatches(reasons);

  return (
    <div className="ev-query-block">
      <div className="ev-query-head">
        <span className="ev-meta-label">Query Match</span>
        <span className={`ev-qlevel ev-qlevel-${lv}`}>{lv}</span>
      </div>
      {summary.length ? (
        <ul className="ev-summary-list">
          {summary.map((line) => (
            <li key={line}>{line}</li>
          ))}
        </ul>
      ) : (
        <p className="ev-muted">핵심 요청어와 직접 일치하는 근거 없음</p>
      )}
      {reasons && reasons.length > 0 && (
        <div className="ev-detail-toggle">
          <button type="button" className="ev-secondary-btn" onClick={() => setOpen((v) => !v)}>
            {open ? "Query Match 상세 접기" : "Query Match 상세 보기"}
          </button>
          {open && (
            <ul className="ev-query-reasons">
              {reasons.map((r, idx) => (
                <li key={`${r.keyword}-${r.field}-${idx}`}>
                  <code>{r.keyword}</code>
                  <span className="ev-sep">matched in</span>
                  <code>{r.field}</code>
                  {r.strength === "weak" ? (
                    <span className="ev-badge-weak-term">weak</span>
                  ) : null}
                  {r.value ? <span className="ev-muted ev-snippet"> — {r.value}</span> : null}
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  );
}

function LinkMatchView({ reasons }: { reasons: MatchReasonItem[] }) {
  const [open, setOpen] = useState(false);
  const summary = summarizeLinkMatches(reasons);

  return (
    <div className="ev-link-match-block">
      <div className="ev-query-head">
        <span className="ev-meta-label">Link Match</span>
        <span className="ev-muted">Git ↔ Change Item</span>
      </div>
      {summary.length ? (
        <ul className="ev-summary-list">
          {summary.map((line) => (
            <li key={line}>{line}</li>
          ))}
        </ul>
      ) : (
        <p className="ev-muted">Link Match 없음</p>
      )}
      {reasons.length > 0 && (
        <div className="ev-detail-toggle">
          <button type="button" className="ev-secondary-btn" onClick={() => setOpen((v) => !v)}>
            {open ? "Link Score 상세 접기" : "Link Score 상세 보기"}
          </button>
          {open && (
            <ul className="ev-reasons">
              {reasons.map((reason, idx) => {
                const primary = PRIMARY_REASON_TYPES.has(reason.type);
                return (
                  <li
                    key={`${reason.type}-${idx}`}
                    className={primary ? "ev-reason ev-reason-primary" : "ev-reason ev-reason-weak"}
                  >
                    <div className="ev-reason-head">
                      <code>{reason.type}</code>
                      <span className="ev-reason-score">+{reason.score}</span>
                      <span className="ev-reason-tag">{primary ? "Primary" : "Weak"}</span>
                    </div>
                    {reason.git_value != null && reason.git_value !== "" && (
                      <div className="ev-reason-line">
                        <span className="ev-reason-label">Git</span>
                        <code>{reason.git_value}</code>
                      </div>
                    )}
                    {reason.change_item_value != null && reason.change_item_value !== "" && (
                      <div className="ev-reason-line">
                        <span className="ev-reason-label">Change Item</span>
                        <code>{reason.change_item_value}</code>
                      </div>
                    )}
                    {reason.distance_days != null && (
                      <div className="ev-reason-line">
                        <span className="ev-reason-label">distance_days</span>
                        <span>{reason.distance_days}</span>
                      </div>
                    )}
                    {reason.match_level != null && reason.match_level !== "" && (
                      <div className="ev-reason-line">
                        <span className="ev-reason-label">match_level</span>
                        <code>{reason.match_level}</code>
                      </div>
                    )}
                  </li>
                );
              })}
            </ul>
          )}
        </div>
      )}
    </div>
  );
}

function EvidenceLinkCard({
  rank,
  link,
  changeItem,
}: {
  rank: number;
  link: EvidenceLinkItem;
  changeItem: ChangeItemCandidate | undefined;
}) {
  const [showDiff, setShowDiff] = useState(false);
  const [showScores, setShowScores] = useState(false);
  const primaryCount = link.match_reasons.filter((r) =>
    PRIMARY_REASON_TYPES.has(r.type),
  ).length;
  const weakOnly = primaryCount === 0;
  const level = link.query_relevance_level || "없음";

  return (
    <article className={weakOnly ? "ev-link-card ev-link-weak-only" : "ev-link-card"}>
      <header className="ev-link-header">
        <span className="ev-rank">#{rank}</span>
        <span className={`ev-qlevel ev-qlevel-${level}`}>관련성 {level}</span>
        {weakOnly ? (
          <span className="ev-badge-warn">Primary 없음</span>
        ) : (
          <span className="ev-badge-ok">Primary {primaryCount}</span>
        )}
      </header>

      <div className="ev-link-title">
        {changeItem?.change_title || "(Change Item 제목 없음)"}
      </div>

      <div className="ev-link-meta">
        <div>
          <span className="ev-meta-label">Git</span>
          <code>{shortenHash(link.git_commit_hash)}</code>
          <span className="ev-sep">·</span>
          <code className="ev-path">{link.git_file_path}</code>
        </div>
        <div>
          <span className="ev-meta-label">문서</span>
          <span>{changeItem?.file_name || `doc#${link.document_cache_id}`}</span>
          <span className="ev-sep">·</span>
          <span>Slide {changeItem?.slide_no ?? "?"}</span>
        </div>
      </div>

      <QueryMatchView level={level} reasons={link.query_match_reasons} />
      <LinkMatchView reasons={link.match_reasons} />

      <div className="ev-detail-toggle">
        <button type="button" className="ev-secondary-btn" onClick={() => setShowScores((v) => !v)}>
          {showScores ? "점수 상세 접기" : "점수 상세 보기"}
        </button>
        {showScores && (
          <div className="ev-score-detail">
            <span>link_score {link.link_score}</span>
            <span className="ev-sep">·</span>
            <span>query_relevance {link.query_relevance_score ?? 0}</span>
            <span className="ev-sep">·</span>
            <span>final_rank {link.final_rank_score ?? link.link_score}</span>
          </div>
        )}
      </div>

      {link.diff_excerpt ? (
        <div className="ev-diff-block">
          <button
            type="button"
            className="ev-secondary-btn"
            onClick={() => setShowDiff((v) => !v)}
          >
            {showDiff ? "diff_excerpt 접기" : "diff_excerpt 보기"}
          </button>
          {showDiff && <pre className="ev-diff-excerpt">{link.diff_excerpt}</pre>}
        </div>
      ) : null}
    </article>
  );
}

function QueryIntentPanel({ result }: { result: EvidenceResponse }) {
  const functions = result.request_functions || [];
  const files = result.request_files || [];
  const scopes = result.path_scopes || [];
  const business = result.query_keywords || [];
  const weak = result.weak_query_terms || [];
  if (
    !functions.length &&
    !files.length &&
    !scopes.length &&
    !business.length &&
    !weak.length
  ) {
    return null;
  }
  return (
    <div className="ev-intent-panel">
      <div className="ev-intent-title">Query Intent</div>
      <p className="ev-intent-help">
        <strong>core(핵심어)</strong>: 실제 검색 의도로 판단한 함수/파일/업무어 ·{" "}
        <strong>weak(약한 표현)</strong>: 질문 표현 또는 일반 단어(검증 화면 전용) ·{" "}
        디렉터리 경로는 검색 범위로만 표시하며 관련성 점수를 올리지 않습니다.
      </p>
      <dl className="ev-intent-grid">
        <div>
          <dt>요청 함수</dt>
          <dd>{functions.length ? functions.map((f) => <code key={f}>{f}</code>) : "—"}</dd>
        </div>
        {files.length > 0 && (
          <div>
            <dt>요청 파일</dt>
            <dd>{files.map((f) => <code key={f}>{f}</code>)}</dd>
          </div>
        )}
        {scopes.length > 0 && (
          <div>
            <dt>검색 범위 경로</dt>
            <dd>{scopes.map((s) => <code key={s}>{s}</code>)}</dd>
          </div>
        )}
        <div>
          <dt>핵심 업무어</dt>
          <dd>{business.length ? business.join(", ") : "—"}</dd>
        </div>
        <div>
          <dt>제외/약한 표현</dt>
          <dd>{weak.length ? weak.join(", ") : "—"}</dd>
        </div>
      </dl>
    </div>
  );
}

const CONFIDENCE_LABELS: Record<string, string> = {
  high: "높음",
  medium: "보통",
  low: "낮음",
};

function EvidenceRefList({ refs }: { refs: EvidenceRefItem[] }) {
  const gitRefs = refs.filter((r) => r.type === "git");
  const docRefs = refs.filter((r) => r.type === "document");
  if (!gitRefs.length && !docRefs.length) return null;
  return (
    <div className="ai-evidence-refs">
      {gitRefs.length > 0 && (
        <div>
          <span className="ev-meta-label">Git 근거</span>
          {gitRefs.map((r, i) => (
            <code key={`git-${i}`}>{shortenHash(r.commit || "")}</code>
          ))}
        </div>
      )}
      {docRefs.length > 0 && (
        <div>
          <span className="ev-meta-label">변경내역서 근거</span>
          {docRefs.map((r, i) => (
            <span key={`doc-${i}`} className="ai-doc-ref">
              {r.file} {r.slide != null ? `· Slide ${r.slide}` : ""}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}

function statusNotice(analysis: AnalysisResponse): string | null {
  const status = analysis.answer_status || "";
  if (status === "no_evidence") {
    return "관련 Git 또는 변경내역서 근거를 찾지 못해 변경 사유를 확인할 수 없습니다.";
  }
  if (status === "ollama_skipped_by_user") {
    return "AI 보조 설명을 사용하지 않고 서버 근거 기반 요약만 표시합니다.";
  }
  if (status === "ollama_timeout" || status === "ollama_unavailable") {
    return analysis.ai_error || "Ollama 응답 실패 — 서버 근거 기반 요약을 표시합니다.";
  }
  if (status === "ollama_disabled") {
    return analysis.ai_error || "AI 분석 기능이 비활성화되어 있습니다. 근거 기반 요약을 표시합니다.";
  }
  if (status === "answered_with_plain_text") {
    return "AI 응답 형식은 표준과 달랐지만, 응답 본문을 표시합니다.";
  }
  if (status === "ollama_parse_error" || status === "ollama_empty_response") {
    return (
      analysis.ai_error ||
      "AI 응답 형식을 해석하지 못해 근거 기반 요약을 표시합니다."
    );
  }
  if (analysis.ai_used && (status === "ok" || status === "partial")) {
    return "AI 보조 설명이 생성되었습니다.";
  }
  return null;
}

function statusBadge(analysis: AnalysisResponse): string | null {
  const status = analysis.answer_status || "";
  if (status === "ollama_skipped_by_user") {
    return "AI 미사용 (사용자 선택)";
  }
  if (status === "ollama_timeout" || status === "ollama_unavailable") {
    return "Ollama 응답 실패";
  }
  if (status === "answered_with_plain_text") {
    return "본문 표시";
  }
  if (status === "ollama_parse_error" || status === "ollama_empty_response") {
    return "근거 기반 요약";
  }
  if (status === "ollama_disabled") {
    return "AI 비활성";
  }
  if (status === "no_evidence") {
    return "근거 없음";
  }
  return null;
}

function AiAnalysisPanel({ analysis }: { analysis: AnalysisResponse }) {
  const [showFull, setShowFull] = useState(false);
  const confidence = analysis.confidence || "low";
  const status = analysis.answer_status || (analysis.parse_error ? "ollama_parse_error" : "ok");
  const notice = statusNotice(analysis);
  const badge = statusBadge(analysis);
  const degraded =
    status === "ollama_timeout" ||
    status === "ollama_unavailable" ||
    status === "ollama_parse_error" ||
    status === "ollama_empty_response" ||
    status === "ollama_disabled";

  const evidenceSummary = (analysis.evidence_summary || analysis.summary || "").trim();
  const evidenceAnswer = (analysis.evidence_answer || analysis.answer || "").trim();
  const aiAnswer = (analysis.ai_answer || "").trim();
  const isLongAiAnswer = aiAnswer.length > 900;

  return (
    <section className={`ai-panel ${degraded ? "ai-panel-degraded" : "ai-panel-ok"}`}>
      <div className="ai-panel-head">
        <h3>AI 근거 기반 분석 (STEP 8)</h3>
        {/* 1. 신뢰도 */}
        <span className={`ai-confidence ai-confidence-${confidence}`}>
          신뢰도 {CONFIDENCE_LABELS[confidence] || confidence}
        </span>
        {analysis.inference && <span className="ai-badge-inference">추정</span>}
        {badge && <span className="ev-badge-warn">{badge}</span>}
      </div>

      {notice && (
        <p className="ev-notice" role="status">
          {notice}
        </p>
      )}

      {/* 2. 서버 근거 기반 요약 — AI 보조 설명이 이 영역을 대체하지 않음 */}
      <div className="ai-evidence-summary-block">
        <div className="ev-meta-label">서버 근거 기반 요약</div>
        {evidenceSummary ? (
          <p className="ai-summary">{evidenceSummary}</p>
        ) : (
          <p className="ev-muted">확인 불가 — 근거에서 변경 사유를 판단할 수 없습니다.</p>
        )}
        {evidenceAnswer && evidenceAnswer !== evidenceSummary && (
          <pre className="ai-answer-text">{evidenceAnswer}</pre>
        )}
      </div>

      {/* 3-4. Git 근거 / 변경내역서 근거 */}
      <EvidenceRefList refs={analysis.evidence} />

      {/* 5. AI 보조 설명 — 실제로 생성된 경우에만 별도 표시 */}
      {analysis.ai_used && aiAnswer && aiAnswer !== evidenceAnswer && (
        <div className="ai-assist-block">
          <div className="ev-meta-label">AI 보조 설명</div>
          <pre className="ai-answer-text ai-answer-main">
            {!isLongAiAnswer || showFull ? aiAnswer : `${aiAnswer.slice(0, 800)}…`}
          </pre>
          {isLongAiAnswer && (
            <div className="ev-detail-toggle">
              <button
                type="button"
                className="ev-secondary-btn"
                onClick={() => setShowFull((v) => !v)}
              >
                {showFull ? "AI 보조 설명 접기" : "AI 보조 설명 전체 보기"}
              </button>
            </div>
          )}
        </div>
      )}
    </section>
  );
}

export default function EvidenceLinkViewer({ equipmentVersion }: EvidenceLinkViewerProps) {
  const [equipmentList, setEquipmentList] = useState<Equipment[]>([]);
  const [equipmentId, setEquipmentId] = useState<number | "">("");
  const [query, setQuery] = useState("");
  const [filePath, setFilePath] = useState("");
  const [selectedCode, setSelectedCode] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<EvidenceResponse | null>(null);
  const [showGuide, setShowGuide] = useState(true);
  const [analysis, setAnalysis] = useState<AnalysisResponse | null>(null);
  const [analysisLoading, setAnalysisLoading] = useState(false);
  const [analysisError, setAnalysisError] = useState<string | null>(null);
  const [useOllama, setUseOllama] = useState(true);

  const loadEquipment = useCallback(async () => {
    try {
      const data = await fetchEquipmentList();
      setEquipmentList(data);
      setEquipmentId((current) => {
        if (current !== "" && !data.some((eq) => eq.id === current)) return "";
        if (current === "" && data.length === 1) return data[0].id;
        return current;
      });
    } catch {
      setEquipmentList([]);
    }
  }, []);

  useEffect(() => {
    void loadEquipment();
  }, [loadEquipment, equipmentVersion]);

  const changeItemById = useMemo(() => {
    const map = new Map<number, ChangeItemCandidate>();
    for (const item of result?.change_item_candidates ?? []) {
      map.set(item.change_item_cache_id, item);
    }
    return map;
  }, [result]);

  const handleRun = async () => {
    if (equipmentId === "" || !query.trim()) {
      setError("장비와 query를 입력해 주세요.");
      return;
    }
    setLoading(true);
    setError(null);
    setResult(null);
    setAnalysis(null);
    setAnalysisError(null);
    try {
      const data = await fetchEvidence({
        equipment_id: equipmentId,
        query: query.trim(),
        file_path: filePath.trim() || undefined,
        selected_code: selectedCode.trim() || undefined,
      });
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Evidence 요청 실패");
    } finally {
      setLoading(false);
    }
  };

  const handleAnalyze = async () => {
    if (equipmentId === "" || !query.trim()) {
      setAnalysisError("장비와 query를 입력해 주세요.");
      return;
    }
    setAnalysisLoading(true);
    setAnalysisError(null);
    setAnalysis(null);
    try {
      const data = await fetchAnalysis({
        equipment_id: equipmentId,
        query: query.trim(),
        file_path: filePath.trim() || undefined,
        selected_code: selectedCode.trim() || undefined,
        use_ollama: useOllama,
      });
      setAnalysis(data);
      setResult({
        equipment_id: data.equipment_id,
        query: data.query,
        query_keywords: data.debug.query_keywords,
        weak_query_terms: data.debug.weak_query_terms,
        request_functions: data.debug.request_functions,
        request_files: data.debug.request_files,
        path_scopes: data.debug.path_scopes,
        git_candidates: data.git_candidates,
        change_item_candidates: data.change_item_candidates,
        evidence_links: data.evidence_links,
        debug: data.debug,
      });
    } catch (err) {
      setAnalysisError(err instanceof Error ? err.message : "AI 분석 요청 실패");
    } finally {
      setAnalysisLoading(false);
    }
  };

  return (
    <div className="ev-viewer">
      <h2>Evidence Link 검증</h2>
      <p className="ev-intro">
        STEP 7 <code>POST /api/trace/evidence</code> 및 STEP 8{" "}
        <code>POST /api/trace/analyze</code> 운영 검증용 화면입니다. Link Score/Query Relevance
        Gate/Weight는 변경하지 않으며, AI 분석은 상위 Evidence만 근거로 사용합니다.
      </p>

      <details className="ev-guide" open={showGuide} onToggle={(e) => setShowGuide(e.currentTarget.open)}>
        <summary>운영 검증 케이스</summary>
        <ol>
          <li>함수명 Query — 1위 Link에 <code>same_function_exact</code> 등 Primary 근거가 있는지</li>
          <li>파일명 Query — <code>same_file_path</code> / <code>same_file_basename</code> 연결</li>
          <li>업무 키워드 Query — message/title 키워드 + Change Item 연결</li>
          <li>날짜만 가까운 unrelated — date-only / weak-only가 상위에 오르지 않는지</li>
          <li>동일 Change Title 다중 Document — 별도 Link로 유지되는지</li>
        </ol>
      </details>

      <section className="ev-controls">
        <div className="ev-row">
          <label>
            장비
            <select
              value={equipmentId}
              onChange={(e) =>
                setEquipmentId(e.target.value ? Number(e.target.value) : "")
              }
              disabled={loading}
            >
              <option value="">선택</option>
              {equipmentList.map((eq) => (
                <option key={eq.id} value={eq.id}>
                  {eq.name}
                </option>
              ))}
            </select>
          </label>
          <label className="ev-grow">
            query
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="예: file_close_init 함수 변경 내역을 보여줘"
              disabled={loading}
            />
          </label>
        </div>
        <div className="ev-row">
          <label className="ev-grow">
            file_path (optional)
            <input
              type="text"
              value={filePath}
              onChange={(e) => setFilePath(e.target.value)}
              placeholder="예: subwaylib/fare/src/file_save_mgt.c"
              disabled={loading}
            />
          </label>
        </div>
        <div className="ev-row">
          <label className="ev-grow">
            selected_code (optional)
            <textarea
              value={selectedCode}
              onChange={(e) => setSelectedCode(e.target.value)}
              rows={3}
              placeholder="선택 코드 붙여넣기 (optional)"
              disabled={loading}
            />
          </label>
        </div>
        <div className="ev-row">
          <button
            type="button"
            className="ev-run-btn"
            onClick={() => void handleRun()}
            disabled={loading || analysisLoading}
          >
            Evidence 실행
          </button>
          <button
            type="button"
            className="ev-run-btn ai-run-btn"
            onClick={() => void handleAnalyze()}
            disabled={loading || analysisLoading}
          >
            AI 분석 실행 (STEP 8)
          </button>
          <label className="ev-checkbox ai-use-ollama-toggle" title="AI 보조 설명은 내부 Ollama 서버 상태에 따라 1분 이상 걸릴 수 있습니다. 체크 해제 시 빠른 서버 근거 요약만 표시합니다.">
            <input
              type="checkbox"
              checked={useOllama}
              onChange={(e) => setUseOllama(e.currentTarget.checked)}
              disabled={analysisLoading}
            />
            AI 보조 설명 생성
          </label>
        </div>
        <p className="ev-hint">
          AI 보조 설명은 내부 Ollama 서버 상태에 따라 1분 이상 걸릴 수 있습니다. 체크 해제 시 빠른 서버 근거 요약만 표시합니다.
        </p>
      </section>

      <LongRunningTaskPanel
        active={loading}
        title="Evidence Link 계산 중"
        description="Git Top 5 + Change Item 검색 + Link Score를 수행합니다. UNC/PPT 분석이 포함되면 수 초~수십 초 걸릴 수 있습니다."
      />
      <LongRunningTaskPanel
        active={analysisLoading}
        title="AI 분석 중"
        description="상위 Evidence를 근거로 Ollama에 답변을 요청합니다. AI가 응답하지 않아도 Evidence 결과는 표시됩니다."
      />

      {error && (
        <p className="ev-error" role="alert">
          {error}
        </p>
      )}
      {analysisError && (
        <p className="ev-error" role="alert">
          {analysisError}
        </p>
      )}

      {analysis && <AiAnalysisPanel analysis={analysis} />}

      {result && (
        <>
          <section className="ev-summary">
            <span>Git {result.git_candidates.length}</span>
            <span className="ev-sep">·</span>
            <span>Change Item {result.change_item_candidates.length}</span>
            <span className="ev-sep">·</span>
            <span>Evidence Link {result.evidence_links.length}</span>
            <span className="ev-sep">·</span>
            <span className="ev-muted">
              debug: link후보 {result.debug.change_item_link_candidate_count} / fallback{" "}
              {result.debug.fallback_documents_parsed} / total {result.debug.change_item_total}
              {typeof result.debug.equipment_filter_excluded === "number"
                ? ` / equipment filter excluded ${result.debug.equipment_filter_excluded}`
                : ""}
              {typeof result.debug.query_relevance_excluded_links === "number"
                ? ` / query relevance excluded ${result.debug.query_relevance_excluded_links}`
                : ""}
            </span>
          </section>

          <QueryIntentPanel result={result} />

          {result.git_candidates.length === 0 && (
            <div className="ev-notice" role="status">
              <p>
                <strong>Git 후보가 없어 Evidence Link를 생성할 수 없습니다.</strong>
              </p>
              <p>
                Git Repository 준비/동기화 상태, 검색어, file_path 입력 여부를 확인하세요.
              </p>
            </div>
          )}

          <section className="ev-section">
            <h3>1. Evidence Links</h3>
            {result.evidence_links.length === 0 ? (
              <p className="ev-muted">
                {result.git_candidates.length === 0
                  ? "Evidence Link 없음 — 원인: Git Candidate 0건"
                  : result.change_item_candidates.length === 0
                    ? "Evidence Link 없음 — 원인: Change Item Candidate 0건"
                    : "Evidence Link 없음 — 원인: Link Gate/Threshold 또는 Query Relevance Gate 통과 결과 0건"}
              </p>
            ) : (
              <div className="ev-link-list">
                {result.evidence_links.map((link, i) => (
                  <EvidenceLinkCard
                    key={`${link.git_commit_id}-${link.git_file_path}-${link.change_item_cache_id}`}
                    rank={i + 1}
                    link={link}
                    changeItem={changeItemById.get(link.change_item_cache_id)}
                  />
                ))}
              </div>
            )}
          </section>

          <section className="ev-section">
            <h3>2. Git Candidates</h3>
            {result.git_candidates.length === 0 ? (
              <p className="ev-muted">Git Candidate 없음</p>
            ) : (
              <div className="ev-table-wrap">
                <table>
                  <thead>
                    <tr>
                      <th>#</th>
                      <th>hash</th>
                      <th>date</th>
                      <th>message</th>
                      <th>file_path</th>
                      <th>git_score</th>
                      <th>query match</th>
                    </tr>
                  </thead>
                  <tbody>
                    {result.git_candidates.map((c, i) => (
                      <tr key={`${c.commit_id}-${c.file_path}`}>
                        <td>{i + 1}</td>
                        <td>
                          <code>{shortenHash(c.commit_hash)}</code>
                        </td>
                        <td>{formatCommitDate(c.commit_date)}</td>
                        <td className="ev-msg">{c.message}</td>
                        <td>
                          <code>{c.file_path}</code>
                        </td>
                        <td>{c.score}</td>
                        <td
                          className="ev-qmatch"
                          title={formatQueryMatchSummary(c.query_match_reasons)}
                        >
                          <span className={`ev-qlevel ev-qlevel-${c.query_relevance_level || "없음"}`}>
                            {c.query_relevance_level || "없음"}
                          </span>
                          <div className="ev-muted">{formatQueryMatchSummary(c.query_match_reasons)}</div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>

          <section className="ev-section">
            <h3>3. Change Item Candidates</h3>
            {result.change_item_candidates.length === 0 ? (
              <p className="ev-muted">Change Item Candidate 없음</p>
            ) : (
              <div className="ev-table-wrap">
                <table>
                  <thead>
                    <tr>
                      <th>#</th>
                      <th>change_title</th>
                      <th>document</th>
                      <th>slide</th>
                      <th>source/function</th>
                      <th>search_score</th>
                      <th>query match</th>
                    </tr>
                  </thead>
                  <tbody>
                    {result.change_item_candidates.map((item, i) => (
                      <tr key={item.change_item_cache_id}>
                        <td>{i + 1}</td>
                        <td>{item.change_title || "—"}</td>
                        <td>{item.file_name}</td>
                        <td>{item.slide_no}</td>
                        <td className="ev-src">{formatSourceFunctions(item.source_functions)}</td>
                        <td>{item.candidate_score}</td>
                        <td
                          className="ev-qmatch"
                          title={formatQueryMatchSummary(item.query_match_reasons)}
                        >
                          <span className={`ev-qlevel ev-qlevel-${item.query_relevance_level || "없음"}`}>
                            {item.query_relevance_level || "없음"}
                          </span>
                          <div className="ev-muted">
                            {formatQueryMatchSummary(item.query_match_reasons)}
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>
        </>
      )}
    </div>
  );
}
