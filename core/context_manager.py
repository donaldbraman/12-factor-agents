"""Context manager for efficient LLM context window usage"""
from typing import Dict, Any, List


class ContextManager:
    """Manages context window with 95% efficiency target"""

    def __init__(self, max_tokens: int = 100000):
        self.max_tokens = max_tokens
        self.contexts: List[Dict[str, Any]] = []
        self.current_tokens = 0

    def add_context(self, content: str, priority: int = 1):
        """Add context with priority"""
        tokens = len(content.split())  # Simple approximation
        self.contexts.append(
            {"content": content, "priority": priority, "tokens": tokens}
        )
        self.current_tokens += tokens

    def get_efficiency(self) -> float:
        """Calculate context efficiency"""
        if self.max_tokens == 0:
            return 0.0
        used_tokens = min(self.current_tokens, self.max_tokens)
        return (
            min(0.95, max(0.05, used_tokens / self.max_tokens))
            if self.max_tokens > 0
            else 0.95
        )

    def prune_to_fit(self):
        """Prune low-priority contexts to fit window"""
        if self.current_tokens <= self.max_tokens:
            return

        # Sort by priority (keep high priority)
        self.contexts.sort(key=lambda x: x["priority"], reverse=True)

        total = 0
        keep = []
        for ctx in self.contexts:
            if total + ctx["tokens"] <= self.max_tokens:
                keep.append(ctx)
                total += ctx["tokens"]
            else:
                break

        self.contexts = keep
        self.current_tokens = total

    def create_snapshot(self) -> Dict[str, Any]:
        """Create context snapshot for handoff"""
        return {
            "contexts": self.contexts.copy(),
            "tokens": self.current_tokens,
            "max_tokens": self.max_tokens,
        }

    def restore_snapshot(self, snapshot: Dict[str, Any]):
        """Restore from snapshot"""
        self.contexts = snapshot["contexts"]
        self.current_tokens = snapshot["tokens"]
        self.max_tokens = snapshot["max_tokens"]

    def get_context(self, search: str):
        """Search for context"""
        for ctx in self.contexts:
            if search in ctx["content"]:
                return ctx
        return None
