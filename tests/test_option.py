import pytest

from rezult import Err, Nothing, Ok, Option, Some, UnwrapError


def _fail_on_int_bool(value: int) -> bool:
    raise AssertionError(f"unexpected call with {value!r}")


def _fail_on_int_none(value: int) -> None:
    raise AssertionError(f"unexpected call with {value!r}")


def _fail_default_int() -> int:
    raise AssertionError("unexpected call")


def _fail_int_option(value: int) -> Option[str]:
    raise AssertionError(f"unexpected call with {value!r}")


def _fail_option() -> Option[int]:
    raise AssertionError("unexpected call")


def _fail_str() -> str:
    raise AssertionError("unexpected call")


def test_is_some_and_is_none() -> None:
    assert Some(1).is_some()
    assert not Some(1).is_none()
    assert Nothing().is_none()
    assert not Nothing().is_some()


def test_is_some_and() -> None:
    assert Some(2).is_some_and(lambda value: value == 2)
    assert not Some(2).is_some_and(lambda value: value == 3)
    assert not Nothing().is_some_and(_fail_on_int_bool)


def test_is_none_or() -> None:
    assert Nothing().is_none_or(_fail_on_int_bool)
    assert Some(1).is_none_or(lambda value: value == 1)
    assert not Some(1).is_none_or(lambda value: value == 2)


def test_ok_or() -> None:
    assert Some(1).ok_or("e") == Ok(1)
    assert Nothing().ok_or("e") == Err("e")


def test_ok_or_else() -> None:
    assert Some(1).ok_or_else(_fail_str) == Ok(1)
    assert Nothing().ok_or_else(lambda: "e") == Err("e")


def test_map() -> None:
    assert Some(1).map(lambda value: value + 1) == Some(2)
    assert Nothing().map(_fail_on_int_bool) == Nothing()


def test_map_or() -> None:
    assert Some(1).map_or(0, lambda value: value + 1) == 2
    assert Nothing().map_or(0, _fail_on_int_bool) == 0


def test_map_or_else() -> None:
    assert Some(1).map_or_else(_fail_default_int, lambda value: value + 1) == 2
    assert Nothing().map_or_else(lambda: 7, _fail_on_int_bool) == 7


def test_inspect() -> None:
    seen: list[int] = []
    option = Some(1)
    assert option.inspect(seen.append) is option
    assert seen == [1]

    nothing = Nothing()
    assert nothing.inspect(_fail_on_int_none) is nothing


def test_unwrap() -> None:
    assert Some(1).unwrap() == 1

    with pytest.raises(UnwrapError) as info:
        Nothing().unwrap()
    assert str(info.value) == "Called unwrap on a Nothing value"


def test_unwrap_or() -> None:
    assert Some(1).unwrap_or(0) == 1
    assert Nothing().unwrap_or(0) == 0


def test_unwrap_or_else() -> None:
    assert Some(1).unwrap_or_else(_fail_default_int) == 1
    assert Nothing().unwrap_or_else(lambda: 7) == 7


def test_expect() -> None:
    assert Some(1).expect("boom") == 1

    with pytest.raises(UnwrapError) as info:
        Nothing().expect("boom")
    assert info.value.args == ("boom",)


def test_filter() -> None:
    some = Some(1)
    assert some.filter(lambda value: value == 1) is some
    assert some.filter(lambda value: value == 2) == Nothing()

    nothing = Nothing()
    assert nothing.filter(_fail_on_int_bool) is nothing


def test_and_opt() -> None:
    assert Some(1).and_opt(Some(2)) == Some(2)
    assert Some(1).and_opt(Nothing()) == Nothing()
    assert Nothing().and_opt(Some(2)) == Nothing()


def test_and_then_opt() -> None:
    assert Some(1).and_then_opt(lambda value: Some(value + 1)) == Some(2)
    assert Nothing().and_then_opt(_fail_int_option) == Nothing()


def test_or_opt() -> None:
    assert Some(1).or_opt(Some(2)) == Some(1)
    assert Nothing().or_opt(Some(2)) == Some(2)


def test_or_else_opt() -> None:
    assert Some(1).or_else_opt(_fail_option) == Some(1)
    assert Nothing().or_else_opt(lambda: Some(2)) == Some(2)


def test_xor() -> None:
    assert Some(1).xor(Some(2)) == Nothing()
    assert Some(1).xor(Nothing()) == Some(1)
    assert Nothing().xor(Some(2)) == Some(2)
    assert Nothing().xor(Nothing()) == Nothing()


def test_zip() -> None:
    assert Some(1).zip(Some("a")) == Some((1, "a"))
    assert Some(1).zip(Nothing()) == Nothing()
    assert Nothing().zip(Some("a")) == Nothing()
    assert Nothing().zip(Nothing()) == Nothing()


def test_flatten() -> None:
    assert Option.flatten(Some(Some(1))) == Some(1)
    assert Option.flatten(Some(Nothing())) == Nothing()
    assert Option.flatten(Nothing()) == Nothing()


def test_transpose() -> None:
    assert Option.transpose(Some(Ok(1))) == Ok(Some(1))
    assert Option.transpose(Some(Err("e"))) == Err("e")
    assert Option.transpose(Nothing()) == Ok(Nothing())


def test_equality() -> None:
    assert Some(1) == Some(1)
    assert Some(1) != Some(2)
    assert Some(1) != Nothing()
    assert Nothing() == Nothing()
    assert Nothing() != object()
    assert Some(1) != Ok(1)
    assert Some(1) != 1


def test_hash() -> None:
    assert hash(Some(1)) == hash(Some(1))
    assert hash(Nothing()) == hash(Nothing())

    mapping = {Some(1): "some", Nothing(): "nothing"}
    assert mapping[Some(1)] == "some"
    assert mapping[Nothing()] == "nothing"


def test_repr() -> None:
    assert repr(Some(1)) == "Some(1)"
    assert repr(Some("x")) == "Some('x')"
    assert repr(Nothing()) == "Nothing"


def test_match_args() -> None:
    assert Some.__match_args__ == ("value",)
    assert Nothing.__match_args__ == ()


def test_pattern_matching() -> None:
    def describe(option: Option[int]) -> str:
        match option:
            case Some(value):
                return f"some:{value}"
            case Nothing():
                return "nothing"
            case _:
                return "unknown"

    assert describe(Some(1)) == "some:1"
    assert describe(Nothing()) == "nothing"


def test_base_class_cannot_be_instantiated() -> None:
    with pytest.raises(NotImplementedError):
        Option()
