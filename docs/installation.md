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

## Development version

```bash
pip install git+https://github.com/DesignSafe-CI/dapi.git@dev
```

Or in a notebook:

```python
%pip uninstall dapi --yes
%pip install git+https://github.com/DesignSafe-CI/dapi.git@dev --quiet
```

## Local editable install

```bash
git clone https://github.com/DesignSafe-CI/dapi.git
cd dapi
pip install -e .
```

### Set up pre-commit hook

The repo includes a pre-commit hook that auto-formats with `ruff format` and blocks commits that fail `ruff check`:

```bash
cp scripts/pre-commit .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
```

## Update

```bash
pip install --upgrade dapi
```
