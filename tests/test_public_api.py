from pathlib import Path

import rezult
import rezult.option as option_module
import rezult.result as result_module

from rezult import (
    Err,
    Nothing,
    Ok,
    Option,
    Result,
    Some,
    UnwrapError,
    option_eval,
    optionally,
    result_eval,
    resulty,
)


def test_root_exports() -> None:
    assert rezult.Ok is Ok
    assert rezult.Err is Err
    assert rezult.Result is Result
    assert rezult.Some is Some
    assert rezult.Nothing is Nothing
    assert rezult.Option is Option
    assert rezult.UnwrapError is UnwrapError
    assert rezult.result_eval is result_eval
    assert rezult.resulty is resulty
    assert rezult.option_eval is option_eval
    assert rezult.optionally is optionally


def test_submodules_are_not_shadowed() -> None:
    assert result_module.Result is Result
    assert option_module.Option is Option
    assert result_module.resulty is resulty
    assert option_module.optionally is optionally


def test_py_typed_marker_exists() -> None:
    marker = Path(__file__).resolve().parents[1] / "src" / "rezult" / "py.typed"
    assert marker.is_file()
