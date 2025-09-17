#!/usr/bin/env python3
"""
Context Handoff Mechanisms - How agent functions pass context between each other

Since Claude agents are stateless functions, the critical design challenge is
how to pass complete context between different agent functions efficiently.
"""

from pathlib import Path
from typing import Dict, List, Any
from dataclasses import dataclass, asdict, field
from datetime import datetime
import json
import pickle
import hashlib


@dataclass
class ContextTransfer:
    """Represents a context handoff between agent functions"""

    from_agent: str
    to_agent: str
    context_hash: str
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)


class ContextHandoffManager:
    """
    Manages context transfers between stateless agent functions.

    Key insights:
    1. Agent functions need COMPLETE context each time
    2. Context can be large - need efficient transfer mechanisms
    3. Context immutability helps with debugging and recovery
    4. Context versioning enables rollback and branching
    """

    def __init__(self, cache_dir: Path = None):
        self.cache_dir = cache_dir or Path.home() / ".cache" / "12factor-agents"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.transfer_log: List[ContextTransfer] = []

    def serialize_context(self, context: Any, format: str = "json") -> str:
        """
        Serialize context for transfer between agent functions.

        Multiple formats supported based on size and complexity.
        """
        if format == "json":
            # Best for simple, readable context
            try:
                if hasattr(context, "__dict__"):
                    return json.dumps(asdict(context), indent=2, default=str)
                else:
                    return json.dumps(context, indent=2, default=str)
            except Exception:
                # Fallback to pickle if JSON fails
                return self.serialize_context(context, "pickle")

        elif format == "pickle":
            # Best for complex objects that can't be JSON serialized
            import base64

            pickled = pickle.dumps(context)
            return base64.b64encode(pickled).decode("utf-8")

        else:
            raise ValueError(f"Unknown format: {format}")

    def deserialize_context(self, serialized: str, format: str = "json") -> Any:
        """Deserialize context from transfer format"""
        if format == "json":
            return json.loads(serialized)
        elif format == "pickle":
            import base64

            pickled = base64.b64decode(serialized.encode("utf-8"))
            return pickle.loads(pickled)
        else:
            raise ValueError(f"Unknown format: {format}")

    def cache_context(self, context: Any, context_id: str) -> str:
        """
        Cache context to disk for large context transfers.

        Returns cache key for retrieval.
        """
        # Generate content hash for deduplication
        serialized = self.serialize_context(context)
        context_hash = hashlib.sha256(serialized.encode()).hexdigest()[:16]

        # Cache to disk
        cache_file = self.cache_dir / f"context-{context_hash}.json"
        with open(cache_file, "w") as f:
            f.write(serialized)

        # Store metadata
        metadata_file = self.cache_dir / f"meta-{context_hash}.json"
        metadata = {
            "context_id": context_id,
            "cached_at": datetime.now().isoformat(),
            "size_bytes": len(serialized),
            "hash": context_hash,
        }
        with open(metadata_file, "w") as f:
            json.dump(metadata, f, indent=2)

        print(f"💾 Cached context {context_id} as {context_hash}")
        return context_hash

    def retrieve_context(self, context_hash: str) -> Any:
        """Retrieve context from cache"""
        cache_file = self.cache_dir / f"context-{context_hash}.json"

        if not cache_file.exists():
            raise FileNotFoundError(f"Context cache not found: {context_hash}")

        with open(cache_file, "r") as f:
            serialized = f.read()

        return self.deserialize_context(serialized)

    def create_handoff(
        self, context: Any, from_agent: str, to_agent: str, handoff_type: str = "direct"
    ) -> Dict[str, Any]:
        """
        Create a context handoff between agent functions.

        Types:
        - direct: Pass context directly (for small contexts)
        - cached: Cache context and pass reference (for large contexts)
        - filtered: Pass only relevant subset of context
        """

        handoff_data = {
            "from_agent": from_agent,
            "to_agent": to_agent,
            "handoff_type": handoff_type,
            "timestamp": datetime.now().isoformat(),
            "context": None,
            "context_ref": None,
        }

        if handoff_type == "direct":
            # Pass context directly
            handoff_data["context"] = context
            print(f"📤 Direct handoff: {from_agent} → {to_agent}")

        elif handoff_type == "cached":
            # Cache context and pass reference
            context_id = f"{from_agent}-to-{to_agent}-{int(datetime.now().timestamp())}"
            context_hash = self.cache_context(context, context_id)
            handoff_data["context_ref"] = context_hash
            print(f"📤 Cached handoff: {from_agent} → {to_agent} (ref: {context_hash})")

        elif handoff_type == "filtered":
            # Pass filtered subset (agent-specific views)
            filtered_context = self._filter_context_for_agent(context, to_agent)
            handoff_data["context"] = filtered_context
            print(f"📤 Filtered handoff: {from_agent} → {to_agent}")

        # Log the transfer
        transfer = ContextTransfer(
            from_agent=from_agent,
            to_agent=to_agent,
            context_hash=handoff_data.get("context_ref", "direct"),
            timestamp=datetime.now(),
            metadata={"handoff_type": handoff_type},
        )
        self.transfer_log.append(transfer)

        return handoff_data

    def receive_handoff(self, handoff_data: Dict[str, Any]) -> Any:
        """
        Receive context from handoff.

        Handles different handoff types transparently.
        """
        handoff_type = handoff_data.get("handoff_type", "direct")

        if handoff_type == "direct":
            return handoff_data["context"]

        elif handoff_type == "cached":
            context_ref = handoff_data["context_ref"]
            return self.retrieve_context(context_ref)

        elif handoff_type == "filtered":
            return handoff_data["context"]

        else:
            raise ValueError(f"Unknown handoff type: {handoff_type}")

    def _filter_context_for_agent(
        self, context: Any, agent_name: str
    ) -> Dict[str, Any]:
        """
        Filter context to include only what's relevant for specific agent.

        This reduces context size and focuses agent attention.
        """
        # Convert context to dict if needed
        if hasattr(context, "__dict__"):
            full_context = asdict(context)
        else:
            full_context = context

        # Agent-specific filtering rules
        if agent_name.endswith("analyzer"):
            # Analysis agents need issue data and files, not PR details
            return {
                "issue_data": full_context.get("issue_data", {}),
                "files_to_process": full_context.get("files_to_process", []),
                "repo_path": full_context.get("repo_path"),
                "analysis_results": full_context.get("analysis_results", {}),
            }

        elif agent_name.endswith("generator"):
            # Code generation agents need analysis results and file context
            return {
                "issue_data": full_context.get("issue_data", {}),
                "analysis_results": full_context.get("analysis_results", {}),
                "files_to_process": full_context.get("files_to_process", []),
                "repo_path": full_context.get("repo_path"),
            }

        elif agent_name.endswith("validator"):
            # Validation agents need changes and repository context
            return {
                "changes_to_apply": full_context.get("changes_to_apply", []),
                "repo_path": full_context.get("repo_path"),
                "validation_results": full_context.get("validation_results", {}),
            }

        elif agent_name.endswith("pr_creator"):
            # PR creation agents need everything for comprehensive PR
            return full_context

        else:
            # Default: pass full context but log warning
            print(f"⚠️ No filtering rules for {agent_name}, passing full context")
            return full_context

    def chain_handoffs(
        self, context: Any, agent_chain: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Chain multiple handoffs for a sequence of agent functions.

        This is useful for complex workflows like: analyze → generate → validate → create_pr
        """
        handoffs = []
        current_context = context

        for i in range(len(agent_chain) - 1):
            from_agent = agent_chain[i]
            to_agent = agent_chain[i + 1]

            # Determine handoff type based on context size
            handoff_type = self._choose_handoff_type(current_context)

            handoff = self.create_handoff(
                current_context, from_agent, to_agent, handoff_type
            )
            handoffs.append(handoff)

            # For chaining, we may want to update context based on intermediate results
            # This would happen in the orchestrator between agent calls

        return handoffs

    def _choose_handoff_type(self, context: Any) -> str:
        """Choose optimal handoff type based on context characteristics"""
        # Estimate context size
        try:
            serialized = self.serialize_context(context)
            size_kb = len(serialized) / 1024

            if size_kb < 10:  # Small context
                return "direct"
            elif size_kb < 100:  # Medium context
                return "filtered"
            else:  # Large context
                return "cached"

        except Exception:
            # If we can't estimate, use cached for safety
            return "cached"

    def get_transfer_history(self) -> List[Dict[str, Any]]:
        """Get history of context transfers for debugging"""
        return [
            {
                "from_agent": t.from_agent,
                "to_agent": t.to_agent,
                "context_hash": t.context_hash,
                "timestamp": t.timestamp.isoformat(),
                "metadata": t.metadata,
            }
            for t in self.transfer_log
        ]

    def cleanup_cache(self, older_than_hours: int = 24):
        """Clean up old cached contexts"""
        cutoff = datetime.now().timestamp() - (older_than_hours * 3600)

        for cache_file in self.cache_dir.glob("context-*.json"):
            if cache_file.stat().st_mtime < cutoff:
                # Remove context and metadata
                cache_file.unlink()
                meta_file = (
                    self.cache_dir / f"meta-{cache_file.stem.split('-', 1)[1]}.json"
                )
                meta_file.unlink(missing_ok=True)
                print(f"🧹 Cleaned up old context cache: {cache_file.name}")


# Example usage
if __name__ == "__main__":
    # Demo context handoffs
    handoff_manager = ContextHandoffManager()

    # Example context
    example_context = {
        "issue_number": 123,
        "issue_data": {"title": "Fix bug", "body": "Something is broken"},
        "files_to_process": ["src/main.py", "tests/test_main.py"],
        "analysis_results": {"complexity": "medium", "risk": "low"},
    }

    # Create handoff from analyzer to generator
    handoff = handoff_manager.create_handoff(
        example_context,
        from_agent="issue_analyzer",
        to_agent="code_generator",
        handoff_type="filtered",
    )

    # Receive the handoff
    received_context = handoff_manager.receive_handoff(handoff)

    print("🧪 Context handoff system ready!")
    print("✅ Efficient context transfer between stateless agent functions")
    print("✅ Multiple transfer strategies based on context size")
    print("✅ Agent-specific context filtering")
    print("✅ Caching for large contexts")
