# Sister Repository Drop Zone

Local file drop integration for sister repositories.

## How It Works

1. **Sister repos drop reports here** (they're local, so just use relative paths)
2. **Auto-processing** picks them up and creates GitHub issues
3. **Quality flywheel** takes over from there

## For Sister Repos

Just drop JSON files in your subdirectory:

```bash
# From cite-assist
echo '{"repo":"cite-assist","data":[{"title":"Fix bug","priority":"high"}]}' > ../12-factor-agents/sister_repos/cite-assist/report_$(date +%s).json

# From any sister repo  
cp my_analysis.json ../12-factor-agents/sister_repos/my-repo/
```

## Directory Structure

```
sister_repos/
├── cite-assist/          # Reports from cite-assist
├── other-repo/           # Reports from other sister repos
├── processed/            # Successfully processed reports
├── failed/               # Failed reports (for debugging)
└── README.md            # This file
```

## Report Format

Just drop any JSON file with this basic structure:

```json
{
  "repo": "donaldbraman/cite-assist",
  "timestamp": "2025-09-18T11:00:00",
  "type": "issues",
  "data": [
    {
      "title": "Fix memory leak",
      "priority": "high",
      "description": "Memory usage keeps growing"
    }
  ]
}
```

## Auto-Processing

The system automatically:
1. **Watches** `sister_repos/*/` for new `.json` files
2. **Processes** them into GitHub issues (high priority items)
3. **Moves** them to `processed/` or `failed/`
4. **Integrates** with the quality flywheel

## Start Watching

```bash
# In 12-factor-agents directory
uv run python scripts/sister_repo_watcher.py
```

## Integration Examples

### From cite-assist:
```bash
# Generate and submit report
echo '{"repo":"donaldbraman/cite-assist","type":"issues","data":[{"title":"Memory leak","priority":"high"}]}' > ../12-factor-agents/sister_repos/cite-assist/$(date +%Y%m%d_%H%M%S).json
```

### From any sister repo:
```bash
# Simple report drop
cp my_analysis.json ../12-factor-agents/sister_repos/my-repo/
```

---
*Much simpler than external submission - just local file drops!*