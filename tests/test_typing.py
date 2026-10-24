import os
import subprocess
import sys
from pathlib import Path

import pytest

pytest.importorskip("mypy")

SRC = Path(__file__).resolve().parents[1] / "src"

CONSUMER = """\
from rezult import (
    Err,
    Nothing,
    Ok,
    Option,
    Result,
    Some,
    option_eval,
    optionally,
    result_eval,
    resulty,
)


def parse(value: str) -> Result[int, str]:
    return Ok(int(value))


result: Result[int, str] = parse("1")
reveal_type(result)

option: Option[int] = Some(1)
nothing: Option[int] = Nothing()
reveal_type(option)
reveal_type(nothing)

nested_result: Result[Option[int], str] = Ok(Some(1))
reveal_type(Result.transpose(nested_result))
reveal_type(Result.flatten(Ok(Ok(1))))

nested_option: Option[Result[int, str]] = Some(Ok(1))
reveal_type(Option.transpose(nested_option))
reveal_type(Option.flatten(Some(Some(1))))


@resulty()
def plain(value: int) -> int:
    return value


@resulty(ValueError)
def checked(value: str) -> int:
    return int(value)


@optionally
def optional(value: int) -> int | None:
    return value


reveal_type(plain(1))
reveal_type(checked("1"))
reveal_type(optional(1))
reveal_type(result_eval(lambda: 1))
reveal_type(option_eval(lambda: None))
"""


def test_mypy_accepts_public_api(tmp_path: Path) -> None:
    consumer = tmp_path / "consumer.py"
    consumer.write_text(CONSUMER, encoding="utf-8")

    env = os.environ.copy()
    env["MYPYPATH"] = str(SRC)

    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "mypy",
            "--no-incremental",
            "--no-site-packages",
            "--cache-dir",
            str(tmp_path / ".mypy_cache"),
            str(consumer),
        ],
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )

    output = completed.stdout + completed.stderr
    assert completed.returncode == 0, output
    assert "Result[int, str]" in output
    assert "Option[int]" in output
