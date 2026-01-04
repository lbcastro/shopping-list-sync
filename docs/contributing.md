# Contributing to Shopping List Sync

Thank you for considering contributing to Shopping List Sync! This document provides guidelines for contributing to the project.

## Getting Started

1. Fork the repository on GitHub
2. Clone your fork locally
3. Set up the development environment

```bash
git clone https://github.com/YOUR_USERNAME/shopping-list-sync.git
cd shopping-list-sync
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -e ".[dev]"
```

## Development Workflow

1. Create a new branch for your feature or bug fix:
```bash
git checkout -b feature/your-feature-name
```

2. Make your changes and ensure they follow the project standards

3. Run tests and code quality checks:
```bash
pytest
black src/
ruff check src/
mypy src/
```

4. Commit your changes with a descriptive message:
```bash
git commit -m "Add feature: description of your changes"
```

5. Push to your fork and submit a pull request

## Code Style

- Follow PEP 8 guidelines
- Use Black for code formatting (line length: 100)
- Use Ruff for linting
- Add type hints where appropriate
- Write docstrings for public functions and classes

## Testing

- Write tests for new features
- Ensure all existing tests pass
- Aim for good test coverage
- Use pytest for testing

## Pull Request Process

1. Update the README.md with details of changes if applicable
2. Update the CHANGELOG.md with your changes
3. Ensure all tests pass and code quality checks are green
4. Request review from maintainers
5. Address any feedback

## Reporting Bugs

- Use the GitHub Issues tracker
- Include a clear title and description
- Provide steps to reproduce the issue
- Include relevant logs and error messages
- Specify your environment (OS, Python version, etc.)

## Suggesting Enhancements

- Use the GitHub Issues tracker with the "enhancement" label
- Clearly describe the enhancement and its benefits
- Provide examples of how it would be used

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
