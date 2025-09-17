#!/usr/bin/env python3
"""
Simple Transactions - Safe operations with automatic rollback

Instead of complex distributed transactions, we use simple, reliable patterns:
1. Git-based rollback (leverage existing tools)
2. File snapshots for non-git changes
3. Operation journaling for recovery
4. Simple atomic operations

This solves Issue #113: No Rollback Mechanism for Failed Operations
"""

from pathlib import Path
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass
from datetime import datetime
import shutil
import subprocess
import contextlib


@dataclass
class OperationRecord:
    """Record of an operation for rollback purposes"""

    operation_id: str
    operation_type: str  # "git", "file", "directory", "external"
    timestamp: datetime
    description: str
    rollback_data: Dict[str, Any]
    completed: bool = False


@dataclass
class TransactionResult:
    """Result of a transaction execution"""

    success: bool
    transaction_id: str
    operations_completed: int
    operations_total: int
    error_message: Optional[str] = None
    rollback_performed: bool = False


class SimpleTransactionManager:
    """
    Simple transaction manager using reliable, existing tools.

    Key insight: Instead of building complex transaction systems,
    leverage git's built-in transaction capabilities and simple file operations.
    """

    def __init__(self, repo_path: Path = None):
        self.repo_path = repo_path or Path.cwd()
        self.transaction_log: List[OperationRecord] = []
        self.active_transaction_id: Optional[str] = None
        self.backup_dir = Path.home() / ".cache" / "12factor-transactions"
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    @contextlib.contextmanager
    def transaction(self, description: str = "Operation"):
        """
        Context manager for safe operations with automatic rollback.

        Usage:
            with transaction_manager.transaction("Fix issue #123"):
                # Do operations
                modify_file("file1.py", content)
                run_git_command(["git", "add", "file1.py"])
        """

        transaction_id = f"tx-{int(datetime.now().timestamp())}"
        self.active_transaction_id = transaction_id

        print(f"🚀 Starting transaction {transaction_id}: {description}")

        # Create git checkpoint (if in git repo)
        initial_commit = self._create_git_checkpoint()

        try:
            yield self

            # If we get here, transaction succeeded
            print(f"✅ Transaction {transaction_id} completed successfully")
            self._cleanup_transaction(transaction_id)

        except Exception as e:
            print(f"❌ Transaction {transaction_id} failed: {e}")
            print("🔄 Rolling back changes...")

            # Perform rollback
            rollback_success = self._rollback_transaction(
                transaction_id, initial_commit
            )

            if rollback_success:
                print("✅ Rollback completed successfully")
            else:
                print("⚠️ Rollback had issues - manual cleanup may be needed")

            # Re-raise the original exception
            raise

        finally:
            self.active_transaction_id = None

    def safe_file_operation(
        self, operation: Callable, file_path: Path, description: str = ""
    ) -> Any:
        """
        Perform a file operation with automatic backup for rollback.

        Args:
            operation: Function that performs the file operation
            file_path: Path to the file being modified
            description: Human-readable description of the operation
        """

        if not self.active_transaction_id:
            raise RuntimeError("File operation must be within a transaction")

        operation_id = f"op-{len(self.transaction_log)}"

        # Create backup before operation
        backup_path = None
        if file_path.exists():
            backup_path = self._backup_file(file_path, operation_id)

        # Record the operation for rollback
        record = OperationRecord(
            operation_id=operation_id,
            operation_type="file",
            timestamp=datetime.now(),
            description=description or f"Modify {file_path}",
            rollback_data={
                "file_path": str(file_path),
                "backup_path": str(backup_path) if backup_path else None,
                "existed_before": file_path.exists(),
            },
        )

        self.transaction_log.append(record)

        try:
            # Perform the operation
            result = operation()
            record.completed = True
            return result

        except Exception as e:
            print(f"🔄 Operation {operation_id} failed, will be rolled back: {e}")
            raise

    def safe_git_operation(self, git_args: List[str], description: str = "") -> str:
        """
        Perform a git operation with rollback support.

        Args:
            git_args: Git command arguments (e.g., ["add", "file.py"])
            description: Human-readable description
        """

        if not self.active_transaction_id:
            raise RuntimeError("Git operation must be within a transaction")

        operation_id = f"git-{len(self.transaction_log)}"

        # Record git state before operation
        git_status_before = self._get_git_status()

        record = OperationRecord(
            operation_id=operation_id,
            operation_type="git",
            timestamp=datetime.now(),
            description=description or f"git {' '.join(git_args)}",
            rollback_data={"command": git_args, "status_before": git_status_before},
        )

        self.transaction_log.append(record)

        try:
            # Execute git command
            result = subprocess.run(
                ["git"] + git_args,
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True,
            )

            record.completed = True
            return result.stdout

        except subprocess.CalledProcessError as e:
            print(f"🔄 Git operation {operation_id} failed: {e}")
            raise

    def _create_git_checkpoint(self) -> Optional[str]:
        """Create a git checkpoint for rollback"""
        try:
            # Get current commit SHA
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True,
            )
            return result.stdout.strip()

        except subprocess.CalledProcessError:
            # Not a git repo or other issue
            return None

    def _get_git_status(self) -> Dict[str, Any]:
        """Get current git status for rollback"""
        try:
            # Get status
            status_result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True,
            )

            # Get staged files
            staged_result = subprocess.run(
                ["git", "diff", "--cached", "--name-only"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True,
            )

            return {
                "status": status_result.stdout,
                "staged_files": staged_result.stdout.split()
                if staged_result.stdout
                else [],
            }

        except subprocess.CalledProcessError:
            return {"status": "", "staged_files": []}

    def _backup_file(self, file_path: Path, operation_id: str) -> Path:
        """Create backup of file for rollback"""
        backup_filename = (
            f"{operation_id}-{file_path.name}-{int(datetime.now().timestamp())}"
        )
        backup_path = self.backup_dir / backup_filename

        shutil.copy2(file_path, backup_path)
        print(f"💾 Backed up {file_path} to {backup_path}")

        return backup_path

    def _rollback_transaction(
        self, transaction_id: str, initial_commit: Optional[str]
    ) -> bool:
        """Roll back all operations in the transaction"""
        rollback_success = True

        # Roll back in reverse order
        for record in reversed(self.transaction_log):
            if not record.completed:
                continue  # Skip operations that didn't complete

            try:
                if record.operation_type == "file":
                    self._rollback_file_operation(record)
                elif record.operation_type == "git":
                    self._rollback_git_operation(record)

            except Exception as e:
                print(f"⚠️ Failed to rollback operation {record.operation_id}: {e}")
                rollback_success = False

        # Final git rollback if we have a checkpoint
        if initial_commit:
            try:
                self._rollback_to_git_commit(initial_commit)
            except Exception as e:
                print(f"⚠️ Failed to rollback to git commit {initial_commit}: {e}")
                rollback_success = False

        return rollback_success

    def _rollback_file_operation(self, record: OperationRecord):
        """Roll back a file operation"""
        file_path = Path(record.rollback_data["file_path"])
        backup_path = record.rollback_data.get("backup_path")
        existed_before = record.rollback_data["existed_before"]

        if backup_path and Path(backup_path).exists():
            # Restore from backup
            shutil.copy2(backup_path, file_path)
            print(f"🔄 Restored {file_path} from backup")

        elif not existed_before and file_path.exists():
            # File was created during transaction, remove it
            file_path.unlink()
            print(f"🔄 Removed created file {file_path}")

    def _rollback_git_operation(self, record: OperationRecord):
        """Roll back a git operation"""
        # For git operations, we rely on the final commit rollback
        # Individual git operation rollback is complex and not always necessary
        print(
            f"🔄 Git operation {record.operation_id} will be rolled back with commit reset"
        )

    def _rollback_to_git_commit(self, commit_sha: str):
        """Reset git to a specific commit"""
        try:
            # Hard reset to the checkpoint commit
            subprocess.run(
                ["git", "reset", "--hard", commit_sha], cwd=self.repo_path, check=True
            )
            print(f"🔄 Git reset to {commit_sha[:8]}")

        except subprocess.CalledProcessError as e:
            print(f"⚠️ Git reset failed: {e}")
            raise

    def _cleanup_transaction(self, transaction_id: str):
        """Clean up after successful transaction"""
        # Remove backups for completed transaction
        for record in self.transaction_log:
            if record.operation_type == "file" and record.rollback_data.get(
                "backup_path"
            ):
                backup_path = Path(record.rollback_data["backup_path"])
                if backup_path.exists():
                    backup_path.unlink()

        # Clear transaction log
        self.transaction_log.clear()


# Convenience functions for common operations
def safe_write_file(
    transaction_manager: SimpleTransactionManager,
    file_path: Path,
    content: str,
    description: str = "",
) -> None:
    """Safely write content to a file with rollback support"""

    def write_operation():
        with open(file_path, "w") as f:
            f.write(content)

    transaction_manager.safe_file_operation(
        write_operation, file_path, description or f"Write to {file_path}"
    )


def safe_modify_file(
    transaction_manager: SimpleTransactionManager,
    file_path: Path,
    modifier_func: Callable[[str], str],
    description: str = "",
) -> None:
    """Safely modify a file using a modifier function"""

    def modify_operation():
        # Read current content
        if file_path.exists():
            with open(file_path, "r") as f:
                current_content = f.read()
        else:
            current_content = ""

        # Apply modification
        new_content = modifier_func(current_content)

        # Write back
        with open(file_path, "w") as f:
            f.write(new_content)

    transaction_manager.safe_file_operation(
        modify_operation, file_path, description or f"Modify {file_path}"
    )


# Example usage
if __name__ == "__main__":
    # Demo safe operations
    transaction_manager = SimpleTransactionManager()

    try:
        with transaction_manager.transaction("Demo safe operations"):
            # These operations will be rolled back if anything fails
            test_file = Path("test_transaction.txt")

            safe_write_file(
                transaction_manager,
                test_file,
                "This is a test file\n",
                "Create test file",
            )

            # Simulate a failure
            # raise Exception("Simulated failure")

        print("✅ Transaction completed successfully")

    except Exception as e:
        print(f"❌ Transaction failed: {e}")

    print("\n🧪 Simple transaction system ready!")
    print("✅ Uses git's built-in transaction capabilities")
    print("✅ Simple file backups for non-git operations")
    print("✅ Automatic rollback on failure")
