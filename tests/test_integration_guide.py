"""Test all code examples from the Integration Guide"""
import sys
import re
from pathlib import Path
import subprocess
import tempfile


def extract_code_blocks(markdown_file):
    """Extract all Python code blocks from markdown"""
    with open(markdown_file) as f:
        content = f.read()

    # Find all ```python blocks
    pattern = r"```python\n(.*?)```"
    return re.findall(pattern, content, re.DOTALL)


def test_code_block(code, block_num):
    """Test a single code block"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(code)
        temp_file = f.name

    try:
        result = subprocess.run(
            ["uv", "run", "python", temp_file],
            capture_output=True,
            text=True,
            timeout=10,
        )
        return result.returncode == 0, result.stderr
    except Exception as e:
        return False, str(e)
    finally:
        Path(temp_file).unlink(missing_ok=True)


def test_integration_guide():
    """Test all examples in the Integration Guide"""
    guide_path = Path(__file__).parent.parent / "docs" / "INTEGRATION-GUIDE.md"

    if not guide_path.exists():
        print(f"⚠️ Integration guide not found at {guide_path}")
        return

    code_blocks = extract_code_blocks(guide_path)

    if not code_blocks:
        print("⚠️ No Python code blocks found in Integration Guide")
        return

    results = []
    for i, block in enumerate(code_blocks, 1):
        # Skip blocks that are clearly incomplete snippets or examples
        if any(
            [
                "from" not in block and "import" not in block,
                "self." in block
                and "class" not in block,  # Method examples without class
                "await" in block and "async def" not in block,  # Async without function
                "my_agent" in block.lower(),  # Placeholder imports
                "CustomAgent" in block
                and "class CustomAgent" not in block,  # Example classes
                len(block.strip()) < 10,  # Very short snippets
            ]
        ):
            print(f"   Skipping block {i} (incomplete example)")
            continue

        success, error = test_code_block(block, i)
        results.append(
            {"block": i, "success": success, "error": error if not success else None}
        )

    # Report results
    failed = [r for r in results if not r["success"]]
    if failed:
        print(f"Failed blocks: {[r['block'] for r in failed]}")
        for r in failed:
            print(f"Block {r['block']}: {r['error']}")
        assert False, f"{len(failed)} code blocks failed"

    print(f"✅ All {len(results)} code blocks passed!")


def test_all_documentation():
    """Test code examples in all documentation files"""
    docs_dir = Path(__file__).parent.parent / "docs"

    if not docs_dir.exists():
        print("⚠️ docs directory not found")
        return

    total_blocks_tested = 0
    total_files_tested = 0

    for md_file in docs_dir.glob("*.md"):
        print(f"\n📄 Testing {md_file.name}...")

        code_blocks = extract_code_blocks(md_file)
        if not code_blocks:
            print("   No Python code blocks found")
            continue

        total_files_tested += 1
        file_results = []

        for i, block in enumerate(code_blocks, 1):
            # Skip clearly incomplete snippets
            if "from" not in block and "import" not in block:
                continue

            success, error = test_code_block(block, i)
            file_results.append(
                {
                    "block": i,
                    "success": success,
                    "error": error if not success else None,
                }
            )
            total_blocks_tested += 1

        # Report file results
        failed = [r for r in file_results if not r["success"]]
        if failed:
            print(f"   ❌ {len(failed)} blocks failed in {md_file.name}")
            for r in failed:
                print(f"      Block {r['block']}: {r['error']}")
        else:
            print(f"   ✅ All {len(file_results)} blocks passed in {md_file.name}")

    print(
        f"\n📊 Summary: Tested {total_blocks_tested} code blocks across {total_files_tested} files"
    )


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--all":
        test_all_documentation()
    else:
        test_integration_guide()
