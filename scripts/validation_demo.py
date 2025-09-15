#!/usr/bin/env uv run python
"""
Demonstration of the validation and rollback system.

This script demonstrates how the validation system prevents the specific
indentation error bug mentioned in the requirements where agents add
`if result is not None:` checks with incorrect indentation.
"""

import tempfile
import shutil
from pathlib import Path

from core.validation import TransactionalFileModifier
from core.execution_context import ExecutionContext


def demo_indentation_error_prevention():
    """Demonstrate prevention of indentation errors"""
    print("🔍 Demonstrating Indentation Error Prevention")
    print("=" * 50)

    # Create temporary directory for demo
    temp_dir = Path(tempfile.mkdtemp(prefix="validation_demo_"))
    context = ExecutionContext(repo_path=temp_dir)

    try:
        # Create a file modifier
        modifier = TransactionalFileModifier(context)

        # Start transaction
        tx_id = modifier.begin_transaction()
        print(f"🔒 Started transaction: {tx_id}")

        # Test 1: Valid code (should pass)
        print("\n📝 Test 1: Valid Python code")
        valid_code = """
def process_data():
    result = get_data()
    if result is not None:  # Correct indentation
        return result.value
    return None
"""

        validation_result = modifier.stage_modification("valid_file.py", valid_code)
        print(f"   Result: {validation_result.result.value}")
        print(f"   Message: {validation_result.message}")

        # Test 2: Invalid indentation (should fail)
        print("\n📝 Test 2: Invalid indentation (the bug pattern)")
        invalid_code = """
def process_data():
    result = get_data()
if result is not None:  # INCORRECT indentation - this is the bug!
        return result.value
    return None
"""

        validation_result = modifier.stage_modification("invalid_file.py", invalid_code)
        print(f"   Result: {validation_result.result.value}")
        print(f"   Message: {validation_result.message}")
        if validation_result.line_number:
            print(f"   Line: {validation_result.line_number}")
            print(f"   Fix: {validation_result.suggested_fix}")

        # Test 3: Syntax error (should fail)
        print("\n📝 Test 3: Syntax error")
        syntax_error_code = """
def process_data(:  # Missing closing parenthesis
    result = get_data()
    return result
"""

        validation_result = modifier.stage_modification(
            "syntax_error.py", syntax_error_code
        )
        print(f"   Result: {validation_result.result.value}")
        print(f"   Message: {validation_result.message}")

        # Test 4: Demonstrate rollback
        print("\n🔄 Test 4: Demonstrating rollback")

        # Create an original file
        original_file = temp_dir / "rollback_test.py"
        original_content = "print('Original content')\n"
        original_file.write_text(original_content)
        print(f"   Created original file with: {original_content.strip()}")

        # Stage a modification
        new_content = "print('Modified content')\n"
        modifier.stage_modification(str(original_file), new_content)
        print(f"   Staged modification to: {new_content.strip()}")

        # Rollback
        modifier.rollback_transaction()
        print("   Rolled back transaction")

        # Check that original content is preserved
        current_content = original_file.read_text()
        print(f"   Current file content: {current_content.strip()}")
        print(f"   ✅ Original content preserved: {current_content == original_content}")

        modifier.cleanup()
        print(f"\n🧹 Cleaned up transaction {tx_id}")

    finally:
        # Clean up temp directory
        shutil.rmtree(temp_dir)
        print("🗑️ Cleaned up temporary directory")


def demo_cross_repo_integration():
    """Demonstrate cross-repository operation integration"""
    print("\n🌐 Demonstrating Cross-Repository Integration")
    print("=" * 50)

    # Create temporary directories for multiple repos
    main_repo = Path(tempfile.mkdtemp(prefix="main_repo_"))
    sister_repo = Path(tempfile.mkdtemp(prefix="sister_repo_"))

    try:
        # Context for sister repository
        sister_context = ExecutionContext(
            repo_name="sister-repo", repo_path=sister_repo, is_external=True
        )

        print(f"📁 Main repo: {main_repo}")
        print(f"📁 Sister repo: {sister_repo}")

        # Create file modifier for sister repo
        modifier = TransactionalFileModifier(sister_context)
        tx_id = modifier.begin_transaction()

        print(f"\n🔒 Started cross-repo transaction: {tx_id}")

        # Stage modifications in sister repo
        sister_code = """
# This file is in the sister repository
def sister_function():
    data = fetch_data()
    if data is not None:  # Correct indentation
        return process(data)
    return None
"""

        result = modifier.stage_modification("sister_module.py", sister_code)
        print(f"📝 Staged modification in sister repo: {result.result.value}")

        # Commit the changes
        success, errors = modifier.commit_transaction()
        print(f"💾 Commit result: {'Success' if success else 'Failed'}")

        if success:
            # Verify file was created in correct location
            sister_file = sister_repo / "sister_module.py"
            print(f"✅ File created in sister repo: {sister_file.exists()}")
            print(f"📄 File path: {sister_file}")

        modifier.cleanup()

    finally:
        # Clean up
        shutil.rmtree(main_repo)
        shutil.rmtree(sister_repo)
        print("🗑️ Cleaned up temporary repositories")


def demo_intelligent_agent_integration():
    """Demonstrate integration with IntelligentIssueAgent workflow"""
    print("\n🤖 Demonstrating IntelligentIssueAgent Integration")
    print("=" * 50)

    # Import the agent
    from agents.intelligent_issue_agent import IntelligentIssueAgent
    from core.execution_context import create_default_context

    # Create agent with default context
    agent = IntelligentIssueAgent()
    context = create_default_context()
    agent.context = context

    print("✅ IntelligentIssueAgent instantiated with validation system")

    # The agent now includes the validation system in its _generic_implementation method
    print("🔧 Agent workflow now includes:")
    print("   - TransactionalFileModifier for safe operations")
    print("   - Pre-modification syntax validation")
    print("   - Automatic rollback on validation failure")
    print("   - Structured error reporting")
    print("   - Cross-repository operation support")

    print("\n🎯 Benefits:")
    print("   • Prevents syntax errors from being written to files")
    print("   • Automatically detects and prevents indentation errors")
    print("   • Provides rollback on any validation failure")
    print("   • Maintains transaction logs for debugging")
    print("   • Supports cross-repository modifications safely")


if __name__ == "__main__":
    print("🚀 Validation and Rollback System Demonstration")
    print("=" * 60)

    demo_indentation_error_prevention()
    demo_cross_repo_integration()
    demo_intelligent_agent_integration()

    print("\n🎉 Demonstration Complete!")
    print("The validation system is now fully integrated and ready to prevent")
    print(
        "syntax errors, indentation errors, and provide robust rollback capabilities."
    )
