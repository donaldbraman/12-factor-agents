# Issue #422: Integrate LLM into PRReviewAgent AnalyzeCodeTool

## Description

Replace the mock analysis in PRReviewAgent's AnalyzeCodeTool with actual LLM integration using OpenAI or Anthropic's Claude. This will enable genuine AI-powered code reviews with meaningful insights and suggestions.

## Objectives

1. Add OpenAI/Anthropic SDK to dependencies
2. Implement real LLM calls in AnalyzeCodeTool
3. Create robust prompt engineering
4. Handle API errors and rate limits
5. Add configuration for LLM selection

## Technical Requirements

### 1. Update AnalyzeCodeTool.execute()

Replace mock response in `agents/pr_review_agent.py`:

```python
def execute(self, pr_data: Dict, guidelines: str = None) -> ToolResponse:
    # ... existing code ...
    
    # Get LLM configuration
    llm_provider = os.getenv("LLM_PROVIDER", "openai")
    
    if llm_provider == "openai":
        review_result = self._call_openai(prompt)
    elif llm_provider == "anthropic":
        review_result = self._call_anthropic(prompt)
    else:
        # Fallback to mock
        review_result = self._mock_review(pr_data, diff_content)
    
    return ToolResponse(success=True, data=review_result)

def _call_openai(self, prompt: str) -> Dict:
    import openai
    openai.api_key = os.getenv("OPENAI_API_KEY")
    
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a senior code reviewer."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3,
        response_format={"type": "json_object"}
    )
    
    return json.loads(response.choices[0].message.content)

def _call_anthropic(self, prompt: str) -> Dict:
    from anthropic import Anthropic
    client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    
    response = client.messages.create(
        model="claude-3-opus-20240229",
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )
    
    # Parse JSON from response
    return json.loads(response.content[0].text)
```

### 2. Enhanced Prompt Template

Create `prompts/pr_review_detailed.prompt`:

```
You are an expert code reviewer for the 12-factor-agents project, a Python-based agent orchestration system.

REVIEW CONTEXT:
- Project: 12-factor-agents (agent orchestration framework)
- Language: Python 3.9+
- Standards: PEP 8, type hints encouraged, comprehensive docstrings required
- Architecture: Modular agents inheriting from BaseAgent
- Key Patterns: Tool-based actions, checkpoint/resume, state management

GUIDELINES:
{guidelines}

PR INFORMATION:
- Title: {pr_title}
- Description: {pr_description}
- Files Changed: {file_count}
- Additions: +{additions} lines
- Deletions: -{deletions} lines

CODE DIFF:
```diff
{diff}
```

REVIEW INSTRUCTIONS:
Analyze the code changes and provide a comprehensive review. Focus on:

1. **Correctness**: Logic errors, bugs, edge cases
2. **Security**: Vulnerabilities, unsafe operations, input validation
3. **Performance**: Inefficiencies, memory leaks, optimization opportunities
4. **Style**: PEP 8 compliance, naming conventions, code organization
5. **Architecture**: Design patterns, modularity, 12-factor compliance
6. **Testing**: Test coverage, test quality, missing tests
7. **Documentation**: Docstrings, comments, README updates

OUTPUT FORMAT (JSON):
{
    "summary": "One paragraph executive summary of the changes",
    "quality_score": 8,  // 1-10 scale
    "approved": true/false,
    "issues": [
        {
            "severity": "critical|major|minor",
            "category": "bug|security|performance|style|architecture",
            "file": "path/to/file.py",
            "line": 42,
            "message": "Specific issue description",
            "suggestion": "How to fix it"
        }
    ],
    "suggestions": [
        "General improvement suggestion 1",
        "General improvement suggestion 2"
    ],
    "needs_changes": [
        "Required change 1 before approval",
        "Required change 2 before approval"
    ],
    "positive_feedback": [
        "Well-implemented feature or pattern",
        "Good practice that was followed"
    ]
}
```

### 3. Configuration

Update `config/pr_review_config.json`:

```json
{
    "llm_provider": "${LLM_PROVIDER}",
    "openai_model": "gpt-4",
    "anthropic_model": "claude-3-opus-20240229",
    "temperature": 0.3,
    "max_tokens": 2000,
    "timeout": 30,
    "retry_attempts": 3,
    "fallback_to_mock": true
}
```

### 4. Error Handling

Add robust error handling:
- API rate limit handling with exponential backoff
- Token limit detection and diff truncation
- Network timeout handling
- Graceful fallback to mock review

### 5. Add Dependencies

Update `pyproject.toml`:
```toml
openai = "^1.3.0"
anthropic = "^0.8.0"
```

## Success Criteria

- [ ] Real LLM integration working with OpenAI
- [ ] Real LLM integration working with Anthropic
- [ ] Structured JSON responses parsing correctly
- [ ] Error handling for API failures
- [ ] Configuration system working
- [ ] Prompt template producing quality reviews

## Agent Assignment

IntelligentIssueAgent

## Priority

High

## Dependencies

- Issue #421 (PyGithub setup) should be complete
- Requires API keys for OpenAI or Anthropic

## Estimated Effort

2-3 hours

## Notes

Start with OpenAI integration as it's more commonly available. Anthropic can be added as an enhancement. Consider token costs and implement smart truncation for large diffs.

## Status
RESOLVED

### Resolution Notes
Resolved by IntelligentIssueAgent at 2025-09-15T10:22:18.672710

### Updated: 2025-09-15T10:22:18.672785
