#!/usr/bin/env uv run python
"""
Retry-enabled wrappers for common operations that frequently fail in agent workflows.

Provides drop-in replacements for subprocess, file I/O, and Git operations with
built-in retry logic and failure telemetry.
"""

import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import json

from core.retry import retry, RetryPolicy
from core.telemetry import EnhancedTelemetryCollector


class RetrySubprocess:
    """Subprocess wrapper with retry logic for external command execution"""

    @staticmethod
    @retry(RetryPolicy.SUBPROCESS, "subprocess_run")
    def run(
        args: Union[str, List[str]],
        timeout: Optional[float] = None,
        check: bool = True,
        capture_output: bool = False,
        text: bool = True,
        **kwargs,
    ) -> subprocess.CompletedProcess:
        """
        Retry-enabled subprocess.run with intelligent error handling

        Args:
            args: Command and arguments
            timeout: Command timeout in seconds
            check: Raise exception on non-zero exit
            capture_output: Capture stdout/stderr
            text: Return strings instead of bytes
            **kwargs: Additional subprocess.run arguments

        Returns:
            CompletedProcess result

        Raises:
            subprocess.CalledProcessError: On command failure after retries
            subprocess.TimeoutExpired: On timeout after retries
        """
        return subprocess.run(
            args,
            timeout=timeout,
            check=check,
            capture_output=capture_output,
            text=text,
            **kwargs,
        )

    @staticmethod
    @retry(RetryPolicy.SUBPROCESS, "subprocess_check_output")
    def check_output(
        args: Union[str, List[str]],
        timeout: Optional[float] = None,
        text: bool = True,
        **kwargs,
    ) -> str:
        """
        Retry-enabled subprocess.check_output

        Args:
            args: Command and arguments
            timeout: Command timeout in seconds
            text: Return string instead of bytes
            **kwargs: Additional subprocess arguments

        Returns:
            Command output as string
        """
        return subprocess.check_output(args, timeout=timeout, text=text, **kwargs)

    @staticmethod
    @retry(RetryPolicy.SUBPROCESS, "subprocess_call")
    def call(args: Union[str, List[str]], **kwargs) -> int:
        """
        Retry-enabled subprocess.call

        Args:
            args: Command and arguments
            **kwargs: Additional subprocess arguments

        Returns:
            Exit code
        """
        return subprocess.call(args, **kwargs)


class RetryGitOperations:
    """Git operations with specialized retry logic for common Git failures"""

    def __init__(self, repo_path: Optional[Path] = None):
        self.repo_path = repo_path or Path.cwd()
        self.telemetry = EnhancedTelemetryCollector()

    @retry(RetryPolicy.GIT_OPERATION, "git_clone")
    def clone(
        self, repo_url: str, dest_path: Path, branch: Optional[str] = None
    ) -> None:
        """
        Clone repository with retry logic

        Args:
            repo_url: Repository URL to clone
            dest_path: Destination path for clone
            branch: Specific branch to clone (optional)
        """
        cmd = ["git", "clone"]
        if branch:
            cmd.extend(["-b", branch])
        cmd.extend([repo_url, str(dest_path)])

        subprocess.run(cmd, check=True, capture_output=True, text=True)

    @retry(RetryPolicy.GIT_OPERATION, "git_pull")
    def pull(self, remote: str = "origin", branch: Optional[str] = None) -> str:
        """
        Pull changes with retry logic

        Args:
            remote: Remote name (default: origin)
            branch: Branch name (optional)

        Returns:
            Git pull output
        """
        cmd = ["git", "pull", remote]
        if branch:
            cmd.append(branch)

        result = subprocess.run(
            cmd, cwd=self.repo_path, check=True, capture_output=True, text=True
        )
        return result.stdout

    @retry(RetryPolicy.GIT_OPERATION, "git_push")
    def push(
        self, remote: str = "origin", branch: Optional[str] = None, force: bool = False
    ) -> str:
        """
        Push changes with retry logic

        Args:
            remote: Remote name (default: origin)
            branch: Branch name (optional)
            force: Force push (use with caution)

        Returns:
            Git push output
        """
        cmd = ["git", "push"]
        if force:
            cmd.append("--force")
        cmd.append(remote)
        if branch:
            cmd.append(branch)

        result = subprocess.run(
            cmd, cwd=self.repo_path, check=True, capture_output=True, text=True
        )
        return result.stdout

    @retry(RetryPolicy.GIT_OPERATION, "git_fetch")
    def fetch(self, remote: str = "origin", all_remotes: bool = False) -> str:
        """
        Fetch changes with retry logic

        Args:
            remote: Remote name (default: origin)
            all_remotes: Fetch from all remotes

        Returns:
            Git fetch output
        """
        cmd = ["git", "fetch"]
        if all_remotes:
            cmd.append("--all")
        else:
            cmd.append(remote)

        result = subprocess.run(
            cmd, cwd=self.repo_path, check=True, capture_output=True, text=True
        )
        return result.stdout

    @retry(RetryPolicy.GIT_OPERATION, "git_status")
    def status(self, porcelain: bool = False) -> str:
        """
        Get repository status with retry logic

        Args:
            porcelain: Use porcelain format for scripting

        Returns:
            Git status output
        """
        cmd = ["git", "status"]
        if porcelain:
            cmd.append("--porcelain")

        result = subprocess.run(
            cmd, cwd=self.repo_path, check=True, capture_output=True, text=True
        )
        return result.stdout

    @retry(RetryPolicy.GIT_OPERATION, "git_add")
    def add(self, files: Union[str, List[str]], all_files: bool = False) -> None:
        """
        Add files to staging with retry logic

        Args:
            files: File path(s) to add
            all_files: Add all files (git add .)
        """
        cmd = ["git", "add"]
        if all_files:
            cmd.append(".")
        else:
            if isinstance(files, str):
                cmd.append(files)
            else:
                cmd.extend(files)

        subprocess.run(
            cmd, cwd=self.repo_path, check=True, capture_output=True, text=True
        )

    @retry(RetryPolicy.GIT_OPERATION, "git_commit")
    def commit(self, message: str, allow_empty: bool = False) -> str:
        """
        Commit changes with retry logic

        Args:
            message: Commit message
            allow_empty: Allow empty commits

        Returns:
            Git commit output
        """
        cmd = ["git", "commit", "-m", message]
        if allow_empty:
            cmd.append("--allow-empty")

        result = subprocess.run(
            cmd, cwd=self.repo_path, check=True, capture_output=True, text=True
        )
        return result.stdout


class RetryFileOperations:
    """File operations with retry logic for handling locks and temporary failures"""

    @staticmethod
    @retry(RetryPolicy.FILESYSTEM, "file_read_text")
    def read_text(file_path: Path, encoding: str = "utf-8") -> str:
        """
        Read text file with retry logic

        Args:
            file_path: Path to file
            encoding: Text encoding

        Returns:
            File contents as string
        """
        return file_path.read_text(encoding=encoding)

    @staticmethod
    @retry(RetryPolicy.FILESYSTEM, "file_write_text")
    def write_text(
        file_path: Path, content: str, encoding: str = "utf-8", create_dirs: bool = True
    ) -> None:
        """
        Write text file with retry logic

        Args:
            file_path: Path to file
            content: Content to write
            encoding: Text encoding
            create_dirs: Create parent directories if needed
        """
        if create_dirs:
            file_path.parent.mkdir(parents=True, exist_ok=True)

        file_path.write_text(content, encoding=encoding)

    @staticmethod
    @retry(RetryPolicy.FILESYSTEM, "file_read_json")
    def read_json(file_path: Path) -> Dict[str, Any]:
        """
        Read JSON file with retry logic

        Args:
            file_path: Path to JSON file

        Returns:
            Parsed JSON data
        """
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)

    @staticmethod
    @retry(RetryPolicy.FILESYSTEM, "file_write_json")
    def write_json(
        file_path: Path, data: Dict[str, Any], indent: int = 2, create_dirs: bool = True
    ) -> None:
        """
        Write JSON file with retry logic

        Args:
            file_path: Path to JSON file
            data: Data to write
            indent: JSON indentation
            create_dirs: Create parent directories if needed
        """
        if create_dirs:
            file_path.parent.mkdir(parents=True, exist_ok=True)

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=indent, ensure_ascii=False)

    @staticmethod
    @retry(RetryPolicy.FILESYSTEM, "file_copy")
    def copy(src: Path, dst: Path, create_dirs: bool = True) -> None:
        """
        Copy file with retry logic

        Args:
            src: Source file path
            dst: Destination file path
            create_dirs: Create parent directories if needed
        """
        if create_dirs:
            dst.parent.mkdir(parents=True, exist_ok=True)

        shutil.copy2(src, dst)

    @staticmethod
    @retry(RetryPolicy.FILESYSTEM, "file_move")
    def move(src: Path, dst: Path, create_dirs: bool = True) -> None:
        """
        Move file with retry logic

        Args:
            src: Source file path
            dst: Destination file path
            create_dirs: Create parent directories if needed
        """
        if create_dirs:
            dst.parent.mkdir(parents=True, exist_ok=True)

        shutil.move(src, dst)

    @staticmethod
    @retry(RetryPolicy.FILESYSTEM, "file_delete")
    def delete(file_path: Path, missing_ok: bool = True) -> None:
        """
        Delete file with retry logic

        Args:
            file_path: Path to file
            missing_ok: Don't raise exception if file doesn't exist
        """
        try:
            file_path.unlink()
        except FileNotFoundError:
            if not missing_ok:
                raise

    @staticmethod
    @retry(RetryPolicy.FILESYSTEM, "dir_create")
    def mkdir(dir_path: Path, parents: bool = True, exist_ok: bool = True) -> None:
        """
        Create directory with retry logic

        Args:
            dir_path: Directory path to create
            parents: Create parent directories
            exist_ok: Don't raise exception if directory exists
        """
        dir_path.mkdir(parents=parents, exist_ok=exist_ok)

    @staticmethod
    @retry(RetryPolicy.FILESYSTEM, "dir_delete")
    def rmdir(dir_path: Path, recursive: bool = False) -> None:
        """
        Delete directory with retry logic

        Args:
            dir_path: Directory path to delete
            recursive: Delete recursively (rm -rf equivalent)
        """
        if recursive:
            shutil.rmtree(dir_path)
        else:
            dir_path.rmdir()


class RetryNetworkOperations:
    """Network operations with retry logic (placeholder for future HTTP/API wrappers)"""

    def __init__(self):
        self.telemetry = EnhancedTelemetryCollector()

    # Future: Add HTTP client wrappers with retry logic
    # @retry(RetryPolicy.NETWORK, "http_get")
    # def get(self, url: str, **kwargs) -> requests.Response:
    #     return requests.get(url, **kwargs)


# Convenience function to create a Git operations instance
def get_git_ops(repo_path: Optional[Path] = None) -> RetryGitOperations:
    """
    Get Git operations instance for a repository

    Args:
        repo_path: Repository path (defaults to current directory)

    Returns:
        RetryGitOperations instance
    """
    return RetryGitOperations(repo_path)


# Module-level convenience aliases for common operations
subprocess_run = RetrySubprocess.run
subprocess_check_output = RetrySubprocess.check_output
subprocess_call = RetrySubprocess.call

read_text = RetryFileOperations.read_text
write_text = RetryFileOperations.write_text
read_json = RetryFileOperations.read_json
write_json = RetryFileOperations.write_json
copy_file = RetryFileOperations.copy
move_file = RetryFileOperations.move
delete_file = RetryFileOperations.delete
mkdir = RetryFileOperations.mkdir
rmdir = RetryFileOperations.rmdir
