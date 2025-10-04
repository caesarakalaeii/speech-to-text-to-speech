# Contributing to Speech-to-Text-to-Speech

Thank you for your interest in contributing! This document provides guidelines for contributing to the project.

## Development Setup

1. Fork the repository
2. Clone your fork:
   ```bash
   git clone https://github.com/YOUR_USERNAME/speech-to-text-to-speech.git
   cd speech-to-text-to-speech
   ```

3. Run the setup script:
   ```bash
   ./setup.sh
   ```

4. Create a new branch for your feature:
   ```bash
   git checkout -b feature/your-feature-name
   ```

## Code Style

- Follow PEP 8 guidelines for Python code
- Use meaningful variable and function names
- Add docstrings to classes and functions
- Keep functions focused and small

## Testing

Before submitting a PR:

1. Run the validation tests:
   ```bash
   python3 test_imports.py
   ```

2. Test your changes with the actual application
3. Ensure the setup script still works
4. Test Docker build if you modified Docker-related files

## Submitting Changes

1. Commit your changes with clear, descriptive messages
2. Push to your fork
3. Create a Pull Request with:
   - Clear description of changes
   - Any relevant issue numbers
   - Testing notes

## Reporting Issues

When reporting issues, please include:

- Python version
- Operating system
- Steps to reproduce
- Expected vs actual behavior
- Any error messages or logs

## Feature Requests

Feature requests are welcome! Please:

- Check if the feature already exists or is planned
- Describe the use case clearly
- Explain why this would be useful to others

## License

By contributing, you agree that your contributions will be licensed under the GNU Affero General Public License v3.0.
