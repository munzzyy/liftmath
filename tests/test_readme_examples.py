"""Every CLI example in README.md with its full output shown has to match what the CLI prints."""

import re
import shlex
from pathlib import Path

import pytest

from liftmath.cli import main

README = Path(__file__).resolve().parent.parent / "README.md"


def _examples():
    blocks = re.findall(r"^```[^\n]*\n(.*?)^```", README.read_text(encoding="utf-8"), re.MULTILINE | re.DOTALL)
    return [b for b in blocks if b.startswith("$ liftmath ") and "..." not in b]


EXAMPLES = _examples()


def test_readme_has_examples_to_check():
    assert len(EXAMPLES) >= 9


@pytest.mark.parametrize("block", EXAMPLES, ids=[b.splitlines()[0][2:] for b in EXAMPLES])
def test_readme_example_matches_cli_output(capsys, block):
    command, *expected = block.rstrip("\n").splitlines()
    assert main(shlex.split(command.removeprefix("$ "))[1:]) == 0
    actual = [line.rstrip() for line in capsys.readouterr().out.splitlines()]
    position = 0
    for line in expected:
        line = line.rstrip()
        try:
            position = actual.index(line, position) + 1
        except ValueError:
            shown = "\n".join(actual)
            pytest.fail(f"README line not in the output (in order):\n{line}\n\nactual output:\n{shown}")
