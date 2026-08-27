package com.atec.sourcetrace.eclipse.core;

import java.io.BufferedReader;
import java.io.File;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.TimeUnit;

/**
 * Port of vscode-extension {@code repoPathResolver.ts}
 * {@code resolveRepoRelativePathForFile} — git CLI first (same as VS Code).
 * Absolute IDE paths are never sent as Backend identity keys.
 */
public final class RepoPathResolver {

	public static final class ResolveError extends Exception {
		private static final long serialVersionUID = 1L;

		public ResolveError(String message) {
			super(message);
		}
	}

	public static final class Result {
		public final String gitRoot;
		public final String repoRelativePath;
		public final String remoteUrl;

		public Result(String gitRoot, String repoRelativePath, String remoteUrl) {
			this.gitRoot = gitRoot;
			this.repoRelativePath = repoRelativePath;
			this.remoteUrl = remoteUrl;
		}
	}

	private static final int GIT_TIMEOUT_SEC = 8;

	private RepoPathResolver() {
	}

	public static String toPosix(String path) {
		if (path == null) {
			return "";
		}
		return path.replace('\\', '/');
	}

	public static String toRepoRelativePath(String gitRoot, String filePath) throws ResolveError {
		String root = toPosix(gitRoot).replaceAll("/+$", "");
		String file = toPosix(filePath);
		String rootCmp = isWindows() ? root.toLowerCase() : root;
		String fileCmp = isWindows() ? file.toLowerCase() : file;
		if (fileCmp.equals(rootCmp)) {
			throw new ResolveError("파일 경로가 Repository 루트입니다.");
		}
		if (!fileCmp.startsWith(rootCmp + "/")) {
			throw new ResolveError("선택한 파일이 Git Repository 루트 밖에 있습니다.");
		}
		String rel = file.substring(root.length()).replaceAll("^/+", "");
		if (rel.isEmpty() || ArraysContainsDotDot(rel)) {
			throw new ResolveError("유효하지 않은 Repository 상대경로입니다.");
		}
		return rel;
	}

	private static boolean ArraysContainsDotDot(String rel) {
		for (String p : rel.split("/")) {
			if ("..".equals(p)) {
				return true;
			}
		}
		return false;
	}

	public static String resolveGitRoot(String filePath) {
		File dir = new File(filePath).getParentFile();
		if (dir == null) {
			return null;
		}
		String out = runGit(dir, "rev-parse", "--show-toplevel");
		if (out == null || out.isEmpty()) {
			return null;
		}
		return toPosix(out.trim());
	}

	public static String resolveGitRemoteUrl(String gitRoot) {
		String out = runGit(new File(gitRoot), "remote", "get-url", "origin");
		if (out == null || out.isEmpty()) {
			return null;
		}
		return out.trim();
	}

	public static Result resolveRepoRelativePathForFile(String filePath) throws ResolveError {
		String gitRoot = resolveGitRoot(filePath);
		if (gitRoot == null) {
			throw new ResolveError("선택한 파일이 Git Repository 안에 있지 않습니다.");
		}
		String rel = toRepoRelativePath(gitRoot, filePath);
		String remote = resolveGitRemoteUrl(gitRoot);
		return new Result(gitRoot, rel, remote);
	}

	/**
	 * Fallback when git CLI is unavailable: walk parents for {@code .git}.
	 */
	public static String findGitRootByDotGit(String filePath) {
		Path p = Path.of(filePath).toAbsolutePath().getParent();
		while (p != null) {
			File git = p.resolve(".git").toFile();
			if (git.exists()) {
				return toPosix(p.toString());
			}
			p = p.getParent();
		}
		return null;
	}

	public static Result resolveWithFallback(String filePath) throws ResolveError {
		try {
			return resolveRepoRelativePathForFile(filePath);
		} catch (ResolveError first) {
			String root = findGitRootByDotGit(filePath);
			if (root == null) {
				throw first;
			}
			String rel = toRepoRelativePath(root, filePath);
			return new Result(root, rel, null);
		}
	}

	private static boolean isWindows() {
		String os = System.getProperty("os.name", "");
		return os.toLowerCase().contains("win");
	}

	private static String runGit(File cwd, String... args) {
		List<String> cmd = new ArrayList<>();
		cmd.add("git");
		for (String a : args) {
			cmd.add(a);
		}
		try {
			ProcessBuilder pb = new ProcessBuilder(cmd);
			pb.directory(cwd);
			pb.redirectErrorStream(true);
			Process p = pb.start();
			boolean finished = p.waitFor(GIT_TIMEOUT_SEC, TimeUnit.SECONDS);
			if (!finished) {
				p.destroyForcibly();
				return null;
			}
			if (p.exitValue() != 0) {
				return null;
			}
			try (BufferedReader r = new BufferedReader(
					new InputStreamReader(p.getInputStream(), StandardCharsets.UTF_8))) {
				StringBuilder sb = new StringBuilder();
				String line;
				while ((line = r.readLine()) != null) {
					if (sb.length() > 0) {
						sb.append('\n');
					}
					sb.append(line);
				}
				return sb.toString();
			}
		} catch (Exception e) {
			return null;
		}
	}
}
