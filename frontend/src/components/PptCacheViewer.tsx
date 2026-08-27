import { useCallback, useEffect, useMemo, useState } from "react";

import { fetchEquipmentList, type Equipment } from "../api/equipment";

import {

  deletePptCache,

  fetchPptCacheDetail,

  fetchPptCacheList,

  runPptAnalysis,

  type DocumentCacheDetail,

  type DocumentCacheSummary,

  type PptAnalysisResponse,

  type SlideCandidateItem,

} from "../api/pptCache";

import "./PptCacheViewer.css";

import {

  DEFAULT_START_DATE,

  formatLocalDateForInput,

  parseKeywordInput,

} from "../utils/searchForm";

import {

  countDistinctDocuments,

  sortChangeItemCandidates,

} from "../utils/changeItemDisplay";

import LongRunningTaskPanel from "./LongRunningTaskPanel";

import ChangeItemResultCard from "./ChangeItemResultCard";

import type { TabWorkCallbacks } from "../types/tabWork";



interface PptCacheViewerProps extends TabWorkCallbacks {

  equipmentVersion: number;

}



function groupSlidesByDocument(slides: SlideCandidateItem[]) {

  const map = new Map<string, { fileName: string; filePath: string; slides: SlideCandidateItem[] }>();

  for (const slide of slides) {

    const key = String(slide.document_cache_id);

    if (!map.has(key)) {

      map.set(key, {

        fileName: slide.file_name,

        filePath: slide.file_path,

        slides: [],

      });

    }

    map.get(key)!.slides.push(slide);

  }

  return Array.from(map.values()).map((doc) => ({

    ...doc,

    slides: doc.slides.sort((a, b) => a.slide_number - b.slide_number),

  }));

}



export default function PptCacheViewer({ equipmentVersion, onWorkStatusChange }: PptCacheViewerProps) {

  const today = formatLocalDateForInput();

  const [equipmentList, setEquipmentList] = useState<Equipment[]>([]);

  const [equipmentId, setEquipmentId] = useState<number | "">("");

  const [cacheList, setCacheList] = useState<DocumentCacheSummary[]>([]);

  const [detail, setDetail] = useState<DocumentCacheDetail | null>(null);

  const [analysis, setAnalysis] = useState<PptAnalysisResponse | null>(null);

  const [keywords, setKeywords] = useState("");

  const [useDateRange, setUseDateRange] = useState(false);

  const [dateFrom, setDateFrom] = useState(DEFAULT_START_DATE);

  const [dateTo, setDateTo] = useState(today);

  const [loading, setLoading] = useState(false);

  const [analyzing, setAnalyzing] = useState(false);

  const [error, setError] = useState<string | null>(null);

  const [showAnalysisDetail, setShowAnalysisDetail] = useState(false);

  const [showCachePanel, setShowCachePanel] = useState(false);

  const [lastKeywords, setLastKeywords] = useState<string[]>([]);

  const [expandedPathIds, setExpandedPathIds] = useState<Set<number>>(new Set());

  const [expandedDetailIds, setExpandedDetailIds] = useState<Set<number>>(new Set());



  const selectedEquipment = useMemo(

    () => equipmentList.find((eq) => eq.id === equipmentId),

    [equipmentList, equipmentId],

  );



  useEffect(() => {

    fetchEquipmentList()

      .then((data) => {

        setEquipmentList(data);

        setEquipmentId((current) => {

          if (current !== "" && !data.some((eq) => eq.id === current)) {

            return "";

          }

          return current;

        });

      })

      .catch((err) => setError(err instanceof Error ? err.message : "장비 목록 실패"));

  }, [equipmentVersion]);



  useEffect(() => {

    if (equipmentId === "") return;

    if (!equipmentList.some((eq) => eq.id === equipmentId)) {

      setAnalysis(null);

      setCacheList([]);

      setDetail(null);

    }

  }, [equipmentList, equipmentId]);



  const loadCache = useCallback(async (id: number) => {

    setLoading(true);

    setError(null);

    try {

      const docs = await fetchPptCacheList(id);

      setCacheList(docs);

    } catch (err) {

      setError(err instanceof Error ? err.message : "Cache 조회 실패");

    } finally {

      setLoading(false);

    }

  }, []);



  const handleEquipmentChange = (id: number) => {

    setEquipmentId(id);

    setDetail(null);

    setAnalysis(null);

    setError(null);

    setExpandedPathIds(new Set());

    setExpandedDetailIds(new Set());

    loadCache(id);

  };



  const handleShowDetail = async (docId: number) => {

    setLoading(true);

    setError(null);

    try {

      setDetail(await fetchPptCacheDetail(docId));

    } catch (err) {

      setError(err instanceof Error ? err.message : "상세 조회 실패");

    } finally {

      setLoading(false);

    }

  };



  const handleDelete = async (docId: number) => {

    if (!window.confirm("Cache만 삭제합니다. 원본 PPT는 유지됩니다. 계속할까요?")) return;

    setLoading(true);

    try {

      await deletePptCache(docId);

      if (equipmentId !== "") await loadCache(equipmentId);

      if (detail?.id === docId) setDetail(null);

    } catch (err) {

      setError(err instanceof Error ? err.message : "삭제 실패");

    } finally {

      setLoading(false);

    }

  };



  const handleAnalysis = async () => {

    if (equipmentId === "") return;

    const parsedKeywords = parseKeywordInput(keywords);

    if (parsedKeywords.length === 0) {

      setError("검색 키워드를 1개 이상 입력해 주세요.");

      setAnalysis(null);

      return;

    }



    setAnalyzing(true);

    setError(null);

    setAnalysis(null);

    setDetail(null);

    setExpandedPathIds(new Set());

    setExpandedDetailIds(new Set());

    onWorkStatusChange?.("running");

    try {

      const request = {

        equipment_id: equipmentId,

        keywords: parsedKeywords,

        ...(useDateRange && dateFrom ? { date_from: dateFrom } : {}),

        ...(useDateRange && dateTo ? { date_to: dateTo } : {}),

      };

      const result = await runPptAnalysis(request);

      setAnalysis(result);

      setLastKeywords(parsedKeywords);

      await loadCache(equipmentId);

      onWorkStatusChange?.("success", "변경내역서 분석이 완료되었습니다.");

    } catch (err) {

      const message = err instanceof Error ? err.message : "분석 실패";

      setError(message);

      setAnalysis(null);

      onWorkStatusChange?.("error", "변경내역서 분석에 실패했습니다.");

    } finally {

      setAnalyzing(false);

    }

  };



  const togglePath = (id: number) => {

    setExpandedPathIds((prev) => {

      const next = new Set(prev);

      if (next.has(id)) next.delete(id);

      else next.add(id);

      return next;

    });

  };



  const toggleDetail = (id: number) => {

    setExpandedDetailIds((prev) => {

      const next = new Set(prev);

      if (next.has(id)) next.delete(id);

      else next.add(id);

      return next;

    });

  };



  const groupedResults = useMemo(

    () => (analysis ? groupSlidesByDocument(analysis.slide_candidates) : []),

    [analysis],

  );



  const sortedChangeItems = useMemo(

    () => (analysis ? sortChangeItemCandidates(analysis.change_item_candidates) : []),

    [analysis],

  );



  const documentCount = useMemo(

    () => (analysis ? countDistinctDocuments(analysis.change_item_candidates) : 0),

    [analysis],

  );



  return (

    <div className="ppt-cache-viewer">

      <h2>변경내역서 분석</h2>

      {error && <p className="error">{error}</p>}



      <section className="ppt-cache-controls">

        <div className="search-row-primary">

          <label>

            장비

            <select

              value={equipmentId}

              onChange={(e) => {

                const v = e.target.value;

                if (v) handleEquipmentChange(Number(v));

                else {

                  setEquipmentId("");

                  setAnalysis(null);

                  setCacheList([]);

                }

              }}

            >

              <option value="">선택</option>

              {equipmentList.map((eq) => (

                <option key={eq.id} value={eq.id}>

                  {eq.name}

                </option>

              ))}

            </select>

          </label>

          <label className="keyword-field">

            <span className="keyword-label-row">

              검색 키워드

              <span className="field-help-inline">예: 함수명, 상수명, 변경 내용</span>

            </span>

            <input

              value={keywords}

              onChange={(e) => setKeywords(e.target.value)}

              placeholder="검색 키워드를 쉼표로 구분하여 입력"

            />

          </label>

          <button

            type="button"

            className="btn-primary analyze-btn"

            onClick={handleAnalysis}

            disabled={equipmentId === "" || analyzing}

          >

            {analyzing ? "분석 중..." : "분석 실행"}

          </button>

        </div>

        <LongRunningTaskPanel

          active={analyzing}

          title="변경내역서를 분석하고 있습니다."

          description="관련 PPT 후보 탐색 및 문서 분석 중..."

        />

        <div className="period-filter">

          <label className="period-toggle">

            <input

              type="checkbox"

              checked={useDateRange}

              onChange={(e) => setUseDateRange(e.target.checked)}

            />

            <span>기간 지정</span>

          </label>

          <label>

            시작일

            <input

              type="date"

              disabled={!useDateRange}

              value={dateFrom}

              onChange={(e) => setDateFrom(e.target.value)}

            />

          </label>

          <label>

            종료일

            <input

              type="date"

              disabled={!useDateRange}

              value={dateTo}

              onChange={(e) => setDateTo(e.target.value)}

            />

          </label>

        </div>

      </section>



      {analysis && (

        <section className="ppt-analysis-result">

          <div className="ci-summary-bar">

            <span className="ci-summary-count">

              변경 항목 {analysis.change_item_total}건

            </span>

            {selectedEquipment && (

              <span className="ci-summary-equipment">[{selectedEquipment.name}]</span>

            )}

            <span className="ci-summary-sub">

              문서 {documentCount}개 · 키워드 {lastKeywords.join(", ") || "-"}

            </span>



          </div>



          {sortedChangeItems.length === 0 ? (

            <p className="empty">

              키워드와 일치하는 변경 항목이 없습니다. 분석 상태 상세에서 Slide 후보를 확인해 보세요.

            </p>

          ) : (

            <div className="ci-result-list">

              {sortedChangeItems.map((item) => (

                <ChangeItemResultCard

                  key={item.change_item_cache_id}

                  item={item}

                  keywords={lastKeywords}

                  expandedPath={expandedPathIds.has(item.change_item_cache_id)}

                  expandedDetail={expandedDetailIds.has(item.change_item_cache_id)}

                  onTogglePath={() => togglePath(item.change_item_cache_id)}

                  onToggleDetail={() => toggleDetail(item.change_item_cache_id)}

                />

              ))}

            </div>

          )}

        </section>

      )}



      {equipmentId !== "" && (

        <div className="ci-collapse-toggles">

          <button

            type="button"

            className="ci-debug-toggle"

            onClick={() => setShowAnalysisDetail((v) => !v)}

          >

            {showAnalysisDetail ? "▼ 분석 상태 상세 닫기" : "▶ 분석 상태 상세"}

          </button>

          <button

            type="button"

            className="ci-debug-toggle"

            onClick={() => setShowCachePanel((v) => !v)}

          >

            {showCachePanel ? "▼ 분석 Cache 보기 닫기" : "▶ 분석 Cache 보기"}

          </button>

        </div>

      )}



      {showAnalysisDetail && equipmentId !== "" && analysis && (

        <section className="ppt-analysis-debug">

          <h3>분석 상태 상세</h3>

          <ul className="analysis-stats">

            <li>PPT 후보: {analysis.ppt_candidate_count}</li>

            <li>처리 문서: {analysis.processed_documents}</li>

            <li>Cache Hit: {analysis.cache_hits}</li>

            <li>Cache Miss: {analysis.cache_misses}</li>

            <li>Parse 실패: {analysis.parse_failures}</li>

            <li>Slide 후보: {analysis.slide_candidates.length}</li>

            <li>Change Item 후보: {analysis.change_item_total}</li>

            <li>추가 탐색 문서: {analysis.fallback_documents_parsed}</li>
            <li>
              장비 불일치 제외 문서: {analysis.equipment_filter_excluded ?? 0}
              <span className="muted"> (filename equipment mismatch)</span>
            </li>

          </ul>



          <h4>Slide 후보 (디버그)</h4>

          {groupedResults.length === 0 ? (

            <p className="empty">키워드와 일치하는 Slide 후보가 없습니다.</p>

          ) : (

            <div className="current-analysis-docs">

              {groupedResults.map((doc) => (

                <article key={doc.filePath} className="analysis-doc-group">

                  <h5 title={doc.filePath}>{doc.fileName}</h5>

                  <p className="doc-path" title={doc.filePath}>

                    {doc.filePath}

                  </p>

                  <ul>

                    {doc.slides.map((slide) => (

                      <li key={slide.slide_cache_id} className="analysis-slide-item">

                        <div className="slide-meta">

                          <strong>Slide {slide.slide_number}</strong>

                          {slide.title ? ` — ${slide.title}` : ""}

                          <span className="slide-score">점수 {slide.candidate_score}</span>

                        </div>

                        <div className="slide-keywords">

                          키워드: {slide.matched_keywords.join(", ")}

                        </div>

                        {slide.content && (

                          <pre className="slide-content-preview">{slide.content}</pre>

                        )}

                      </li>

                    ))}

                  </ul>

                </article>

              ))}

            </div>

          )}

        </section>

      )}



      {showCachePanel && equipmentId !== "" && (

        <section className="ppt-analysis-debug ppt-cache-panel">

          <h3>분석 Cache {loading ? "(로딩…)" : ""}</h3>

          <p className="section-hint">전체 Parse Cache 목록입니다.</p>

          <table>

            <thead>

              <tr>

                <th>파일명</th>

                <th>Slide</th>

                <th>Hash (앞 12자)</th>

                <th>parsed_at</th>

                <th></th>

              </tr>

            </thead>

            <tbody>

              {cacheList.map((doc) => (

                <tr key={doc.id}>

                  <td>{doc.file_name}</td>

                  <td>{doc.slide_count}</td>

                  <td title={doc.file_hash}>{doc.file_hash.slice(0, 12)}…</td>

                  <td>{doc.parsed_at}</td>

                  <td>

                    <button type="button" onClick={() => handleShowDetail(doc.id)}>

                      상세

                    </button>

                    <button type="button" onClick={() => handleDelete(doc.id)}>

                      삭제

                    </button>

                  </td>

                </tr>

              ))}

            </tbody>

          </table>



          {detail && (

            <div className="ppt-cache-detail">

              <h4>Cache 상세: {detail.file_name}</h4>

              {detail.slides.map((slide) => (

                <div key={slide.id} className="slide-block">

                  <h5>

                    Slide {slide.slide_number}

                    {slide.title ? `: ${slide.title}` : ""}

                  </h5>

                  <pre>{slide.content || "(빈 Slide)"}</pre>

                </div>

              ))}

            </div>

          )}

        </section>

      )}

    </div>

  );

}


