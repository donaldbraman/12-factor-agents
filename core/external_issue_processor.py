#!/usr/bin/env python3
"""
External Issue Processor - Simplified version for cite-assist integration
Compatible with a100408 codebase architecture
"""

from pathlib import Path
from typing import Dict
from dataclasses import dataclass

from core.telemetry import TelemetryCollector


@dataclass
class ExternalIssue:
    """Simple external issue data structure"""

    number: int
    title: str
    body: str
    repository: str
    labels: list = None


class SimpleExternalIssueProcessor:
    """
    Simplified processor for external issues that works with the a100408 codebase.
    Focuses on the core functionality needed for cite-assist integration.
    """

    def __init__(self):
        self.telemetry = TelemetryCollector()

    def process_cite_assist_issue(self, issue_number: int, issue_content: str) -> Dict:
        """
        Process an issue from cite-assist using the current system.

        Args:
            issue_number: The issue number from cite-assist
            issue_content: The markdown content of the issue

        Returns:
            Processing result dictionary
        """
        print(f"🚀 Processing cite-assist issue #{issue_number}")

        try:
            # Parse the issue content
            issue_data = self._parse_issue_content(issue_content, issue_number)

            # Determine which agent should handle this
            assigned_agent = self._determine_agent(issue_data)

            # Create a local issue file in the 12-factor-agents issues directory
            issue_file = self._create_local_issue_file(issue_data, assigned_agent)

            # Process using IntelligentIssueAgent
            result = self._process_with_intelligent_agent(issue_file, issue_data)

            return {
                "success": result.get("success", False),
                "issue_number": issue_number,
                "issue_title": issue_data["title"],
                "assigned_agent": assigned_agent,
                "local_issue_file": str(issue_file),
                "processing_result": result,
                "repository": "cite-assist",
            }

        except Exception as e:
            self.telemetry.record_error(
                repo_name="cite-assist",
                agent_name="SimpleExternalIssueProcessor",
                error_type="ProcessingError",
                error_message=str(e),
                context={"issue_number": issue_number},
            )

            return {
                "success": False,
                "error": str(e),
                "issue_number": issue_number,
                "repository": "cite-assist",
            }

    def _parse_issue_content(self, content: str, issue_number: int) -> Dict:
        """Parse issue markdown content into structured data"""
        lines = content.split("\n")

        issue_data = {
            "number": issue_number,
            "title": "Unknown Title",
            "description": "",
            "goal": "",
            "key_components": [],
            "technical_implementation": "",
            "files_to_create": [],
            "repository": "cite-assist",
        }

        current_section = None
        current_content = []

        for line in lines:
            line = line.strip()

            # Extract title from header
            if line.startswith("# Issue #") or line.startswith("# "):
                issue_data["title"] = (
                    line.replace("# Issue #", "").replace("# ", "").strip()
                )
                if ":" in issue_data["title"]:
                    issue_data["title"] = issue_data["title"].split(":", 1)[1].strip()

            # Section headers
            elif line.startswith("## Goal"):
                current_section = "goal"
                current_content = []
            elif line.startswith("## Key Components"):
                current_section = "key_components"
                current_content = []
            elif line.startswith("## Technical Implementation"):
                current_section = "technical_implementation"
                current_content = []
            elif line.startswith("## Description"):
                current_section = "description"
                current_content = []
            elif line.startswith("##"):
                # End current section
                if current_section and current_content:
                    issue_data[current_section] = "\n".join(current_content).strip()
                current_section = None
                current_content = []

            # Content within sections
            elif current_section and line:
                current_content.append(line)

                # Extract file paths for creation
                if current_section == "technical_implementation" and line.startswith(
                    "- "
                ):
                    if any(ext in line for ext in [".py", ".md", ".json", ".yaml"]):
                        # Extract file path
                        import re

                        file_match = re.search(
                            r"`([^`]+\.(py|md|json|yaml|yml))`", line
                        )
                        if file_match:
                            issue_data["files_to_create"].append(file_match.group(1))

        # Handle final section
        if current_section and current_content:
            issue_data[current_section] = "\n".join(current_content).strip()

        return issue_data

    def _determine_agent(self, issue_data: Dict) -> str:
        """Determine which agent should handle this issue"""
        title = issue_data.get("title", "").lower()
        description = issue_data.get("description", "").lower()
        goal = issue_data.get("goal", "").lower()

        # Check for feature creation indicators
        if any(keyword in title for keyword in ["implement", "create", "add", "build"]):
            return "IntelligentIssueAgent"

        # Check content for new feature indicators
        content = f"{title} {description} {goal}".lower()
        if any(
            keyword in content
            for keyword in [
                "new",
                "implement",
                "create",
                "add",
                "build",
                "enhance",
                "feature",
                "functionality",
            ]
        ):
            return "IntelligentIssueAgent"

        # Check if files need to be created
        if issue_data.get("files_to_create"):
            return "IntelligentIssueAgent"

        # Default to IntelligentIssueAgent for sister repo issues
        return "IntelligentIssueAgent"

    def _create_local_issue_file(self, issue_data: Dict, assigned_agent: str) -> Path:
        """Create a local issue file that the system can process"""

        # Create issues directory if it doesn't exist
        issues_dir = Path("issues")
        issues_dir.mkdir(exist_ok=True)

        # Generate issue filename
        issue_number = issue_data["number"]
        title_slug = (
            issue_data["title"][:30].replace(" ", "-").replace("/", "-").lower()
        )
        issue_file = issues_dir / f"{issue_number}-cite-assist-{title_slug}.md"

        # Generate issue content in the format expected by the system
        content = f"""# Issue #{issue_number}: {issue_data['title']}

## Description
{issue_data.get('description', 'Feature request from cite-assist repository.')}

## Goal
{issue_data.get('goal', 'Process feature request from sister repository.')}

## Key Components
{issue_data.get('key_components', 'Components to be implemented as specified.')}

## Technical Implementation
{issue_data.get('technical_implementation', 'Implementation details from original issue.')}

## Files to Create
{chr(10).join(f'- {file}' for file in issue_data.get('files_to_create', []))}

## Metadata
- **Source Repository**: cite-assist
- **Original Issue**: #{issue_number}
- **Processing Agent**: {assigned_agent}

## Agent Assignment
{assigned_agent}

## Type
feature

## Priority
high

## Status
open
"""

        # Write the issue file
        issue_file.write_text(content)

        print(f"📝 Created local issue file: {issue_file}")
        return issue_file

    def _process_with_intelligent_agent(
        self, issue_file: Path, issue_data: Dict
    ) -> Dict:
        """Process the issue using IntelligentIssueAgent"""
        try:
            # Import and use the IntelligentIssueAgent from current system
            from agents.intelligent_issue_agent import IntelligentIssueAgent

            # Create the agent
            agent = IntelligentIssueAgent()

            # Process the issue
            task = f"Process the issue file at {issue_file}"
            result = agent.execute_task(task)

            if result.success:
                print(
                    f"✅ Successfully processed cite-assist issue #{issue_data['number']}"
                )
                return {
                    "success": True,
                    "agent_result": result.data,
                    "message": "Issue processed successfully by IntelligentIssueAgent",
                }
            else:
                print(
                    f"❌ Failed to process cite-assist issue #{issue_data['number']}: {result.error}"
                )
                return {
                    "success": False,
                    "error": result.error,
                    "message": "IntelligentIssueAgent processing failed",
                }

        except Exception as e:
            print(f"❌ Error processing with IntelligentIssueAgent: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to invoke IntelligentIssueAgent",
            }


def main():
    """Test the external issue processor"""
    processor = SimpleExternalIssueProcessor()

    # Test with cite-assist issue 123 content
    test_issue_content = """# Issue #123: Implement Document-Level Summary Embeddings for Whole-Document Relevance

## Goal
Add whole-document relevance scoring by creating AI-generated summaries (1500-1800 chars) that get embedded as single vectors.

## Key Components

1. **DocumentSummarizer** - Uses Gemini to create optimized summaries
2. **Document Summary Store** - New Qdrant collection for document-level vectors  
3. **Enhanced Search** - Weighted combination of chunk + document relevance
4. **Caching System** - Avoids re-summarization of documents

## Technical Implementation

This requires creating new Python modules in the cite-assist codebase:
- `src/cite_assist/document_summarizer.py`
- `src/cite_assist/document_summary_store.py`  
- `src/cite_assist/enhanced_search.py`
- `tests/test_document_summaries.py`

## Success Criteria

- 8 comprehensive test suites covering quality, performance, and integration
- Summaries must be 1500-1800 chars (optimal for embeddings)
- Cache hit rate > 90%
- < 5 seconds per summary generation
- Configurable weighting between chunk and document relevance
"""

    print("🧪 Testing External Issue Processor")
    result = processor.process_cite_assist_issue(123, test_issue_content)

    print("\n📊 Processing Result:")
    print(f"Success: {result['success']}")
    print(f"Title: {result.get('issue_title', 'Unknown')}")
    print(f"Agent: {result.get('assigned_agent', 'Unknown')}")
    if result.get("local_issue_file"):
        print(f"Local file: {result['local_issue_file']}")

    if not result["success"]:
        print(f"Error: {result.get('error', 'Unknown error')}")


if __name__ == "__main__":
    main()
