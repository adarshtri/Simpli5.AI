# Python Project

This is a Python project template with a basic structure and common development tools.

## Setup

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Development

- Run tests: `pytest`
- Format code: `black .`
- Lint code: `flake8`

## Project Structure

```
.
├── README.md
├── requirements.txt
├── src/
│   └── main.py
└── tests/
    └── __init__.py
```

# Simpli5.AI

An extensible AI CLI with agent and tool support.

## Development Setup

1. Install in editable mode:

    pip install -e src

2. Run the CLI:

    simpli5

You should see a welcome message. 