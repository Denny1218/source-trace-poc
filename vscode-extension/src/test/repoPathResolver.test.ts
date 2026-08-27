/**
 * PROJECT_SPEC v2.5.1 — repo path matching helpers (no VS Code API).
 */
import { test } from "node:test";
import assert from "node:assert/strict";

import {
  canonicalizeRemoteUrl,
  clearResolvedRepoCache,
  matchEquipmentRepository,
  rememberResolvedRepo,
  toRepoRelativePath,
  RepoPathResolveError,
} from "../repoPathResolver";

test("toRepoRelativePath strips git root with slash normalization", () => {
  const rel = toRepoRelativePath(
    "/home/op/ws/device-a",
    "/home/op/ws/device-a/Fare/src/fare_calc.c"
  );
  assert.equal(rel, "Fare/src/fare_calc.c");
});

test("toRepoRelativePath rejects path outside root", () => {
  assert.throws(
    () => toRepoRelativePath("/home/op/ws/a", "/home/op/ws/b/file.c"),
    (err: unknown) => err instanceof RepoPathResolveError
  );
});

test("canonicalizeRemoteUrl absorbs .git suffix", () => {
  assert.equal(
    canonicalizeRemoteUrl("http://git.example/fare.git"),
    canonicalizeRemoteUrl("http://git.example/fare")
  );
});

test("canonicalizeRemoteUrl maps SCP-style SSH and ssh:// to same key", () => {
  const a = canonicalizeRemoteUrl("git@git.example:group/fare.git");
  const b = canonicalizeRemoteUrl("ssh://git@git.example/group/fare.git");
  const c = canonicalizeRemoteUrl("https://git.example/group/fare");
  assert.equal(a, b);
  assert.equal(a, c);
});

test("canonicalizeRemoteUrl maps SSH vs HTTPS same repo", () => {
  assert.equal(
    canonicalizeRemoteUrl("git@host:path/repo.git"),
    canonicalizeRemoteUrl("https://host/path/repo")
  );
});

test("matchEquipmentRepository prefers remote URL", () => {
  const { repo, method } = matchEquipmentRepository(
    [
      {
        id: 1,
        name: "other",
        canonical_repository_url: "http://git.example/other.git",
        status: "ready",
      },
      {
        id: 2,
        name: "fare",
        canonical_repository_url: "http://git.example/fare.git",
        status: "ready",
      },
    ],
    {
      gitRoot: "/home/op/ws/fare",
      remoteUrl: "http://git.example/fare.git",
    }
  );
  assert.equal(repo.id, 2);
  assert.equal(method, "remote_url");
});

test("matchEquipmentRepository matches SCP remote to https canonical", () => {
  const { repo, method } = matchEquipmentRepository(
    [
      {
        id: 2,
        name: "fare",
        canonical_repository_url: "https://git.example/group/fare",
        status: "ready",
      },
      { id: 3, name: "other", status: "ready" },
    ],
    {
      gitRoot: "/home/op/ws/fare",
      remoteUrl: "git@git.example:group/fare.git",
    }
  );
  assert.equal(repo.id, 2);
  assert.equal(method, "remote_url");
});

test("matchEquipmentRepository uses preferred repo_id first", () => {
  const { repo, method } = matchEquipmentRepository(
    [
      { id: 1, name: "a", status: "ready" },
      {
        id: 2,
        name: "fare",
        canonical_repository_url: "http://git.example/fare.git",
        status: "ready",
      },
    ],
    {
      gitRoot: "/home/op/ws/fare",
      remoteUrl: "http://git.example/fare.git",
      preferredRepoId: 1,
    }
  );
  assert.equal(repo.id, 1);
  assert.equal(method, "preferred_repo_id");
});

test("matchEquipmentRepository uses cached repo after URL miss", () => {
  const { repo, method } = matchEquipmentRepository(
    [
      { id: 7, name: "cached-one", status: "ready" },
      { id: 8, name: "other", status: "ready" },
    ],
    {
      gitRoot: "/tmp/x",
      remoteUrl: null,
      cachedRepoId: 7,
    }
  );
  assert.equal(repo.id, 7);
  assert.equal(method, "cached_repo_id");
});

test("matchEquipmentRepository uses single ready repo fallback", () => {
  const { repo, method } = matchEquipmentRepository(
    [{ id: 9, name: "only", status: "ready" }],
    { gitRoot: "/tmp/x", remoteUrl: null }
  );
  assert.equal(repo.id, 9);
  assert.equal(method, "single_repo");
});

test("matchEquipmentRepository refuses ambiguous multi-repo without remote", () => {
  assert.throws(
    () =>
      matchEquipmentRepository(
        [
          { id: 1, name: "a", status: "ready" },
          { id: 2, name: "b", status: "ready" },
        ],
        { gitRoot: "/tmp/x", remoteUrl: null }
      ),
    (err: unknown) =>
      err instanceof RepoPathResolveError &&
      err.message.includes("매칭하지 못했습니다") &&
      err.hintLines.some((h) => h.includes("remote URL"))
  );
});

test("rememberResolvedRepo cache helpers do not throw", () => {
  clearResolvedRepoCache();
  rememberResolvedRepo({
    serverUrl: "http://127.0.0.1:8000",
    equipmentId: 1,
    gitRoot: "/tmp/repo",
    repoId: 42,
  });
  clearResolvedRepoCache();
});
