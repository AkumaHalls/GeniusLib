# Contributing

Contributions are welcome! Here's how to get started.

## Development Setup

```sh
# Clone the repository
git clone https://github.com/AkumaHalls/GeniusLib.git
cd GeniusLib

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows

# Install in editable mode with dev dependencies
pip install -e ".[dev]"
```

## Running Tests

```sh
pytest tests/ -v
```

## Code Style

This project uses [Ruff](https://github.com/astral-sh/ruff) for linting and formatting:

```sh
ruff check .
ruff format .
```

## Pull Request Process

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/my-feature`)
3. Make your changes
4. Run tests (`pytest tests/ -v`)
5. Run linter (`ruff check .`)
6. Commit your changes with a descriptive message
7. Push to your fork and submit a pull request

## Reporting Issues

Please use the [GitHub Issues](https://github.com/AkumaHalls/GeniusLib/issues) tracker for bug reports and feature requests.

When reporting a bug, include:
- Python version
- GeniusLib version
- Minimal code to reproduce the issue
- Full error traceback

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
