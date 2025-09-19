# 🚀 SPARKY Test Suite

## Standardized Testing Framework for Agent Validation

This comprehensive test suite provides **disposable, reusable issues** for testing SPARKY implementations across all complexity levels. No more manual issue creation - just run the suite and get consistent, measurable results!

## 🎯 **Why This Exists**

**Problem Solved**: Testing SPARKY required manually creating issues, running tests, and cleaning up afterward. This was time-consuming and inconsistent.

**Solution**: Standardized test battery with **progressive complexity** that automatically resets between runs.

## 📁 **Directory Structure**

```
tests/sparky_test_suite/
├── issues/                           # Test issues by complexity
│   ├── level_1_basic/               # Single action, one file (1 tool call)
│   │   └── 001-add-comment.md
│   ├── level_2_intermediate/        # Multi-action, few files (4+ tool calls)
│   │   └── 011-refactor-function.md
│   ├── level_3_advanced/           # Complex workflows (12+ tool calls)
│   │   └── 021-implement-error-handling.md
│   └── level_4_integration/        # Full pipeline (25+ tool calls)
│       └── 031-full-feature-implementation.md
├── fixtures/                       # Target files for modification
│   ├── simple_function.py          # Basic test target
│   ├── data_processor.py           # Multi-file test target
│   └── main_app.py                 # Integration test target
├── run_suite.py                    # Execute full test battery
├── reset_suite.py                  # Reset to clean state
└── README.md                       # This file
```

## 🎮 **Quick Start**

### Run Complete Test Suite
```bash
cd tests/sparky_test_suite
uv run python run_suite.py
```

### Reset Between Tests  
```bash
uv run python reset_suite.py
```

### Run Single Level
```python
from run_suite import SPARKYTestSuite
suite = SPARKYTestSuite()
suite.run_level("level_1_basic", suite.discover_test_issues()["level_1_basic"])
```

## 📊 **Complexity Progression**

### Level 1: Basic Operations
- **Tool Calls**: 1
- **Files**: 1  
- **Examples**: Add comment, replace text, create file
- **Time**: ~2 seconds
- **Purpose**: Validate core structured output functionality

### Level 2: Intermediate Coordination
- **Tool Calls**: 4-8
- **Files**: 2-3
- **Examples**: Refactor function across files, update dependencies
- **Time**: ~5 seconds  
- **Purpose**: Test multi-file coordination and dependency handling

### Level 3: Advanced Workflows
- **Tool Calls**: 12-20
- **Files**: 4-6
- **Examples**: Error handling, logging, comprehensive refactoring
- **Time**: ~15 seconds
- **Purpose**: Validate complex dependency management and order execution

### Level 4: Full Integration  
- **Tool Calls**: 25+
- **Files**: 8+
- **Examples**: Complete feature implementation with tests, docs, deployment
- **Time**: ~30 seconds
- **Purpose**: End-to-end pipeline validation with Git workflow

## 🧪 **Test Issue Format**

Each test issue follows this standardized format:

```markdown
# Test Issue #XXX: Description (Level X - Category)

## Description
Clear description of what should be implemented

## Type  
enhancement|bug|feature|refactoring

## Target Files
- List of files that will be modified
- Clear expectations for each file

## Expected Actions
1. Detailed list of structured actions
2. Order-dependent operations noted
3. Dependencies clearly marked

## Success Criteria
- Measurable outcomes
- No breaking changes
- Performance expectations

## Complexity: Level X
- File count
- Action count  
- Dependencies
- Integration requirements

## Tool Calls Expected: N
Breakdown of expected structured actions

## Dependencies (if any)
Order requirements and dependencies between actions
```

## 🔄 **Reset Mechanism**

The test suite is **fully disposable** - run `reset_suite.py` to restore everything to clean state:

- ♻️ **Git Reset**: Restores fixture files to original state
- 🗑️ **File Cleanup**: Removes generated files and directories  
- 📁 **Directory Reset**: Cleans cache, logs, temp directories
- 📄 **Report Cleanup**: Removes old test reports

## 📈 **Performance Benchmarking**

The suite automatically measures:

- **Success Rate**: Percentage of successful completions
- **Execution Time**: Per test and per level
- **Action Throughput**: Actions per minute
- **Complexity Scaling**: How performance changes with complexity

Example output:
```
LEVEL 1 (BASIC): 1/1 (100%) - 1.2s avg
LEVEL 2 (INTERMEDIATE): 1/1 (100%) - 4.8s avg  
LEVEL 3 (ADVANCED): 1/1 (100%) - 14.2s avg
LEVEL 4 (INTEGRATION): 1/1 (100%) - 28.5s avg

Overall Success Rate: 4/4 (100%)
Actions/Minute: 42.3
```

## 🎯 **Adding New Test Issues**

### 1. Choose Complexity Level
- Level 1: Single simple operation
- Level 2: Multi-file coordination
- Level 3: Complex dependencies  
- Level 4: Full feature implementation

### 2. Create Issue File
```bash
# Copy template and modify
cp issues/level_1_basic/001-add-comment.md issues/level_1_basic/00X-your-test.md
```

### 3. Update Fixtures (if needed)
Add target files to `fixtures/` directory

### 4. Test Your Issue
```bash
uv run python run_suite.py  # Will auto-discover new issues
```

## 🔧 **Integration with SPARKY Versions**

The test suite is designed to work with any SPARKY implementation:

### SPARKY 3.0 (Documentation Generator)
- Will create documentation files
- Limited actual code changes
- Useful for pipeline testing

### SPARKY 4.0 (Structured Outputs)  
- Executes real structured actions
- Makes actual code modifications
- Full Factor 4 implementation

### Future SPARKY Versions
- Just update the import in `run_suite.py`
- All tests remain compatible
- Progressive complexity still valid

## 🎭 **Use Cases**

### 🔬 **Development**
- Test new SPARKY features
- Validate refactoring changes
- Measure performance improvements
- Debug complex scenarios

### 🏗️ **CI/CD Integration**
```bash
# Add to CI pipeline
python tests/sparky_test_suite/run_suite.py
exit_code=$?
if [ $exit_code -ne 0 ]; then
    echo "SPARKY tests failed"
    exit 1
fi
```

### 📊 **Benchmarking**
- Compare SPARKY versions
- Track performance over time
- Identify regression issues
- Validate optimizations

### 🎓 **Training & Demo**
- Demonstrate SPARKY capabilities
- Show progressive complexity
- Educational examples
- Live testing demos

## 🚀 **Next Steps**

1. **Run the suite** to validate current SPARKY implementation
2. **Add more test issues** at each complexity level
3. **Integrate with CI/CD** for automated validation  
4. **Extend fixture files** for domain-specific testing
5. **Add performance profiling** for detailed analysis

---

## 🎉 **The Result**

**No more manual test creation!** Just run:

```bash
uv run python run_suite.py
```

And get comprehensive SPARKY validation across all complexity levels with consistent, measurable results. 

**Time saved**: Hours of manual testing → Minutes of automated validation

**Reliability**: Consistent test conditions and reproducible results

**Coverage**: Progressive complexity from basic operations to full feature implementation

---
*SPARKY Test Suite - Making Agent Testing Fast, Consistent, and Comprehensive* 🚀