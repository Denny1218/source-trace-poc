import { useCallback, useEffect, useRef, useState } from "react";
import {
  fetchCommitDetail,
  fetchCommitList,
  fetchEquipmentList,
  syncGitHistory,
  type CommitDetail,
  type CommitListItem,
  type CommitSearchParams,
  type Equipment,
} from "../api/gitHistory";
import { fetchRepositories, type GitRepository } from "../api/repositories";
import DiffViewer, { formatCommitDate, shortenHash } from "./DiffViewer";
import LongRunningTaskPanel from "./LongRunningTaskPanel";
import type { TabWorkCallbacks } from "../types/tabWork";
import "./GitHistory.css";
import {
  DEFAULT_START_DATE,
  formatLocalDateForInput,
} from "../utils/searchForm";

interface GitHistoryProps extends TabWorkCallbacks {
  equipmentVersion: number;
}

const EMPTY_SEARCH: CommitSearchParams = {
  page: 1,
  page_size: 50,
  date_from: DEFAULT_START_DATE,
  date_to: formatLocalDateForInput(),
};

export default function GitHistory({ equipmentVersion, onWorkStatusChange }: GitHistoryProps) {
  const [equipmentList, setEquipmentList] = useState<Equipment[]>([]);
  const [equipmentId, setEquipmentId] = useState<number | "">("");
  const [repositoryId, setRepositoryId] = useState<number | "">("");
  const [repositories, setRepositories] = useState<GitRepository[]>([]);
  const [searchInput, setSearchInput] = useState<CommitSearchParams>(EMPTY_SEARCH);
  const [activeSearch, setActiveSearch] = useState<CommitSearchParams>(EMPTY_SEARCH);
  const [useDateRange, setUseDateRange] = useState(false);
  const [commits, setCommits] = useState<CommitListItem[]>([]);
  const [pagination, setPagination] = useState({ page: 1, total: 0, total_pages: 0 });
  const [selectedCommitId, setSelectedCommitId] = useState<number | null>(null);
  const [commitDetail, setCommitDetail] = useState<CommitDetail | null>(null);
  const [selectedChangeId, setSelectedChangeId] = useState<number | null>(null);
  const [loadingList, setLoadingList] = useState(false);
  const [loadingDetail, setLoadingDetail] = useState(false);
  const [syncing, setSyncing] = useState(false);
  const [listError, setListError] = useState<string | null>(null);
  const [searched, setSearched] = useState(false);
  const [syncMessage, setSyncMessage] = useState<string | null>(null);
  const nextLoadShouldNotifyRef = useRef(false);

  const loadEquipment = useCallback(async () => {
    try {
      const data = await fetchEquipmentList();
      setEquipmentList(data);
      setEquipmentId((current) => {
        if (current !== "" && !data.some((eq) => eq.id === current)) {
          return "";
        }
        if (current === "" && data.length === 1) {
          return data[0].id;
        }
        return current;
      });
    } catch {
      setEquipmentList([]);
    }
  }, []);

  useEffect(() => {
    void loadEquipment();
  }, [loadEquipment, equipmentVersion]);

  useEffect(() => {
    if (equipmentId === "") return;
    if (!equipmentList.some((eq) => eq.id === equipmentId)) {
      setRepositoryId("");
      setRepositories([]);
      setCommits([]);
      setSelectedCommitId(null);
      setCommitDetail(null);
      setSearched(false);
      setListError(null);
    }
  }, [equipmentList, equipmentId]);

  useEffect(() => {
    if (!equipmentId) {
      setRepositories([]);
      setRepositoryId("");
      return;
    }
    fetchRepositories(equipmentId)
      .then(setRepositories)
      .catch(() => setRepositories([]));
    setRepositoryId("");
  }, [equipmentId]);

  const loadCommits = useCallback(async (options?: { notify?: boolean }) => {
    const notify = options?.notify ?? false;
    if (!equipmentId) return;
    setLoadingList(true);
    setListError(null);
    if (notify) {
      onWorkStatusChange?.("running");
    }
    try {
      const params: CommitSearchParams = { ...activeSearch };
      if (repositoryId) params.repository_id = repositoryId;
      const data = await fetchCommitList(equipmentId, params);
      setCommits(data.items);
      setPagination({
        page: data.page,
        total: data.total,
        total_pages: data.total_pages,
      });
      setSearched(true);
      if (notify) {
        onWorkStatusChange?.("success", "Git 변경 이력 조회가 완료되었습니다.");
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : "목록 조회 실패";
      setListError(message);
      setCommits([]);
      if (notify) {
        onWorkStatusChange?.("error", message);
      }
    } finally {
      setLoadingList(false);
    }
  }, [equipmentId, repositoryId, activeSearch, onWorkStatusChange]);

  useEffect(() => {
    if (equipmentId) {
      const notify = nextLoadShouldNotifyRef.current;
      nextLoadShouldNotifyRef.current = false;
      void loadCommits({ notify });
    }
  }, [equipmentId, activeSearch, loadCommits]);

  const loadDetail = useCallback(async (commitId: number) => {
    setLoadingDetail(true);
    setSelectedChangeId(null);
    try {
      const detail = await fetchCommitDetail(commitId);
      setCommitDetail(detail);
      if (detail.changes.length > 0) {
        setSelectedChangeId(detail.changes[0].id);
      }
    } catch (err) {
      setCommitDetail(null);
    } finally {
      setLoadingDetail(false);
    }
  }, []);

  const handleSelectCommit = (commit: CommitListItem) => {
    setSelectedCommitId(commit.id);
    loadDetail(commit.id);
  };

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    const nextSearch: CommitSearchParams = {
      q: searchInput.q,
      file_path: searchInput.file_path,
      author: searchInput.author,
      page: 1,
      page_size: 50,
    };
    if (useDateRange) {
      if (searchInput.date_from) nextSearch.date_from = searchInput.date_from;
      if (searchInput.date_to) nextSearch.date_to = searchInput.date_to;
    }
    if (JSON.stringify(nextSearch) === JSON.stringify(activeSearch)) {
      void loadCommits({ notify: true });
      return;
    }
    nextLoadShouldNotifyRef.current = true;
    setActiveSearch(nextSearch);
    setSelectedCommitId(null);
    setCommitDetail(null);
  };

  const handleReset = () => {
    setUseDateRange(false);
    setSearchInput({
      page: 1,
      page_size: 50,
      date_from: DEFAULT_START_DATE,
      date_to: formatLocalDateForInput(),
    });
    setActiveSearch({ page: 1, page_size: 50 });
    setSelectedCommitId(null);
    setCommitDetail(null);
  };

  const handleSync = async () => {
    if (!equipmentId || syncing) return;
    setSyncing(true);
    setSyncMessage(null);
    onWorkStatusChange?.("running");
    try {
      const result = await syncGitHistory(equipmentId);
      const message = `동기화 완료: 신규 Commit ${result.new_commits}개, 변경 ${result.new_changes}건`;
      setSyncMessage(message);
      onWorkStatusChange?.("success", "Git 동기화가 완료되었습니다.");
      await loadCommits();
    } catch (err) {
      const message = err instanceof Error ? err.message : "동기화 실패";
      setSyncMessage(message);
      onWorkStatusChange?.("error", message);
    } finally {
      setSyncing(false);
    }
  };

  const selectedChange = commitDetail?.changes.find((c) => c.id === selectedChangeId);

  if (equipmentList.length === 0) {
    return (
      <div className="git-history">
        <div className="empty-state">먼저 장비 관리에서 장비를 등록하십시오.</div>
      </div>
    );
  }

  return (
    <div className="git-history">
      <header className="git-history-header">
        <h1>Git 변경 이력 조회</h1>
        <div className="equipment-row">
          <label>
            장비 선택
            <select
              value={equipmentId}
              onChange={(e) => {
                setEquipmentId(e.target.value ? Number(e.target.value) : "");
                setSelectedCommitId(null);
                setCommitDetail(null);
                setSearched(false);
              }}
            >
              <option value="">선택...</option>
              {equipmentList.map((eq) => (
                <option key={eq.id} value={eq.id}>
                  {eq.name}
                </option>
              ))}
            </select>
          </label>
          {equipmentId && (
            <label>
              Repository
              <select
                value={repositoryId}
                onChange={(e) => {
                  setRepositoryId(e.target.value ? Number(e.target.value) : "");
                  setSelectedCommitId(null);
                  setCommitDetail(null);
                }}
              >
                <option value="">전체 Repository</option>
                {repositories.map((repo) => (
                  <option key={repo.id} value={repo.id}>
                    {repo.name}
                  </option>
                ))}
              </select>
            </label>
          )}
          {equipmentId && (
            <button type="button" onClick={handleSync} disabled={syncing}>
              {syncing ? "동기화 중..." : "Git 동기화"}
            </button>
          )}
        </div>
        {syncMessage && <div className="sync-message">{syncMessage}</div>}
        <LongRunningTaskPanel
          active={syncing}
          title="Git 동기화 중..."
          description="Git Commit 및 변경 파일을 수집하고 있습니다."
        />
      </header>

      {equipmentId && (
        <>
          <form className="search-form" onSubmit={handleSearch}>
            <div className="search-row search-row-main">
              <label className="search-main">
                통합 검색어
                <input
                  type="text"
                  value={searchInput.q ?? ""}
                  onChange={(e) => setSearchInput({ ...searchInput, q: e.target.value })}
                  placeholder="커밋 메시지, 함수명, 파일명 등 검색"
                />
              </label>
              <button type="submit" className="btn-primary" disabled={loadingList}>
                {loadingList ? "검색 중..." : "검색"}
              </button>
            </div>
            <div className="search-row search-filters">
              <div className="period-filter">
                <label className="period-toggle">
                  <input
                    type="checkbox"
                    checked={useDateRange}
                    onChange={(e) => {
                      setUseDateRange(e.target.checked);
                    }}
                  />
                  <span>기간 지정</span>
                </label>
                <label>
                  시작일
                  <input
                    type="date"
                    disabled={!useDateRange}
                    value={searchInput.date_from?.slice(0, 10) ?? ""}
                    onChange={(e) =>
                      setSearchInput({
                        ...searchInput,
                        date_from: e.target.value || DEFAULT_START_DATE,
                      })
                    }
                  />
                </label>
                <label>
                  종료일
                  <input
                    type="date"
                    disabled={!useDateRange}
                    value={searchInput.date_to?.slice(0, 10) ?? ""}
                    onChange={(e) =>
                      setSearchInput({
                        ...searchInput,
                        date_to: e.target.value || formatLocalDateForInput(),
                      })
                    }
                  />
                </label>
              </div>
              <label>
                파일 경로
                <input
                  type="text"
                  value={searchInput.file_path ?? ""}
                  onChange={(e) =>
                    setSearchInput({ ...searchInput, file_path: e.target.value })
                  }
                />
              </label>
              <label>
                작성자
                <input
                  type="text"
                  value={searchInput.author ?? ""}
                  onChange={(e) =>
                    setSearchInput({ ...searchInput, author: e.target.value })
                  }
                />
              </label>
              <button type="button" onClick={handleReset}>
                초기화
              </button>
            </div>
          </form>

          <LongRunningTaskPanel
            active={loadingList && !syncing}
          title="Git 변경 이력을 조회하고 있습니다."
            description="Git Commit 및 변경 파일 검색 중..."
          />

          {listError && <div className="banner error">{listError}</div>}

          <div className="git-history-body">
            <section className="commit-list-panel">
              <h2>Commit 목록 {pagination.total > 0 && `(${pagination.total})`}</h2>
              <div className="commit-list-scroll">
                {!loadingList && searched && commits.length === 0 && !listError ? (
                  <p className="empty-state">검색 결과가 없습니다.</p>
                ) : pagination.total === 0 && !loadingList && searched ? (
                  <p className="empty-state">
                    Git 변경 이력이 없습니다.
                    <br />
                    Git 동기화 버튼을 눌러 이력을 수집하십시오.
                  </p>
                ) : (
                  <ul className="commit-list">
                    {commits.map((c) => (
                      <li
                        key={c.id}
                        className={selectedCommitId === c.id ? "selected" : ""}
                      >
                        <button type="button" onClick={() => handleSelectCommit(c)}>
                          <div className="commit-summary">
                            <span className="commit-repo">[{c.repository_name}]</span>
                            <span className="commit-msg">{c.message.split("\n")[0]}</span>
                          </div>
                          <span className="commit-meta">
                            <span title={c.commit_hash}>{shortenHash(c.commit_hash)}</span>
                            <span>{formatCommitDate(c.commit_date)}</span>
                            <span>{c.author}</span>
                            <span>
                              {c.changed_file_count} files +{c.additions} -{c.deletions}
                            </span>
                          </span>
                        </button>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
              {pagination.total_pages > 1 && (
                <div className="pagination">
                  <button
                    type="button"
                    disabled={pagination.page <= 1}
                    onClick={() =>
                      setActiveSearch((prev) => ({ ...prev, page: pagination.page - 1 }))
                    }
                  >
                    이전
                  </button>
                  <span>
                    {pagination.page} / {pagination.total_pages}
                  </span>
                  <button
                    type="button"
                    disabled={pagination.page >= pagination.total_pages}
                    onClick={() =>
                      setActiveSearch((prev) => ({ ...prev, page: pagination.page + 1 }))
                    }
                  >
                    다음
                  </button>
                </div>
              )}
            </section>

            <section className="commit-detail-panel">
              <h2>Commit 상세</h2>
              <div className="commit-detail-scroll">
                {!selectedCommitId ? (
                  <p className="empty-hint">Commit을 선택하세요.</p>
                ) : loadingDetail ? (
                  <p>불러오는 중...</p>
                ) : commitDetail ? (
                  <>
                    <dl className="commit-info">
                      <dt>Hash</dt>
                      <dd className="mono">{commitDetail.commit_hash}</dd>
                      <dt>Date</dt>
                      <dd>{formatCommitDate(commitDetail.commit_date)}</dd>
                      <dt>Author</dt>
                      <dd>{commitDetail.author}</dd>
                      <dt>Message</dt>
                      <dd className="pre-wrap">{commitDetail.message}</dd>
                      {commitDetail.parent_hash && (
                        <>
                          <dt>Parent</dt>
                          <dd className="mono">{commitDetail.parent_hash}</dd>
                        </>
                      )}
                    </dl>
                    <h3>변경 파일</h3>
                    <ul className="change-list">
                      {commitDetail.changes.map((ch) => (
                        <li
                          key={ch.id}
                          className={selectedChangeId === ch.id ? "selected" : ""}
                        >
                          <button type="button" onClick={() => setSelectedChangeId(ch.id)}>
                            <span className="file-path">{ch.file_path}</span>
                            <span className="change-meta">
                              {ch.change_type}
                              {ch.additions != null && ` +${ch.additions}`}
                              {ch.deletions != null && ` -${ch.deletions}`}
                            </span>
                          </button>
                        </li>
                      ))}
                    </ul>
                    {selectedChange && (
                      <div className="diff-panel">
                        <h3>{selectedChange.file_path}</h3>
                        <DiffViewer diff={selectedChange.diff} />
                      </div>
                    )}
                  </>
                ) : null}
              </div>
            </section>
          </div>
        </>
      )}
    </div>
  );
}
