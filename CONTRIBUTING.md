# Contributing to VaultPulse

Thank you for your interest in contributing to **VaultPulse**, an open-source project engineered and maintained by **Neelbyte Websolution**.

## Development Workflow

1. **Fork the Repository** on GitHub.
2. **Clone your fork**:
   ```bash
   git clone https://github.com/YOUR_USERNAME/vaultpulse.git
   cd vaultpulse
   ```
3. **Setup environment**:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
4. **Make your changes** and test thoroughly:
   ```bash
   python test_suite.py
   ```
   All 11 tests must pass before submitting a Pull Request.

5. **Commit with clean messages**:
   ```bash
   git commit -m "feat: add webhook integration for download triggers"
   ```

6. **Submit a Pull Request**.

## Code Style & Ethics
- Maintain clean, robust code with zero unnecessary dependencies.
- Follow PEP 8 guidelines.
- Always include automated test coverage for new endpoints.
