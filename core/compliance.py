"""
12-Factor Agent Compliance Validation Framework
Ensures that pin-citer inspired patterns maintain strict 12-factor compliance.

This module validates implementations against:
https://github.com/humanlayer/12-factor-agents
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Tuple
from enum import Enum
import inspect
from pathlib import Path

from .agent import BaseAgent
from .tools import Tool


class ComplianceLevel(Enum):
    """Compliance levels for 12-factor validation"""

    FULLY_COMPLIANT = "fully_compliant"  # 100% compliant
    MOSTLY_COMPLIANT = "mostly_compliant"  # 80-99% compliant
    PARTIALLY_COMPLIANT = "partially_compliant"  # 50-79% compliant
    NON_COMPLIANT = "non_compliant"  # <50% compliant


class FactorValidator(ABC):
    """Abstract base for validating individual 12-factor principles"""

    def __init__(self, factor_number: int, factor_name: str):
        self.factor_number = factor_number
        self.factor_name = factor_name

    @abstractmethod
    def validate(
        self, agent: BaseAgent, context: Dict[str, Any] = None
    ) -> Tuple[ComplianceLevel, Dict[str, Any]]:
        """
        Validate agent compliance with this factor.

        Returns:
            Tuple of (compliance_level, validation_details)
        """
        pass


class Factor1Validator(FactorValidator):
    """Factor 1: Natural Language to Tool Calls"""

    def __init__(self):
        super().__init__(1, "Natural Language to Tool Calls")

    def validate(
        self, agent: BaseAgent, context: Dict[str, Any] = None
    ) -> Tuple[ComplianceLevel, Dict[str, Any]]:
        """Validate that agent properly converts natural language to tool calls"""
        details = {
            "factor": self.factor_name,
            "checks": {},
            "score": 0.0,
            "issues": [],
            "recommendations": [],
        }

        # Check if execute_task method is implemented
        if hasattr(agent, "execute_task") and callable(agent.execute_task):
            details["checks"]["has_execute_task"] = True
            details["score"] += 0.3
        else:
            details["checks"]["has_execute_task"] = False
            details["issues"].append("Missing execute_task method")

        # Check if agent has registered tools
        if agent.tools and len(agent.tools) > 0:
            details["checks"]["has_tools"] = True
            details["score"] += 0.3
            details["tool_count"] = len(agent.tools)
        else:
            details["checks"]["has_tools"] = False
            details["issues"].append("No tools registered")

        # Check if tools have proper structure
        if agent.tools:
            structured_tools = all(isinstance(tool, Tool) for tool in agent.tools)
            details["checks"]["structured_tools"] = structured_tools
            if structured_tools:
                details["score"] += 0.4
            else:
                details["issues"].append("Tools are not properly structured")

        # Determine compliance level
        if details["score"] >= 0.9:
            compliance = ComplianceLevel.FULLY_COMPLIANT
        elif details["score"] >= 0.8:
            compliance = ComplianceLevel.MOSTLY_COMPLIANT
        elif details["score"] >= 0.5:
            compliance = ComplianceLevel.PARTIALLY_COMPLIANT
        else:
            compliance = ComplianceLevel.NON_COMPLIANT

        return compliance, details


class Factor2Validator(FactorValidator):
    """Factor 2: Own Your Prompts"""

    def __init__(self):
        super().__init__(2, "Own Your Prompts")

    def validate(
        self, agent: BaseAgent, context: Dict[str, Any] = None
    ) -> Tuple[ComplianceLevel, Dict[str, Any]]:
        """Validate proper prompt management"""
        details = {
            "factor": self.factor_name,
            "checks": {},
            "score": 0.0,
            "issues": [],
            "recommendations": [],
        }

        # Check if agent has prompt manager
        if hasattr(agent, "prompt_manager") and agent.prompt_manager:
            details["checks"]["has_prompt_manager"] = True
            details["score"] += 0.4
        else:
            details["checks"]["has_prompt_manager"] = False
            details["issues"].append("Missing prompt manager")

        # Check if prompts are externalized
        prompt_dir = Path("prompts")
        if prompt_dir.exists():
            details["checks"]["external_prompts"] = True
            details["score"] += 0.3
            details["prompt_files"] = len(list(prompt_dir.glob("**/*.prompt")))
        else:
            details["checks"]["external_prompts"] = False
            details["recommendations"].append(
                "Create external prompt files in prompts/ directory"
            )

        # Check for hardcoded prompts in code (basic check)
        agent_code = inspect.getsource(agent.__class__)
        hardcoded_prompts = "prompt" in agent_code.lower() and '"' in agent_code
        details["checks"]["no_hardcoded_prompts"] = not hardcoded_prompts
        if not hardcoded_prompts:
            details["score"] += 0.3
        else:
            details["issues"].append("Possible hardcoded prompts detected")

        # Determine compliance level
        if details["score"] >= 0.9:
            compliance = ComplianceLevel.FULLY_COMPLIANT
        elif details["score"] >= 0.8:
            compliance = ComplianceLevel.MOSTLY_COMPLIANT
        elif details["score"] >= 0.5:
            compliance = ComplianceLevel.PARTIALLY_COMPLIANT
        else:
            compliance = ComplianceLevel.NON_COMPLIANT

        return compliance, details


class Factor6Validator(FactorValidator):
    """Factor 6: Launch/Pause/Resume APIs"""

    def __init__(self):
        super().__init__(6, "Launch/Pause/Resume APIs")

    def validate(
        self, agent: BaseAgent, context: Dict[str, Any] = None
    ) -> Tuple[ComplianceLevel, Dict[str, Any]]:
        """Validate pause/resume capability - enhanced by pin-citer patterns"""
        details = {
            "factor": self.factor_name,
            "checks": {},
            "score": 0.0,
            "issues": [],
            "recommendations": [],
            "pin_citer_enhancements": {},
        }

        # Check basic launch/pause/resume methods
        required_methods = ["launch", "pause", "resume"]
        for method in required_methods:
            if hasattr(agent, method) and callable(getattr(agent, method)):
                details["checks"][f"has_{method}"] = True
                details["score"] += 0.2
            else:
                details["checks"][f"has_{method}"] = False
                details["issues"].append(f"Missing {method} method")

        # Check checkpoint functionality (enhanced by pin-citer)
        if hasattr(agent, "save_checkpoint") and hasattr(agent, "load_checkpoint"):
            details["checks"]["has_checkpointing"] = True
            details["score"] += 0.2

            # Check for pin-citer enhanced checkpoint features
            if hasattr(agent, "progress") and hasattr(agent, "current_stage"):
                details["pin_citer_enhancements"]["progress_tracking"] = True
                details["score"] += 0.1

            if hasattr(agent, "error_context") and hasattr(agent, "workflow_data"):
                details["pin_citer_enhancements"]["error_context"] = True
                details["score"] += 0.1
        else:
            details["checks"]["has_checkpointing"] = False
            details["issues"].append("Missing checkpoint functionality")

        # Determine compliance level
        if details["score"] >= 0.9:
            compliance = ComplianceLevel.FULLY_COMPLIANT
        elif details["score"] >= 0.8:
            compliance = ComplianceLevel.MOSTLY_COMPLIANT
        elif details["score"] >= 0.5:
            compliance = ComplianceLevel.PARTIALLY_COMPLIANT
        else:
            compliance = ComplianceLevel.NON_COMPLIANT

        return compliance, details


class Factor10Validator(FactorValidator):
    """Factor 10: Small, Focused Agents"""

    def __init__(self):
        super().__init__(10, "Small, Focused Agents")

    def validate(
        self, agent: BaseAgent, context: Dict[str, Any] = None
    ) -> Tuple[ComplianceLevel, Dict[str, Any]]:
        """Validate single responsibility principle - supported by pin-citer pipeline pattern"""
        details = {
            "factor": self.factor_name,
            "checks": {},
            "score": 0.0,
            "issues": [],
            "recommendations": [],
            "pin_citer_enhancements": {},
        }

        # Analyze agent complexity
        agent_methods = [
            method
            for method in dir(agent)
            if not method.startswith("_") and callable(getattr(agent, method))
        ]

        details["checks"]["method_count"] = len(agent_methods)

        # Score based on method count (fewer methods = more focused)
        if len(agent_methods) <= 10:
            details["score"] += 0.3
            details["checks"]["focused_interface"] = True
        else:
            details["checks"]["focused_interface"] = False
            details["issues"].append(
                f"Agent has {len(agent_methods)} public methods - consider decomposition"
            )

        # Check if agent has single execute_task method (single responsibility)
        if hasattr(agent, "execute_task"):
            details["checks"]["single_responsibility"] = True
            details["score"] += 0.3

        # Check for pin-citer inspired pipeline composition
        if hasattr(agent, "pipeline") or hasattr(agent, "stages"):
            details["pin_citer_enhancements"]["pipeline_composition"] = True
            details["score"] += 0.2
            details["recommendations"].append(
                "Good use of pipeline pattern for decomposition"
            )

        # Check tool count (focused agents should have focused tools)
        if agent.tools:
            tool_count = len(agent.tools)
            details["checks"]["tool_count"] = tool_count
            if tool_count <= 5:
                details["score"] += 0.2
            elif tool_count > 10:
                details["issues"].append(
                    f"Agent has {tool_count} tools - consider decomposition"
                )

        # Determine compliance level
        if details["score"] >= 0.9:
            compliance = ComplianceLevel.FULLY_COMPLIANT
        elif details["score"] >= 0.8:
            compliance = ComplianceLevel.MOSTLY_COMPLIANT
        elif details["score"] >= 0.5:
            compliance = ComplianceLevel.PARTIALLY_COMPLIANT
        else:
            compliance = ComplianceLevel.NON_COMPLIANT

        return compliance, details


class Factor4Validator(FactorValidator):
    """Factor 4: Tools are Structured Outputs"""

    def __init__(self):
        super().__init__(4, "Tools are Structured Outputs")

    def validate(
        self, agent: BaseAgent, context: Dict[str, Any] = None
    ) -> Tuple[ComplianceLevel, Dict[str, Any]]:
        """
        Validate that all tools have structured, predictable outputs.
        """
        details = {
            "factor": self.factor_name,
            "checks": {},
            "score": 0.0,
            "issues": [],
            "recommendations": [],
        }

        # Check 1: All tools return ToolResponse (0.25 points)
        tools_return_toolresponse = True
        toolresponse_issues = []

        if agent.tools:
            for tool in agent.tools:
                # Check if tool inherits from Tool base class
                if not isinstance(tool, Tool):
                    tools_return_toolresponse = False
                    toolresponse_issues.append(
                        f"Tool '{tool.__class__.__name__}' does not inherit from Tool base class"
                    )
                    continue

                # Check if execute method exists and returns ToolResponse
                if hasattr(tool, "execute"):
                    try:
                        source = inspect.getsource(tool.execute)
                        if "ToolResponse" not in source:
                            tools_return_toolresponse = False
                            toolresponse_issues.append(
                                f"Tool '{tool.name}' execute method may not return ToolResponse"
                            )
                    except Exception:
                        # Can't analyze source, assume it's okay if it inherits from Tool
                        pass
        else:
            # No tools is not necessarily bad, but we can't validate ToolResponse usage
            pass

        details["checks"]["tools_return_toolresponse"] = tools_return_toolresponse
        if tools_return_toolresponse:
            details["score"] += 0.25
        else:
            details["issues"].extend(toolresponse_issues)

        # Check 2: Schema compliance (0.25 points)
        schema_compliance = True
        schema_issues = []

        if agent.tools:
            for tool in agent.tools:
                # Check if tool has get_parameters_schema method
                if not hasattr(tool, "get_parameters_schema"):
                    schema_compliance = False
                    schema_issues.append(
                        f"Tool '{tool.__class__.__name__}' missing get_parameters_schema method"
                    )
                    continue

                # Check if schema is properly defined
                try:
                    schema = tool.get_parameters_schema()
                    if not isinstance(schema, dict) or not schema:
                        schema_compliance = False
                        schema_issues.append(
                            f"Tool '{tool.__class__.__name__}' has invalid schema"
                        )
                except Exception as e:
                    schema_compliance = False
                    schema_issues.append(
                        f"Tool '{tool.__class__.__name__}' schema error: {str(e)}"
                    )

        details["checks"]["schema_compliance"] = schema_compliance
        if schema_compliance:
            details["score"] += 0.25
        else:
            details["issues"].extend(schema_issues)

        # Check 3: Error handling patterns (0.25 points)
        error_handling = True
        error_issues = []

        if agent.tools:
            for tool in agent.tools:
                if hasattr(tool, "execute"):
                    try:
                        source = inspect.getsource(tool.execute)
                        # Check for try/except blocks and ToolResponse error handling
                        if "try:" not in source or "except" not in source:
                            error_handling = False
                            error_issues.append(
                                f"Tool '{tool.__class__.__name__}' missing error handling"
                            )
                        elif "ToolResponse" in source and "success=False" not in source:
                            error_handling = False
                            error_issues.append(
                                f"Tool '{tool.__class__.__name__}' doesn't use ToolResponse error pattern"
                            )
                    except Exception:
                        # Can't analyze source
                        pass

        details["checks"]["error_handling"] = error_handling
        if error_handling:
            details["score"] += 0.25
        else:
            details["issues"].extend(error_issues)

        # Check 4: Output documentation (0.25 points)
        output_documentation = True
        doc_issues = []

        if agent.tools:
            for tool in agent.tools:
                # Check if tool has description
                if not hasattr(tool, "description") or not tool.description:
                    output_documentation = False
                    doc_issues.append(
                        f"Tool '{tool.__class__.__name__}' missing description"
                    )

                # Check if execute method has docstring
                if hasattr(tool, "execute"):
                    if not tool.execute.__doc__:
                        output_documentation = False
                        doc_issues.append(
                            f"Tool '{tool.__class__.__name__}' execute method missing docstring"
                        )

        details["checks"]["output_documentation"] = output_documentation
        if output_documentation:
            details["score"] += 0.25
        else:
            details["issues"].extend(doc_issues)

        # Provide recommendations based on failures
        if details["score"] < 1.0:
            if not tools_return_toolresponse:
                details["recommendations"].append(
                    "Ensure all tools inherit from Tool base class and return ToolResponse objects"
                )
            if not schema_compliance:
                details["recommendations"].append(
                    "Implement get_parameters_schema() method for all tools with proper JSON schema"
                )
            if not error_handling:
                details["recommendations"].append(
                    "Add try/catch blocks and return ToolResponse(success=False, error=...) for errors"
                )
            if not output_documentation:
                details["recommendations"].append(
                    "Add descriptions and docstrings documenting tool output formats"
                )

        # Determine compliance level
        if details["score"] >= 0.9:
            compliance = ComplianceLevel.FULLY_COMPLIANT
        elif details["score"] >= 0.75:
            compliance = ComplianceLevel.MOSTLY_COMPLIANT
        elif details["score"] >= 0.5:
            compliance = ComplianceLevel.PARTIALLY_COMPLIANT
        else:
            compliance = ComplianceLevel.NON_COMPLIANT

        return compliance, details


class Factor3Validator(FactorValidator):
    """Factor 3: Own Your Context Window"""

    def __init__(self):
        super().__init__(3, "Own Your Context Window")

    def validate(
        self, agent: BaseAgent, context: Dict[str, Any] = None
    ) -> Tuple[ComplianceLevel, Dict[str, Any]]:
        """
        Validate that agent properly manages its context window.
        """
        details = {
            "factor": self.factor_name,
            "checks": {},
            "score": 0.0,
            "issues": [],
            "recommendations": [],
        }

        # Check 1: Context Manager presence (0.25 points)
        has_context_manager = False
        context_issues = []

        if hasattr(agent, "context_manager") and agent.context_manager:
            has_context_manager = True
            # Check if it's a proper ContextManager instance
            if hasattr(agent.context_manager, "add_context") and hasattr(
                agent.context_manager, "build_prompt"
            ):
                pass  # Good
            else:
                has_context_manager = False
                context_issues.append(
                    "context_manager is not a proper ContextManager instance"
                )
        else:
            context_issues.append("Missing context_manager attribute")

        details["checks"]["has_context_manager"] = has_context_manager
        if has_context_manager:
            details["score"] += 0.25
        else:
            details["issues"].extend(context_issues)

        # Check 2: Context size management (0.25 points)
        context_size_management = False
        size_issues = []

        if has_context_manager and agent.context_manager:
            # Check for token limits
            if hasattr(agent.context_manager, "max_tokens"):
                max_tokens = getattr(agent.context_manager, "max_tokens", 0)
                if max_tokens > 0 and max_tokens <= 200000:  # Reasonable limit
                    context_size_management = True
                else:
                    size_issues.append(f"Unreasonable max_tokens limit: {max_tokens}")
            else:
                size_issues.append("Context manager missing max_tokens limit")

            # Check for token usage tracking
            if hasattr(agent.context_manager, "get_token_usage"):
                try:
                    usage = agent.context_manager.get_token_usage()
                    if isinstance(usage, dict) and "total" in usage:
                        # Good token tracking
                        pass
                    else:
                        size_issues.append("get_token_usage() returns invalid format")
                except Exception:
                    size_issues.append("get_token_usage() method error")
            else:
                size_issues.append("Missing get_token_usage() method")
        else:
            size_issues.append("Cannot check size management without context manager")

        details["checks"]["context_size_management"] = context_size_management
        if context_size_management:
            details["score"] += 0.25
        else:
            details["issues"].extend(size_issues)

        # Check 3: Context structure and organization (0.25 points)
        context_structure = False
        structure_issues = []

        if has_context_manager and agent.context_manager:
            # Check for priority-based context management
            if hasattr(agent.context_manager, "add_context"):
                # Check method signature for priority parameter
                try:
                    import inspect

                    sig = inspect.signature(agent.context_manager.add_context)
                    if "priority" in sig.parameters:
                        context_structure = True
                    else:
                        structure_issues.append(
                            "add_context method missing priority parameter"
                        )
                except Exception:
                    structure_issues.append(
                        "Could not analyze add_context method signature"
                    )

            # Check for ExecutionContext support
            if hasattr(agent, "context"):
                # Check if it can handle ExecutionContext
                context_structure = True
            else:
                structure_issues.append("Missing ExecutionContext support")
        else:
            structure_issues.append("Cannot check structure without context manager")

        details["checks"]["context_structure"] = context_structure
        if context_structure:
            details["score"] += 0.25
        else:
            details["issues"].extend(structure_issues)

        # Check 4: Context optimization (0.25 points)
        context_optimization = False
        optimization_issues = []

        if has_context_manager and agent.context_manager:
            # Check for context pruning/cleanup methods
            optimization_methods = ["clear", "remove_old_context", "compact_errors"]
            found_methods = []

            for method in optimization_methods:
                if hasattr(agent.context_manager, method):
                    found_methods.append(method)

            if len(found_methods) >= 2:  # At least 2 optimization methods
                context_optimization = True
            else:
                optimization_issues.append(
                    f"Missing context optimization methods. Found: {found_methods}"
                )

            # Check for intelligent truncation
            if hasattr(agent.context_manager, "_truncate_content") or hasattr(
                agent.context_manager, "build_prompt"
            ):
                # Assume build_prompt handles truncation intelligently
                pass
            else:
                optimization_issues.append("Missing intelligent content truncation")
        else:
            optimization_issues.append(
                "Cannot check optimization without context manager"
            )

        details["checks"]["context_optimization"] = context_optimization
        if context_optimization:
            details["score"] += 0.25
        else:
            details["issues"].extend(optimization_issues)

        # Provide recommendations based on failures
        if details["score"] < 1.0:
            if not has_context_manager:
                details["recommendations"].append(
                    "Implement ContextManager class and assign to agent.context_manager"
                )
            if not context_size_management:
                details["recommendations"].append(
                    "Add max_tokens limit and get_token_usage() method to context manager"
                )
            if not context_structure:
                details["recommendations"].append(
                    "Add priority parameter to add_context() and ExecutionContext support"
                )
            if not context_optimization:
                details["recommendations"].append(
                    "Implement context cleanup methods: clear(), remove_old_context(), compact_errors()"
                )

        # Determine compliance level
        if details["score"] >= 0.9:
            compliance = ComplianceLevel.FULLY_COMPLIANT
        elif details["score"] >= 0.75:
            compliance = ComplianceLevel.MOSTLY_COMPLIANT
        elif details["score"] >= 0.5:
            compliance = ComplianceLevel.PARTIALLY_COMPLIANT
        else:
            compliance = ComplianceLevel.NON_COMPLIANT

        return compliance, details


class Factor5Validator(FactorValidator):
    """Factor 5: Unify Execution and Business State"""

    def __init__(self):
        super().__init__(5, "Unify Execution and Business State")

    def validate(
        self, agent: BaseAgent, context: Dict[str, Any] = None
    ) -> Tuple[ComplianceLevel, Dict[str, Any]]:
        """
        Validate that agent unifies execution and business state.
        """
        details = {
            "factor": self.factor_name,
            "checks": {},
            "score": 0.0,
            "issues": [],
            "recommendations": [],
        }

        # Check 1: Unified state presence (0.25 points)
        has_unified_state = False
        state_issues = []

        if hasattr(agent, "state") and agent.state:
            # Check if it's a UnifiedState instance or equivalent
            required_methods = ["get", "set", "update", "to_dict", "from_dict"]
            if all(hasattr(agent.state, method) for method in required_methods):
                has_unified_state = True

                # Check for both execution and business state
                if hasattr(agent.state, "execution_state") and hasattr(
                    agent.state, "business_state"
                ):
                    # Good - proper unified state structure
                    pass
                else:
                    state_issues.append(
                        "State missing execution_state or business_state attributes"
                    )
            else:
                missing_methods = [
                    m for m in required_methods if not hasattr(agent.state, m)
                ]
                state_issues.append(
                    f"State missing required methods: {missing_methods}"
                )
        else:
            state_issues.append("Missing unified state attribute")

        details["checks"]["has_unified_state"] = has_unified_state
        if has_unified_state:
            details["score"] += 0.25
        else:
            details["issues"].extend(state_issues)

        # Check 2: State management capabilities (0.25 points)
        state_management = False
        management_issues = []

        if has_unified_state and agent.state:
            # Check for state transition tracking
            if hasattr(agent.state, "history"):
                state_management = True
            else:
                management_issues.append("State missing history tracking")

            # Check for state update mechanism via tool responses
            if hasattr(agent.state, "update"):
                # Check if update method can handle ToolResponse
                try:
                    sig = inspect.signature(agent.state.update)
                    params = list(sig.parameters.keys())
                    if len(params) >= 1:  # Should accept tool_response parameter
                        pass  # Good
                    else:
                        management_issues.append(
                            "State update method has incorrect signature"
                        )
                except Exception:
                    management_issues.append("Could not analyze state update method")
            else:
                management_issues.append("State missing update method")
        else:
            management_issues.append(
                "Cannot check state management without unified state"
            )

        details["checks"]["state_management"] = state_management
        if state_management:
            details["score"] += 0.25
        else:
            details["issues"].extend(management_issues)

        # Check 3: State persistence (0.25 points)
        state_persistence = False
        persistence_issues = []

        if has_unified_state and agent.state:
            # Check for serialization capabilities
            serialization_methods = ["to_dict", "from_dict"]
            has_serialization = all(
                hasattr(agent.state, method) for method in serialization_methods
            )

            if has_serialization:
                # Check if agent has checkpoint/persistence functionality
                if hasattr(agent, "save_checkpoint") and hasattr(
                    agent, "load_checkpoint"
                ):
                    state_persistence = True
                else:
                    persistence_issues.append(
                        "Agent missing save_checkpoint/load_checkpoint methods"
                    )
            else:
                missing_methods = [
                    m for m in serialization_methods if not hasattr(agent.state, m)
                ]
                persistence_issues.append(
                    f"State missing serialization methods: {missing_methods}"
                )
        else:
            persistence_issues.append("Cannot check persistence without unified state")

        details["checks"]["state_persistence"] = state_persistence
        if state_persistence:
            details["score"] += 0.25
        else:
            details["issues"].extend(persistence_issues)

        # Check 4: State observability (0.25 points)
        state_observability = False
        observability_issues = []

        if has_unified_state and agent.state:
            # Check for state inspection capabilities
            if hasattr(agent.state, "get_summary"):
                state_observability = True
            else:
                observability_issues.append("State missing get_summary method")

            # Check for history access
            if hasattr(agent.state, "get_recent_history") or hasattr(
                agent.state, "history"
            ):
                # Good - has history access
                pass
            else:
                observability_issues.append("State missing history access methods")

            # Check if agent status includes state information
            if hasattr(agent, "get_status"):
                # Assume get_status includes state information
                pass
            else:
                observability_issues.append(
                    "Agent missing get_status method for state observability"
                )
        else:
            observability_issues.append(
                "Cannot check observability without unified state"
            )

        details["checks"]["state_observability"] = state_observability
        if state_observability:
            details["score"] += 0.25
        else:
            details["issues"].extend(observability_issues)

        # Provide recommendations based on failures
        if details["score"] < 1.0:
            if not has_unified_state:
                details["recommendations"].append(
                    "Implement UnifiedState class with execution_state and business_state"
                )
            if not state_management:
                details["recommendations"].append(
                    "Add history tracking and update() method to handle ToolResponse objects"
                )
            if not state_persistence:
                details["recommendations"].append(
                    "Implement save_checkpoint/load_checkpoint methods and state serialization"
                )
            if not state_observability:
                details["recommendations"].append(
                    "Add get_summary() and get_recent_history() methods for state inspection"
                )

        # Determine compliance level
        if details["score"] >= 0.9:
            compliance = ComplianceLevel.FULLY_COMPLIANT
        elif details["score"] >= 0.75:
            compliance = ComplianceLevel.MOSTLY_COMPLIANT
        elif details["score"] >= 0.5:
            compliance = ComplianceLevel.PARTIALLY_COMPLIANT
        else:
            compliance = ComplianceLevel.NON_COMPLIANT

        return compliance, details


class Factor8Validator(FactorValidator):
    """Factor 8: Own Your Control Flow"""

    def __init__(self):
        super().__init__(8, "Own Your Control Flow")

    def validate(
        self, agent: BaseAgent, context: Dict[str, Any] = None
    ) -> Tuple[ComplianceLevel, Dict[str, Any]]:
        """
        Validate that agent maintains explicit control over execution flow.
        """
        details = {
            "factor": self.factor_name,
            "checks": {},
            "score": 0.0,
            "issues": [],
            "recommendations": [],
        }

        # Check 1: Explicit execution stages (0.25 points)
        has_explicit_stages = False
        stage_issues = []

        if hasattr(agent, "execute_task"):
            try:
                source = inspect.getsource(agent.execute_task)
                # Look for stage-based execution patterns
                stage_indicators = [
                    "stages",
                    "workflow_stages",
                    "set_workflow_stages",
                    "current_stage",
                    "advance_stage",
                    "stage_index",
                ]

                has_explicit_stages = any(
                    indicator in source for indicator in stage_indicators
                )

                # Also check for explicit sequential execution patterns
                if not has_explicit_stages:
                    sequential_patterns = [
                        "for stage",
                        "for step",
                        "stages =",
                        "workflow =",
                        "pipeline",
                        "sequence",
                    ]
                    has_explicit_stages = any(
                        pattern in source for pattern in sequential_patterns
                    )

            except Exception:
                stage_issues.append(
                    "Could not analyze execute_task method for stage patterns"
                )

        if not has_explicit_stages:
            stage_issues.append("No explicit execution stages detected in execute_task")

        details["checks"]["explicit_stages"] = has_explicit_stages
        if has_explicit_stages:
            details["score"] += 0.25
        else:
            details["issues"].extend(stage_issues)

        # Check 2: Flow observability (0.25 points)
        flow_observability = True
        observability_issues = []

        # Check for progress tracking
        progress_attrs = ["progress", "current_stage", "total_stages"]
        missing_attrs = [attr for attr in progress_attrs if not hasattr(agent, attr)]

        if missing_attrs:
            flow_observability = False
            observability_issues.append(
                f"Missing flow tracking attributes: {missing_attrs}"
            )

        # Check for get_status method
        if not hasattr(agent, "get_status") or not callable(agent.get_status):
            flow_observability = False
            observability_issues.append(
                "Missing get_status method for flow observability"
            )

        details["checks"]["flow_observability"] = flow_observability
        if flow_observability:
            details["score"] += 0.25
        else:
            details["issues"].extend(observability_issues)

        # Check 3: Deterministic decision points (0.25 points)
        deterministic_flow = True
        determinism_issues = []

        if hasattr(agent, "execute_task"):
            try:
                source = inspect.getsource(agent.execute_task)
                # Check for non-deterministic patterns that should be avoided
                nondeterministic_patterns = [
                    "random",
                    "shuffle",
                    "choice",
                    "randint",
                    "time.time()",
                    "uuid",
                    "os.urandom",
                ]

                for pattern in nondeterministic_patterns:
                    if pattern in source:
                        deterministic_flow = False
                        determinism_issues.append(
                            f"Non-deterministic pattern detected: {pattern}"
                        )

                # Check for explicit decision criteria
                decision_patterns = [
                    "if.*success",
                    "if.*error",
                    "if.*result",
                    "elif",
                    "match",
                    "switch",
                ]
                has_decision_logic = any(
                    any(word in line for word in decision_patterns)
                    for line in source.split("\n")
                )

                if not has_decision_logic:
                    determinism_issues.append(
                        "No explicit decision logic found in execute_task"
                    )

            except Exception:
                determinism_issues.append(
                    "Could not analyze execute_task for decision patterns"
                )

        details["checks"]["deterministic_flow"] = deterministic_flow
        if deterministic_flow:
            details["score"] += 0.25
        else:
            details["issues"].extend(determinism_issues)

        # Check 4: Flow control methods (0.25 points)
        flow_control = True
        control_issues = []

        # Check for essential flow control methods
        required_methods = ["set_progress", "advance_stage"]
        missing_methods = []

        for method in required_methods:
            if not hasattr(agent, method) or not callable(getattr(agent, method)):
                missing_methods.append(method)

        if missing_methods:
            flow_control = False
            control_issues.append(f"Missing flow control methods: {missing_methods}")

        # Check for workflow stage management
        if hasattr(agent, "set_workflow_stages") and callable(
            agent.set_workflow_stages
        ):
            # Good - has workflow stage management
            pass
        else:
            control_issues.append(
                "Missing set_workflow_stages method for workflow management"
            )

        details["checks"]["flow_control_methods"] = flow_control
        if flow_control:
            details["score"] += 0.25
        else:
            details["issues"].extend(control_issues)

        # Provide recommendations based on failures
        if details["score"] < 1.0:
            if not has_explicit_stages:
                details["recommendations"].append(
                    "Implement explicit execution stages using set_workflow_stages() and stage-based execution"
                )
            if not flow_observability:
                details["recommendations"].append(
                    "Add progress tracking attributes (progress, current_stage, total_stages) and get_status() method"
                )
            if not deterministic_flow:
                details["recommendations"].append(
                    "Remove non-deterministic elements and add explicit decision criteria with clear if/elif logic"
                )
            if not flow_control:
                details["recommendations"].append(
                    "Implement flow control methods: set_progress(), advance_stage(), set_workflow_stages()"
                )

        # Determine compliance level
        if details["score"] >= 0.9:
            compliance = ComplianceLevel.FULLY_COMPLIANT
        elif details["score"] >= 0.75:
            compliance = ComplianceLevel.MOSTLY_COMPLIANT
        elif details["score"] >= 0.5:
            compliance = ComplianceLevel.PARTIALLY_COMPLIANT
        else:
            compliance = ComplianceLevel.NON_COMPLIANT

        return compliance, details


class Factor12Validator(FactorValidator):
    """Factor 12: Stateless Reducer"""

    def __init__(self):
        super().__init__(12, "Stateless Reducer")

    def validate(
        self, agent: BaseAgent, context: Dict[str, Any] = None
    ) -> Tuple[ComplianceLevel, Dict[str, Any]]:
        """
        Validate that agent functions as a stateless reducer.
        Checks for pure functions, no side effects, and predictable behavior.
        """
        details = {
            "factor": self.factor_name,
            "checks": {},
            "score": 0.0,
            "issues": [],
            "recommendations": [],
        }

        # Check 1: No instance variable modifications in execute_task
        has_state_mutation = False
        if hasattr(agent, "execute_task"):
            try:
                source = inspect.getsource(agent.execute_task)

                # Use AST to precisely detect self assignments
                import ast
                import textwrap

                try:
                    # Need to dedent the source for AST parsing
                    dedented_source = textwrap.dedent(source)
                    tree = ast.parse(dedented_source)

                    for node in ast.walk(tree):
                        if isinstance(node, ast.Assign):
                            for target in node.targets:
                                if (
                                    isinstance(target, ast.Attribute)
                                    and isinstance(target.value, ast.Name)
                                    and target.value.id == "self"
                                ):
                                    has_state_mutation = True
                                    details["issues"].append(
                                        f"State mutation found: self.{target.attr}"
                                    )
                        # Also check for augmented assignments (+=, -=, etc.)
                        elif isinstance(node, ast.AugAssign):
                            if (
                                isinstance(node.target, ast.Attribute)
                                and isinstance(node.target.value, ast.Name)
                                and node.target.value.id == "self"
                            ):
                                has_state_mutation = True
                                details["issues"].append(
                                    f"State mutation found: self.{node.target.attr} (augmented assignment)"
                                )
                except Exception:
                    # If AST parsing fails, fall back to simple heuristic
                    simple_patterns = [
                        "self." + word + " ="
                        for word in ["counter", "state", "last_", "current_", "data"]
                    ]
                    has_state_mutation = any(
                        pattern in source for pattern in simple_patterns
                    )

                details["checks"]["no_state_mutation"] = not has_state_mutation
                if not has_state_mutation:
                    details["score"] += 0.25
            except Exception:
                details["checks"]["no_state_mutation"] = False
                details["issues"].append("Could not analyze execute_task method")

        # Check 2: All inputs are explicit in method signature
        if hasattr(agent, "execute_task"):
            sig = inspect.signature(agent.execute_task)
            params = list(sig.parameters.keys())
            # Should have task and optional context, nothing hidden
            has_explicit_inputs = len(params) >= 2  # self, task, [context]
            details["checks"]["explicit_inputs"] = has_explicit_inputs
            if has_explicit_inputs:
                details["score"] += 0.25
            else:
                details["issues"].append(
                    "execute_task should have explicit task and context parameters"
                )

        # Check 3: No global state access
        if hasattr(agent, "execute_task"):
            try:
                source = inspect.getsource(agent.execute_task)
                global_patterns = ["global ", "globals()", "__builtins__"]
                has_global_access = any(
                    pattern in source for pattern in global_patterns
                )
                details["checks"]["no_global_access"] = not has_global_access
                if not has_global_access:
                    details["score"] += 0.25
                else:
                    details["issues"].append("Global state access detected")
            except Exception:
                details["checks"]["no_global_access"] = False

        # Check 4: Returns ToolResponse (predictable output)
        if hasattr(agent, "execute_task"):
            try:
                source = inspect.getsource(agent.execute_task)
                # Check for ToolResponse in return statements or type annotations
                returns_toolresponse = (
                    "ToolResponse" in source and "return" in source
                ) or ("-> ToolResponse" in source)
                details["checks"]["returns_toolresponse"] = returns_toolresponse
                if returns_toolresponse:
                    details["score"] += 0.25
                else:
                    details["issues"].append(
                        "Should return ToolResponse for predictable output"
                    )
            except Exception:
                details["checks"]["returns_toolresponse"] = False

        # Provide recommendations based on findings
        if details["score"] < 1.0:
            if (
                "no_state_mutation" in details["checks"]
                and not details["checks"]["no_state_mutation"]
            ):
                details["recommendations"].append(
                    "Remove instance variable assignments from execute_task"
                )
            if (
                "explicit_inputs" in details["checks"]
                and not details["checks"]["explicit_inputs"]
            ):
                details["recommendations"].append(
                    "Make all inputs explicit: execute_task(self, task: str, context: ExecutionContext = None)"
                )
            if (
                "no_global_access" in details["checks"]
                and not details["checks"]["no_global_access"]
            ):
                details["recommendations"].append(
                    "Remove global state access, pass all data through parameters"
                )
            if (
                "returns_toolresponse" in details["checks"]
                and not details["checks"]["returns_toolresponse"]
            ):
                details["recommendations"].append(
                    "Return ToolResponse objects for consistent output"
                )

        # Determine compliance level
        if details["score"] >= 0.9:
            compliance = ComplianceLevel.FULLY_COMPLIANT
        elif details["score"] >= 0.75:
            compliance = ComplianceLevel.MOSTLY_COMPLIANT
        elif details["score"] >= 0.5:
            compliance = ComplianceLevel.PARTIALLY_COMPLIANT
        else:
            compliance = ComplianceLevel.NON_COMPLIANT

        return compliance, details


class Factor7Validator(FactorValidator):
    """Factor 7: Contact Humans with Tool Calls"""

    def __init__(self):
        super().__init__(7, "Contact Humans with Tool Calls")

    def validate(
        self, agent: BaseAgent, context: Dict[str, Any] = None
    ) -> Tuple[ComplianceLevel, Dict[str, Any]]:
        """
        Validate that agents use tool calls for human interaction.

        Checks:
        1. Human interaction tools exist and are properly structured
        2. Communication protocols are implemented (timeout handling, escalation)
        3. User experience elements are present (clear prompts, context)
        4. Tool calls follow standard patterns for human contact
        """
        details = {
            "factor": 7,
            "name": "Contact Humans with Tool Calls",
            "score": 0.0,
            "checks": {
                "has_human_tools": False,
                "communication_protocols": False,
                "user_experience": False,
                "tool_call_patterns": False,
            },
            "issues": [],
            "recommendations": [],
        }

        # Check 1: Human interaction tools exist and are properly structured (0.25)
        tools = agent.get_tools() if hasattr(agent, "get_tools") else []
        human_tools = []

        for tool in tools:
            tool_name = getattr(tool, "name", "").lower()
            tool_desc = getattr(tool, "description", "").lower()

            if any(
                keyword in tool_name or keyword in tool_desc
                for keyword in [
                    "human",
                    "interaction",
                    "approval",
                    "contact",
                    "escalate",
                ]
            ):
                human_tools.append(tool)

        details["checks"]["has_human_tools"] = len(human_tools) > 0
        if len(human_tools) > 0:
            details["score"] += 0.25

            # Verify tools are properly structured
            properly_structured = True
            for tool in human_tools:
                if not hasattr(tool, "execute") or not hasattr(
                    tool, "get_parameters_schema"
                ):
                    properly_structured = False
                    break

            if not properly_structured:
                details["issues"].append(
                    "Human interaction tools lack proper Tool structure"
                )
                details["score"] -= 0.125  # Partial deduction
        else:
            details["issues"].append("No human interaction tools found")

        # Check 2: Communication protocols implemented (0.25)
        has_protocols = False
        if human_tools:
            for tool in human_tools:
                try:
                    source = (
                        inspect.getsource(tool.execute)
                        if hasattr(tool, "execute")
                        else ""
                    )

                    # Check for timeout handling
                    has_timeout = "timeout" in source.lower()

                    # Check for structured request/response
                    has_structure = any(
                        keyword in source
                        for keyword in ["request", "response", "message", "context"]
                    )

                    # Check for error handling
                    has_error_handling = "except" in source or "error" in source.lower()

                    if has_timeout and has_structure and has_error_handling:
                        has_protocols = True
                        break
                except Exception:
                    continue

        details["checks"]["communication_protocols"] = has_protocols
        if has_protocols:
            details["score"] += 0.25
        else:
            details["issues"].append(
                "Missing communication protocols (timeout, error handling, structured format)"
            )

        # Check 3: User experience elements (0.25)
        has_ux_elements = False
        if human_tools:
            for tool in human_tools:
                try:
                    schema = (
                        tool.get_parameters_schema()
                        if hasattr(tool, "get_parameters_schema")
                        else {}
                    )

                    # Check for clear prompts/messages
                    has_message_param = False
                    has_context_param = False

                    if "properties" in schema:
                        props = schema["properties"]
                        for prop_name, prop_info in props.items():
                            if (
                                "message" in prop_name.lower()
                                or "prompt" in prop_name.lower()
                            ):
                                has_message_param = True
                            if "context" in prop_name.lower():
                                has_context_param = True

                    # Check for descriptions in parameters
                    has_descriptions = False
                    if "properties" in schema:
                        for prop_info in schema["properties"].values():
                            if "description" in prop_info:
                                has_descriptions = True
                                break

                    if has_message_param and has_context_param and has_descriptions:
                        has_ux_elements = True
                        break
                except Exception:
                    continue

        details["checks"]["user_experience"] = has_ux_elements
        if has_ux_elements:
            details["score"] += 0.25
        else:
            details["issues"].append(
                "Missing UX elements (clear prompts, context parameters, descriptions)"
            )

        # Check 4: Tool calls follow standard patterns (0.25)
        follows_patterns = False
        if human_tools:
            for tool in human_tools:
                try:
                    source = (
                        inspect.getsource(tool.execute)
                        if hasattr(tool, "execute")
                        else ""
                    )

                    # Check for ToolResponse usage
                    returns_toolresponse = "ToolResponse" in source

                    # Check for proper parameter validation
                    has_validation = (
                        "validate" in source.lower() or "required" in source.lower()
                    )

                    # Check for ToolResponse and validation
                    if returns_toolresponse and has_validation:
                        follows_patterns = True
                        break
                except Exception:
                    continue

        details["checks"]["tool_call_patterns"] = follows_patterns
        if follows_patterns:
            details["score"] += 0.25
        else:
            details["issues"].append(
                "Human tools don't follow standard tool call patterns"
            )

        # Provide recommendations based on findings
        if details["score"] < 1.0:
            if not details["checks"]["has_human_tools"]:
                details["recommendations"].append(
                    "Implement HumanInteractionTool or similar for human contact"
                )
            if not details["checks"]["communication_protocols"]:
                details["recommendations"].append(
                    "Add timeout handling, error handling, and structured request/response format"
                )
            if not details["checks"]["user_experience"]:
                details["recommendations"].append(
                    "Include clear message prompts, context parameters, and parameter descriptions"
                )
            if not details["checks"]["tool_call_patterns"]:
                details["recommendations"].append(
                    "Ensure human tools return ToolResponse and include parameter validation"
                )

        # Determine compliance level
        if details["score"] >= 0.9:
            compliance = ComplianceLevel.FULLY_COMPLIANT
        elif details["score"] >= 0.75:
            compliance = ComplianceLevel.MOSTLY_COMPLIANT
        elif details["score"] >= 0.5:
            compliance = ComplianceLevel.PARTIALLY_COMPLIANT
        else:
            compliance = ComplianceLevel.NON_COMPLIANT

        return compliance, details


class Factor9Validator(FactorValidator):
    """Factor 9: Compact Errors into Context Window"""

    def __init__(self):
        super().__init__(9, "Compact Errors into Context Window")

    def validate(
        self, agent: BaseAgent, context: Dict[str, Any] = None
    ) -> Tuple[ComplianceLevel, Dict[str, Any]]:
        """
        Validate that agents compact errors efficiently for context windows.

        Checks:
        1. Error messages are concise and summarized (not verbose)
        2. Error patterns are recognized and have codes
        3. Error context is relevant and efficient
        4. Historical errors are summarized and trends identified
        """
        details = {
            "factor": 9,
            "name": "Compact Errors into Context Window",
            "score": 0.0,
            "checks": {
                "error_compaction": False,
                "error_patterns": False,
                "context_efficiency": False,
                "error_summarization": False,
            },
            "issues": [],
            "recommendations": [],
        }

        # Check 1: Error compaction - messages are concise (0.25)
        has_error_compaction = self._check_error_compaction(agent)
        details["checks"]["error_compaction"] = has_error_compaction
        if has_error_compaction:
            details["score"] += 0.25
        else:
            details["issues"].append("Error messages are not properly compacted")

        # Check 2: Error patterns - codes and recognition (0.25)
        has_error_patterns = self._check_error_patterns(agent)
        details["checks"]["error_patterns"] = has_error_patterns
        if has_error_patterns:
            details["score"] += 0.25
        else:
            details["issues"].append("Error patterns and codes not implemented")

        # Check 3: Context efficiency - relevant error context (0.25)
        has_context_efficiency = self._check_context_efficiency(agent)
        details["checks"]["context_efficiency"] = has_context_efficiency
        if has_context_efficiency:
            details["score"] += 0.25
        else:
            details["issues"].append("Error context is not efficiently managed")

        # Check 4: Error summarization - historical errors (0.25)
        has_error_summarization = self._check_error_summarization(agent)
        details["checks"]["error_summarization"] = has_error_summarization
        if has_error_summarization:
            details["score"] += 0.25
        else:
            details["issues"].append("Historical error summarization not implemented")

        # Provide recommendations based on findings
        if details["score"] < 1.0:
            if not details["checks"]["error_compaction"]:
                details["recommendations"].append(
                    "Implement error compaction to summarize verbose errors"
                )
            if not details["checks"]["error_patterns"]:
                details["recommendations"].append(
                    "Add error codes and pattern recognition for common errors"
                )
            if not details["checks"]["context_efficiency"]:
                details["recommendations"].append(
                    "Improve error context relevance and efficiency"
                )
            if not details["checks"]["error_summarization"]:
                details["recommendations"].append(
                    "Implement historical error summarization and trend identification"
                )

        # Determine compliance level
        if details["score"] >= 0.9:
            compliance = ComplianceLevel.FULLY_COMPLIANT
        elif details["score"] >= 0.75:
            compliance = ComplianceLevel.MOSTLY_COMPLIANT
        elif details["score"] >= 0.5:
            compliance = ComplianceLevel.PARTIALLY_COMPLIANT
        else:
            compliance = ComplianceLevel.NON_COMPLIANT

        return compliance, details

    def _check_error_compaction(self, agent: BaseAgent) -> bool:
        """Check if agent compacts error messages."""
        # Look for error handling methods
        methods_to_check = [
            "handle_error",
            "_handle_error",
            "process_error",
            "compact_error",
        ]

        for method_name in methods_to_check:
            if hasattr(agent, method_name):
                try:
                    method = getattr(agent, method_name)
                    source = inspect.getsource(method)

                    # Check for compaction patterns
                    compaction_indicators = [
                        "summary",
                        "compact",
                        "truncate",
                        "shorten",
                        "[:50]",
                        "[:100]",
                        "max_length",
                        "limit",
                    ]

                    if any(
                        indicator in source.lower()
                        for indicator in compaction_indicators
                    ):
                        return True
                except Exception:
                    continue

        # Check if agent has state management with error compaction
        if hasattr(agent, "state") and agent.state:
            try:
                # Look for error handling in state updates
                if hasattr(agent.state, "update"):
                    source = inspect.getsource(agent.state.update)
                    if "error" in source.lower() and any(
                        word in source.lower()
                        for word in ["compact", "summary", "truncate"]
                    ):
                        return True
            except Exception:
                pass

        return False

    def _check_error_patterns(self, agent: BaseAgent) -> bool:
        """Check if agent uses error patterns and codes."""
        # Look for error code constants or patterns
        try:
            # Check class attributes for error codes (more specific)
            error_code_count = 0
            for attr_name in dir(agent.__class__):
                if (
                    attr_name.upper().startswith(("ERR_", "ERROR_"))
                    and not attr_name.startswith("_")
                    and isinstance(getattr(agent.__class__, attr_name, None), str)
                ):
                    error_code_count += 1

            # Need at least 2 error codes to show pattern recognition
            if error_code_count >= 2:
                return True

            # Check for error handling methods with pattern recognition
            methods_to_check = ["classify_error", "categorize_error", "get_error_code"]

            for method_name in methods_to_check:
                if hasattr(agent, method_name):
                    try:
                        method = getattr(agent, method_name)
                        source = inspect.getsource(method)

                        # Check for error pattern indicators
                        pattern_indicators = [
                            "ERR_",
                            "ERROR_",
                            "error_code",
                            "error_type",
                            "classify",
                            "pattern",
                            "category",
                        ]

                        if any(indicator in source for indicator in pattern_indicators):
                            return True
                    except Exception:
                        continue
        except Exception:
            pass

        return False

    def _check_context_efficiency(self, agent: BaseAgent) -> bool:
        """Check if agent manages error context efficiently."""
        # Look for specific error context methods (most strict)
        error_context_methods = [
            "get_error_context",
            "get_relevant_errors",
            "compact_error_context",
        ]

        for method_name in error_context_methods:
            if hasattr(agent, method_name):
                return True

        return False

    def _check_error_summarization(self, agent: BaseAgent) -> bool:
        """Check if agent summarizes historical errors."""
        # Look for error summarization methods (most strict)
        summarization_methods = [
            "summarize_errors",
            "get_error_summary",
            "compact_error_history",
        ]

        for method_name in summarization_methods:
            if hasattr(agent, method_name):
                return True

        return False


class Factor11Validator(FactorValidator):
    """Factor 11: Trigger from Anywhere"""

    def __init__(self):
        super().__init__(11, "Trigger from Anywhere")

    def validate(
        self, agent: BaseAgent, context: Dict[str, Any] = None
    ) -> Tuple[ComplianceLevel, Dict[str, Any]]:
        """
        Validate that agents can be triggered from multiple entry points.

        Checks:
        1. Multiple entry points exist (CLI, API, events, schedule)
        2. Trigger registration system implemented
        3. Trigger flexibility (async/sync, remote/local)
        4. Trigger documentation and permissions
        """
        details = {
            "factor": 11,
            "name": "Trigger from Anywhere",
            "score": 0.0,
            "checks": {
                "multiple_entry_points": False,
                "trigger_registration": False,
                "trigger_flexibility": False,
                "trigger_documentation": False,
            },
            "issues": [],
            "recommendations": [],
        }

        # Check 1: Multiple entry points (0.25)
        has_multiple_entry_points = self._check_multiple_entry_points(agent)
        details["checks"]["multiple_entry_points"] = has_multiple_entry_points
        if has_multiple_entry_points:
            details["score"] += 0.25
        else:
            details["issues"].append("Multiple entry points not implemented")

        # Check 2: Trigger registration (0.25)
        has_trigger_registration = self._check_trigger_registration(agent)
        details["checks"]["trigger_registration"] = has_trigger_registration
        if has_trigger_registration:
            details["score"] += 0.25
        else:
            details["issues"].append("Trigger registration system not implemented")

        # Check 3: Trigger flexibility (0.25)
        has_trigger_flexibility = self._check_trigger_flexibility(agent)
        details["checks"]["trigger_flexibility"] = has_trigger_flexibility
        if has_trigger_flexibility:
            details["score"] += 0.25
        else:
            details["issues"].append("Trigger flexibility not implemented")

        # Check 4: Trigger documentation (0.25)
        has_trigger_documentation = self._check_trigger_documentation(agent)
        details["checks"]["trigger_documentation"] = has_trigger_documentation
        if has_trigger_documentation:
            details["score"] += 0.25
        else:
            details["issues"].append("Trigger documentation not implemented")

        # Provide recommendations based on findings
        if details["score"] < 1.0:
            if not details["checks"]["multiple_entry_points"]:
                details["recommendations"].append(
                    "Implement multiple entry points (CLI, API, events, scheduling)"
                )
            if not details["checks"]["trigger_registration"]:
                details["recommendations"].append(
                    "Add trigger registration system to manage different trigger types"
                )
            if not details["checks"]["trigger_flexibility"]:
                details["recommendations"].append(
                    "Support both async/sync and remote/local trigger mechanisms"
                )
            if not details["checks"]["trigger_documentation"]:
                details["recommendations"].append(
                    "Document trigger mechanisms and define trigger permissions"
                )

        # Determine compliance level
        if details["score"] >= 0.9:
            compliance = ComplianceLevel.FULLY_COMPLIANT
        elif details["score"] >= 0.75:
            compliance = ComplianceLevel.MOSTLY_COMPLIANT
        elif details["score"] >= 0.5:
            compliance = ComplianceLevel.PARTIALLY_COMPLIANT
        else:
            compliance = ComplianceLevel.NON_COMPLIANT

        return compliance, details

    def _check_multiple_entry_points(self, agent: BaseAgent) -> bool:
        """Check if agent supports multiple entry points."""
        entry_points = 0

        # Check for CLI entry point indicators
        cli_indicators = [
            "main",
            "__main__",
            "cli",
            "run_cli",
            "command_line",
            "execute_from_cli",
            "parse_args",
        ]

        for indicator in cli_indicators:
            if hasattr(agent, indicator) or hasattr(agent.__class__, indicator):
                entry_points += 1
                break

        # Check for API entry point indicators
        api_indicators = [
            "api",
            "rest",
            "http",
            "server",
            "endpoint",
            "route",
            "handle_request",
            "process_request",
        ]

        for indicator in api_indicators:
            if hasattr(agent, indicator) or any(
                indicator in attr.lower() for attr in dir(agent)
            ):
                entry_points += 1
                break

        # Check for event-driven indicators
        event_indicators = [
            "on_event",
            "event_handler",
            "trigger",
            "listener",
            "callback",
            "subscribe",
            "handle_event",
        ]

        for indicator in event_indicators:
            if hasattr(agent, indicator) or any(
                indicator in attr.lower() for attr in dir(agent)
            ):
                entry_points += 1
                break

        # Check for schedule indicators
        schedule_indicators = [
            "schedule",
            "cron",
            "timer",
            "periodic",
            "interval",
            "run_scheduled",
            "scheduled_task",
        ]

        for indicator in schedule_indicators:
            if hasattr(agent, indicator) or any(
                indicator in attr.lower() for attr in dir(agent)
            ):
                entry_points += 1
                break

        # Need at least 2 different entry points
        return entry_points >= 2

    def _check_trigger_registration(self, agent: BaseAgent) -> bool:
        """Check if agent has trigger registration system."""
        registration_indicators = [
            "register_trigger",
            "add_trigger",
            "trigger_registry",
            "triggers",
            "register_handler",
            "trigger_map",
        ]

        for indicator in registration_indicators:
            if hasattr(agent, indicator):
                return True

        # Check for trigger registration in class attributes or methods
        for attr_name in dir(agent):
            if any(
                indicator in attr_name.lower() for indicator in registration_indicators
            ):
                return True

        # Check if agent has a triggers collection or registry
        if hasattr(agent, "__dict__") and any(
            "trigger" in key.lower() for key in agent.__dict__.keys()
        ):
            return True

        return False

    def _check_trigger_flexibility(self, agent: BaseAgent) -> bool:
        """Check if agent supports flexible trigger mechanisms."""
        flexibility_indicators = [
            "async",
            "sync",
            "remote",
            "local",
            "webhook",
            "queue",
            "message",
            "pubsub",
            "stream",
        ]

        flexibility_count = 0

        # Check methods for flexibility indicators
        for attr_name in dir(agent):
            attr_lower = attr_name.lower()
            for indicator in flexibility_indicators:
                if indicator in attr_lower:
                    flexibility_count += 1
                    break

        # Check if agent supports async execution
        if hasattr(agent, "execute_task"):
            try:
                import inspect

                if inspect.iscoroutinefunction(agent.execute_task):
                    flexibility_count += 1
            except Exception:
                pass

        # Check for async/await patterns in methods
        for attr_name in dir(agent):
            if callable(getattr(agent, attr_name, None)):
                try:
                    method = getattr(agent, attr_name)
                    source = inspect.getsource(method)
                    if "async " in source or "await " in source:
                        flexibility_count += 1
                        break
                except Exception:
                    continue

        # Need at least 2 flexibility features
        return flexibility_count >= 2

    def _check_trigger_documentation(self, agent: BaseAgent) -> bool:
        """Check if triggers are documented."""
        documentation_indicators = [
            "get_triggers",
            "get_trigger_info",  # Added to recognize more descriptive method names
            "list_triggers",
            "trigger_help",
            "trigger_docs",
            "available_triggers",
            "supported_triggers",
        ]

        # Require explicit trigger documentation methods
        for indicator in documentation_indicators:
            if hasattr(agent, indicator):
                return True

        return False


class ComplianceAuditor:
    """
    Comprehensive 12-factor compliance auditor.
    Validates pin-citer inspired patterns against 12-factor methodology.
    """

    def __init__(self):
        self.validators = {
            1: Factor1Validator(),
            2: Factor2Validator(),
            3: Factor3Validator(),  # Added Factor 3
            4: Factor4Validator(),  # Added Factor 4
            5: Factor5Validator(),  # Added Factor 5
            6: Factor6Validator(),
            7: Factor7Validator(),  # Added Factor 7
            8: Factor8Validator(),  # Added Factor 8
            9: Factor9Validator(),  # Added Factor 9
            10: Factor10Validator(),
            11: Factor11Validator(),  # Added Factor 11
            12: Factor12Validator(),  # Added Factor 12
        }

        # Validators for remaining factors are implemented as needed
        # 7: Factor 7 (Contact Humans with Tool Calls)
        # 9: Factor 9 (Compact Errors)
        # 11: Factor 11 (Trigger from Anywhere)

    def audit_agent(self, agent: BaseAgent) -> Dict[str, Any]:
        """
        Perform comprehensive 12-factor compliance audit.

        Returns detailed compliance report with pin-citer pattern analysis.
        """
        audit_report = {
            "agent_id": agent.agent_id,
            "agent_type": agent.__class__.__name__,
            "timestamp": agent.created_at.isoformat(),
            "overall_compliance": ComplianceLevel.NON_COMPLIANT.value,
            "overall_score": 0.0,
            "factor_results": {},
            "pin_citer_enhancements": {},
            "summary": {
                "compliant_factors": 0,
                "total_factors": len(self.validators),
                "critical_issues": [],
                "recommendations": [],
            },
        }

        total_score = 0.0
        compliant_factors = 0

        # Validate each factor
        for factor_num, validator in self.validators.items():
            compliance, details = validator.validate(agent)

            audit_report["factor_results"][factor_num] = {
                "compliance": compliance.value,
                "details": details,
            }

            # Add score to total
            total_score += details["score"]

            # Count fully/mostly compliant factors
            if compliance in [
                ComplianceLevel.FULLY_COMPLIANT,
                ComplianceLevel.MOSTLY_COMPLIANT,
            ]:
                compliant_factors += 1

            # Collect critical issues
            if compliance == ComplianceLevel.NON_COMPLIANT:
                audit_report["summary"]["critical_issues"].extend(details["issues"])

            # Collect recommendations
            audit_report["summary"]["recommendations"].extend(
                details["recommendations"]
            )

            # Collect pin-citer enhancements
            if "pin_citer_enhancements" in details:
                audit_report["pin_citer_enhancements"][factor_num] = details[
                    "pin_citer_enhancements"
                ]

        # Calculate overall compliance
        avg_score = total_score / len(self.validators)
        audit_report["overall_score"] = avg_score
        audit_report["summary"]["compliant_factors"] = compliant_factors

        if avg_score >= 0.9:
            audit_report["overall_compliance"] = ComplianceLevel.FULLY_COMPLIANT.value
        elif avg_score >= 0.8:
            audit_report["overall_compliance"] = ComplianceLevel.MOSTLY_COMPLIANT.value
        elif avg_score >= 0.5:
            audit_report[
                "overall_compliance"
            ] = ComplianceLevel.PARTIALLY_COMPLIANT.value
        else:
            audit_report["overall_compliance"] = ComplianceLevel.NON_COMPLIANT.value

        return audit_report

    def audit_pin_citer_patterns(self, agent: BaseAgent) -> Dict[str, Any]:
        """
        Audit pin-citer specific patterns for 12-factor compliance.
        Ensures learned patterns don't violate principles.
        """
        pattern_audit = {
            "checkpoint_system": self._audit_checkpoint_pattern(agent),
            "pipeline_architecture": self._audit_pipeline_pattern(agent),
            "progress_tracking": self._audit_progress_pattern(agent),
            "error_handling": self._audit_error_pattern(agent),
        }

        return pattern_audit

    def _audit_checkpoint_pattern(self, agent: BaseAgent) -> Dict[str, Any]:
        """Audit pin-citer inspired checkpoint system"""
        audit = {
            "pattern_name": "Enhanced Checkpoint System",
            "compliant": True,
            "benefits": [],
            "concerns": [],
        }

        if hasattr(agent, "progress") and hasattr(agent, "current_stage"):
            audit["benefits"].append("Enhanced progress tracking supports Factor 6")

        if hasattr(agent, "workflow_data"):
            audit["benefits"].append("Workflow data supports Factor 5 (Unified State)")

        if hasattr(agent, "error_context"):
            audit["benefits"].append("Error context supports Factor 9 (Compact Errors)")

        return audit

    def _audit_pipeline_pattern(self, agent: BaseAgent) -> Dict[str, Any]:
        """Audit pin-citer inspired pipeline architecture"""
        audit = {
            "pattern_name": "Multi-Stage Pipeline",
            "compliant": True,
            "benefits": [],
            "concerns": [],
        }

        if hasattr(agent, "pipeline"):
            audit["benefits"].append(
                "Pipeline composition supports Factor 10 (Small, Focused Agents)"
            )

            # Check if pipeline stages are small and focused
            pipeline = getattr(agent, "pipeline")
            if hasattr(pipeline, "stages") and len(pipeline.stages) > 1:
                audit["benefits"].append(
                    "Multiple focused stages demonstrate proper decomposition"
                )

        return audit

    def _audit_progress_pattern(self, agent: BaseAgent) -> Dict[str, Any]:
        """Audit progress tracking pattern"""
        audit = {
            "pattern_name": "Progress Tracking",
            "compliant": True,
            "benefits": [],
            "concerns": [],
        }

        if hasattr(agent, "set_progress") and hasattr(agent, "progress"):
            audit["benefits"].append(
                "Progress tracking enhances Factor 6 (Pause/Resume)"
            )

        return audit

    def _audit_error_pattern(self, agent: BaseAgent) -> Dict[str, Any]:
        """Audit error handling pattern"""
        audit = {
            "pattern_name": "Enhanced Error Handling",
            "compliant": True,
            "benefits": [],
            "concerns": [],
        }

        if hasattr(agent, "handle_error") and hasattr(agent, "error_context"):
            audit["benefits"].append(
                "Enhanced error context supports Factor 9 (Compact Errors)"
            )

        return audit

    def generate_compliance_report(
        self, agent: BaseAgent, output_path: Path = None
    ) -> str:
        """Generate comprehensive compliance report"""
        audit_results = self.audit_agent(agent)
        pin_citer_results = self.audit_pin_citer_patterns(agent)

        report = f"""
# 12-Factor Agent Compliance Report

## Agent Information
- **Agent ID**: {audit_results['agent_id']}
- **Agent Type**: {audit_results['agent_type']}
- **Audit Timestamp**: {audit_results['timestamp']}

## Overall Compliance
- **Compliance Level**: {audit_results['overall_compliance'].upper()}
- **Overall Score**: {audit_results['overall_score']:.2f}/1.0
- **Compliant Factors**: {audit_results['summary']['compliant_factors']}/{audit_results['summary']['total_factors']}

## Factor-by-Factor Analysis
"""

        for factor_num, results in audit_results["factor_results"].items():
            details = results["details"]
            report += f"""
### Factor {factor_num}: {details['factor']}
- **Compliance**: {results['compliance'].upper()}
- **Score**: {details['score']:.2f}/1.0
- **Issues**: {', '.join(details['issues']) if details['issues'] else 'None'}
- **Pin-citer Enhancements**: {audit_results['pin_citer_enhancements'].get(factor_num, {})}
"""

        report += """
## Pin-citer Pattern Analysis
"""

        for pattern_name, pattern_audit in pin_citer_results.items():
            report += f"""
### {pattern_audit['pattern_name']}
- **Compliant**: {pattern_audit['compliant']}
- **Benefits**: {', '.join(pattern_audit['benefits'])}
- **Concerns**: {', '.join(pattern_audit['concerns']) if pattern_audit['concerns'] else 'None'}
"""

        if output_path:
            output_path.write_text(report)

        return report


# Example usage
def validate_pin_citer_integration():
    """Validate that pin-citer patterns maintain 12-factor compliance"""
    from ..agents.enhanced_workflow_agent import EnhancedWorkflowAgent

    # Create agent with pin-citer patterns
    agent = EnhancedWorkflowAgent()

    # Audit compliance
    auditor = ComplianceAuditor()
    report = auditor.generate_compliance_report(agent)

    print("Pin-citer Integration Compliance Report:")
    print(report)

    return report


if __name__ == "__main__":
    validate_pin_citer_integration()
