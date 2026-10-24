import pytest

from rezult import (
    Err,
    Nothing,
    Ok,
    Some,
    option_eval,
    optionally,
    result_eval,
    resulty,
)


def test_resulty_default_catches_exception() -> None:
    @resulty()
    def divide(a: int, b: int) -> float:
        return a / b

    assert divide(4, 2) == Ok(2.0)

    result = divide(1, 0)
    assert isinstance(result, Err)
    assert isinstance(result.value, ZeroDivisionError)


def test_resulty_selective_catch() -> None:
    @resulty(ValueError)
    def parse(text: str) -> int:
        return int(text)

    assert parse("42") == Ok(42)
    assert isinstance(parse("x"), Err)

    @resulty(ValueError)
    def raise_key_error() -> None:
        raise KeyError("missing")

    with pytest.raises(KeyError):
        raise_key_error()


def test_resulty_multiple_exceptions() -> None:
    @resulty(ValueError, KeyError)
    def fail(kind: str) -> None:
        if kind == "value":
            raise ValueError("bad value")
        raise KeyError("bad key")

    assert isinstance(fail("value"), Err)
    assert isinstance(fail("key"), Err)


def test_resulty_catches_subclasses() -> None:
    class CustomError(ValueError):
        pass

    @resulty(ValueError)
    def fail() -> None:
        raise CustomError("custom")

    result = fail()
    assert isinstance(result, Err)
    assert isinstance(result.value, CustomError)


def test_resulty_requires_exception_types() -> None:
    with pytest.raises(TypeError, match="expects exception types"):
        resulty(lambda: 1)  # type: ignore[call-overload]

    with pytest.raises(TypeError, match="expects exception types"):
        resulty("ValueError")  # type: ignore[call-overload]


def test_resulty_rejects_bare_decorator() -> None:
    with pytest.raises(TypeError, match="expects exception types"):

        @resulty  # type: ignore[call-overload]
        def fail() -> int:
            return 1


def test_resulty_rejects_async() -> None:
    async def afunc() -> int:
        return 1

    with pytest.raises(TypeError, match="cannot decorate async functions"):
        resulty()(afunc)


def test_resulty_preserves_metadata() -> None:
    def original(value: int) -> int:
        """Return the value."""
        return value

    wrapped = resulty()(original)
    assert wrapped.__name__ == "original"
    assert wrapped.__doc__ == "Return the value."
    assert getattr(wrapped, "__wrapped__") is original


def test_resulty_forwards_arguments() -> None:
    @resulty()
    def add(a: int, b: int = 0, *, c: int = 0) -> int:
        return a + b + c

    assert add(1, 2, c=3) == Ok(6)


def test_resulty_keeps_exception_instance() -> None:
    error = ValueError("bad")

    @resulty(ValueError)
    def fail() -> None:
        raise error

    result = fail()
    assert isinstance(result, Err)
    assert result.value is error


def test_optionally_some_and_nothing() -> None:
    @optionally
    def head(items: list[int]) -> int | None:
        return items[0] if items else None

    assert head([1, 2]) == Some(1)
    assert head([]) == Nothing()


def test_optionally_keeps_falsey_values() -> None:
    @optionally
    def identity(value: int | str | bool | None) -> int | str | bool | None:
        return value

    assert identity(0) == Some(0)
    assert identity("") == Some("")
    assert identity(False) == Some(False)
    assert identity(None) == Nothing()


def test_optionally_preserves_metadata() -> None:
    def original(value: int) -> int | None:
        """Return the value."""
        return value

    wrapped = optionally(original)
    assert wrapped.__name__ == "original"
    assert wrapped.__doc__ == "Return the value."
    assert getattr(wrapped, "__wrapped__") is original


def test_optionally_rejects_async() -> None:
    async def afunc() -> int | None:
        return 1

    with pytest.raises(TypeError, match="cannot decorate async functions"):
        optionally(afunc)


def test_optionally_propagates_exceptions() -> None:
    @optionally
    def fail() -> int | None:
        raise ValueError("bad")

    with pytest.raises(ValueError, match="bad"):
        fail()


def test_result_eval_ok() -> None:
    assert result_eval(lambda: 1) == Ok(1)


def test_result_eval_err() -> None:
    result = result_eval(lambda: 1 / 0)
    assert isinstance(result, Err)
    assert isinstance(result.value, ZeroDivisionError)


def test_result_eval_does_not_catch_base_exception() -> None:
    class FatalError(BaseException):
        pass

    def fail() -> None:
        raise FatalError

    with pytest.raises(FatalError):
        result_eval(fail)


def test_option_eval() -> None:
    assert option_eval(lambda: None) == Nothing()
    assert option_eval(lambda: 1) == Some(1)


def test_option_eval_keeps_falsey_values() -> None:
    assert option_eval(lambda: 0) == Some(0)
    assert option_eval(lambda: "") == Some("")
    assert option_eval(lambda: False) == Some(False)


def test_option_eval_propagates_exceptions() -> None:
    def fail() -> None:
        raise ValueError("bad")

    with pytest.raises(ValueError, match="bad"):
        option_eval(fail)
