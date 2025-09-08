"""
Integration tests for Context Bundles with real agent handoff scenarios
Tests perfect handoffs between cite-assist, pin-citer, and other agents
"""

import pytest
import asyncio
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, patch

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from core.context_bundles import (
    ContextBundleManager,
    BundleEnabledAgent,
    ActionType,
    ContextBundle
)
from core.base import ToolResponse
from core.autonomous import AutonomousImplementationAgent
from core.github_integration import GitHubIntegrationAgent
from core.handoff import HandoffAgent


class CitationAnalysisAgent(BundleEnabledAgent):
    """Test agent simulating cite-assist citation analysis"""
    
    async def _execute_task_impl(self, task: str) -> ToolResponse:
        """Simulate citation analysis work"""
        # Simulate analysis work
        self.bundle_manager.update_state({
            "analysis_phase": "analyzing_citations",
            "documents_processed": 25,
            "citations_found": 150,
            "adequacy_scores": [0.8, 0.9, 0.7, 0.85, 0.92] * 30
        })
        
        self.bundle_manager.create_checkpoint("citation_analysis", 0.6)
        
        return ToolResponse(
            success=True,
            data={
                "citations_analyzed": 150,
                "average_adequacy": 0.844,
                "analysis_summary": "Citation analysis completed with high adequacy scores"
            }
        )


class PDFProcessingAgent(BundleEnabledAgent):
    """Test agent simulating pin-citer PDF processing"""
    
    async def _execute_task_impl(self, task: str) -> ToolResponse:
        """Simulate PDF processing work"""
        # Simulate processing work
        self.bundle_manager.update_state({
            "processing_phase": "extracting_citations",
            "pdfs_processed": 12,
            "pages_processed": 340,
            "citations_extracted": 89,
            "validation_results": {"valid": 82, "invalid": 7}
        })
        
        self.bundle_manager.create_checkpoint("pdf_extraction", 0.8)
        
        return ToolResponse(
            success=True,
            data={
                "pdfs_processed": 12,
                "citations_extracted": 89,
                "validation_rate": 0.921,
                "processing_summary": "PDF processing completed successfully"
            }
        )


class DocumentationAgent(BundleEnabledAgent):
    """Test agent for documentation tasks"""
    
    async def _execute_task_impl(self, task: str) -> ToolResponse:
        """Simulate documentation work"""
        # Simulate documentation work
        self.bundle_manager.update_state({
            "documentation_phase": "generating_reports",
            "sections_completed": 8,
            "diagrams_created": 3,
            "examples_added": 15
        })
        
        self.bundle_manager.create_checkpoint("documentation", 0.9)
        
        return ToolResponse(
            success=True,
            data={
                "documentation_created": True,
                "sections": 8,
                "completeness": 0.9,
                "doc_summary": "Comprehensive documentation generated"
            }
        )


class TestCiteAssistHandoffs:
    """Test handoffs in cite-assist legal research workflows"""
    
    @pytest.mark.asyncio
    async def test_legal_research_to_analysis_handoff(self):
        """Test handoff from legal research to citation analysis"""
        # Create research agent with legal research data
        research_agent = BundleEnabledAgent("legal_researcher")
        
        # Simulate legal research work
        research_agent.bundle_manager.update_state({
            "research_topic": "Supreme Court constitutional law precedents",
            "cases_found": 45,
            "statutes_identified": 12,
            "research_phase": "completed",
            "zotero_items": [f"case_{i}" for i in range(45)],
            "search_queries": [
                "constitutional law AND Supreme Court",
                "precedent AND constitutional interpretation",
                "judicial review AND constitutional rights"
            ]
        })
        
        research_agent.bundle_manager.create_checkpoint("research_complete", 1.0)
        
        # Create handoff to analysis agent
        analysis_agent = CitationAnalysisAgent("citation_analyzer")
        
        handoff_data = {
            "work_completed": "Legal research phase completed",
            "findings": f"Found {45} relevant cases and {12} statutes",
            "next_phase": "Citation adequacy analysis",
            "data_location": "zotero_items in state",
            "priority_cases": ["case_1", "case_15", "case_32"]
        }
        
        handoff_session = await research_agent.create_handoff("citation_analyzer", handoff_data)
        
        # Analysis agent receives handoff
        success = await analysis_agent.receive_handoff(handoff_session)
        assert success
        
        # Verify perfect handoff
        assert analysis_agent.workflow_data["research_topic"] == "Supreme Court constitutional law precedents"
        assert analysis_agent.workflow_data["cases_found"] == 45
        assert analysis_agent.workflow_data["statutes_identified"] == 12
        assert len(analysis_agent.workflow_data["zotero_items"]) == 45
        
        # Continue work with full context
        analysis_result = await analysis_agent.execute_task("Analyze citation adequacy for found cases")
        
        assert analysis_result.success
        assert "citations_analyzed" in analysis_result.data
        
        # Verify continuity in bundle
        final_stats = analysis_agent.bundle_manager.get_bundle_stats()
        assert final_stats["total_actions"] >= 5  # Research actions + analysis actions
        assert "handoff" in analysis_agent.bundle_manager.metadata.tags
    
    @pytest.mark.asyncio
    async def test_analysis_to_documentation_handoff(self):
        """Test handoff from citation analysis to documentation"""
        # Set up analysis agent with completed analysis
        analysis_agent = CitationAnalysisAgent("citation_analyzer")
        
        # Execute analysis task
        await analysis_agent.execute_task("Analyze legal citations")
        
        # Add analysis results
        analysis_agent.bundle_manager.update_state({
            "analysis_complete": True,
            "citation_scores": {
                "average_adequacy": 0.844,
                "total_citations": 150,
                "high_quality": 127,
                "needs_improvement": 23
            },
            "recommendations": [
                "Strengthen citations for constitutional arguments",
                "Add more recent Supreme Court cases",
                "Include circuit court perspectives"
            ]
        })
        
        # Create handoff to documentation agent
        doc_agent = DocumentationAgent("documenter")
        
        handoff_data = {
            "work_completed": "Citation analysis completed",
            "analysis_summary": "Analyzed 150 citations with 84.4% average adequacy",
            "next_phase": "Generate comprehensive analysis report",
            "key_findings": "127 high-quality citations, 23 need improvement",
            "recommendations_ready": True
        }
        
        handoff_session = await analysis_agent.create_handoff("documenter", handoff_data)
        
        # Documentation agent receives handoff
        success = await doc_agent.receive_handoff(handoff_session)
        assert success
        
        # Verify complete context transfer
        assert doc_agent.workflow_data["analysis_complete"] is True
        assert doc_agent.workflow_data["citation_scores"]["average_adequacy"] == 0.844
        assert doc_agent.workflow_data["citation_scores"]["total_citations"] == 150
        assert len(doc_agent.workflow_data["recommendations"]) == 3
        
        # Continue with documentation
        doc_result = await doc_agent.execute_task("Generate legal analysis report")
        
        assert doc_result.success
        assert doc_result.data["documentation_created"] is True
        
        # Verify end-to-end context preservation
        handoff_summary = doc_agent.get_handoff_summary()
        assert handoff_summary["agent_type"] == "DocumentationAgent"
        assert handoff_summary["total_actions"] >= 6  # Analysis + documentation actions


class TestPinCiterHandoffs:
    """Test handoffs in pin-citer PDF processing workflows"""
    
    @pytest.mark.asyncio
    async def test_pdf_processing_to_validation_handoff(self):
        """Test handoff from PDF processing to validation"""
        # Create PDF processing agent
        pdf_agent = PDFProcessingAgent("pdf_processor")
        
        # Execute PDF processing
        await pdf_agent.execute_task("Process legal PDF corpus")
        
        # Add processing results
        pdf_agent.bundle_manager.update_state({
            "processing_complete": True,
            "pdf_metadata": {
                "total_pdfs": 12,
                "total_pages": 340,
                "file_sizes": [2.5, 3.1, 1.8] * 4,  # MB
                "processing_time": 145.7  # seconds
            },
            "extraction_results": {
                "citations_found": 89,
                "references_found": 156,
                "footnotes_found": 203
            },
            "files_processed": [
                "legal_brief_1.pdf",
                "supreme_court_opinion.pdf", 
                "circuit_court_decision.pdf"
            ]
        })
        
        # Create validation agent (simulated)
        validation_agent = BundleEnabledAgent("validator")
        
        # Create handoff
        handoff_data = {
            "work_completed": "PDF processing and citation extraction completed",
            "processing_summary": f"Processed {12} PDFs, extracted {89} citations",
            "next_phase": "Validate extracted citations against legal databases",
            "extraction_confidence": 0.921,
            "files_ready": True
        }
        
        handoff_session = await pdf_agent.create_handoff("validator", handoff_data)
        
        # Validation agent receives handoff
        success = await validation_agent.receive_handoff(handoff_session)
        assert success
        
        # Verify perfect handoff
        assert validation_agent.workflow_data["processing_complete"] is True
        assert validation_agent.workflow_data["pdf_metadata"]["total_pdfs"] == 12
        assert validation_agent.workflow_data["extraction_results"]["citations_found"] == 89
        assert len(validation_agent.workflow_data["files_processed"]) == 3
        
        # Verify bundle continuity
        bundle_stats = validation_agent.bundle_manager.get_bundle_stats()
        assert bundle_stats["total_actions"] >= 4  # PDF processing + handoff actions
    
    @pytest.mark.asyncio
    async def test_validation_to_analysis_handoff(self):
        """Test handoff from validation to final analysis"""
        # Set up validation agent with validation results
        validation_agent = BundleEnabledAgent("validator")
        
        # Simulate validation work
        validation_agent.bundle_manager.update_state({
            "validation_phase": "database_verification",
            "citations_validated": 89,
            "validation_results": {
                "valid_citations": 82,
                "invalid_citations": 7,
                "confidence_scores": [0.95, 0.87, 0.91] * 30,
                "database_matches": 78
            },
            "validation_complete": True
        })
        
        validation_agent.bundle_manager.create_checkpoint("validation_complete", 1.0)
        
        # Create final analysis agent
        analysis_agent = BundleEnabledAgent("final_analyzer")
        
        # Create handoff
        handoff_data = {
            "work_completed": "Citation validation completed",
            "validation_summary": f"Validated {89} citations: {82} valid, {7} invalid",
            "next_phase": "Generate final analysis and recommendations",
            "validation_rate": 0.921,
            "ready_for_analysis": True
        }
        
        handoff_session = await validation_agent.create_handoff("final_analyzer", handoff_data)
        
        # Final analyzer receives handoff
        success = await analysis_agent.receive_handoff(handoff_session)
        assert success
        
        # Verify complete context
        assert analysis_agent.workflow_data["validation_complete"] is True
        assert analysis_agent.workflow_data["citations_validated"] == 89
        assert analysis_agent.workflow_data["validation_results"]["valid_citations"] == 82
        assert analysis_agent.workflow_data["validation_results"]["database_matches"] == 78


class TestComplexWorkflowHandoffs:
    """Test complex multi-agent workflow handoffs"""
    
    @pytest.mark.asyncio
    async def test_three_agent_workflow_chain(self):
        """Test handoffs through a 3-agent workflow chain"""
        # Agent 1: Data Collection
        collector = BundleEnabledAgent("data_collector")
        collector.bundle_manager.update_state({
            "collection_phase": "completed",
            "data_sources": ["legal_database", "court_records", "case_law"],
            "records_collected": 250,
            "collection_metadata": {
                "start_time": "2024-01-15T10:00:00",
                "end_time": "2024-01-15T12:30:00",
                "duration_hours": 2.5
            }
        })
        
        # Agent 2: Data Processing  
        processor = BundleEnabledAgent("data_processor")
        
        # First handoff: Collection → Processing
        handoff1_data = {
            "work_completed": "Data collection completed",
            "data_summary": f"Collected {250} records from 3 sources",
            "next_phase": "Data processing and normalization"
        }
        
        handoff1_session = await collector.create_handoff("data_processor", handoff1_data)
        success1 = await processor.receive_handoff(handoff1_session)
        assert success1
        
        # Verify first handoff
        assert processor.workflow_data["records_collected"] == 250
        assert len(processor.workflow_data["data_sources"]) == 3
        
        # Processing work
        processor.bundle_manager.update_state({
            "processing_phase": "completed", 
            "records_processed": 250,
            "records_normalized": 245,
            "processing_errors": 5,
            "quality_score": 0.98
        })
        
        # Agent 3: Analysis
        analyzer = BundleEnabledAgent("analyzer")
        
        # Second handoff: Processing → Analysis
        handoff2_data = {
            "work_completed": "Data processing completed",
            "processing_summary": f"Processed {250} records, normalized {245}",
            "next_phase": "Final analysis and reporting",
            "quality_assessment": "High quality (98% success rate)"
        }
        
        handoff2_session = await processor.create_handoff("analyzer", handoff2_data)
        success2 = await analyzer.receive_handoff(handoff2_session)
        assert success2
        
        # Verify complete chain context
        assert analyzer.workflow_data["collection_phase"] == "completed"  # From agent 1
        assert analyzer.workflow_data["records_collected"] == 250  # From agent 1
        assert analyzer.workflow_data["processing_phase"] == "completed"  # From agent 2
        assert analyzer.workflow_data["records_normalized"] == 245  # From agent 2
        assert analyzer.workflow_data["quality_score"] == 0.98  # From agent 2
        
        # Verify bundle chain integrity
        analyzer_stats = analyzer.bundle_manager.get_bundle_stats()
        assert analyzer_stats["total_actions"] >= 6  # Actions from all 3 agents
        
        # Get handoff summary
        summary = analyzer.get_handoff_summary()
        assert summary["agent_type"] == "BundleEnabledAgent"
        assert summary["total_actions"] >= 6
    
    @pytest.mark.asyncio
    async def test_parallel_handoff_convergence(self):
        """Test convergence of parallel workflow handoffs"""
        # Create parallel processing agents
        processor_a = BundleEnabledAgent("processor_a")
        processor_b = BundleEnabledAgent("processor_b")
        
        # Set up parallel work
        processor_a.bundle_manager.update_state({
            "work_partition": "legal_documents_1_50",
            "documents_processed": 50,
            "citations_found": 124,
            "processing_time": 45.2
        })
        
        processor_b.bundle_manager.update_state({
            "work_partition": "legal_documents_51_100", 
            "documents_processed": 50,
            "citations_found": 98,
            "processing_time": 52.7
        })
        
        # Create convergence agent
        merger = BundleEnabledAgent("merger")
        
        # Receive both handoffs
        handoff_a_data = {
            "work_completed": "Processed documents 1-50",
            "partition_results": "124 citations found in 45.2s"
        }
        handoff_b_data = {
            "work_completed": "Processed documents 51-100", 
            "partition_results": "98 citations found in 52.7s"
        }
        
        handoff_a_session = await processor_a.create_handoff("merger", handoff_a_data)
        handoff_b_session = await processor_b.create_handoff("merger", handoff_b_data)
        
        success_a = await merger.receive_handoff(handoff_a_session)
        success_b = await merger.receive_handoff(handoff_b_session)
        
        assert success_a and success_b
        
        # Verify merged context (latest handoff should dominate)
        assert merger.workflow_data["work_partition"] == "legal_documents_51_100"
        assert merger.workflow_data["documents_processed"] == 50  # From latest
        assert merger.workflow_data["citations_found"] == 98  # From latest
        
        # But bundle should contain history from both
        merger_stats = merger.bundle_manager.get_bundle_stats()
        assert merger_stats["total_actions"] >= 4  # Actions from both processors


class TestHandoffRecovery:
    """Test handoff recovery and error scenarios"""
    
    @pytest.mark.asyncio
    async def test_handoff_with_checkpoint_recovery(self):
        """Test handoff recovery using checkpoints"""
        # Create agent with multiple checkpoints
        source_agent = BundleEnabledAgent("source_agent")
        
        # Create progression of checkpoints
        source_agent.bundle_manager.update_state({"phase": "initialization", "progress": 0.1})
        cp1 = source_agent.bundle_manager.create_checkpoint("init", 0.1)
        
        source_agent.bundle_manager.update_state({"phase": "processing", "progress": 0.5})
        cp2 = source_agent.bundle_manager.create_checkpoint("processing", 0.5)
        
        source_agent.bundle_manager.update_state({"phase": "completion", "progress": 0.9})
        cp3 = source_agent.bundle_manager.create_checkpoint("completion", 0.9)
        
        # Create handoff
        target_agent = BundleEnabledAgent("target_agent")
        handoff_session = await source_agent.create_handoff("target_agent", {"status": "ready"})
        
        # Receive handoff
        success = await target_agent.receive_handoff(handoff_session)
        assert success
        
        # Verify all checkpoints transferred
        assert len(target_agent.bundle_manager.checkpoints) == 3
        assert target_agent.bundle_manager.checkpoints[0].checkpoint_id == cp1
        assert target_agent.bundle_manager.checkpoints[1].checkpoint_id == cp2
        assert target_agent.bundle_manager.checkpoints[2].checkpoint_id == cp3
        
        # Test recovery to middle checkpoint
        recovery_success = target_agent.bundle_manager.restore_from_checkpoint(cp2)
        assert recovery_success
        
        # Verify recovery
        assert target_agent.bundle_manager.current_state["phase"] == "processing"
        assert target_agent.bundle_manager.current_state["progress"] == 0.5
    
    @pytest.mark.asyncio
    async def test_handoff_bundle_corruption_handling(self):
        """Test handling of corrupted handoff bundles"""
        # Create source agent
        source_agent = BundleEnabledAgent("source_agent")
        source_agent.bundle_manager.update_state({"important_data": "critical_information"})
        
        # Create target agent
        target_agent = BundleEnabledAgent("target_agent")
        
        # Test with invalid session ID
        success = await target_agent.receive_handoff("invalid_session_id")
        assert not success  # Should gracefully handle invalid handoff
        
        # Verify target agent state unchanged
        assert "important_data" not in target_agent.workflow_data


class TestHandoffPerformance:
    """Performance tests for handoff operations"""
    
    @pytest.mark.asyncio
    async def test_large_context_handoff_performance(self):
        """Test handoff performance with large context"""
        import time
        
        # Create agent with large context
        source_agent = BundleEnabledAgent("large_context_source")
        
        # Add large amount of data
        large_data = {
            f"dataset_{i}": [f"data_point_{j}" for j in range(100)]
            for i in range(20)
        }
        
        source_agent.bundle_manager.update_state(large_data)
        
        # Add many actions
        for i in range(200):
            source_agent.bundle_manager.append_action(
                ActionType.STATE_CHANGE,
                {"iteration": i, "data": f"large_data_block_{i}" * 10},
                "source_agent"
            )
        
        # Measure handoff performance
        target_agent = BundleEnabledAgent("large_context_target")
        
        start_time = time.time()
        handoff_session = await source_agent.create_handoff("target", {"data": "large"})
        handoff_create_time = time.time()
        
        success = await target_agent.receive_handoff(handoff_session)
        handoff_receive_time = time.time()
        
        # Verify performance
        create_time = handoff_create_time - start_time
        receive_time = handoff_receive_time - handoff_create_time
        total_time = handoff_receive_time - start_time
        
        assert success
        assert create_time < 2.0  # Handoff creation under 2 seconds
        assert receive_time < 3.0  # Handoff reception under 3 seconds  
        assert total_time < 5.0   # Total handoff under 5 seconds
        
        # Verify data integrity
        assert len(target_agent.workflow_data) == len(source_agent.workflow_data)
        assert target_agent.workflow_data["dataset_0"] == source_agent.workflow_data["dataset_0"]
    
    def test_handoff_compression_efficiency(self):
        """Test handoff bundle compression"""
        # Create agent with repetitive data
        agent = BundleEnabledAgent("compression_test")
        
        # Add repetitive data that should compress well
        repetitive_data = {
            "repeated_field": "This is repeated data that should compress well " * 100,
            "pattern_data": ["pattern_item_" + str(i % 10) for i in range(500)]
        }
        
        agent.bundle_manager.update_state(repetitive_data)
        
        # Create bundle and test compression
        bundle = agent.bundle_manager.create_bundle_snapshot()
        
        uncompressed_size = bundle.get_size_bytes()
        compressed_data = bundle.compress()
        compressed_size = len(compressed_data)
        
        # Verify compression effectiveness
        compression_ratio = compressed_size / uncompressed_size
        assert compression_ratio < 0.3  # Should compress to less than 30%
        
        # Verify decompression integrity
        decompressed_bundle = ContextBundle.decompress(compressed_data)
        assert decompressed_bundle.state == bundle.state
        assert len(decompressed_bundle.actions) == len(bundle.actions)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--asyncio-mode=auto"])