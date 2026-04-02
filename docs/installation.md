# Installation

Requires Python 3.9 or later.

## From PyPI

```bash
pip install dapi
```

## In a Jupyter notebook

```python
%pip install dapi --quiet
```

## Check version

```python
import dapi
print(dapi.__version__)
```

## Update

```bash
pip install --upgrade dapi
```

## Development

### Install the dev branch

To test unreleased features from the `dev` branch:

```bash
pip install git+https://github.com/DesignSafe-CI/dapi.git@dev
```

Or in a DesignSafe Jupyter notebook:

```python
%pip uninstall dapi --yes
%pip install git+https://github.com/DesignSafe-CI/dapi.git@dev --quiet
```

Restart the kernel after installing.

### Local editable install

For local development where changes take effect immediately:

```bash
git clone https://github.com/DesignSafe-CI/dapi.git
cd dapi
git checkout dev
pip install -e .
```

### Pre-commit hook

The repo includes a pre-commit hook that auto-formats code with `ruff format` and blocks commits that fail `ruff check`:

```bash
cp scripts/pre-commit .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
```

### Running tests

```bash
pip install pytest
pytest tests/ -v
```

### Linting

```bash
ruff format --check .
ruff check .
```

To auto-fix lint errors:

```bash
ruff check --fix .
```
