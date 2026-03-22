# Installation

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

## Update

```bash
pip install --upgrade dapi
```
