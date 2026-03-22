"""PyLauncher parameter sweep utilities for DesignSafe.

This module provides functions for generating parameter sweeps and writing
PyLauncher input files. These are pure local operations — PyLauncher itself
runs on TACC compute nodes, not locally.

Functions:
    generate_sweep: Generate sweep commands and optionally write PyLauncher input files.
"""

from __future__ import annotations

from itertools import product
from pathlib import Path
from typing import Any, List, Mapping, Sequence, Union

import pandas as pd


def _validate_sweep(sweep: Mapping[str, Sequence[Any]]) -> None:
    """Validate sweep values are non-empty, non-string sequences."""
    for k, vals in sweep.items():
        if not isinstance(vals, Sequence) or isinstance(vals, (str, bytes)):
            raise TypeError(f"sweep[{k!r}] must be a non-string sequence of values.")
        if len(vals) == 0:
            raise ValueError(f"sweep[{k!r}] is empty; provide at least one value.")


def _expand_commands(
    command: str,
    sweep: Mapping[str, Sequence[Any]],
    placeholder_style: str,
) -> List[str]:
    """Expand a command template into all parameter combinations."""
    if not sweep:
        return [command]

    _validate_sweep(sweep)

    if placeholder_style not in ("token", "braces"):
        raise ValueError("placeholder_style must be 'token' or 'braces'.")

    keys = list(sweep.keys())
    commands: List[str] = []
    for combo in product(*[sweep[k] for k in keys]):
        cmd = command
        for k, v in zip(keys, combo):
            if placeholder_style == "token":
                cmd = cmd.replace(k, str(v))
            else:
                cmd = cmd.replace("{" + k + "}", str(v))
        commands.append(cmd)

    return commands


def generate_sweep(
    command: str,
    sweep: Mapping[str, Sequence[Any]],
    directory: Union[str, Path, None] = None,
    *,
    placeholder_style: str = "token",
    debug: str | None = None,
    preview: bool = False,
) -> Union[List[str], pd.DataFrame]:
    """Generate sweep commands and write PyLauncher input files.

    When *preview* is ``True``, returns a DataFrame of all parameter
    combinations without writing any files — useful for inspecting the
    sweep in a notebook before committing.

    When *preview* is ``False`` (default), expands *command* into one
    command per parameter combination and writes ``runsList.txt`` and
    ``call_pylauncher.py`` into *directory*.

    Args:
        command: Command template containing placeholders that match
            keys in *sweep*. Environment variables like ``$WORK`` or
            ``$SLURM_JOB_ID`` are left untouched.
        sweep: Mapping of placeholder name to a sequence of values.
            Example: ``{"ALPHA": [0.3, 0.5], "BETA": [1, 2]}``.
        directory: Directory to write files into. Created if it doesn't
            exist. Required when *preview* is ``False``.
        placeholder_style: How placeholders appear in *command*:

            - ``"token"`` (default): bare tokens, e.g. ``ALPHA``
            - ``"braces"``: brace-wrapped, e.g. ``{ALPHA}``

        debug: Optional debug string passed to ``ClassicLauncher``
            (e.g. ``"host+job"``). Ignored when *preview* is ``True``.
        preview: If ``True``, return a DataFrame of parameter combinations
            without writing files.

    Returns:
        ``List[str]`` of generated commands when *preview* is ``False``,
        or a ``pandas.DataFrame`` of parameter combinations when ``True``.

    Raises:
        TypeError: If a sweep value is not a non-string sequence.
        ValueError: If a sweep value is empty, *placeholder_style* is
            invalid, or *directory* is missing when *preview* is ``False``.
    """
    if sweep:
        _validate_sweep(sweep)

    if preview:
        if not sweep:
            return pd.DataFrame()
        keys = list(sweep.keys())
        rows = [dict(zip(keys, combo)) for combo in product(*[sweep[k] for k in keys])]
        return pd.DataFrame(rows)

    if directory is None:
        raise ValueError("directory is required when preview=False.")

    commands = _expand_commands(command, sweep, placeholder_style)

    dirpath = Path(directory)
    dirpath.mkdir(parents=True, exist_ok=True)

    # Write runsList.txt
    (dirpath / "runsList.txt").write_text("\n".join(commands) + "\n", encoding="utf-8")

    # Write call_pylauncher.py
    if debug is not None:
        script = (
            "import pylauncher\n"
            f'pylauncher.ClassicLauncher("runsList.txt", debug="{debug}")\n'
        )
    else:
        script = 'import pylauncher\npylauncher.ClassicLauncher("runsList.txt")\n'
    (dirpath / "call_pylauncher.py").write_text(script, encoding="utf-8")

    return commands
