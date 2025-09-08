"""
Context window management for agents.
Factor 3: Own your context window.
"""
from typing import List, Tuple, Optional, Dict
from dataclasses import dataclass
import json


@dataclass
class ContextItem:
    """Single item in context with priority"""
    content: str
    priority: int  # 1-10, higher = more important
    tokens: int
    source: str = "user"
    
    def __lt__(self, other):
        # Higher priority items sort first
        return self.priority > other.priority


class ContextManager:
    """
    Manages context window for LLM interactions.
    
    Features:
    - Priority-based content management
    - Token counting and limiting
    - Smart truncation
    - Context compression
    """
    
    def __init__(self, max_tokens: int = 100000):
        self.max_tokens = max_tokens
        self.items: List[ContextItem] = []
        self.system_prompt: Optional[str] = None
        self.reserved_tokens = 10000  # Reserve for response
    
    def set_system_prompt(self, prompt: str):
        """Set system prompt (highest priority)"""
        self.system_prompt = prompt
    
    def add_context(self, content: str, priority: int = 5, source: str = "user"):
        """
        Add content to context with priority.
        Priority: 1-10 (10 = highest)
        """
        if not 1 <= priority <= 10:
            raise ValueError("Priority must be between 1 and 10")
        
        tokens = self._estimate_tokens(content)
        item = ContextItem(
            content=content,
            priority=priority,
            tokens=tokens,
            source=source
        )
        self.items.append(item)
        
        # Maintain sorted order
        self.items.sort()
    
    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count (rough approximation)"""
        # Rough estimate: 1 token per 4 characters
        return len(text) // 4
    
    def build_prompt(self) -> str:
        """
        Build final prompt within token limits.
        Prioritizes high-priority content.
        """
        prompt_parts = []
        used_tokens = 0
        
        # Add system prompt first (if set)
        if self.system_prompt:
            system_tokens = self._estimate_tokens(self.system_prompt)
            prompt_parts.append(self.system_prompt)
            used_tokens += system_tokens
        
        # Add context items by priority
        available_tokens = self.max_tokens - self.reserved_tokens - used_tokens
        
        for item in self.items:
            if used_tokens + item.tokens <= available_tokens:
                prompt_parts.append(f"[{item.source}]: {item.content}")
                used_tokens += item.tokens
            else:
                # Try to fit truncated version
                remaining = available_tokens - used_tokens
                if remaining > 100:  # Only truncate if meaningful amount remains
                    truncated = self._truncate_content(item.content, remaining)
                    prompt_parts.append(f"[{item.source}][truncated]: {truncated}")
                    break
        
        return "\n\n".join(prompt_parts)
    
    def _truncate_content(self, content: str, max_tokens: int) -> str:
        """Intelligently truncate content to fit token limit"""
        # Estimate characters from tokens
        max_chars = max_tokens * 4
        
        if len(content) <= max_chars:
            return content
        
        # Try to truncate at sentence boundary
        truncated = content[:max_chars]
        last_period = truncated.rfind('.')
        last_newline = truncated.rfind('\n')
        
        # Truncate at last complete sentence/line
        boundary = max(last_period, last_newline)
        if boundary > max_chars * 0.7:  # Only if we keep most content
            truncated = truncated[:boundary + 1]
        
        return truncated + "..."
    
    def clear(self):
        """Clear all context items"""
        self.items = []
    
    def remove_old_context(self, keep_recent: int = 10):
        """Remove old low-priority context, keeping recent high-priority items"""
        # Keep all high priority items (8+)
        high_priority = [i for i in self.items if i.priority >= 8]
        
        # Keep recent medium priority items
        medium_priority = [i for i in self.items if 4 <= i.priority < 8][-keep_recent:]
        
        # Keep very recent low priority items  
        low_priority = [i for i in self.items if i.priority < 4][-5:]
        
        self.items = high_priority + medium_priority + low_priority
        self.items.sort()
    
    def get_token_usage(self) -> Dict[str, int]:
        """Get current token usage statistics"""
        total = sum(item.tokens for item in self.items)
        system = self._estimate_tokens(self.system_prompt) if self.system_prompt else 0
        
        return {
            "total": total + system,
            "system": system,
            "context": total,
            "available": self.max_tokens - total - system - self.reserved_tokens,
            "max": self.max_tokens
        }
    
    def compact_errors(self, errors: List[str]) -> str:
        """
        Factor 9: Compact errors into context window.
        Convert verbose errors into concise messages.
        """
        if not errors:
            return ""
        
        compacted = []
        for error in errors[-5:]:  # Keep only recent errors
            # Extract key information
            lines = error.split('\n')
            
            # Find actual error message
            error_line = None
            for line in lines:
                if 'Error' in line or 'Exception' in line:
                    error_line = line.strip()
                    break
            
            if error_line:
                compacted.append(error_line)
            else:
                # Use first non-empty line
                compacted.append(next((l.strip() for l in lines if l.strip()), "Unknown error"))
        
        return "Recent errors:\n" + "\n".join(f"- {e}" for e in compacted)


# Alias for backwards compatibility
class AgentContext(ContextManager):
    """Alias for ContextManager for backwards compatibility"""
    
    def add(self, key: str, value: str):
        """Add context item with default priority"""
        self.add_context(value, priority=5, source=key)
    
    def __str__(self):
        """String representation of context"""
        return self.build_prompt()