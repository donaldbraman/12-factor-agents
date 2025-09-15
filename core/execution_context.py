"""
ExecutionContext for Cross-Repository Operations

This module provides the ExecutionContext dataclass that enables proper file resolution
and context tracking across different repositories. It addresses the critical issue where
agents working on sister repositories would look for files in the wrong directory.

Key Features:
- Repository context tracking
- Path resolution relative to target repo
- Telemetry integration
- Child context creation for nested operations
- External repository support

This is the architectural foundation that enables cross-repository agent operations.
"""

import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Dict, Any


@dataclass
class ExecutionContext:
    """
    Context for cross-repository execution

    This class provides the necessary context for agents to operate correctly
    across different repositories, ensuring file operations target the correct
    directory structure.

    Attributes:
        repo_name: Name of the repository (e.g., "pin-citer")
        repo_path: Absolute path to the repository root
        repo_url: GitHub URL of the repository
        source_repo: Original repository identifier (e.g., "pin-citer/pin-citer")
        issue_number: Associated issue number
        issue_url: GitHub issue URL
        working_directory: Current working directory for operations
        is_external: Whether this is an external repository context
        parent_context: Parent context for nested operations
        workflow_id: Unique identifier for this workflow execution
        trace_id: Unique identifier for tracing execution flow
        metadata: Additional context-specific metadata
    """

    # Repository information
    repo_name: str = "12-factor-agents"
    repo_path: Path = field(default_factory=lambda: Path.cwd())
    repo_url: Optional[str] = None

    # Issue tracking
    source_repo: Optional[str] = None  # e.g., "pin-citer/pin-citer"
    issue_number: Optional[int] = None
    issue_url: Optional[str] = None

    # Execution state
    working_directory: Path = field(default_factory=lambda: Path.cwd())
    is_external: bool = False
    parent_context: Optional["ExecutionContext"] = None

    # Telemetry & debugging
    workflow_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    trace_id: str = field(default_factory=lambda: str(uuid.uuid4()))

    # Additional metadata
    metadata: Dict[str, Any] = field(default_factory=dict)

    def resolve_path(self, relative_path: str) -> Path:
        """
        Resolve a path relative to the repository context

        This is the critical method that ensures file operations target
        the correct repository directory, not the current working directory.

        Args:
            relative_path: Path relative to repository root (e.g., "tests/test_file.py")

        Returns:
            Path: Absolute path resolved within the repository context

        Examples:
            >>> context = ExecutionContext(repo_path=Path("/path/to/pin-citer"))
            >>> context.resolve_path("tests/test_file.py")
            Path("/path/to/pin-citer/tests/test_file.py")
        """
        return self.repo_path / relative_path

    def create_child_context(self, **overrides) -> "ExecutionContext":
        """
        Create a child context for nested operations

        Child contexts inherit all properties from the parent but can override
        specific attributes. The parent relationship is maintained for tracing.

        Args:
            **overrides: Properties to override in the child context

        Returns:
            ExecutionContext: New child context with parent reference

        Examples:
            >>> parent = ExecutionContext(repo_name="main-repo")
            >>> child = parent.create_child_context(repo_name="sub-repo")
            >>> child.parent_context == parent
            True
        """
        child_data = {**self.__dict__, **overrides}
        child_data.pop("parent_context", None)  # Don't copy parent reference

        child = ExecutionContext(**child_data)
        child.parent_context = self

        # Create new IDs for child unless explicitly overridden
        if "workflow_id" not in overrides:
            child.workflow_id = str(uuid.uuid4())
        if "trace_id" not in overrides:
            child.trace_id = str(uuid.uuid4())

        return child

    def is_path_within_repo(self, path: Path) -> bool:
        """
        Check if a path is within the repository boundaries

        Args:
            path: Path to check (can be absolute or relative)

        Returns:
            bool: True if path is within the repository
        """
        try:
            if not path.is_absolute():
                path = self.resolve_path(str(path))
            path.relative_to(self.repo_path)
            return True
        except ValueError:
            return False

    def get_relative_path(self, absolute_path: Path) -> Path:
        """
        Get path relative to repository root

        Args:
            absolute_path: Absolute path to convert

        Returns:
            Path: Path relative to repository root

        Raises:
            ValueError: If path is not within repository
        """
        return absolute_path.relative_to(self.repo_path)

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert context to dictionary for serialization

        Returns:
            Dict: Serializable representation of the context
        """
        return {
            "repo_name": self.repo_name,
            "repo_path": str(self.repo_path),
            "repo_url": self.repo_url,
            "source_repo": self.source_repo,
            "issue_number": self.issue_number,
            "issue_url": self.issue_url,
            "working_directory": str(self.working_directory),
            "is_external": self.is_external,
            "workflow_id": self.workflow_id,
            "trace_id": self.trace_id,
            "metadata": self.metadata,
            "has_parent": self.parent_context is not None,
        }

    def __str__(self) -> str:
        """String representation for debugging"""
        external_marker = " (EXTERNAL)" if self.is_external else ""
        return f"ExecutionContext[{self.repo_name}{external_marker}@{self.repo_path}]"

    def __repr__(self) -> str:
        """Detailed string representation"""
        return (
            f"ExecutionContext(repo_name='{self.repo_name}', "
            f"repo_path='{self.repo_path}', is_external={self.is_external}, "
            f"workflow_id='{self.workflow_id}')"
        )


def create_external_context(
    repo: str,
    repo_path: Path,
    issue_number: Optional[int] = None,
    workflow_id: Optional[str] = None,
) -> ExecutionContext:
    """
    Convenience function to create an external repository context

    Args:
        repo: Repository identifier (e.g., "pin-citer/pin-citer")
        repo_path: Local path to the repository
        issue_number: Associated issue number
        workflow_id: Optional workflow ID (generated if not provided)

    Returns:
        ExecutionContext: Configured external context
    """
    repo_name = repo.split("/")[-1]  # Extract repo name from "owner/repo"

    return ExecutionContext(
        repo_name=repo_name,
        repo_path=repo_path,
        repo_url=f"https://github.com/{repo}",
        source_repo=repo,
        issue_number=issue_number,
        issue_url=f"https://github.com/{repo}/issues/{issue_number}"
        if issue_number
        else None,
        working_directory=repo_path,
        is_external=True,
        workflow_id=workflow_id or str(uuid.uuid4()),
    )


def create_default_context() -> ExecutionContext:
    """
    Create a default context for the current repository

    Returns:
        ExecutionContext: Default context for 12-factor-agents repo
    """
    current_path = Path.cwd()

    return ExecutionContext(
        repo_name="12-factor-agents",
        repo_path=current_path,
        repo_url="https://github.com/donaldbraman/12-factor-agents",
        working_directory=current_path,
        is_external=False,
    )
