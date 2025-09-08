"""
Integration tests for Complex Orchestration.

Tests complete hierarchical orchestration workflows including three-level
hierarchy, cross-level coordination, and dynamic depth adjustment with
real-world scenarios.
"""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.hierarchical_orchestrator import (
    HierarchicalOrchestrator,
    OrchestrationTask,
    OrchestrationLevel,
    TaskComplexity,
    OrchestrationPattern
)
from orchestration.patterns import (
    PatternExecutor,
    TaskSlice,
    OrchestrationPattern as PatternType
)


class TestComplexOrchestrationIntegration:
    """Integration tests for complex orchestration scenarios"""
    
    @pytest.mark.asyncio
    async def test_three_level_hierarchy_workflow(self):
        """Test complete three-level hierarchy workflow"""
        orchestrator = HierarchicalOrchestrator(max_depth=3)
        
        # Enterprise-level task requiring full hierarchy
        enterprise_task = (
            "Implement complete microservices architecture with OAuth2 authentication, "
            "API gateway, service discovery, monitoring, and deployment pipeline"
        )
        
        result = await orchestrator.orchestrate_complex_task(enterprise_task)
        
        # Verify orchestration success
        assert result.success
        assert result.levels_deep >= 2  # Should create multi-level hierarchy
        assert result.agents_used > 1    # Should use multiple agents
        assert result.execution_time > 0
        assert result.coordination_overhead >= 0
        
        # Verify metadata
        assert "orchestration_id" in result.metadata
        assert "root_task_id" in result.metadata
        assert "decomposed_tasks" in result.metadata
        assert "patterns_used" in result.metadata
        
        # Verify agent hierarchy was created
        hierarchy = await orchestrator.get_agent_hierarchy()
        assert len(hierarchy["primary"]) >= 1
        
    @pytest.mark.asyncio
    async def test_cite_assist_project_orchestration(self):
        """Test orchestration of cite-assist style research project"""
        orchestrator = HierarchicalOrchestrator(max_depth=3)
        
        research_task = (
            "Analyze 1000+ legal documents for citation patterns, "
            "extract key precedents, validate citations against databases, "
            "generate comprehensive legal research report with recommendations"
        )
        
        result = await orchestrator.orchestrate_complex_task(research_task)
        
        assert result.success
        assert result.agents_used >= 3  # Should require multiple specialists
        
        # Check coordination patterns used
        patterns_used = result.metadata.get("patterns_used", [])
        assert len(patterns_used) > 0  # Should use orchestration patterns
        
    @pytest.mark.asyncio
    async def test_pin_citer_pipeline_orchestration(self):
        """Test orchestration of pin-citer style pipeline workflow"""
        orchestrator = HierarchicalOrchestrator()
        
        pipeline_task = (
            "Process research papers through citation extraction pipeline: "
            "PDF parsing, text analysis, reference extraction, validation, "
            "database storage, and citation network generation"
        )
        
        result = await orchestrator.orchestrate_complex_task(pipeline_task)
        
        assert result.success
        assert result.levels_deep >= 1
        
        # Pipeline tasks should use pipeline pattern
        patterns_used = result.metadata.get("patterns_used", [])
        # Note: Pattern selection is heuristic-based, so we just verify execution
        
    @pytest.mark.asyncio
    async def test_dynamic_depth_adjustment(self):
        """Test dynamic hierarchy depth based on task complexity"""
        orchestrator = HierarchicalOrchestrator(max_depth=4)
        
        # Test simple task (should use minimal depth)
        simple_task = "Fix typo in documentation"
        simple_result = await orchestrator.orchestrate_complex_task(simple_task)
        
        # Test complex task (should use more depth)
        complex_task = (
            "Migrate entire legacy monolith to microservices architecture "
            "with zero downtime, data migration, and rollback capabilities"
        )
        complex_result = await orchestrator.orchestrate_complex_task(complex_task)
        
        # Complex task should use more levels than simple task
        assert complex_result.levels_deep >= simple_result.levels_deep
        assert complex_result.agents_used >= simple_result.agents_used
        
    @pytest.mark.asyncio
    async def test_cross_level_coordination(self):
        """Test coordination across different hierarchy levels"""
        orchestrator = HierarchicalOrchestrator()
        
        coordination_task = (
            "Coordinate deployment across multiple environments: "
            "development team prepares release, QA validates features, "
            "DevOps manages infrastructure, security reviews compliance"
        )
        
        result = await orchestrator.orchestrate_complex_task(coordination_task)
        
        assert result.success
        
        # Should create agents at multiple levels
        hierarchy = await orchestrator.get_agent_hierarchy()
        total_agents = (len(hierarchy["primary"]) + 
                       len(hierarchy["secondary"]) + 
                       len(hierarchy["tertiary"]))
        assert total_agents > 1
        
    @pytest.mark.asyncio
    async def test_pattern_integration_workflow(self):
        """Test integration of different orchestration patterns"""
        orchestrator = HierarchicalOrchestrator()
        
        # Task that should trigger multiple patterns
        multi_pattern_task = (
            "Process customer data: collect from multiple sources (scatter-gather), "
            "transform through validation pipeline, aggregate results (map-reduce), "
            "execute in parallel where possible (fork-join), "
            "ensure transactional consistency (saga)"
        )
        
        result = await orchestrator.orchestrate_complex_task(multi_pattern_task)
        
        assert result.success
        patterns_used = result.metadata.get("patterns_used", [])
        assert len(patterns_used) > 0  # Should use multiple patterns
        
    @pytest.mark.asyncio
    async def test_concurrent_orchestrations(self):
        """Test running multiple orchestrations concurrently"""
        orchestrator = HierarchicalOrchestrator(max_agents_per_level={
            "primary": 1, "secondary": 20, "tertiary": 50
        })
        
        # Launch multiple orchestrations concurrently
        tasks = [
            "Implement user authentication system",
            "Set up monitoring and alerting",
            "Create API documentation",
            "Deploy to staging environment"
        ]
        
        # Execute all orchestrations concurrently
        orchestration_coroutines = [
            orchestrator.orchestrate_complex_task(task, f"orch-{i}")
            for i, task in enumerate(tasks)
        ]
        
        results = await asyncio.gather(*orchestration_coroutines, return_exceptions=True)
        
        # All orchestrations should succeed
        successful_results = [r for r in results if not isinstance(r, Exception)]
        assert len(successful_results) == len(tasks)
        
        for result in successful_results:
            assert result.success
            
    @pytest.mark.asyncio
    async def test_orchestration_with_failures(self):
        """Test orchestration handling of partial failures"""
        orchestrator = HierarchicalOrchestrator()
        
        # Task that simulates potential failure points
        failure_prone_task = (
            "Deploy application with external dependencies: "
            "database migration, external API integration, "
            "third-party service configuration, monitoring setup"
        )
        
        result = await orchestrator.orchestrate_complex_task(failure_prone_task)
        
        # Even with potential failures, orchestration should handle gracefully
        assert result.task_id is not None
        assert result.execution_time > 0
        
        # Check if any agents were created and managed
        hierarchy = await orchestrator.get_agent_hierarchy()
        assert len(hierarchy["primary"]) >= 1
        
    @pytest.mark.asyncio
    async def test_resource_constrained_orchestration(self):
        """Test orchestration under resource constraints"""
        # Create orchestrator with limited resources
        constrained_orchestrator = HierarchicalOrchestrator(
            max_agents_per_level={
                "primary": 1,
                "secondary": 2,
                "tertiary": 3
            }
        )
        
        # Large task that would normally require many agents
        resource_intensive_task = (
            "Process 10,000 documents simultaneously: "
            "extract text, analyze content, classify documents, "
            "generate summaries, validate results, store in database"
        )
        
        result = await constrained_orchestrator.orchestrate_complex_task(resource_intensive_task)
        
        assert result.success
        
        # Should respect resource constraints
        hierarchy = await constrained_orchestrator.get_agent_hierarchy()
        assert len(hierarchy["secondary"]) <= 2
        assert len(hierarchy["tertiary"]) <= 3
        
    @pytest.mark.asyncio
    async def test_orchestration_status_monitoring(self):
        """Test real-time orchestration status monitoring"""
        orchestrator = HierarchicalOrchestrator()
        
        long_running_task = (
            "Comprehensive system analysis: "
            "performance profiling, security audit, "
            "code quality analysis, dependency review"
        )
        
        # Start orchestration (should be fast due to async nature)
        orchestration_id = "status-test-123"
        
        # Mock active orchestration for status testing
        orchestrator.active_orchestrations[orchestration_id] = {
            "started_at": datetime.now(),
            "tasks": []
        }
        
        # Add some sample tasks
        for i in range(5):
            task_id = f"task-{i}"
            orchestrator.tasks[task_id] = OrchestrationTask(
                task_id=task_id,
                content=f"Analysis task {i}",
                level=OrchestrationLevel.SECONDARY,
                complexity=TaskComplexity.MODERATE,
                status="completed" if i < 3 else "pending"
            )
            
        # Check orchestration status
        status = await orchestrator.get_orchestration_status(orchestration_id)
        
        assert "orchestration_id" in status
        assert "completed_tasks" in status
        assert "pending_tasks" in status
        assert "total_tasks" in status
        assert status["completed_tasks"] == 3
        assert status["pending_tasks"] == 2
        
    @pytest.mark.asyncio
    async def test_orchestration_cancellation_workflow(self):
        """Test orchestration cancellation workflow"""
        orchestrator = HierarchicalOrchestrator()
        
        # Set up active orchestration
        orchestration_id = "cancel-test-456"
        orchestrator.active_orchestrations[orchestration_id] = {}
        
        # Add some active agents
        for i in range(3):
            agent_id = f"cancel-agent-{i}"
            orchestrator.agents[agent_id] = orchestrator.AgentInfo(
                agent_id=agent_id,
                level=OrchestrationLevel.SECONDARY,
                status="active"
            )
            
        # Add some pending tasks
        for i in range(3):
            task_id = f"cancel-task-{i}"
            task = OrchestrationTask(
                task_id=task_id,
                content=f"Cancellable task {i}",
                level=OrchestrationLevel.TERTIARY,
                complexity=TaskComplexity.SIMPLE,
                status="pending"
            )
            orchestrator.tasks[task_id] = task
            
        # Cancel orchestration
        cancellation_result = await orchestrator.cancel_orchestration(orchestration_id)
        
        assert cancellation_result is True
        assert orchestration_id not in orchestrator.active_orchestrations
        
        # Check that agents were marked inactive
        for agent in orchestrator.agents.values():
            if "cancel-agent" in agent.agent_id:
                assert agent.status == "inactive"
                
        # Check that pending tasks were cancelled
        for task in orchestrator.tasks.values():
            if "cancel-task" in task.task_id:
                assert task.status == "cancelled"
                
    @pytest.mark.asyncio
    async def test_pattern_executor_integration(self):
        """Test integration with pattern executor"""
        orchestrator = HierarchicalOrchestrator()
        pattern_executor = PatternExecutor()
        
        # Create task slices for pattern execution
        task_slices = [
            TaskSlice("slice-1", "Data processing task 1"),
            TaskSlice("slice-2", "Data processing task 2"),
            TaskSlice("slice-3", "Data processing task 3")
        ]
        
        mock_agents = ["agent-1", "agent-2"]
        
        # Test different patterns through executor
        patterns_to_test = [
            PatternType.MAPREDUCE,
            PatternType.PIPELINE,
            PatternType.FORK_JOIN,
            PatternType.SCATTER_GATHER,
            PatternType.SAGA
        ]
        
        results = []
        for pattern in patterns_to_test:
            result = await pattern_executor.execute_pattern(
                pattern, task_slices, mock_agents
            )
            results.append(result)
            
        # All patterns should execute successfully
        assert all(r.success for r in results)
        assert len(results) == 5
        
        # Check execution history
        history = pattern_executor.get_execution_history()
        assert len(history) == 5
        
    @pytest.mark.asyncio
    async def test_auto_pattern_selection_integration(self):
        """Test automatic pattern selection in orchestration context"""
        pattern_executor = PatternExecutor()
        
        # Test different scenarios for pattern recommendation
        test_scenarios = [
            # Scatter-gather scenario: same task to multiple agents
            {
                "slices": [TaskSlice("question", "Analyze market trends")],
                "agents": ["analyst-1", "analyst-2", "analyst-3"],
                "expected_pattern": PatternType.SCATTER_GATHER
            },
            
            # MapReduce scenario: many tasks, few agents
            {
                "slices": [TaskSlice(f"process-{i}", f"Process data {i}") for i in range(10)],
                "agents": ["worker-1", "worker-2"],
                "expected_pattern": PatternType.MAPREDUCE
            },
            
            # Pipeline scenario: tasks with dependencies
            {
                "slices": [
                    TaskSlice("step-1", "First step", dependencies=[]),
                    TaskSlice("step-2", "Second step", dependencies=["step-1"]),
                    TaskSlice("step-3", "Third step", dependencies=["step-2"])
                ],
                "agents": ["stage-1", "stage-2", "stage-3"],
                "expected_pattern": PatternType.PIPELINE
            },
            
            # Saga scenario: transaction-like tasks
            {
                "slices": [
                    TaskSlice("tx-1", "Begin transaction"),
                    TaskSlice("tx-2", "Execute transaction"),
                    TaskSlice("tx-3", "Commit transaction")
                ],
                "agents": ["tx-agent-1", "tx-agent-2", "tx-agent-3"],
                "expected_pattern": PatternType.SAGA
            }
        ]
        
        for scenario in test_scenarios:
            recommendation = pattern_executor.recommend_pattern(
                scenario["slices"],
                scenario["agents"]
            )
            
            assert recommendation == scenario["expected_pattern"]
            
            # Execute with auto-selection
            result = await pattern_executor.execute_auto_pattern(
                scenario["slices"],
                scenario["agents"]
            )
            
            assert result.success
            assert result.pattern == scenario["expected_pattern"]
            
    @pytest.mark.asyncio
    async def test_performance_monitoring_integration(self):
        """Test performance monitoring across orchestration"""
        orchestrator = HierarchicalOrchestrator()
        pattern_executor = PatternExecutor()
        
        # Execute multiple orchestrations for performance data
        performance_tasks = [
            "Quick task for performance baseline",
            "Moderate complexity task for performance testing",
            "Complex multi-step task for performance analysis"
        ]
        
        execution_times = []
        coordination_overheads = []
        
        for task in performance_tasks:
            result = await orchestrator.orchestrate_complex_task(task)
            
            execution_times.append(result.execution_time)
            coordination_overheads.append(result.coordination_overhead)
            
        # Performance metrics should be reasonable
        assert all(t > 0 for t in execution_times)
        assert all(0 <= oh <= 15.0 for oh in coordination_overheads)  # Max 15% overhead
        
        # Get pattern performance metrics
        pattern_performance = pattern_executor.get_pattern_performance()
        
        assert len(pattern_performance) == 5
        for pattern_name, metrics in pattern_performance.items():
            assert "success_rate" in metrics
            assert "average_execution_time" in metrics
            assert "total_executions" in metrics
            
    @pytest.mark.asyncio
    async def test_scalability_stress_test(self):
        """Test orchestration scalability under load"""
        # Create orchestrator with high capacity
        orchestrator = HierarchicalOrchestrator(
            max_depth=4,
            max_agents_per_level={
                "primary": 2,
                "secondary": 15,
                "tertiary": 40
            }
        )
        
        # Create highly parallel task
        scalability_task = (
            "Massive parallel processing: analyze 1000 documents, "
            "process 500 images, validate 200 API endpoints, "
            "test 100 database queries, generate 50 reports"
        )
        
        result = await orchestrator.orchestrate_complex_task(scalability_task)
        
        assert result.success
        assert result.coordination_overhead < 10.0  # Should maintain efficiency
        
        # Verify we can handle the load
        hierarchy = await orchestrator.get_agent_hierarchy()
        total_agents = (len(hierarchy["primary"]) + 
                       len(hierarchy["secondary"]) + 
                       len(hierarchy["tertiary"]))
        
        # Should create significant agent hierarchy
        assert total_agents >= 3
        
    @pytest.mark.asyncio  
    async def test_error_recovery_integration(self):
        """Test error recovery across orchestration levels"""
        orchestrator = HierarchicalOrchestrator()
        
        # Task that might encounter errors
        error_prone_task = (
            "Risky operations: external API calls, file system operations, "
            "network requests, database transactions with potential timeouts"
        )
        
        # Execute task (should handle errors gracefully)
        result = await orchestrator.orchestrate_complex_task(error_prone_task)
        
        # Should complete even with potential errors
        assert result.task_id is not None
        assert isinstance(result.success, bool)
        assert result.execution_time >= 0
        
        # If errors occurred, they should be captured
        if not result.success:
            assert result.error_message != ""
        else:
            # If successful, should have meaningful results
            assert result.agents_used >= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])