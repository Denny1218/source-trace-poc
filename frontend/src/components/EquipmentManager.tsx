import { useCallback, useEffect, useState } from "react";
import {
  createEquipment,
  deleteEquipment,
  fetchEquipmentList,
  updateEquipment,
  validateDocumentPath,
  type Equipment,
  type EquipmentInput,
  type ValidationResult,
} from "../api/equipment";
import {
  createRepository,
  deleteRepository,
  fetchRepositories,
  prepareRepository,
  updateRepository,
  validateLocalPath,
  validateRemoteUrl,
  type GitRepository,
  type GitRepositoryCreate,
  type SourceType,
  type ValidationResult as RepoValidationResult,
} from "../api/repositories";
import LongRunningTaskPanel from "./LongRunningTaskPanel";
import { canonicalRepoUrl } from "../utils/repositoryUrl";
import "./EquipmentManager.css";

type FormMode = "create" | "edit" | null;
type RepoFormMode = "create" | "edit" | null;
type SavePhase = "idle" | "equipment" | "repositories";

type PendingRepo = GitRepositoryCreate & { tempId: string };

type RepoProgressItem = {
  repositoryId?: number;
  name: string;
  status: "pending" | "running" | "done" | "error";
  message?: string;
};

const emptyForm: EquipmentInput = {
  name: "",
  document_path: "",
};

const emptyRepoForm: GitRepositoryCreate = {
  name: "",
  source_type: "remote",
  repository_url: "",
  local_path: "",
};

function newTempId() {
  return `pending-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
}

const DUPLICATE_REPOSITORY_URL_MESSAGE = "동일 장비에 이미 등록된 Repository URL입니다.";

function repoFieldsChanged(existing: GitRepository, form: GitRepositoryCreate): boolean {
  if (existing.name !== form.name.trim()) return true;
  if (existing.source_type !== form.source_type) return true;
  if (form.source_type === "remote") {
    const existingUrl = (existing.repository_url ?? existing.canonical_repository_url ?? "").trim();
    return existingUrl !== (form.repository_url ?? "").trim();
  }
  return (existing.local_path ?? "").trim() !== (form.local_path ?? "").trim();
}

function collectExistingRepoUrls(
  repositories: GitRepository[],
  pendingRepos: PendingRepo[],
  excludePendingId?: string | null,
): Set<string> {
  const urls = new Set<string>();
  for (const repo of repositories) {
    if (repo.source_type === "remote") {
      const url = repo.canonical_repository_url ?? repo.repository_url;
      if (url) urls.add(canonicalRepoUrl(url));
    }
  }
  for (const repo of pendingRepos) {
    if (excludePendingId && repo.tempId === excludePendingId) continue;
    if (repo.source_type === "remote" && repo.repository_url) {
      urls.add(canonicalRepoUrl(repo.repository_url));
    }
  }
  return urls;
}

interface EquipmentManagerProps {
  onEquipmentChange?: () => void;
}

export default function EquipmentManager({ onEquipmentChange }: EquipmentManagerProps) {
  const [items, setItems] = useState<Equipment[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [formMode, setFormMode] = useState<FormMode>(null);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [form, setForm] = useState<EquipmentInput>(emptyForm);
  const [formError, setFormError] = useState<string | null>(null);
  const [formNotice, setFormNotice] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [docValidation, setDocValidation] = useState<ValidationResult | null>(null);
  const [validatingDoc, setValidatingDoc] = useState(false);
  const [savePhase, setSavePhase] = useState<SavePhase>("idle");
  const [repoProgress, setRepoProgress] = useState<RepoProgressItem[]>([]);

  const [repositories, setRepositories] = useState<GitRepository[]>([]);
  const [pendingRepos, setPendingRepos] = useState<PendingRepo[]>([]);
  const [repoFormMode, setRepoFormMode] = useState<RepoFormMode>(null);
  const [editingRepoId, setEditingRepoId] = useState<number | null>(null);
  const [editingPendingId, setEditingPendingId] = useState<string | null>(null);
  const [repoForm, setRepoForm] = useState<GitRepositoryCreate>(emptyRepoForm);
  const [repoFormError, setRepoFormError] = useState<string | null>(null);
  const [repoSaving, setRepoSaving] = useState(false);
  const [repoValidation, setRepoValidation] = useState<RepoValidationResult | null>(null);
  const [validatingRepo, setValidatingRepo] = useState(false);

  const clearRepoEditorError = useCallback(() => {
    setRepoFormError(null);
  }, []);

  const loadList = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchEquipmentList();
      setItems(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "목록 조회 실패");
    } finally {
      setLoading(false);
    }
  }, []);

  const loadRepositories = useCallback(async (equipmentId: number) => {
    try {
      const data = await fetchRepositories(equipmentId);
      setRepositories(data);
    } catch (err) {
      setRepositories([]);
      setError(err instanceof Error ? err.message : "Repository 조회 실패");
    }
  }, []);

  useEffect(() => {
    loadList();
  }, [loadList]);

  useEffect(() => {
    if (formMode === "edit" && editingId !== null) {
      loadRepositories(editingId);
    } else {
      setRepositories([]);
    }
  }, [formMode, editingId, loadRepositories]);

  const resetRepoForm = () => {
    setRepoFormMode(null);
    setEditingRepoId(null);
    setEditingPendingId(null);
    setRepoForm(emptyRepoForm);
    setRepoFormError(null);
    setRepoValidation(null);
  };

  const updateRepoForm = (next: GitRepositoryCreate) => {
    clearRepoEditorError();
    setRepoForm(next);
    setRepoValidation(null);
  };

  const openCreate = () => {
    setForm(emptyForm);
    setFormMode("create");
    setEditingId(null);
    setFormError(null);
    setFormNotice(null);
    setDocValidation(null);
    setPendingRepos([]);
    resetRepoForm();
  };

  const openEdit = (item: Equipment) => {
    setForm({
      name: item.name,
      document_path: item.document_path,
    });
    setFormMode("edit");
    setEditingId(item.id);
    setFormError(null);
    setFormNotice(null);
    setDocValidation(null);
    setPendingRepos([]);
    resetRepoForm();
  };

  const closeForm = () => {
    setFormMode(null);
    setEditingId(null);
    setForm(emptyForm);
    setFormError(null);
    setFormNotice(null);
    setDocValidation(null);
    setPendingRepos([]);
    resetRepoForm();
    setRepositories([]);
  };

  const handleValidateDocument = async (path?: string) => {
    const target = (path ?? form.document_path).trim();
    if (!target) {
      setDocValidation({ valid: false, message: "변경내역서 경로를 입력하세요." });
      return;
    }
    setValidatingDoc(true);
    setDocValidation(null);
    try {
      const result = await validateDocumentPath(target);
      if (result.valid) {
        const pptxMatch = result.message.match(/PPTX\s+(\d+)개/);
        const count = pptxMatch?.[1] ?? "0";
        setDocValidation({
          valid: true,
          message: `변경내역서 폴더 확인 완료\nPPTX ${count}개 · 하위 폴더 포함`,
        });
      } else {
        setDocValidation(result);
      }
    } catch (err) {
      setDocValidation({
        valid: false,
        message: err instanceof Error ? err.message : "검증 실패",
      });
    } finally {
      setValidatingDoc(false);
    }
  };

  const createPendingRepositories = async (equipmentId: number) => {
    const failures: string[] = [];
    const created: GitRepository[] = [];

    for (const repo of pendingRepos) {
      try {
        const saved = await createRepository(equipmentId, {
          name: repo.name,
          source_type: repo.source_type,
          repository_url: repo.repository_url,
          local_path: repo.local_path,
        });
        created.push(saved);
      } catch (err) {
        failures.push(`${repo.name}: ${err instanceof Error ? err.message : "등록 실패"}`);
      }
    }

    return { created, failures };
  };

  const prepareCreatedRepositories = async (createdRepos: GitRepository[]) => {
    const failures: string[] = [];
    const items: RepoProgressItem[] = createdRepos.map((repo) => ({
      repositoryId: repo.id,
      name: repo.name,
      status: repo.source_type === "remote" ? "pending" : "done",
      message: repo.source_type === "local" ? "준비 완료" : undefined,
    }));
    setRepoProgress(items);

    for (let index = 0; index < createdRepos.length; index += 1) {
      const repo = createdRepos[index];
      if (repo.source_type !== "remote") continue;

      setRepoProgress((prev) =>
        prev.map((item, idx) => (idx === index ? { ...item, status: "running" } : item)),
      );
      try {
        await prepareRepository(repo.id);
        setRepoProgress((prev) =>
          prev.map((item, idx) => (idx === index ? { ...item, status: "done" } : item)),
        );
      } catch (err) {
        const message = err instanceof Error ? err.message : "준비 실패";
        failures.push(`${repo.name}: ${message}`);
        setRepoProgress((prev) =>
          prev.map((item, idx) =>
            idx === index ? { ...item, status: "error", message } : item,
          ),
        );
      }
    }

    return failures;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setSavePhase("equipment");
    setFormError(null);
    setFormNotice(null);
    setRepoProgress([]);
    const payload = {
      name: form.name.trim(),
      document_path: form.document_path.trim(),
    };
    try {
      if (formMode === "create") {
        const created = await createEquipment(payload);
        onEquipmentChange?.();
        setFormNotice("장비 정보를 저장했습니다.");
        let failures: string[] = [];
        if (pendingRepos.length > 0) {
          setSavePhase("repositories");
          const result = await createPendingRepositories(created.id);
          failures = [...result.failures];
          setFormNotice("장비 정보가 저장되었습니다. Git Repository를 준비하고 있습니다.");
          failures = failures.concat(await prepareCreatedRepositories(result.created));
        }
        await loadList();
        if (failures.length > 0) {
          const failureNotice =
            `장비는 등록되었지만 일부 Repository 준비에 실패했습니다. (${failures.join("; ")})`;
          openEdit(created);
          setFormNotice(failureNotice);
        } else if (pendingRepos.length > 0) {
          setFormNotice("장비 및 Git Repository 준비가 완료되었습니다.");
          closeForm();
        } else {
          closeForm();
        }
      } else if (formMode === "edit" && editingId !== null) {
        const hadPendingRepos = pendingRepos.length > 0;
        await updateEquipment(editingId, payload);
        onEquipmentChange?.();
        setFormNotice("장비 정보를 저장했습니다.");
        let failures: string[] = [];
        if (hadPendingRepos) {
          setSavePhase("repositories");
          const result = await createPendingRepositories(editingId);
          failures = [...result.failures];
          setFormNotice("장비 정보가 저장되었습니다. Git Repository를 준비하고 있습니다.");
          failures = failures.concat(await prepareCreatedRepositories(result.created));
          setPendingRepos([]);
        }
        await loadList();
        await loadRepositories(editingId);
        if (failures.length > 0) {
          setFormNotice(
            `장비는 저장되었지만 일부 Repository 준비에 실패했습니다. (${failures.join("; ")})`,
          );
        } else if (hadPendingRepos) {
          setFormNotice("장비 및 신규 Git Repository 준비가 완료되었습니다.");
        }
      }
    } catch (err) {
      setFormError(err instanceof Error ? err.message : "저장 실패");
    } finally {
      setSaving(false);
      setSavePhase("idle");
    }
  };

  const handleDelete = async (item: Equipment) => {
    if (!window.confirm(`"${item.name}" 장비를 삭제하시겠습니까?`)) return;
    try {
      await deleteEquipment(item.id);
      onEquipmentChange?.();
      await loadList();
    } catch (err) {
      setError(err instanceof Error ? err.message : "삭제 실패");
    }
  };

  const openRepoCreate = () => {
    setRepoForm(emptyRepoForm);
    setRepoFormMode("create");
    setEditingRepoId(null);
    setEditingPendingId(null);
    setRepoFormError(null);
    setRepoValidation(null);
  };

  const openRepoEdit = (repo: GitRepository) => {
    setRepoForm({
      name: repo.name,
      source_type: repo.source_type,
      repository_url: repo.repository_url ?? "",
      local_path: repo.source_type === "local" ? repo.local_path : "",
    });
    setRepoFormMode("edit");
    setEditingRepoId(repo.id);
    setEditingPendingId(null);
    setRepoFormError(null);
    setRepoValidation(null);
  };

  const openPendingRepoEdit = (repo: PendingRepo) => {
    setRepoForm({
      name: repo.name,
      source_type: repo.source_type,
      repository_url: repo.repository_url ?? "",
      local_path: repo.local_path ?? "",
    });
    setRepoFormMode("edit");
    setEditingPendingId(repo.tempId);
    setEditingRepoId(null);
    setRepoFormError(null);
    setRepoValidation(null);
  };

  const handleValidateRepo = async () => {
    setValidatingRepo(true);
    try {
      if (repoForm.source_type === "remote") {
        if (!repoForm.repository_url?.trim()) {
          setRepoValidation({ valid: false, message: "Git Repository URL을 입력하세요." });
          return;
        }
        const result = await validateRemoteUrl(repoForm.repository_url.trim());
        setRepoValidation(result);
        if (result.valid) {
          clearRepoEditorError();
        }
      } else {
        if (!repoForm.local_path?.trim()) {
          setRepoValidation({ valid: false, message: "Local 경로를 입력하세요." });
          return;
        }
        const result = await validateLocalPath(repoForm.local_path.trim());
        setRepoValidation(result);
        if (result.valid) {
          clearRepoEditorError();
        }
      }
    } catch (err) {
      setRepoValidation({
        valid: false,
        message: err instanceof Error ? err.message : "검증 실패",
      });
    } finally {
      setValidatingRepo(false);
    }
  };

  const handleRepoSubmit = async () => {
    setRepoSaving(true);
    setRepoFormError(null);
    try {
      if (repoFormMode === "create") {
        if (repoForm.source_type === "remote") {
          const url = repoForm.repository_url?.trim() ?? "";
          if (!url) {
            setRepoFormError("Git Repository URL을 입력하세요.");
            return;
          }
          const existingUrls = collectExistingRepoUrls(repositories, pendingRepos);
          if (existingUrls.has(canonicalRepoUrl(url))) {
            setRepoFormError(DUPLICATE_REPOSITORY_URL_MESSAGE);
            return;
          }
        }
        setPendingRepos((prev) => [...prev, { ...repoForm, tempId: newTempId() }]);
        resetRepoForm();
      } else if (repoFormMode === "edit" && editingPendingId) {
        if (repoForm.source_type === "remote") {
          const url = repoForm.repository_url?.trim() ?? "";
          if (!url) {
            setRepoFormError("Git Repository URL을 입력하세요.");
            return;
          }
          const existingUrls = collectExistingRepoUrls(
            repositories,
            pendingRepos,
            editingPendingId,
          );
          if (existingUrls.has(canonicalRepoUrl(url))) {
            setRepoFormError(DUPLICATE_REPOSITORY_URL_MESSAGE);
            return;
          }
        }
        setPendingRepos((prev) =>
          prev.map((repo) =>
            repo.tempId === editingPendingId ? { ...repo, ...repoForm } : repo,
          ),
        );
        resetRepoForm();
      } else if (repoFormMode === "edit" && editingRepoId !== null && formMode === "edit" && editingId !== null) {
        const existing = repositories.find((repo) => repo.id === editingRepoId);
        if (existing && !repoFieldsChanged(existing, repoForm)) {
          resetRepoForm();
          return;
        }
        const updated = await updateRepository(editingRepoId, {
          name: repoForm.name,
          repository_url: repoForm.repository_url,
          local_path: repoForm.local_path,
        });
        if (updated.source_type === "remote" && updated.status === "pending") {
          await prepareRepository(updated.id);
        }
        resetRepoForm();
        await loadRepositories(editingId);
      }
    } catch (err) {
      setRepoFormError(err instanceof Error ? err.message : "Repository 저장 실패");
    } finally {
      setRepoSaving(false);
    }
  };

  const handleRepoDelete = async (repo: GitRepository) => {
    if (!window.confirm(`"${repo.name}" Repository를 삭제하시겠습니까?`)) return;
    if (editingId === null) return;
    try {
      await deleteRepository(repo.id);
      await loadRepositories(editingId);
    } catch (err) {
      setRepoFormError(err instanceof Error ? err.message : "삭제 실패");
    }
  };

  const handlePendingRepoDelete = (tempId: string) => {
    setPendingRepos((prev) => prev.filter((repo) => repo.tempId !== tempId));
  };

  const statusLabel = (status: string) => {
    if (status === "ready") return "Ready";
    if (status === "pending") return "Pending";
    if (status === "error") return "Error";
    return status;
  };

  const repoPathLabel = (sourceType: SourceType, url?: string | null, localPath?: string | null) =>
    sourceType === "remote" ? (url ?? "") : (localPath ?? "");

  return (
    <div className="equipment-manager">
      <header className="equipment-header">
        <div>
          <h1>장비 관리</h1>
          <p className="hint">
            변경내역서 폴더는 UNC 네트워크 공유 경로만 사용합니다.
          </p>
        </div>
        <button type="button" className="btn-primary" onClick={openCreate}>
          장비 추가
        </button>
      </header>

      {error && <div className="banner error">{error}</div>}

      {formMode && (
        <section className="equipment-form-card">
          <h2>{formMode === "create" ? "장비 추가" : "장비 수정"}</h2>
          <form onSubmit={handleSubmit} className="equipment-form">
            {formMode === "edit" && editingId !== null && (
              <div className="form-row">
                <span className="form-label">장비 ID</span>
                <span className="form-id-readonly">{editingId}</span>
              </div>
            )}
            <div className="form-row">
              <label className="form-label" htmlFor="equipment-name">
                장비명
              </label>
              <input
                id="equipment-name"
                type="text"
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
                required
              />
            </div>

            <div className="form-row">
              <label className="form-label" htmlFor="equipment-document-path">
                변경내역서 폴더
              </label>
              <div className="form-field-stack">
                <div className="path-row">
                  <input
                    id="equipment-document-path"
                    type="text"
                    value={form.document_path}
                    onChange={(e) => {
                      setForm({ ...form, document_path: e.target.value });
                      setDocValidation(null);
                    }}
                    placeholder="예: \\서버명\공유폴더\장비명"
                    required
                  />
                  <button type="button" onClick={() => handleValidateDocument()} disabled={validatingDoc}>
                    {validatingDoc ? "확인 중..." : "경로 확인"}
                  </button>
                </div>
                <LongRunningTaskPanel
                  active={validatingDoc}
                  title="변경내역서 폴더를 확인하고 있습니다."
                  description="네트워크 폴더 접근 및 PPTX 파일을 확인 중입니다."
                />
                <span className="field-help">
                  Windows 탐색기에서 네트워크 폴더 경로를 복사하여 붙여넣으세요.
                </span>
                {docValidation && (
                  <span className={docValidation.valid ? "validate-ok" : "validate-error"} style={{ whiteSpace: "pre-line" }}>
                    {docValidation.message}
                  </span>
                )}
              </div>
            </div>

            <section className="repo-section">
              <div className="repo-header">
                <h3>Git Repository</h3>
                <button type="button" className="btn-primary" onClick={openRepoCreate}>
                  + Repository 추가
                </button>
              </div>

              {formMode === "edit" ? (
                repositories.length === 0 && pendingRepos.length === 0 ? (
                  <p className="empty">등록된 Git Repository가 없습니다.</p>
                ) : (
                  <ul className="repo-list">
                    {repositories.map((repo) => (
                      <li key={repo.id} className="repo-row">
                        <span className="repo-row-name">{repo.name}</span>
                        <span className="repo-row-type">
                          {repo.source_type === "remote" ? "Remote" : "Local"}
                        </span>
                        <span className="repo-row-path" title={repoPathLabel(repo.source_type, repo.repository_url, repo.local_path)}>
                          {repoPathLabel(repo.source_type, repo.repository_url, repo.local_path)}
                        </span>
                        <span className="repo-row-status">{statusLabel(repo.status)}</span>
                        <span className="repo-row-actions">
                          <button type="button" onClick={() => openRepoEdit(repo)}>
                            수정
                          </button>
                          <button type="button" className="btn-danger" onClick={() => handleRepoDelete(repo)}>
                            삭제
                          </button>
                        </span>
                      </li>
                    ))}
                    {pendingRepos.map((repo) => (
                      <li key={repo.tempId} className="repo-row">
                        <span className="repo-row-name">{repo.name}</span>
                        <span className="repo-row-type">
                          {repo.source_type === "remote" ? "Remote" : "Local"}
                        </span>
                        <span
                          className="repo-row-path"
                          title={repoPathLabel(repo.source_type, repo.repository_url, repo.local_path)}
                        >
                          {repoPathLabel(repo.source_type, repo.repository_url, repo.local_path)}
                        </span>
                        <span className="repo-row-status">등록 예정</span>
                        <span className="repo-row-actions">
                          <button type="button" onClick={() => openPendingRepoEdit(repo)}>
                            수정
                          </button>
                          <button type="button" className="btn-danger" onClick={() => handlePendingRepoDelete(repo.tempId)}>
                            제거
                          </button>
                        </span>
                      </li>
                    ))}
                  </ul>
                )
              ) : pendingRepos.length === 0 ? (
                <p className="empty">추가할 Git Repository가 없습니다. (0개 허용)</p>
              ) : (
                <ul className="repo-list">
                  {pendingRepos.map((repo) => (
                    <li key={repo.tempId} className="repo-row">
                      <span className="repo-row-name">{repo.name}</span>
                      <span className="repo-row-type">
                        {repo.source_type === "remote" ? "Remote" : "Local"}
                      </span>
                      <span
                        className="repo-row-path"
                        title={repoPathLabel(repo.source_type, repo.repository_url, repo.local_path)}
                      >
                        {repoPathLabel(repo.source_type, repo.repository_url, repo.local_path)}
                      </span>
                      <span className="repo-row-status">등록 예정</span>
                      <span className="repo-row-actions">
                        <button type="button" onClick={() => openPendingRepoEdit(repo)}>
                          수정
                        </button>
                        <button type="button" className="btn-danger" onClick={() => handlePendingRepoDelete(repo.tempId)}>
                          제거
                        </button>
                      </span>
                    </li>
                  ))}
                </ul>
              )}

              {repoFormMode && (
                <div className="repo-form">
                  <h4>{repoFormMode === "create" ? "Repository 추가" : "Repository 수정"}</h4>
                  <div className="repo-form-grid">
                    <label>
                      Repository 이름
                      <input
                        type="text"
                        value={repoForm.name}
                        onChange={(e) => updateRepoForm({ ...repoForm, name: e.target.value })}
                        required
                      />
                    </label>
                    <label>
                      Source Type
                      <select
                        value={repoForm.source_type}
                        onChange={(e) =>
                          updateRepoForm({
                            ...repoForm,
                            source_type: e.target.value as SourceType,
                          })
                        }
                        disabled={repoFormMode === "edit" && formMode === "edit"}
                      >
                        <option value="remote">Remote</option>
                        <option value="local">Local</option>
                      </select>
                    </label>
                  </div>
                  {repoForm.source_type === "remote" ? (
                    <label>
                      Git Repository URL
                      <div className="path-row">
                        <input
                          type="text"
                          value={repoForm.repository_url ?? ""}
                          onChange={(e) =>
                            updateRepoForm({ ...repoForm, repository_url: e.target.value })
                          }
                          placeholder="Yona Git Repository URL 입력"
                          required
                        />
                        <button type="button" onClick={handleValidateRepo} disabled={validatingRepo}>
                          {validatingRepo ? "확인 중..." : "연결 확인"}
                        </button>
                      </div>
                      <span className="field-help">
                        예: http://사용자ID@서버주소:포트/프로젝트/저장소
                      </span>
                    </label>
                  ) : (
                    <label>
                      Local Path
                      <div className="path-row">
                        <input
                          type="text"
                          value={repoForm.local_path ?? ""}
                          onChange={(e) =>
                            updateRepoForm({ ...repoForm, local_path: e.target.value })
                          }
                          placeholder="D:\Source\project"
                          required
                        />
                        <button type="button" onClick={handleValidateRepo} disabled={validatingRepo}>
                          {validatingRepo ? "확인 중..." : "경로 확인"}
                        </button>
                      </div>
                    </label>
                  )}
                  {repoValidation && (
                    <span className={repoValidation.valid ? "validate-ok" : "validate-error"}>
                      {repoValidation.message}
                    </span>
                  )}
                  {repoFormError && <div className="banner error">{repoFormError}</div>}
                  <div className="form-actions">
                    <button
                      type="button"
                      className="btn-primary"
                      disabled={repoSaving}
                      onClick={handleRepoSubmit}
                    >
                      {repoSaving ? "저장 중..." : repoFormMode === "create" ? "목록에 추가" : "변경 저장"}
                    </button>
                    <button type="button" onClick={resetRepoForm}>
                      취소
                    </button>
                  </div>
                </div>
              )}
            </section>

            {formError && <div className="banner error form-banner">{formError}</div>}
            {formNotice && <div className="banner notice form-banner">{formNotice}</div>}
            {savePhase === "repositories" && repoProgress.length > 0 && (
              <div className="repo-progress-panel">
                <p>
                  Git Repository를 준비하고 있습니다. (
                  {repoProgress.filter((item) => item.status === "done").length}/{repoProgress.length})
                </p>
                <ul>
                  {repoProgress.map((item) => (
                    <li key={item.name} className={`repo-progress-${item.status}`}>
                      {item.name}{" "}
                      {item.status === "running" && "준비 중..."}
                      {item.status === "done" && "준비 완료"}
                      {item.status === "error" && (item.message ?? "준비 실패")}
                      {item.status === "pending" && "대기 중..."}
                    </li>
                  ))}
                </ul>
              </div>
            )}
            <LongRunningTaskPanel
              active={savePhase === "equipment"}
              title="장비 정보를 저장하고 있습니다."
            />

            <div className="form-actions">
              <button type="submit" className="btn-primary" disabled={saving}>
                {savePhase === "equipment"
                  ? "장비 정보 저장 중..."
                  : savePhase === "repositories"
                    ? "Repository 준비 중..."
                    : "장비 저장"}
              </button>
              <button type="button" onClick={closeForm}>
                취소
              </button>
            </div>
          </form>
        </section>
      )}

      <section className="equipment-list-card">
        <h2>장비 목록</h2>
        {loading ? (
          <p>불러오는 중...</p>
        ) : items.length === 0 ? (
          <p className="empty">등록된 장비가 없습니다.</p>
        ) : (
          <table>
            <thead>
              <tr>
                <th className="col-id">ID</th>
                <th>장비명</th>
                <th>변경내역서 경로</th>
                <th>수정일</th>
                <th>작업</th>
              </tr>
            </thead>
            <tbody>
              {items.map((item) => (
                <tr key={item.id}>
                  <td className="col-id">{item.id}</td>
                  <td>{item.name}</td>
                  <td className="path-cell" title={item.document_path}>
                    {item.document_path}
                  </td>
                  <td>{item.updated_at.replace("T", " ").replace("+00:00", " UTC")}</td>
                  <td className="actions">
                    <button type="button" onClick={() => openEdit(item)}>
                      수정
                    </button>
                    <button type="button" className="btn-danger" onClick={() => handleDelete(item)}>
                      삭제
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>
    </div>
  );
}
