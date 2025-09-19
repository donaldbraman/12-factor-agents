#!/usr/bin/env python3
"""Detect potential secrets in files."""

import sys
import re
from pathlib import Path

# Patterns that indicate actual secrets (not environment variable references)
SECRET_PATTERNS = [
    # API Keys
    (
        r'["\']?[Aa][Pp][Ii][-_]?[Kk][Ee][Yy]["\']?\s*[:=]\s*["\'][A-Za-z0-9+/]{20,}["\']',
        "API Key",
    ),
    (
        r'["\']?[Aa][Pp][Ii][-_]?[Ss][Ee][Cc][Rr][Ee][Tt]["\']?\s*[:=]\s*["\'][A-Za-z0-9+/]{20,}["\']',
        "API Secret",
    ),
    # Tokens
    (
        r'["\']?[Tt][Oo][Kk][Ee][Nn]["\']?\s*[:=]\s*["\'][A-Za-z0-9+/=_-]{20,}["\']',
        "Token",
    ),
    (
        r'["\']?[Aa][Cc][Cc][Ee][Ss][Ss][-_]?[Tt][Oo][Kk][Ee][Nn]["\']?\s*[:=]\s*["\'][A-Za-z0-9+/=_-]{20,}["\']',
        "Access Token",
    ),
    # Passwords
    (
        r'["\']?[Pp][Aa][Ss][Ss][Ww][Oo][Rr][Dd]["\']?\s*[:=]\s*["\'][^"\']{8,}["\']',
        "Password",
    ),
    (r'["\']?[Pp][Ww][Dd]["\']?\s*[:=]\s*["\'][^"\']{8,}["\']', "Password"),
    # Specific service patterns
    (r"sk-[a-zA-Z0-9]{48}", "OpenAI API Key"),
    (r"ghp_[a-zA-Z0-9]{36}", "GitHub Personal Access Token"),
    (r"ghs_[a-zA-Z0-9]{36}", "GitHub Secret"),
    (r"github_pat_[a-zA-Z0-9]{22}_[a-zA-Z0-9]{59}", "GitHub Fine-grained PAT"),
    # AWS
    (r"AKIA[0-9A-Z]{16}", "AWS Access Key ID"),
    (r'["\'][A-Za-z0-9+/]{40}["\']', "AWS Secret Key (possible)"),
    # Private keys
    (r"-----BEGIN (RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----", "Private Key"),
]

# Patterns that are OK (environment variables, examples)
ALLOWED_PATTERNS = [
    r"os\.environ",
    r"os\.getenv",
    r"ENV\[",
    r"getenv\(",
    r"YOUR_API_KEY",
    r"YOUR_TOKEN",
    r"EXAMPLE_",
    r"example_",
    r"<your[_-]",
    r"xxx+",
    r"\.env\.example",
]


def is_allowed_context(content, match_start, match_end):
    """Check if the match is in an allowed context."""
    # Get surrounding context (50 chars before and after)
    context_start = max(0, match_start - 50)
    context_end = min(len(content), match_end + 50)
    context = content[context_start:context_end]

    # Check if it's an environment variable reference
    for pattern in ALLOWED_PATTERNS:
        if re.search(pattern, context, re.IGNORECASE):
            return True

    return False


def detect_secrets(filepath):
    """Check file for potential secrets."""
    path = Path(filepath)

    # Skip certain files
    skip_patterns = [".env.example", ".env.sample", "test_", "_test.py", ".md"]
    if any(pattern in str(path) for pattern in skip_patterns):
        return True

    # Skip non-text files
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
    except (UnicodeDecodeError, IsADirectoryError, FileNotFoundError):
        return True

    violations = []
    for pattern, secret_type in SECRET_PATTERNS:
        matches = re.finditer(pattern, content)
        for match in matches:
            if not is_allowed_context(content, match.start(), match.end()):
                # Get line number
                line_num = content[: match.start()].count("\n") + 1
                violations.append((line_num, secret_type, match.group(0)[:50]))

    if violations:
        print(f"\n❌ {filepath}: Potential secrets detected:")
        for line_num, secret_type, preview in violations:
            # Truncate preview for security
            if len(preview) > 20:
                preview = preview[:20] + "..."
            print(f"   Line {line_num}: {secret_type} - {preview}")
        print("   Fix: Use environment variables instead (os.getenv('KEY_NAME'))")
        return False

    return True


def main():
    """Main entry point for pre-commit hook."""
    if len(sys.argv) == 1:
        print("No files to check")
        sys.exit(0)

    all_clean = True
    for filepath in sys.argv[1:]:
        # Only check relevant file types
        if filepath.endswith((".py", ".json", ".yaml", ".yml", ".txt", ".sh")):
            if not detect_secrets(filepath):
                all_clean = False

    if not all_clean:
        print("\n🔒 Security tip: Never commit secrets! Use .env files and os.getenv()")
        print("   See .env.example for the pattern to follow")

    sys.exit(0 if all_clean else 1)


if __name__ == "__main__":
    main()
