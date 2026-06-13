"""gaokao-sync-remotes CLI tests (T10.3)."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = PROJECT_ROOT / "scripts" / "gaokao-sync-remotes"
DEFAULT_REMOTES = ("gitea", "origin", "tksea")


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
    )


def _run_cli(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT_PATH), *args],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
    )


def _init_repo(tmp_path: Path) -> tuple[Path, dict[str, Path]]:
    repo = tmp_path / "repo"
    repo.mkdir()
    assert _git(repo, "init", "-b", "main").returncode == 0
    assert _git(repo, "config", "user.name", "T10 Tester").returncode == 0
    assert _git(repo, "config", "user.email", "t10@example.com").returncode == 0

    readme = repo / "README.md"
    readme.write_text("hello\n", encoding="utf-8")
    assert _git(repo, "add", "README.md").returncode == 0
    assert _git(repo, "commit", "-m", "init").returncode == 0

    remotes: dict[str, Path] = {}
    for name in DEFAULT_REMOTES:
        bare = tmp_path / f"{name}.git"
        assert _git(tmp_path, "init", "--bare", str(bare)).returncode == 0
        assert _git(repo, "remote", "add", name, str(bare)).returncode == 0
        remotes[name] = bare
    return repo, remotes


def _remote_head(remote_path: Path, branch: str = "main") -> str:
    result = subprocess.run(
        ["git", "--git-dir", str(remote_path), "rev-parse", branch],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    return result.stdout.strip()


def test_dry_run_lists_all_three_push_commands(tmp_path: Path) -> None:
    repo, remotes = _init_repo(tmp_path)

    result = _run_cli(repo, "--dry-run")

    assert result.returncode == 0, result.stderr
    for remote_name in remotes:
        assert f"[DRY-RUN] git push {remote_name} main" in result.stdout
    for remote_path in remotes.values():
        assert not (remote_path / "refs" / "heads" / "main").exists()


def test_pushes_main_to_all_three_remotes_and_verifies_heads(tmp_path: Path) -> None:
    repo, remotes = _init_repo(tmp_path)

    result = _run_cli(repo)

    assert result.returncode == 0, result.stderr
    local_head = _git(repo, "rev-parse", "HEAD").stdout.strip()
    for remote_name, remote_path in remotes.items():
        assert f"OK {remote_name}: main @ {local_head}" in result.stdout
        assert _remote_head(remote_path) == local_head


def test_missing_remote_fails_before_push(tmp_path: Path) -> None:
    repo, _ = _init_repo(tmp_path)
    assert _git(repo, "remote", "remove", "tksea").returncode == 0

    result = _run_cli(repo)

    assert result.returncode == 2
    assert "missing remotes: tksea" in result.stderr
