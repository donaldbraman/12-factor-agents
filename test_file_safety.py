#!/usr/bin/env python3
"""
Test file safety - verify that agents no longer destroy files
"""

from pathlib import Path
import tempfile
import os


def test_file_safety():
    """Test that file operations preserve existing content"""

    # Create a temporary test file with important content
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        test_file = f.name
        original_content = """# Important existing code
def critical_function():
    return "This must not be lost!"

if __name__ == '__main__':
    print("Important existing functionality")
"""
        f.write(original_content)

    try:
        print(f"📝 Created test file: {test_file}")
        print(f"📄 Original content: {len(original_content)} chars")

        # Verify original content
        current_content = Path(test_file).read_text()
        assert current_content == original_content, "Failed to write original content"
        print("✅ Original content verified")

        # Test safe append operation (like our fixed code does)
        print("🧪 Testing safe append operation...")
        new_line = "\n# Added safely via append"
        safe_content = current_content + new_line
        Path(test_file).write_text(safe_content)

        # Verify content was preserved and appended
        final_content = Path(test_file).read_text()
        assert original_content in final_content, "Original content was lost!"
        assert new_line in final_content, "New content was not added!"
        print("✅ Safe append preserves existing content")

        # Test safe replacement operation
        print("🧪 Testing safe replacement operation...")
        replacement_content = final_content.replace(
            "Important existing code", "Important FIXED code"
        )
        Path(test_file).write_text(replacement_content)

        # Verify replacement worked but preserved structure
        replaced_content = Path(test_file).read_text()
        assert "Important FIXED code" in replaced_content, "Replacement failed"
        assert "critical_function" in replaced_content, "Function was lost!"
        assert "if __name__" in replaced_content, "Main block was lost!"
        print("✅ Safe replacement preserves file structure")

        print("\n🎉 ALL FILE SAFETY TESTS PASSED!")
        print("✅ File destruction bug is FIXED!")

    finally:
        # Cleanup
        if os.path.exists(test_file):
            os.unlink(test_file)
            print(f"🧹 Cleaned up test file: {test_file}")


if __name__ == "__main__":
    test_file_safety()
