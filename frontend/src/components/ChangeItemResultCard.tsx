import { useState } from "react";
import type { ChangeItemCandidate } from "../api/pptCache";
import {
  copyTextToClipboard,
  PATH_COPY_FAILURE_MESSAGE,
  PATH_COPY_SUCCESS_MESSAGE,
} from "../utils/clipboardUtils";
import {
  formatApplicableScopes,
  formatMetaPrimaryLine,
} from "../utils/changeItemDisplay";
import { highlightKeywords } from "../utils/highlightKeywords";
import {
  getRelevanceLabel,
  getRelevanceLevel,
  type RelevanceLevel,
} from "../utils/changeItemRelevance";
import { getUncParentDirectory } from "../utils/uncPathUtils";

interface ChangeItemResultCardProps {
  item: ChangeItemCandidate;
  keywords: string[];
  expandedPath: boolean;
  expandedDetail: boolean;
  onTogglePath: () => void;
  onToggleDetail: () => void;
}

function relevanceClass(level: RelevanceLevel): string {
  return `ci-relevance ci-relevance-${level}`;
}

export default function ChangeItemResultCard({
  item,
  keywords,
  expandedPath,
  expandedDetail,
  onTogglePath,
  onToggleDetail,
}: ChangeItemResultCardProps) {
  const [copyFeedback, setCopyFeedback] = useState<{
    type: "success" | "error";
    text: string;
  } | null>(null);

  const level = getRelevanceLevel(item.candidate_score);
  const metaPrimary = formatMetaPrimaryLine(item);
  const scopesLine = formatApplicableScopes(item.applicable_scopes);
  const uncParentDirectory = getUncParentDirectory(item.file_path);
  const canCopyFolderPath = uncParentDirectory !== null;

  const handleCopyFolderPath = async () => {
    if (!uncParentDirectory) {
      setCopyFeedback({ type: "error", text: PATH_COPY_FAILURE_MESSAGE });
      return;
    }
    const ok = await copyTextToClipboard(uncParentDirectory);
    setCopyFeedback({
      type: ok ? "success" : "error",
      text: ok ? PATH_COPY_SUCCESS_MESSAGE : PATH_COPY_FAILURE_MESSAGE,
    });
  };

  return (
    <article className="ci-card">
      <header className="ci-card-head">
        <h4 className="ci-title">
          {highlightKeywords(item.change_title || "(제목 없음)", keywords)}
        </h4>
        <span className={relevanceClass(level)}>{getRelevanceLabel(item.candidate_score)}</span>
      </header>

      {metaPrimary && <p className="ci-meta-primary">{metaPrimary}</p>}
      {scopesLine && (
        <p className="ci-meta-scopes">
          <span className="ci-meta-scopes-label">적용 대상</span>
          <span className="ci-meta-scopes-value">{scopesLine}</span>
        </p>
      )}

      <div className="ci-field-grid">
        {item.business_background && (
          <>
            <span className="ci-field-label">배경</span>
            <span className="ci-field-value">
              {highlightKeywords(item.business_background, keywords)}
            </span>
          </>
        )}
        {item.current_status && (
          <>
            <span className="ci-field-label">현황</span>
            <span className="ci-field-value">
              {highlightKeywords(item.current_status, keywords)}
            </span>
          </>
        )}
        {item.as_is && (
          <>
            <span className="ci-field-label">As-Is</span>
            <span className="ci-field-value">
              {highlightKeywords(item.as_is, keywords)}
            </span>
          </>
        )}
        {item.to_be && (
          <>
            <span className="ci-field-label ci-field-label-tobe">To-Be</span>
            <span className="ci-field-value ci-field-value-tobe">
              {highlightKeywords(item.to_be, keywords)}
            </span>
          </>
        )}
      </div>

      {item.source_functions.length > 0 && (
        <div className="ci-sources-block">
          <span className="ci-field-label">소스/함수</span>
          <ul className="ci-source-list">
            {item.source_functions.map((sf, idx) => (
              <li key={idx} className="ci-source-entry">
                {sf.file_path && (
                  <code className="ci-src-path">
                    {highlightKeywords(sf.file_path, keywords)}
                  </code>
                )}
                {sf.functions.length > 0 && (
                  <ul className="ci-func-list">
                    {sf.functions.map((fn, fidx) => (
                      <li key={fidx} className="ci-func-item">
                        <span className="ci-func-tree">└ </span>
                        <code className="ci-func">
                          {highlightKeywords(fn, keywords)}
                        </code>
                      </li>
                    ))}
                  </ul>
                )}
                {!sf.file_path && sf.functions.length === 0 && sf.raw_text && (
                  <code className="ci-src-path">
                    {highlightKeywords(sf.raw_text, keywords)}
                  </code>
                )}
              </li>
            ))}
          </ul>
        </div>
      )}

      {item.test_cases.length > 0 && (
        <div className="ci-field-grid ci-field-grid-test">
          <span className="ci-field-label">테스트</span>
          <span className="ci-field-value">{item.test_cases.join(", ")}</span>
        </div>
      )}

      <footer className="ci-card-footer">
        <div className="ci-source-info">
          <span className="ci-source-label">출처</span>
          <span className="ci-source-filename" title={item.file_name}>
            {item.file_name}
          </span>
          <span className="ci-source-slide">Slide {item.slide_no}</span>
        </div>
        <div className="ci-card-actions">
          {canCopyFolderPath && (
            <button
              type="button"
              className="ci-action-btn"
              onClick={() => void handleCopyFolderPath()}
            >
              폴더 경로 복사
            </button>
          )}
          <button type="button" className="ci-action-btn" onClick={onTogglePath}>
            {expandedPath ? "경로 닫기" : "경로 보기"}
          </button>
          <button type="button" className="ci-action-btn" onClick={onToggleDetail}>
            {expandedDetail ? "상세 닫기" : "상세 보기"}
          </button>
        </div>
        {copyFeedback && (
          <p
            className={
              copyFeedback.type === "success"
                ? "ci-copy-feedback ci-copy-feedback-success"
                : "ci-copy-feedback ci-copy-feedback-error"
            }
            role="status"
          >
            {copyFeedback.text}
          </p>
        )}
      </footer>

      {expandedPath && (
        <div className="ci-expand ci-expand-path">
          <span className="ci-expand-label">경로</span>
          <code className="ci-path-full">{item.file_path}</code>
        </div>
      )}

      {expandedDetail && (
        <div className="ci-expand ci-expand-detail">
          <dl className="ci-detail-dl">
            {item.item_no && (
              <>
                <dt>항목 번호</dt>
                <dd>{item.item_no}</dd>
              </>
            )}
            {item.csr_no && (
              <>
                <dt>CSR</dt>
                <dd>{item.csr_no}</dd>
              </>
            )}
            {item.matched_keywords.length > 0 && (
              <>
                <dt>매칭 키워드</dt>
                <dd>{item.matched_keywords.join(", ")}</dd>
              </>
            )}
            {item.from_fallback && (
              <>
                <dt>탐색</dt>
                <dd>추가 탐색으로 발견</dd>
              </>
            )}
            {item.from_cache_search && !item.from_fallback && (
              <>
                <dt>탐색</dt>
                <dd>캐시 검색으로 발견</dd>
              </>
            )}
            <dt>내부 점수</dt>
            <dd>{item.candidate_score}</dd>
          </dl>
        </div>
      )}
    </article>
  );
}
