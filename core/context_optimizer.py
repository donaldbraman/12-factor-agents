"""
Context Optimizer implementing Claude Code's R&D Framework
Enhances Factor 3: Own Your Context Window with systematic optimization
"""

from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import json
import hashlib
from datetime import datetime
from .base import BaseAgent, ToolResponse


class ContextReductionStrategy(Enum):
    """Strategies for reducing context size"""
    REMOVE_REDUNDANT = "remove_redundant"
    SUMMARIZE_VERBOSE = "summarize_verbose"
    EXTRACT_RELEVANT = "extract_relevant"
    COMPRESS_HISTORY = "compress_history"
    DELEGATE_COMPLEX = "delegate_complex"


@dataclass
class ContextMetrics:
    """Metrics for context optimization"""
    original_tokens: int
    reduced_tokens: int
    reduction_percentage: float
    strategies_applied: List[str]
    delegation_recommended: bool
    estimated_cost_savings: float


@dataclass
class ReducedContext:
    """Optimized context with metrics"""
    content: Dict[str, Any]
    metrics: ContextMetrics
    delegated_tasks: List[Dict[str, Any]]
    session_id: str


class ContextOptimizer:
    """
    Implements R&D Framework: Reduce and Delegate
    Treats context window as a limited and expensive resource
    """
    
    def __init__(self, max_tokens: int = 8000, delegation_threshold: float = 0.3):
        """
        Initialize context optimizer with R&D Framework
        
        Args:
            max_tokens: Maximum context window size
            delegation_threshold: Delegate if context usage > threshold
        """
        self.max_tokens = max_tokens
        self.delegation_threshold = delegation_threshold
        self.reduction_strategies = [
            self.remove_redundant_context,
            self.summarize_verbose_sections,
            self.extract_relevant_only,
            self.compress_conversation_history
        ]
        self.metrics_history = []
        
    def optimize_context(self, context: Dict[str, Any], task: str) -> ReducedContext:
        """
        Apply R&D Framework to optimize context
        
        Args:
            context: Current context dictionary
            task: Task description for relevance filtering
            
        Returns:
            ReducedContext with optimized content and metrics
        """
        original_tokens = self.estimate_tokens(context)
        reduced_context = context.copy()
        strategies_applied = []
        delegated_tasks = []
        
        # REDUCE: Apply reduction strategies
        for strategy in self.reduction_strategies:
            if self.estimate_tokens(reduced_context) <= self.max_tokens:
                break
                
            reduced_context, strategy_name = strategy(reduced_context, task)
            strategies_applied.append(strategy_name)
            
        # DELEGATE: Check if delegation needed
        final_tokens = self.estimate_tokens(reduced_context)
        usage_ratio = final_tokens / self.max_tokens
        
        if usage_ratio > self.delegation_threshold:
            # Identify tasks to delegate
            delegated_tasks = self.identify_delegatable_tasks(reduced_context, task)
            # Remove delegated content from context
            reduced_context = self.remove_delegated_content(reduced_context, delegated_tasks)
            final_tokens = self.estimate_tokens(reduced_context)
        
        # Calculate metrics
        reduction_percentage = (original_tokens - final_tokens) / original_tokens * 100
        estimated_cost_savings = self.calculate_cost_savings(original_tokens, final_tokens)
        
        metrics = ContextMetrics(
            original_tokens=original_tokens,
            reduced_tokens=final_tokens,
            reduction_percentage=reduction_percentage,
            strategies_applied=strategies_applied,
            delegation_recommended=len(delegated_tasks) > 0,
            estimated_cost_savings=estimated_cost_savings
        )
        
        # Store metrics for analysis
        self.metrics_history.append({
            "timestamp": datetime.now().isoformat(),
            "metrics": metrics.__dict__
        })
        
        return ReducedContext(
            content=reduced_context,
            metrics=metrics,
            delegated_tasks=delegated_tasks,
            session_id=self.generate_session_id()
        )
    
    def remove_redundant_context(self, context: Dict[str, Any], task: str) -> Tuple[Dict, str]:
        """Remove duplicate or redundant information"""
        cleaned = {}
        seen_hashes = set()
        
        for key, value in context.items():
            # Create hash of content to detect duplicates
            content_hash = hashlib.md5(str(value).encode()).hexdigest()
            
            if content_hash not in seen_hashes:
                cleaned[key] = value
                seen_hashes.add(content_hash)
                
        return cleaned, ContextReductionStrategy.REMOVE_REDUNDANT.value
    
    def summarize_verbose_sections(self, context: Dict[str, Any], task: str) -> Tuple[Dict, str]:
        """Summarize verbose sections while preserving key information"""
        summarized = {}
        
        for key, value in context.items():
            if isinstance(value, str) and len(value) > 1000:
                # Long strings get summarized
                summarized[key] = self.create_summary(value)
            elif isinstance(value, list) and len(value) > 10:
                # Long lists get truncated with summary
                summarized[key] = {
                    "summary": f"List of {len(value)} items",
                    "sample": value[:3],
                    "full_data_available": True
                }
            else:
                summarized[key] = value
                
        return summarized, ContextReductionStrategy.SUMMARIZE_VERBOSE.value
    
    def extract_relevant_only(self, context: Dict[str, Any], task: str) -> Tuple[Dict, str]:
        """Extract only task-relevant context"""
        relevant = {}
        task_keywords = self.extract_keywords(task)
        
        for key, value in context.items():
            # Check relevance based on task keywords
            if self.is_relevant_to_task(key, value, task_keywords):
                relevant[key] = value
                
        return relevant, ContextReductionStrategy.EXTRACT_RELEVANT.value
    
    def compress_conversation_history(self, context: Dict[str, Any], task: str) -> Tuple[Dict, str]:
        """Compress conversation history while preserving important exchanges"""
        compressed = context.copy()
        
        if "conversation_history" in compressed:
            history = compressed["conversation_history"]
            if isinstance(history, list) and len(history) > 20:
                # Keep first 5, last 10, and important middle messages
                compressed["conversation_history"] = {
                    "initial": history[:5],
                    "recent": history[-10:],
                    "summary": f"Full history: {len(history)} messages",
                    "important_points": self.extract_important_messages(history[5:-10])
                }
                
        return compressed, ContextReductionStrategy.COMPRESS_HISTORY.value
    
    def identify_delegatable_tasks(self, context: Dict[str, Any], task: str) -> List[Dict]:
        """Identify tasks that should be delegated to specialized agents"""
        delegatable = []
        
        # Analyze task complexity
        if "subtasks" in context:
            for subtask in context["subtasks"]:
                if self.is_complex_subtask(subtask):
                    delegatable.append({
                        "task": subtask,
                        "recommended_agent": self.recommend_agent_type(subtask),
                        "context_subset": self.extract_subtask_context(context, subtask)
                    })
                    
        # Check for specialized domains
        if self.requires_specialized_knowledge(task):
            delegatable.append({
                "task": "specialized_analysis",
                "recommended_agent": "DomainExpertAgent",
                "context_subset": self.extract_domain_context(context)
            })
            
        return delegatable
    
    def remove_delegated_content(self, context: Dict[str, Any], delegated: List[Dict]) -> Dict:
        """Remove content that will be handled by delegated agents"""
        cleaned = context.copy()
        
        for delegation in delegated:
            # Remove delegated subtasks
            if "subtasks" in cleaned and delegation["task"] in cleaned["subtasks"]:
                cleaned["subtasks"].remove(delegation["task"])
                
            # Remove specialized context
            for key in delegation["context_subset"].keys():
                if key in cleaned and key != "core_requirements":
                    del cleaned[key]
                    
        return cleaned
    
    def estimate_tokens(self, context: Any) -> int:
        """Estimate token count for context"""
        # Simplified estimation: ~4 characters per token
        context_str = json.dumps(context) if isinstance(context, dict) else str(context)
        return len(context_str) // 4
    
    def calculate_cost_savings(self, original: int, reduced: int) -> float:
        """Calculate estimated cost savings from context reduction"""
        # Assuming $0.01 per 1K tokens (adjust based on actual pricing)
        cost_per_1k = 0.01
        original_cost = (original / 1000) * cost_per_1k
        reduced_cost = (reduced / 1000) * cost_per_1k
        return original_cost - reduced_cost
    
    def create_summary(self, text: str, max_length: int = 500) -> str:
        """Create summary of verbose text"""
        if len(text) <= max_length:
            return text
        # Simple truncation with ellipsis (could be enhanced with NLP)
        return text[:max_length-3] + "..."
    
    def extract_keywords(self, task: str) -> List[str]:
        """Extract keywords from task description"""
        # Simple word extraction (could be enhanced with NLP)
        words = task.lower().split()
        # Filter common words
        stopwords = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for"}
        return [w for w in words if w not in stopwords and len(w) > 3]
    
    def is_relevant_to_task(self, key: str, value: Any, keywords: List[str]) -> bool:
        """Check if context item is relevant to task"""
        # Check key relevance
        key_lower = key.lower()
        if any(kw in key_lower for kw in keywords):
            return True
            
        # Check value relevance for strings
        if isinstance(value, str):
            value_lower = value.lower()
            if any(kw in value_lower for kw in keywords):
                return True
                
        # Core items always relevant
        if key in ["requirements", "constraints", "objectives", "current_state"]:
            return True
            
        return False
    
    def extract_important_messages(self, messages: List) -> List:
        """Extract important messages from conversation history"""
        important = []
        keywords = ["error", "important", "critical", "decision", "requirement", "must"]
        
        for msg in messages:
            msg_str = str(msg).lower()
            if any(kw in msg_str for kw in keywords):
                important.append(msg)
                
        return important[:5]  # Keep top 5 important messages
    
    def is_complex_subtask(self, subtask: Any) -> bool:
        """Check if subtask is complex enough to delegate"""
        subtask_str = str(subtask)
        # Complex if: long description, multiple steps, specialized domain
        return (len(subtask_str) > 200 or 
                "step" in subtask_str.lower() or
                any(domain in subtask_str.lower() for domain in ["legal", "medical", "financial"]))
    
    def recommend_agent_type(self, subtask: Any) -> str:
        """Recommend appropriate agent type for subtask"""
        subtask_str = str(subtask).lower()
        
        if "implement" in subtask_str or "create" in subtask_str:
            return "ImplementationAgent"
        elif "test" in subtask_str or "validate" in subtask_str:
            return "TestingAgent"
        elif "analyze" in subtask_str or "research" in subtask_str:
            return "ResearchAgent"
        elif "document" in subtask_str:
            return "DocumentationAgent"
        else:
            return "GeneralPurposeAgent"
    
    def extract_subtask_context(self, context: Dict, subtask: Any) -> Dict:
        """Extract relevant context for subtask"""
        return {
            "subtask": subtask,
            "requirements": context.get("requirements", {}),
            "constraints": context.get("constraints", {}),
            "related_data": self.find_related_data(context, subtask)
        }
    
    def requires_specialized_knowledge(self, task: str) -> bool:
        """Check if task requires specialized domain knowledge"""
        specialized_domains = ["legal", "medical", "financial", "scientific", "regulatory"]
        task_lower = task.lower()
        return any(domain in task_lower for domain in specialized_domains)
    
    def extract_domain_context(self, context: Dict) -> Dict:
        """Extract domain-specific context"""
        domain_keys = ["domain_requirements", "regulations", "standards", "precedents"]
        return {k: v for k, v in context.items() if any(dk in k.lower() for dk in domain_keys)}
    
    def find_related_data(self, context: Dict, subtask: Any) -> Dict:
        """Find data related to specific subtask"""
        related = {}
        subtask_keywords = self.extract_keywords(str(subtask))
        
        for key, value in context.items():
            if self.is_relevant_to_task(key, value, subtask_keywords):
                related[key] = value
                
        return related
    
    def generate_session_id(self) -> str:
        """Generate unique session ID"""
        timestamp = datetime.now().isoformat()
        return hashlib.md5(timestamp.encode()).hexdigest()[:12]
    
    def get_optimization_report(self) -> Dict:
        """Generate optimization metrics report"""
        if not self.metrics_history:
            return {"message": "No optimization metrics available"}
            
        total_original = sum(m["metrics"]["original_tokens"] for m in self.metrics_history)
        total_reduced = sum(m["metrics"]["reduced_tokens"] for m in self.metrics_history)
        total_savings = sum(m["metrics"]["estimated_cost_savings"] for m in self.metrics_history)
        
        return {
            "total_optimizations": len(self.metrics_history),
            "total_tokens_saved": total_original - total_reduced,
            "average_reduction_percentage": sum(m["metrics"]["reduction_percentage"] 
                                               for m in self.metrics_history) / len(self.metrics_history),
            "total_cost_savings": total_savings,
            "most_used_strategies": self.get_most_used_strategies(),
            "delegation_rate": sum(1 for m in self.metrics_history 
                                 if m["metrics"]["delegation_recommended"]) / len(self.metrics_history)
        }
    
    def get_most_used_strategies(self) -> List[str]:
        """Get most frequently used reduction strategies"""
        strategy_counts = {}
        for metric in self.metrics_history:
            for strategy in metric["metrics"]["strategies_applied"]:
                strategy_counts[strategy] = strategy_counts.get(strategy, 0) + 1
                
        return sorted(strategy_counts.keys(), key=lambda x: strategy_counts[x], reverse=True)[:3]


class ContextOptimizedAgent(BaseAgent):
    """
    Agent enhanced with R&D Framework for context optimization
    Automatically optimizes context and delegates when necessary
    """
    
    def __init__(self, agent_id: str = None, max_context_tokens: int = 8000):
        """Initialize context-optimized agent"""
        super().__init__(agent_id)
        self.context_optimizer = ContextOptimizer(
            max_tokens=max_context_tokens,
            delegation_threshold=0.3
        )
        self.delegated_agents = []
        
    async def execute_task(self, task: str) -> ToolResponse:
        """Execute task with R&D Framework optimization"""
        # Get current context
        current_context = await self.get_current_context()
        
        # Apply R&D Framework
        optimized = self.context_optimizer.optimize_context(current_context, task)
        
        # Log optimization metrics
        self.log_info(f"Context optimized: {optimized.metrics.reduction_percentage:.1f}% reduction")
        self.log_info(f"Tokens: {optimized.metrics.original_tokens} → {optimized.metrics.reduced_tokens}")
        
        # Handle delegated tasks if any
        if optimized.delegated_tasks:
            delegation_results = await self.handle_delegations(optimized.delegated_tasks)
            # Merge delegation results into context
            optimized.content["delegation_results"] = delegation_results
            
        # Execute with optimized context
        self.set_context(optimized.content)
        result = await self.process_with_optimized_context(task, optimized)
        
        # Return comprehensive response
        return ToolResponse(
            success=True,
            data={
                "result": result,
                "optimization_metrics": optimized.metrics.__dict__,
                "delegations": len(optimized.delegated_tasks),
                "session_id": optimized.session_id
            },
            metadata={
                "context_optimization": self.context_optimizer.get_optimization_report()
            }
        )
    
    async def handle_delegations(self, delegated_tasks: List[Dict]) -> List[Dict]:
        """Handle task delegations to specialized agents"""
        results = []
        
        for delegation in delegated_tasks:
            # Spawn specialized agent
            agent = await self.spawn_specialized_agent(
                agent_type=delegation["recommended_agent"],
                context=delegation["context_subset"]
            )
            
            # Execute delegated task
            result = await agent.execute_task(delegation["task"])
            results.append({
                "task": delegation["task"],
                "agent": delegation["recommended_agent"],
                "result": result
            })
            
            self.delegated_agents.append(agent)
            
        return results
    
    async def spawn_specialized_agent(self, agent_type: str, context: Dict) -> BaseAgent:
        """Spawn specialized agent for delegation"""
        # This would create appropriate agent type
        # For now, return a base agent
        agent = BaseAgent(agent_id=f"{self.agent_id}_delegate_{len(self.delegated_agents)}")
        agent.set_context(context)
        return agent
    
    async def process_with_optimized_context(self, task: str, optimized: ReducedContext) -> Any:
        """Process task with optimized context"""
        # Implement actual task processing
        return f"Processed task with {optimized.metrics.reduced_tokens} tokens"
    
    async def get_current_context(self) -> Dict:
        """Get current agent context"""
        # Would retrieve actual context
        return self.workflow_data