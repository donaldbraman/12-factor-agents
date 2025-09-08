# Issue #009: Migrate All Python Operations to UV

## Description
Update all Python operations throughout the codebase to use `uv` instead of `python3` or `pip`, as per CLAUDE.md requirements.

## Acceptance Criteria
- [ ] All documentation references use `uv run` instead of `python3`
- [ ] All subprocess calls use `uv run`
- [ ] Setup script checks for and uses `uv`
- [ ] Example files use `uv`
- [ ] README updated with `uv` instructions
- [ ] Launcher scripts use `uv`
- [ ] Agent self-test comments show `uv run` usage

## Files to Update
- `setup.sh` - Use `uv venv` and `uv pip install`
- `README.md` - Update all examples
- `agents/*.py` - Update self-test comments
- `agents/issue_orchestrator_agent.py` - subprocess calls
- `examples/triggers/*.py` - Update shebangs and examples
- `bin/event` - Update shebang
- `IMPLEMENTATION-PLAN.md` - Update commands
- `12-FACTOR-LOCAL-ARCHITECTURE.md` - Update examples

## Technical Requirements
- Replace `#!/usr/bin/env python3` with `#!/usr/bin/env uv run python`
- Replace `python3` commands with `uv run`
- Replace `pip install` with `uv pip install`
- Replace `sys.executable` with `["uv", "run"]` in subprocess

## Agent Assignment
`UvMigrationAgent`

## Priority
P0 - Critical (CLAUDE.md requirement)

## Dependencies
None - can run independently

## Labels
tooling, migration, uv, python

## Status
RESOLVED

### Resolution Notes
Resolved by UvMigrationAgent at 2025-09-08T09:42:34.521519

### Updated: 2025-09-08T09:42:34.521605
