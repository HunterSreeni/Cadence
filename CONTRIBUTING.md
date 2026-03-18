# Contributing to cadence

Thank you for considering contributing to cadence! This guide will help you get started.

## How to Contribute

### Reporting Bugs

1. Check [existing issues](../../issues) to avoid duplicates
2. Use the **Bug Report** template when creating a new issue
3. Include: Python version, OS, steps to reproduce, expected vs actual behavior
4. Paste relevant error messages or logs (redact any tokens/personal data)

### Suggesting Features

1. Check [existing issues](../../issues) and [discussions](../../discussions) first
2. Use the **Feature Request** template
3. Describe the problem you're trying to solve, not just the solution
4. If possible, include a mockup of how the Telegram message would look

### Submitting Code

#### First time?

1. Fork the repo
2. Clone your fork: `git clone https://github.com/YOUR_USERNAME/Cadence.git`
3. Create a branch: `git checkout -b feature/your-feature-name`
4. Make your changes
5. Test locally (see below)
6. Commit with a clear message
7. Push and open a Pull Request

#### Branch naming

- `feature/description` — new features
- `fix/description` — bug fixes
- `docs/description` — documentation changes
- `refactor/description` — code improvements without behavior change

#### Commit messages

Keep them clear and concise:
```
Add reply parsing for exercise tracking
Fix evening message timezone calculation
Update setup wizard to validate time format
```

### Testing Locally

```bash
# Verify Python files compile
python3 -c "import py_compile; py_compile.compile('cadence.py', doraise=True)"
python3 -c "import py_compile; py_compile.compile('setup.py', doraise=True)"

# Run the setup wizard (generates config)
python3 setup.py

# Test the bot
python3 cadence.py test

# If you have pytest installed
python3 -m pytest tests/
```

### Code Style

- **Python 3.8+ compatible** — no walrus operators, no `match` statements, no `list[str]` type hints
- **stdlib only** in `cadence.py` — no external dependencies in the core bot
- External deps are fine in `setup.py`, `mcp/`, and `schedulers/` but should be optional
- Follow existing code patterns — single-file architecture, config-driven behavior
- Keep functions focused — one function, one job
- Add comments only where the logic isn't self-evident

### What We're Looking For

**High-value contributions:**
- New tracking categories (exercise, mood, habits)
- Better reply parsing (NLP, fuzzy matching)
- Telegram inline keyboards for quick status updates
- New scheduler support (systemd timers, Windows services)
- Quarterly/yearly review message builders
- Multi-language message templates (i18n)
- Web dashboard for viewing logs/stats
- Integration with other tools (Notion, Obsidian, Google Calendar)

**Always welcome:**
- Bug fixes
- Documentation improvements
- Test coverage
- Cross-platform compatibility fixes
- Performance improvements

### Pull Request Checklist

- [ ] Code compiles without errors (`python3 -c "import py_compile; ..."`)
- [ ] No personal data, tokens, or secrets in the code
- [ ] Works on Python 3.8+
- [ ] `cadence.py` changes use stdlib only (no new pip dependencies)
- [ ] Existing functionality isn't broken
- [ ] Commit messages are clear
- [ ] PR description explains what and why

## Code of Conduct

Please read our [Code of Conduct](CODE_OF_CONDUCT.md). We are committed to providing a welcoming and inclusive environment for everyone.

## Questions?

- Open a [Discussion](../../discussions) for general questions
- Open an [Issue](../../issues) for bugs or feature requests

Thank you for helping make cadence better!
