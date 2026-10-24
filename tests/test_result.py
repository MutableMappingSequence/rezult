import pytest

from rezult import Err, Nothing, Ok, Result, Some, UnwrapError


def _fail_on_int(value: int) -> None:
    raise AssertionError(f"unexpected call with {value!r}")


def _fail_on_str(value: str) -> None:
    raise AssertionError(f"unexpected call with {value!r}")


def _fail_on_str_int(value: str) -> int:
    raise AssertionError(f"unexpected call with {value!r}")


def _fail_on_int_result(value: int) -> Result[str, str]:
    raise AssertionError(f"unexpected call with {value!r}")


def _fail_on_str_result(value: str) -> Result[int, str]:
    raise AssertionError(f"unexpected call with {value!r}")


def test_is_ok_and_is_err() -> None:
    assert Ok(1).is_ok()
    assert not Ok(1).is_err()
    assert Err("e").is_err()
    assert not Err("e").is_ok()


def test_is_ok_and() -> None:
    assert Ok(2).is_ok_and(lambda value: value == 2)
    assert not Ok(2).is_ok_and(lambda value: value == 3)
    assert not Err("e").is_ok_and(lambda value: True)


def test_is_err_and() -> None:
    assert Err("e").is_err_and(lambda error: error == "e")
    assert not Err("e").is_err_and(lambda error: error == "f")
    assert not Ok(1).is_err_and(lambda error: True)


def test_ok_and_err() -> None:
    assert Ok(1).ok() == Some(1)
    assert Err("e").ok() == Nothing()
    assert Ok(1).err() == Nothing()
    assert Err("e").err() == Some("e")


def test_map() -> None:
    assert Ok(1).map(lambda value: value + 1) == Ok(2)
    assert Err("e").map(lambda value: value + 1) == Err("e")


def test_map_or() -> None:
    assert Ok(1).map_or(0, lambda value: value + 1) == 2
    assert Err("e").map_or(0, lambda value: value + 1) == 0


def test_map_err() -> None:
    assert Ok(1).map_err(str.upper) == Ok(1)
    assert Err("e").map_err(str.upper) == Err("E")


def test_inspect() -> None:
    seen: list[int] = []
    result = Ok(1)
    assert result.inspect(seen.append) is result
    assert seen == [1]

    error = Err("e")
    assert error.inspect(_fail_on_int) is error


def test_inspect_err() -> None:
    seen: list[str] = []
    error = Err("e")
    assert error.inspect_err(seen.append) is error
    assert seen == ["e"]

    result = Ok(1)
    assert result.inspect_err(_fail_on_str) is result


def test_unwrap() -> None:
    assert Ok(1).unwrap() == 1

    with pytest.raises(UnwrapError) as info:
        Err("e").unwrap()
    assert info.value.args == ("e",)


def test_unwrap_or() -> None:
    assert Ok(1).unwrap_or(0) == 1
    assert Err("e").unwrap_or(0) == 0


def test_unwrap_or_else() -> None:
    assert Ok(1).unwrap_or_else(_fail_on_str_int) == 1
    assert Err("e").unwrap_or_else(len) == 1


def test_expect() -> None:
    assert Ok(1).expect("boom") == 1

    with pytest.raises(UnwrapError) as info:
        Err("e").expect("boom")
    assert info.value.args == ("boom",)


def test_unwrap_err() -> None:
    assert Err("e").unwrap_err() == "e"

    with pytest.raises(UnwrapError) as info:
        Ok(1).unwrap_err()
    assert info.value.args == (1,)


def test_expect_err() -> None:
    assert Err("e").expect_err("boom") == "e"

    with pytest.raises(UnwrapError) as info:
        Ok(1).expect_err("boom")
    assert info.value.args == ("boom",)


def test_and_res() -> None:
    assert Ok(1).and_res(Ok("x")) == Ok("x")
    assert Ok(1).and_res(Err("x")) == Err("x")
    assert Err("e").and_res(Ok("x")) == Err("e")


def test_and_then_res() -> None:
    assert Ok(1).and_then_res(lambda value: Ok(value + 1)) == Ok(2)
    assert Err("e").and_then_res(_fail_on_int_result) == Err("e")


def test_or_res() -> None:
    assert Ok(1).or_res(Ok(2)) == Ok(1)
    assert Err("e").or_res(Ok(2)) == Ok(2)


def test_or_else_res() -> None:
    assert Ok(1).or_else_res(_fail_on_str_result) == Ok(1)
    assert Err("e").or_else_res(lambda error: Ok(len(error))) == Ok(1)


def test_transpose() -> None:
    assert Result.transpose(Ok(Some(1))) == Some(Ok(1))
    assert Result.transpose(Ok(Nothing())) == Nothing()
    assert Result.transpose(Err("e")) == Some(Err("e"))


def test_flatten() -> None:
    assert Result.flatten(Ok(Ok(1))) == Ok(1)
    assert Result.flatten(Ok(Err("e"))) == Err("e")
    assert Result.flatten(Err("e")) == Err("e")


def test_equality() -> None:
    assert Ok(1) == Ok(1)
    assert Ok(1) != Ok(2)
    assert Ok(1) != Err(1)
    assert Err("e") == Err("e")
    assert Err("e") != Err("f")
    assert Ok(1) != Some(1)
    assert Ok(1) != 1
    assert Err("e") != "e"


def test_hash() -> None:
    assert hash(Ok(1)) == hash(Ok(1))
    assert hash(Err("e")) == hash(Err("e"))
    assert {Ok(1): "ok"}[Ok(1)] == "ok"


def test_repr() -> None:
    assert repr(Ok(1)) == "Ok(1)"
    assert repr(Ok("x")) == "Ok('x')"
    assert repr(Err("e")) == "Err('e')"
    assert repr(Ok(Some(1))) == "Ok(Some(1))"


def test_match_args() -> None:
    assert Ok.__match_args__ == ("value",)
    assert Err.__match_args__ == ("value",)


def test_pattern_matching() -> None:
    def describe(result: Result[int, str]) -> str:
        match result:
            case Ok(value):
                return f"ok:{value}"
            case Err(error):
                return f"err:{error}"
            case _:
                return "unknown"

    assert describe(Ok(1)) == "ok:1"
    assert describe(Err("e")) == "err:e"


def test_base_class_cannot_be_instantiated() -> None:
    with pytest.raises(NotImplementedError):
        Result()
