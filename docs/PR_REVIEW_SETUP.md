# PR Review Agent Setup Guide

The PR Review Agent provides automated code reviews using Claude AI for GitHub pull requests.

## Features

- 🤖 AI-powered code analysis using Claude
- 💬 Automatic PR comments with detailed feedback
- 📊 Code quality scoring
- 🔍 Issue detection (bugs, security, performance, style)
- 💡 Improvement suggestions
- 👍 Positive feedback recognition
- 🔄 Multiple trigger options (webhook, GitHub Actions, manual)

## Prerequisites

1. **API Keys Required:**
   - `GITHUB_TOKEN` - GitHub personal access token with repo scope
   - `ANTHROPIC_API_KEY` - Claude API key from Anthropic

2. **Dependencies:**
   ```bash
   uv pip install PyGithub anthropic flask
   ```

## Setup Options

### Option 1: GitHub Actions (Recommended)

1. **Add API Key to GitHub Secrets:**
   - Go to Settings → Secrets → Actions
   - Add `ANTHROPIC_API_KEY` with your Claude API key

2. **Enable the Workflow:**
   - The workflow is already configured in `.github/workflows/pr-review.yml`
   - It will automatically run on new PRs and updates

3. **Manual Trigger:**
   - Go to Actions tab → "Automated PR Review" workflow
   - Click "Run workflow" and enter a PR number

### Option 2: Webhook Listener

1. **Start the Webhook Server:**
   ```bash
   export GITHUB_TOKEN=your_github_token
   export ANTHROPIC_API_KEY=your_claude_api_key
   export GITHUB_WEBHOOK_SECRET=your_webhook_secret
   
   python bin/pr-webhook-listener.py
   ```

2. **Configure GitHub Webhook:**
   - Go to Settings → Webhooks → Add webhook
   - **URL:** `https://your-domain.com/webhook`
   - **Content type:** `application/json`
   - **Secret:** Same as `GITHUB_WEBHOOK_SECRET`
   - **Events:** Select "Pull requests"

3. **For Local Development (using ngrok):**
   ```bash
   # Install ngrok
   brew install ngrok  # macOS
   
   # Start webhook listener
   python bin/pr-webhook-listener.py &
   
   # Expose with ngrok
   ngrok http 8080
   
   # Use the ngrok URL for GitHub webhook
   ```

### Option 3: Manual CLI Usage

```bash
# Review a specific PR
uv run agent run PRReviewAgent "review PR #123"

# Review PR in specific repo
uv run agent run PRReviewAgent "review PR #456 in owner/repo"

# Analyze without posting comments
uv run agent run PRReviewAgent "analyze PR #789"
```

## Configuration

Edit `config/pr_review_config.json`:

```json
{
  "auto_approve_threshold": 8,      // Quality score for auto-approval
  "post_comments": true,             // Post comments to PR
  "update_description": true,        // Update PR description
  "anthropic_model": "claude-3-haiku-20240307",  // Claude model
  "temperature": 0.3,                // Response consistency
  "max_tokens": 2000                 // Max response length
}
```

## Environment Variables

```bash
# Required
export GITHUB_TOKEN=ghp_xxxxxxxxxxxx        # GitHub PAT
export ANTHROPIC_API_KEY=sk-ant-xxxxx      # Claude API key

# Optional
export GITHUB_DEFAULT_REPO=owner/repo      # Default repository
export GITHUB_WEBHOOK_SECRET=secret123     # Webhook verification
export WEBHOOK_PORT=8080                   # Webhook server port
```

## Testing

1. **Test with Public Repository:**
   ```bash
   uv run agent run PRReviewAgent "analyze PR #1 in microsoft/vscode"
   ```

2. **Test Webhook Locally:**
   ```bash
   # Send test webhook
   curl -X POST http://localhost:8080/webhook \
     -H "Content-Type: application/json" \
     -H "X-GitHub-Event: pull_request" \
     -d '{"action": "opened", "pull_request": {"number": 123}}'
   ```

3. **Health Check:**
   ```bash
   curl http://localhost:8080/health
   ```

## Review Output Format

The agent posts structured reviews with:

- **Summary** - Executive overview of changes
- **Quality Score** - 1-10 rating
- **Approval Status** - Approved or Changes Requested
- **Issues Found** - Categorized by severity
- **Required Changes** - Must-fix items
- **Suggestions** - Improvements to consider
- **Positive Feedback** - What was done well

## Troubleshooting

### Common Issues

1. **"GITHUB_TOKEN not set"**
   - Ensure token is exported: `export GITHUB_TOKEN=your_token`

2. **"ANTHROPIC_API_KEY not set"**
   - Ensure API key is exported: `export ANTHROPIC_API_KEY=your_key`

3. **"Failed to fetch PR"**
   - Check GitHub token has repo scope
   - Verify repository exists and is accessible

4. **"Failed to analyze code"**
   - Check Claude API key is valid
   - Verify you have API credits remaining

5. **Webhook not triggering**
   - Check webhook secret matches
   - Verify ngrok is running (for local testing)
   - Check GitHub webhook delivery logs

### Debug Mode

```bash
# Enable debug output
export DEBUG=1
python bin/pr-webhook-listener.py
```

## Security Best Practices

1. **Never commit API keys** - Use environment variables
2. **Use webhook secrets** - Verify GitHub signatures
3. **Limit token scopes** - Only grant necessary permissions
4. **Rotate keys regularly** - Update tokens periodically
5. **Use HTTPS** - Always use SSL in production

## Advanced Usage

### Custom Review Guidelines

Create `docs/CODING_STANDARDS.md` with your team's standards:

```markdown
# Coding Standards

- Follow PEP 8 for Python code
- All functions must have docstrings
- Use type hints for function parameters
- Maximum line length: 100 characters
- Prefer composition over inheritance
```

### Batch Reviews

```python
# Review multiple PRs
for pr_num in [123, 124, 125]:
    subprocess.run([
        'uv', 'run', 'agent', 'run', 'PRReviewAgent',
        f'review PR #{pr_num}'
    ])
```

### Integration with CI/CD

Add to your CI pipeline:

```yaml
- name: Code Review
  if: github.event_name == 'pull_request'
  run: |
    uv run agent run PRReviewAgent "review PR #${{ github.event.pull_request.number }}"
```

## Support

For issues or questions:
- Check the [Issues](https://github.com/donaldbraman/12-factor-agents/issues) page
- Review agent logs in `.claude/agents/checkpoints/`
- Enable debug mode for detailed output