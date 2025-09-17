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


class ComplianceAuditor:
    """
    Comprehensive 12-factor compliance auditor.
    Validates pin-citer inspired patterns against 12-factor methodology.
    """

    def __init__(self):
        self.validators = {
            1: Factor1Validator(),
            2: Factor2Validator(),
            6: Factor6Validator(),
            10: Factor10Validator(),
            12: Factor12Validator(),  # Added Factor 12
        }

        # Validators for remaining factors are implemented as needed
        # 3: Factor 3 (Own Your Context Window)
        # 4: Factor 4 (Tools are Structured Outputs)
        # 5: Factor 5 (Unify Execution & Business State)
        # 7: Factor 7 (Contact Humans with Tool Calls)
        # 8: Factor 8 (Own Your Control Flow)
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
