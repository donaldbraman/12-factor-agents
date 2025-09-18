# Incoming Reports System

This directory receives and processes reports from external repositories to automatically improve the 12-factor-agents quality flywheel.

## Directory Structure

```
incoming_reports/
├── pending/     # New reports waiting to be processed
├── processed/   # Successfully processed reports (archived)
├── failed/      # Reports that failed processing (for debugging)
└── README.md    # This file
```

## How It Works

1. **External repos** (like cite-assist) submit reports by placing JSON files in `pending/`
2. **Report processor** monitors `pending/` and automatically processes new reports
3. **Quality flywheel** creates GitHub issues, analyzes patterns, and triggers improvements
4. **Reports are archived** to `processed/` or `failed/` directories

## Report Types

### 1. Analysis Report
```json
{
  "repo": "donaldbraman/cite-assist",
  "timestamp": "2025-09-18T10:53:20",
  "report_type": "analysis",
  "issues": [
    {
      "title": "Placeholder implementation in parser.py",
      "description": "Function has TODO comment instead of implementation",
      "priority": "high",
      "type": "placeholder",
      "file": "src/parser.py",
      "line": 42
    }
  ],
  "patterns": [
    {
      "pattern": "todo_comments",
      "count": 15,
      "severity": "medium"
    }
  ],
  "recommendations": [
    "Replace placeholder implementations with real code"
  ]
}
```

### 2. Quality Report
```json
{
  "repo": "donaldbraman/cite-assist",
  "timestamp": "2025-09-18T10:53:20",
  "report_type": "quality",
  "quality_score": 75,
  "quality_issues": [
    {
      "type": "complexity",
      "description": "Function complexity too high",
      "category": "maintainability",
      "file": "src/complex_function.py"
    }
  ],
  "recommendations": [
    "Refactor complex functions to improve maintainability"
  ]
}
```

### 3. Issue List Report
```json
{
  "repo": "donaldbraman/cite-assist",
  "timestamp": "2025-09-18T10:53:20",
  "report_type": "issue_list",
  "issues": [
    {
      "title": "Memory leak in processing loop",
      "priority": "high",
      "type": "bug",
      "description": "Long-running process consumes increasing memory"
    }
  ]
}
```

## Submission Methods

### Method 1: Direct File Drop
Copy your report JSON file directly to `incoming_reports/pending/`:

```bash
cp my_analysis_report.json /path/to/12-factor-agents/incoming_reports/pending/
```

### Method 2: Using the Submission Script
Use the provided script from your repository:

```bash
# Download the script
curl -O https://raw.githubusercontent.com/donaldbraman/12-factor-agents/main/scripts/submit_external_report.py

# Submit an analysis report
uv run python submit_external_report.py --repo "myorg/myrepo" --type analysis --file issues.json

# Submit via Git (automatic clone, commit, push)
uv run python submit_external_report.py --repo "myorg/myrepo" --type analysis --file issues.json --submit-via-git

# Submit a quality report
uv run python submit_external_report.py --repo "myorg/myrepo" --type quality --score 85 --file quality_issues.json
```

### Method 3: GitHub PR/Commit
1. Fork the 12-factor-agents repository
2. Add your report file to `incoming_reports/pending/`
3. Create a pull request or commit directly (if you have access)

## Processing

Reports are automatically processed by the system:

### Automatic Processing
Start the continuous processor:
```bash
cd /path/to/12-factor-agents
uv run python scripts/external_report_processor.py --watch
```

### Manual Processing
Process all pending reports once:
```bash
uv run python scripts/external_report_processor.py
```

## What Happens to Your Report

1. **Validation**: Report format and required fields are checked
2. **Processing**: Based on report type:
   - **High priority issues** → Automatic GitHub issue creation
   - **Quality problems** → Quality alerts and analysis
   - **Patterns** → Integration with telemetry learning system
3. **Response**: The system may:
   - Create GitHub issues in this repository
   - Trigger automatic improvements through Sparky
   - Update quality patterns and recommendations
   - Generate analysis reports

## Integration Examples

### For cite-assist repository:
```bash
# After running analysis
uv run python submit_external_report.py \\
  --repo "donaldbraman/cite-assist" \\
  --type analysis \\
  --file cite_assist_analysis.json \\
  --submit-via-git
```

### For automated CI/CD:
```yaml
# GitHub Actions example
- name: Submit Quality Report
  run: |
    uv run python submit_external_report.py \\
      --repo "${{ github.repository }}" \\
      --type quality \\
      --score $QUALITY_SCORE \\
      --file quality_report.json \\
      --submit-via-git
```

## Monitoring

Watch the processing logs:
```bash
# Follow processing in real-time
tail -f /tmp/12-factor-telemetry/12-factor-agents_workflow.jsonl
```

Check GitHub issues created: https://github.com/donaldbraman/12-factor-agents/issues

## Support

For questions or issues with report submission:
1. Check the `failed/` directory for error details
2. Create an issue in the 12-factor-agents repository
3. Review the processing logs for debugging information

---

*This system enables the quality flywheel to continuously learn and improve from multiple repositories in the ecosystem.*