"""
Security Framework - 12-Factor Agents Framework
Production-ready security validation, sandboxing, and access control for agent marketplace
"""

import ast
import hashlib
import hmac
import json
import os
import sys
import tempfile
import subprocess
import threading
import time
from pathlib import Path
from typing import Dict, Any, List, Optional, Set, Union, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
import importlib.util
import resource
import signal
from contextlib import contextmanager
import tarfile
import zipfile

from ..base import ToolResponse
from .registry import AgentMetadata, AgentCapability


class SecurityLevel(Enum):
    """Security levels for plugins and agents"""
    UNRESTRICTED = "unrestricted"  # Full system access
    TRUSTED = "trusted"            # Most operations allowed
    STANDARD = "standard"          # Standard sandbox restrictions
    RESTRICTED = "restricted"      # Heavy restrictions
    QUARANTINED = "quarantined"    # Minimal access, mostly read-only


class SecurityRisk(Enum):
    """Security risk levels"""
    LOW = "low"
    MEDIUM = "medium" 
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class SecurityViolation:
    """Security violation record"""
    violation_type: str
    severity: SecurityRisk
    description: str
    location: str  # file:line or function name
    detected_at: str = None
    
    def __post_init__(self):
        if self.detected_at is None:
            self.detected_at = datetime.now().isoformat()


@dataclass
class SecurityPolicy:
    """Security policy configuration"""
    allowed_modules: Set[str] = None
    banned_modules: Set[str] = None
    allowed_functions: Set[str] = None
    banned_functions: Set[str] = None
    max_memory_mb: int = 512
    max_cpu_seconds: int = 30
    max_file_size_mb: int = 100
    allowed_file_operations: Set[str] = None
    network_access: bool = False
    subprocess_access: bool = False
    file_system_access: bool = True
    require_signature: bool = False
    
    def __post_init__(self):
        if self.allowed_modules is None:
            self.allowed_modules = {
                'os', 'sys', 'json', 'datetime', 'pathlib', 're', 
                'asyncio', 'typing', 'dataclasses', 'enum', 'collections',
                'itertools', 'functools', 'math', 'random', 'uuid',
                'logging', 'time', 'hashlib'
            }
        if self.banned_modules is None:
            self.banned_modules = {
                'eval', 'exec', 'compile', '__import__', 'globals', 'locals',
                'subprocess', 'multiprocessing', 'threading', 'ctypes',
                'socket', 'urllib', 'requests', 'http'
            }
        if self.allowed_functions is None:
            self.allowed_functions = set()
        if self.banned_functions is None:
            self.banned_functions = {
                'eval', 'exec', 'compile', '__import__', 'open',
                'input', 'raw_input', 'exit', 'quit'
            }
        if self.allowed_file_operations is None:
            self.allowed_file_operations = {'read', 'write', 'list'}


@dataclass 
class SecurityAuditResult:
    """Result of security audit"""
    passed: bool
    risk_level: SecurityRisk
    violations: List[SecurityViolation]
    allowed_capabilities: List[AgentCapability]
    recommended_policy: SecurityPolicy
    signature_valid: bool = False
    checksum: str = ""
    audit_time: str = None
    
    def __post_init__(self):
        if self.audit_time is None:
            self.audit_time = datetime.now().isoformat()


class SecurityValidator:
    """
    Advanced security validator for agent code analysis
    Performs static analysis to detect potential security risks
    """
    
    def __init__(self, policy: SecurityPolicy = None):
        self.policy = policy or SecurityPolicy()
        self.violations = []
        
    def validate_code(self, code: str, filename: str = "<string>") -> SecurityAuditResult:
        """
        Validate Python code for security risks
        
        Args:
            code: Python source code to validate
            filename: Source filename for error reporting
            
        Returns:
            SecurityAuditResult with validation results
        """
        self.violations = []
        
        try:
            # Parse AST
            tree = ast.parse(code, filename)
            
            # Analyze AST nodes
            self._analyze_ast(tree, filename)
            
            # Calculate risk level
            risk_level = self._calculate_risk_level()
            
            # Determine allowed capabilities
            allowed_capabilities = self._determine_capabilities()
            
            # Generate recommended policy
            recommended_policy = self._generate_policy_recommendation()
            
            return SecurityAuditResult(
                passed=len([v for v in self.violations if v.severity in [SecurityRisk.HIGH, SecurityRisk.CRITICAL]]) == 0,
                risk_level=risk_level,
                violations=self.violations.copy(),
                allowed_capabilities=allowed_capabilities,
                recommended_policy=recommended_policy,
                checksum=hashlib.sha256(code.encode()).hexdigest()
            )
            
        except SyntaxError as e:
            self.violations.append(SecurityViolation(
                violation_type="syntax_error",
                severity=SecurityRisk.HIGH,
                description=f"Syntax error: {e}",
                location=f"{filename}:{e.lineno}"
            ))
            
            return SecurityAuditResult(
                passed=False,
                risk_level=SecurityRisk.HIGH,
                violations=self.violations.copy(),
                allowed_capabilities=[],
                recommended_policy=SecurityPolicy()
            )
        
        except Exception as e:
            return SecurityAuditResult(
                passed=False,
                risk_level=SecurityRisk.CRITICAL,
                violations=[SecurityViolation(
                    violation_type="analysis_error",
                    severity=SecurityRisk.CRITICAL,
                    description=f"Analysis failed: {e}",
                    location=filename
                )],
                allowed_capabilities=[],
                recommended_policy=SecurityPolicy()
            )
    
    def _analyze_ast(self, tree: ast.AST, filename: str):
        """Analyze AST for security violations"""
        for node in ast.walk(tree):
            self._check_imports(node, filename)
            self._check_function_calls(node, filename)
            self._check_attribute_access(node, filename)
            self._check_dangerous_operations(node, filename)
            self._check_exec_eval(node, filename)
            self._check_file_operations(node, filename)
    
    def _check_imports(self, node: ast.AST, filename: str):
        """Check for dangerous imports"""
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            for alias in node.names:
                module_name = alias.name
                if hasattr(node, 'module') and node.module:
                    module_name = node.module
                
                if module_name in self.policy.banned_modules:
                    self.violations.append(SecurityViolation(
                        violation_type="banned_import",
                        severity=SecurityRisk.HIGH,
                        description=f"Import of banned module: {module_name}",
                        location=f"{filename}:{node.lineno}"
                    ))
                
                # Check for potentially dangerous modules
                dangerous_patterns = ['subprocess', 'os.system', 'eval', 'exec', 'compile']
                for pattern in dangerous_patterns:
                    if pattern in module_name:
                        self.violations.append(SecurityViolation(
                            violation_type="dangerous_import",
                            severity=SecurityRisk.MEDIUM,
                            description=f"Import of potentially dangerous module: {module_name}",
                            location=f"{filename}:{node.lineno}"
                        ))
    
    def _check_function_calls(self, node: ast.AST, filename: str):
        """Check for dangerous function calls"""
        if isinstance(node, ast.Call):
            func_name = None
            
            if isinstance(node.func, ast.Name):
                func_name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                func_name = node.func.attr
            
            if func_name in self.policy.banned_functions:
                self.violations.append(SecurityViolation(
                    violation_type="banned_function",
                    severity=SecurityRisk.HIGH,
                    description=f"Call to banned function: {func_name}",
                    location=f"{filename}:{node.lineno}"
                ))
            
            # Check for system command execution
            if func_name in ['system', 'popen', 'spawn', 'exec']:
                self.violations.append(SecurityViolation(
                    violation_type="system_execution",
                    severity=SecurityRisk.CRITICAL,
                    description=f"System command execution: {func_name}",
                    location=f"{filename}:{node.lineno}"
                ))
    
    def _check_attribute_access(self, node: ast.AST, filename: str):
        """Check for dangerous attribute access"""
        if isinstance(node, ast.Attribute):
            dangerous_attrs = ['__globals__', '__locals__', '__builtins__', '__code__', '__dict__']
            
            if node.attr in dangerous_attrs:
                self.violations.append(SecurityViolation(
                    violation_type="dangerous_attribute",
                    severity=SecurityRisk.HIGH,
                    description=f"Access to dangerous attribute: {node.attr}",
                    location=f"{filename}:{node.lineno}"
                ))
    
    def _check_dangerous_operations(self, node: ast.AST, filename: str):
        """Check for other dangerous operations"""
        # Check for dynamic code execution patterns
        if isinstance(node, ast.Call):
            if (isinstance(node.func, ast.Name) and 
                node.func.id in ['eval', 'exec', 'compile']):
                self.violations.append(SecurityViolation(
                    violation_type="code_injection",
                    severity=SecurityRisk.CRITICAL,
                    description=f"Dynamic code execution: {node.func.id}",
                    location=f"{filename}:{node.lineno}"
                ))
    
    def _check_exec_eval(self, node: ast.AST, filename: str):
        """Specifically check for eval/exec usage"""
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id in ['eval', 'exec']:
                self.violations.append(SecurityViolation(
                    violation_type="eval_exec",
                    severity=SecurityRisk.CRITICAL,
                    description=f"Use of {node.func.id}() - potential code injection",
                    location=f"{filename}:{node.lineno}"
                ))
    
    def _check_file_operations(self, node: ast.AST, filename: str):
        """Check file operation permissions"""
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id == 'open':
                # Check if writing is allowed
                if len(node.args) > 1:
                    if isinstance(node.args[1], ast.Constant) and 'w' in str(node.args[1].value):
                        if 'write' not in self.policy.allowed_file_operations:
                            self.violations.append(SecurityViolation(
                                violation_type="file_write_denied",
                                severity=SecurityRisk.MEDIUM,
                                description="File write operation not allowed by policy",
                                location=f"{filename}:{node.lineno}"
                            ))
    
    def _calculate_risk_level(self) -> SecurityRisk:
        """Calculate overall risk level based on violations"""
        if any(v.severity == SecurityRisk.CRITICAL for v in self.violations):
            return SecurityRisk.CRITICAL
        elif any(v.severity == SecurityRisk.HIGH for v in self.violations):
            return SecurityRisk.HIGH
        elif any(v.severity == SecurityRisk.MEDIUM for v in self.violations):
            return SecurityRisk.MEDIUM
        else:
            return SecurityRisk.LOW
    
    def _determine_capabilities(self) -> List[AgentCapability]:
        """Determine allowed capabilities based on code analysis"""
        capabilities = []
        
        # This is a simplified capability determination
        # In production, you'd have more sophisticated analysis
        
        violation_types = {v.violation_type for v in self.violations}
        
        if 'system_execution' not in violation_types:
            capabilities.append(AgentCapability.CODE_EXECUTION)
        
        if 'file_write_denied' not in violation_types:
            capabilities.append(AgentCapability.FILE_OPERATIONS)
        
        if self.policy.network_access:
            capabilities.append(AgentCapability.NETWORK_ACCESS)
        
        # Always allow basic capabilities if no critical violations
        critical_violations = [v for v in self.violations if v.severity == SecurityRisk.CRITICAL]
        if not critical_violations:
            capabilities.extend([
                AgentCapability.NATURAL_LANGUAGE,
                AgentCapability.DATA_ANALYSIS
            ])
        
        return capabilities
    
    def _generate_policy_recommendation(self) -> SecurityPolicy:
        """Generate recommended security policy based on analysis"""
        policy = SecurityPolicy()
        
        # Adjust policy based on violations
        if any(v.violation_type == 'system_execution' for v in self.violations):
            policy.subprocess_access = False
        
        if any(v.violation_type == 'file_write_denied' for v in self.violations):
            policy.allowed_file_operations = {'read', 'list'}
        
        # Set resource limits based on complexity
        ast_node_count = len(self.violations) * 10  # Rough complexity estimate
        if ast_node_count > 1000:
            policy.max_memory_mb = 256
            policy.max_cpu_seconds = 15
        
        return policy


class SecurityManager:
    """
    Production-ready security manager for agent marketplace
    Handles validation, sandboxing, and access control
    """
    
    def __init__(self, 
                 default_policy: SecurityPolicy = None,
                 signature_key: bytes = None):
        """Initialize security manager"""
        self.default_policy = default_policy or SecurityPolicy()
        self.signature_key = signature_key or os.urandom(32)
        self.policies: Dict[str, SecurityPolicy] = {}
        self.audit_history: List[SecurityAuditResult] = []
        
        # Security levels mapping
        self.level_policies = {
            SecurityLevel.UNRESTRICTED: SecurityPolicy(
                banned_modules=set(),
                banned_functions=set(),
                max_memory_mb=2048,
                max_cpu_seconds=300,
                network_access=True,
                subprocess_access=True,
                require_signature=False
            ),
            SecurityLevel.TRUSTED: SecurityPolicy(
                banned_modules={'ctypes', 'subprocess'},
                max_memory_mb=1024,
                max_cpu_seconds=120,
                network_access=True,
                subprocess_access=False,
                require_signature=True
            ),
            SecurityLevel.STANDARD: self.default_policy,
            SecurityLevel.RESTRICTED: SecurityPolicy(
                banned_modules={'ctypes', 'subprocess', 'socket', 'urllib', 'requests'},
                max_memory_mb=256,
                max_cpu_seconds=30,
                network_access=False,
                subprocess_access=False,
                file_system_access=False,
                require_signature=True
            ),
            SecurityLevel.QUARANTINED: SecurityPolicy(
                banned_modules={'ctypes', 'subprocess', 'socket', 'urllib', 'requests', 'os', 'sys'},
                max_memory_mb=128,
                max_cpu_seconds=10,
                network_access=False,
                subprocess_access=False,
                file_system_access=False,
                allowed_file_operations={'read'},
                require_signature=True
            )
        }
    
    async def audit_agent(self, 
                         agent_path: Union[str, Path],
                         metadata: AgentMetadata = None,
                         security_level: SecurityLevel = SecurityLevel.STANDARD) -> ToolResponse:
        """
        Comprehensive security audit of agent
        
        Args:
            agent_path: Path to agent file or directory
            metadata: Agent metadata for validation
            security_level: Required security level
            
        Returns:
            ToolResponse with audit results
        """
        try:
            agent_path = Path(agent_path)
            policy = self.level_policies[security_level]
            
            if agent_path.is_file():
                # Single file audit
                audit_result = await self._audit_file(agent_path, policy)
            elif agent_path.is_dir():
                # Directory audit
                audit_result = await self._audit_directory(agent_path, policy)
            else:
                return ToolResponse(
                    success=False,
                    data={},
                    error=f"Agent path does not exist: {agent_path}"
                )
            
            # Store audit history
            self.audit_history.append(audit_result)
            
            # Validate against metadata if provided
            if metadata:
                validation_result = self._validate_metadata_consistency(audit_result, metadata)
                if not validation_result.success:
                    return validation_result
            
            return ToolResponse(
                success=audit_result.passed,
                data={
                    "audit_result": asdict(audit_result),
                    "security_level": security_level.value
                },
                metadata={"operation": "audit_agent"}
            )
            
        except Exception as e:
            return ToolResponse(
                success=False,
                data={},
                error=f"Security audit failed: {str(e)}"
            )
    
    async def _audit_file(self, file_path: Path, policy: SecurityPolicy) -> SecurityAuditResult:
        """Audit single Python file"""
        try:
            code = file_path.read_text(encoding='utf-8')
            validator = SecurityValidator(policy)
            return validator.validate_code(code, str(file_path))
        except Exception as e:
            return SecurityAuditResult(
                passed=False,
                risk_level=SecurityRisk.CRITICAL,
                violations=[SecurityViolation(
                    violation_type="file_read_error",
                    severity=SecurityRisk.CRITICAL,
                    description=f"Cannot read file: {e}",
                    location=str(file_path)
                )],
                allowed_capabilities=[],
                recommended_policy=SecurityPolicy()
            )
    
    async def _audit_directory(self, dir_path: Path, policy: SecurityPolicy) -> SecurityAuditResult:
        """Audit all Python files in directory"""
        all_violations = []
        max_risk = SecurityRisk.LOW
        all_capabilities = set()
        
        python_files = list(dir_path.rglob("*.py"))
        if not python_files:
            return SecurityAuditResult(
                passed=False,
                risk_level=SecurityRisk.HIGH,
                violations=[SecurityViolation(
                    violation_type="no_python_files",
                    severity=SecurityRisk.HIGH,
                    description="No Python files found in agent directory",
                    location=str(dir_path)
                )],
                allowed_capabilities=[],
                recommended_policy=policy
            )
        
        for py_file in python_files:
            file_result = await self._audit_file(py_file, policy)
            all_violations.extend(file_result.violations)
            all_capabilities.update(file_result.allowed_capabilities)
            
            # Track highest risk level
            if file_result.risk_level.value == "critical":
                max_risk = SecurityRisk.CRITICAL
            elif file_result.risk_level.value == "high" and max_risk != SecurityRisk.CRITICAL:
                max_risk = SecurityRisk.HIGH
            elif file_result.risk_level.value == "medium" and max_risk not in [SecurityRisk.CRITICAL, SecurityRisk.HIGH]:
                max_risk = SecurityRisk.MEDIUM
        
        return SecurityAuditResult(
            passed=max_risk not in [SecurityRisk.HIGH, SecurityRisk.CRITICAL],
            risk_level=max_risk,
            violations=all_violations,
            allowed_capabilities=list(all_capabilities),
            recommended_policy=policy
        )
    
    def _validate_metadata_consistency(self, 
                                     audit_result: SecurityAuditResult, 
                                     metadata: AgentMetadata) -> ToolResponse:
        """Validate that audit results match declared metadata"""
        try:
            # Check capabilities consistency
            declared_caps = set(metadata.capabilities)
            allowed_caps = set(audit_result.allowed_capabilities)
            
            undeclared_caps = declared_caps - allowed_caps
            if undeclared_caps:
                return ToolResponse(
                    success=False,
                    data={
                        "undeclared_capabilities": [cap.value for cap in undeclared_caps]
                    },
                    error=f"Agent claims capabilities not supported by code: {undeclared_caps}"
                )
            
            # Check for high-risk violations if agent claims to be safe
            if audit_result.risk_level in [SecurityRisk.HIGH, SecurityRisk.CRITICAL]:
                return ToolResponse(
                    success=False,
                    data={
                        "risk_level": audit_result.risk_level.value,
                        "violations": [asdict(v) for v in audit_result.violations]
                    },
                    error="Agent has high security risk but metadata doesn't reflect this"
                )
            
            return ToolResponse(success=True, data={})
            
        except Exception as e:
            return ToolResponse(
                success=False,
                data={},
                error=f"Metadata validation failed: {str(e)}"
            )
    
    def create_sandbox(self, 
                      security_level: SecurityLevel = SecurityLevel.STANDARD) -> 'SandboxContext':
        """Create execution sandbox for agent"""
        policy = self.level_policies[security_level]
        return SandboxContext(policy)
    
    def sign_agent(self, agent_path: Union[str, Path]) -> ToolResponse:
        """Create signature for agent"""
        try:
            agent_path = Path(agent_path)
            
            if agent_path.is_file():
                content = agent_path.read_bytes()
            elif agent_path.is_dir():
                # Create tar archive for directory
                with tempfile.NamedTemporaryFile(suffix='.tar') as tmp:
                    with tarfile.open(tmp.name, 'w') as tar:
                        tar.add(agent_path, arcname='.')
                    tmp.seek(0)
                    content = tmp.read()
            else:
                return ToolResponse(
                    success=False,
                    data={},
                    error=f"Agent path does not exist: {agent_path}"
                )
            
            # Create signature
            signature = hmac.new(self.signature_key, content, hashlib.sha256).hexdigest()
            
            return ToolResponse(
                success=True,
                data={
                    "signature": signature,
                    "algorithm": "HMAC-SHA256",
                    "size": len(content)
                },
                metadata={"operation": "sign_agent"}
            )
            
        except Exception as e:
            return ToolResponse(
                success=False,
                data={},
                error=f"Agent signing failed: {str(e)}"
            )
    
    def verify_signature(self, 
                        agent_path: Union[str, Path], 
                        signature: str) -> ToolResponse:
        """Verify agent signature"""
        try:
            sign_result = self.sign_agent(agent_path)
            if not sign_result.success:
                return sign_result
            
            expected_signature = sign_result.data["signature"]
            is_valid = hmac.compare_digest(signature, expected_signature)
            
            return ToolResponse(
                success=True,
                data={
                    "signature_valid": is_valid,
                    "signature": signature,
                    "expected": expected_signature
                },
                metadata={"operation": "verify_signature"}
            )
            
        except Exception as e:
            return ToolResponse(
                success=False,
                data={},
                error=f"Signature verification failed: {str(e)}"
            )
    
    async def get_security_report(self, agent_id: str = None) -> ToolResponse:
        """Generate security report"""
        try:
            if agent_id:
                # Report for specific agent
                agent_audits = [a for a in self.audit_history if agent_id in str(a.checksum)]
                if not agent_audits:
                    return ToolResponse(
                        success=False,
                        data={},
                        error=f"No audit history found for agent {agent_id}"
                    )
                audits = agent_audits
            else:
                # Overall security report
                audits = self.audit_history
            
            # Generate statistics
            total_audits = len(audits)
            passed_audits = len([a for a in audits if a.passed])
            
            risk_counts = {}
            for risk in SecurityRisk:
                risk_counts[risk.value] = len([a for a in audits if a.risk_level == risk])
            
            violation_types = {}
            for audit in audits:
                for violation in audit.violations:
                    vtype = violation.violation_type
                    if vtype not in violation_types:
                        violation_types[vtype] = 0
                    violation_types[vtype] += 1
            
            report = {
                "total_audits": total_audits,
                "passed_audits": passed_audits,
                "pass_rate": passed_audits / total_audits if total_audits > 0 else 0,
                "risk_distribution": risk_counts,
                "common_violations": dict(sorted(violation_types.items(), 
                                               key=lambda x: x[1], reverse=True)[:10]),
                "recent_audits": [asdict(a) for a in audits[-5:]]  # Last 5 audits
            }
            
            return ToolResponse(
                success=True,
                data=report,
                metadata={"operation": "security_report"}
            )
            
        except Exception as e:
            return ToolResponse(
                success=False,
                data={},
                error=f"Security report generation failed: {str(e)}"
            )


class SandboxContext:
    """
    Execution sandbox context manager
    Provides resource limits and access control
    """
    
    def __init__(self, policy: SecurityPolicy):
        self.policy = policy
        self.original_limits = {}
        self.temp_dirs = []
    
    def __enter__(self):
        """Enter sandbox context"""
        self._apply_resource_limits()
        self._setup_restricted_environment()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit sandbox context"""
        self._restore_environment()
        self._cleanup_temp_dirs()
    
    def _apply_resource_limits(self):
        """Apply resource limits"""
        try:
            # Memory limit
            if self.policy.max_memory_mb > 0:
                memory_limit = self.policy.max_memory_mb * 1024 * 1024
                resource.setrlimit(resource.RLIMIT_AS, (memory_limit, memory_limit))
            
            # CPU time limit  
            if self.policy.max_cpu_seconds > 0:
                resource.setrlimit(resource.RLIMIT_CPU, 
                                 (self.policy.max_cpu_seconds, self.policy.max_cpu_seconds))
        except (OSError, resource.error) as e:
            print(f"Warning: Could not apply resource limits: {e}")
    
    def _setup_restricted_environment(self):
        """Setup restricted execution environment"""
        # Store original builtins
        import builtins
        self.original_builtins = {}
        
        # Restrict dangerous builtins
        dangerous_builtins = ['eval', 'exec', 'compile', '__import__', 'open']
        for builtin in dangerous_builtins:
            if hasattr(builtins, builtin):
                self.original_builtins[builtin] = getattr(builtins, builtin)
                if builtin in self.policy.banned_functions:
                    setattr(builtins, builtin, self._create_restricted_function(builtin))
    
    def _create_restricted_function(self, func_name: str):
        """Create restricted version of function"""
        def restricted_func(*args, **kwargs):
            raise PermissionError(f"Function {func_name} is not allowed in sandbox")
        return restricted_func
    
    def _restore_environment(self):
        """Restore original environment"""
        import builtins
        
        # Restore original builtins
        for name, original_func in self.original_builtins.items():
            setattr(builtins, name, original_func)
    
    def _cleanup_temp_dirs(self):
        """Cleanup temporary directories"""
        for temp_dir in self.temp_dirs:
            try:
                import shutil
                shutil.rmtree(temp_dir)
            except Exception as e:
                print(f"Warning: Could not cleanup temp dir {temp_dir}: {e}")
    
    def create_temp_workspace(self) -> Path:
        """Create temporary workspace for agent"""
        temp_dir = Path(tempfile.mkdtemp(prefix="agent_sandbox_"))
        self.temp_dirs.append(temp_dir)
        return temp_dir
    
    @contextmanager
    def timeout(self, seconds: int = None):
        """Context manager for operation timeout"""
        timeout_seconds = seconds or self.policy.max_cpu_seconds
        
        def timeout_handler(signum, frame):
            raise TimeoutError(f"Operation timed out after {timeout_seconds} seconds")
        
        # Set up timeout
        old_handler = signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(timeout_seconds)
        
        try:
            yield
        finally:
            # Restore original handler
            signal.alarm(0)
            signal.signal(signal.SIGALRM, old_handler)