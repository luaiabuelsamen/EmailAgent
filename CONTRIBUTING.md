# Contributing to Cognitive Email Ecosystem

Thank you for your interest in contributing to the Cognitive Email Ecosystem project! This document provides guidelines and instructions for contributing.

## Code of Conduct

Please be respectful and considerate of others when contributing to this project. We aim to foster an inclusive and welcoming community.

## How to Contribute

### Reporting Issues

If you find a bug or have a suggestion for improvement:

1. Check if the issue already exists in the issue tracker
2. If not, create a new issue with a descriptive title and detailed description
3. Include steps to reproduce the bug if applicable
4. Mention your environment (OS, Python version, etc.)

### Pull Requests

1. Fork the repository
2. Create a new branch for your feature or bug fix
3. Make your changes
4. Ensure your code follows the project's coding style
5. Write or update tests as necessary
6. Update documentation if needed
7. Submit a pull request

## Development Setup

Follow the instructions in the [INSTALL.md](INSTALL.md) file to set up your development environment.

## Project Structure

- `cognitive_email_ecosystem.py`: Core hierarchical agent system
- `src/`: Source code for individual agents
  - `ingestionAgent.py`: Email data loading and normalization
  - `observerAgent.py`: Email categorization and user trait detection
  - `cognitive_email_adapter.py`: Connects agents to the cognitive system
- `tests/`: Unit tests
- `data/`: Sample data files
- `email_interface.py`: Flask web interface

## Coding Guidelines

- Follow PEP 8 style guidelines
- Include docstrings for all classes and functions
- Write meaningful commit messages
- Keep functions focused on a single responsibility
- Use type hints where appropriate

## Adding a New Agent

To add a new specialized agent to the ecosystem:

1. Create a new Python file in the `src/` directory
2. Implement the agent's core functionality
3. Add appropriate integration with the `CognitiveEmailSystem` class
4. Include unit tests in the `tests/` directory
5. Update documentation to explain the agent's purpose and functionality

## Testing

Run tests with:

```
python -m unittest discover tests
```

Please ensure all tests pass before submitting a pull request.

## Documentation

When adding new features, please update the relevant documentation to reflect your changes. 