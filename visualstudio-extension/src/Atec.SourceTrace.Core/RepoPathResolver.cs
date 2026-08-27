using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Text;

namespace Atec.SourceTrace.Core;

/// <summary>Port of vscode-extension repoPathResolver.ts resolveRepoRelativePathForFile.</summary>
public static class RepoPathResolver
{
    public sealed class ResolveError : Exception
    {
        public ResolveError(string message) : base(message) { }
    }

    public sealed class Result
    {
        public string GitRoot { get; }
        public string RepoRelativePath { get; }
        public string? RemoteUrl { get; }

        public Result(string gitRoot, string repoRelativePath, string? remoteUrl)
        {
            GitRoot = gitRoot;
            RepoRelativePath = repoRelativePath;
            RemoteUrl = remoteUrl;
        }
    }

    private const int GitTimeoutMs = 8000;

    public static string ToPosix(string? path)
    {
        return (path ?? string.Empty).Replace('\\', '/');
    }

    public static string ToRepoRelativePath(string gitRoot, string filePath)
    {
        var root = ToPosix(gitRoot).TrimEnd('/');
        var file = ToPosix(filePath);
        var rootCmp = IsWindows() ? root.ToLowerInvariant() : root;
        var fileCmp = IsWindows() ? file.ToLowerInvariant() : file;

        if (fileCmp == rootCmp)
        {
            throw new ResolveError("파일 경로가 Repository 루트입니다.");
        }

        if (!fileCmp.StartsWith(rootCmp + "/", StringComparison.Ordinal))
        {
            throw new ResolveError("선택한 파일이 Git Repository 루트 밖에 있습니다.");
        }

        var rel = file.Substring(root.Length).TrimStart('/');
        if (rel.Length == 0 || ContainsDotDot(rel))
        {
            throw new ResolveError("유효하지 않은 Repository 상대경로입니다.");
        }

        return rel;
    }

    private static bool ContainsDotDot(string rel)
    {
        foreach (var p in rel.Split('/'))
        {
            if (p == "..")
            {
                return true;
            }
        }

        return false;
    }

    public static string? ResolveGitRoot(string filePath)
    {
        var dir = Path.GetDirectoryName(filePath);
        if (string.IsNullOrEmpty(dir))
        {
            return null;
        }

        var outText = RunGit(dir, "rev-parse", "--show-toplevel");
        return string.IsNullOrWhiteSpace(outText) ? null : ToPosix(outText.Trim());
    }

    public static string? ResolveGitRemoteUrl(string gitRoot)
    {
        var outText = RunGit(gitRoot, "remote", "get-url", "origin");
        return string.IsNullOrWhiteSpace(outText) ? null : outText.Trim();
    }

    public static Result ResolveRepoRelativePathForFile(string filePath)
    {
        var gitRoot = ResolveGitRoot(filePath);
        if (gitRoot == null)
        {
            throw new ResolveError("선택한 파일이 Git Repository 안에 있지 않습니다.");
        }

        var rel = ToRepoRelativePath(gitRoot, filePath);
        var remote = ResolveGitRemoteUrl(gitRoot);
        return new Result(gitRoot, rel, remote);
    }

    public static string? FindGitRootByDotGit(string filePath)
    {
        var p = new DirectoryInfo(Path.GetFullPath(filePath)).Parent;
        while (p != null)
        {
            if (Directory.Exists(Path.Combine(p.FullName, ".git")) || File.Exists(Path.Combine(p.FullName, ".git")))
            {
                return ToPosix(p.FullName);
            }

            p = p.Parent;
        }

        return null;
    }

    public static Result ResolveWithFallback(string filePath)
    {
        try
        {
            return ResolveRepoRelativePathForFile(filePath);
        }
        catch (ResolveError first)
        {
            var root = FindGitRootByDotGit(filePath);
            if (root == null)
            {
                throw first;
            }

            var rel = ToRepoRelativePath(root, filePath);
            return new Result(root, rel, null);
        }
    }

    private static bool IsWindows()
    {
        return Environment.OSVersion.Platform == PlatformID.Win32NT;
    }

    private static string? RunGit(string cwd, params string[] args)
    {
        var cmd = new List<string> { "git" };
        cmd.AddRange(args);
        try
        {
            var psi = new ProcessStartInfo
            {
                FileName = "git",
                Arguments = string.Join(" ", args),
                WorkingDirectory = cwd,
                RedirectStandardOutput = true,
                RedirectStandardError = true,
                UseShellExecute = false,
                CreateNoWindow = true,
                StandardOutputEncoding = Encoding.UTF8,
            };

            using var p = Process.Start(psi);
            if (p == null)
            {
                return null;
            }

            if (!p.WaitForExit(GitTimeoutMs))
            {
                try { p.Kill(); } catch { /* ignore */ }
                return null;
            }

            if (p.ExitCode != 0)
            {
                return null;
            }

            return p.StandardOutput.ReadToEnd();
        }
        catch
        {
            return null;
        }
    }
}
