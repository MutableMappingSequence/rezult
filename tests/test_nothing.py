import copy
import pickle

import pytest

from rezult import Nothing, Option


def test_singleton_identity() -> None:
    assert Nothing() is Nothing()


def test_is_option() -> None:
    assert isinstance(Nothing(), Nothing)
    assert isinstance(Nothing(), Option)


def test_copy_and_deepcopy() -> None:
    nothing = Nothing()
    assert copy.copy(nothing) is nothing
    assert copy.deepcopy(nothing) is nothing


def test_pickle() -> None:
    nothing = Nothing()
    assert pickle.loads(pickle.dumps(nothing)) is nothing


def test_equality() -> None:
    assert Nothing() == Nothing()
    assert Nothing() != object()


def test_hash() -> None:
    assert hash(Nothing()) == hash(Nothing())


def test_repr() -> None:
    assert repr(Nothing()) == "Nothing"


def test_match_args() -> None:
    assert Nothing.__match_args__ == ()


def test_cannot_subclass() -> None:
    with pytest.raises(TypeError, match="Nothing cannot be subclassed"):

        class SubNothing(Nothing):  # type: ignore[misc]
            pass
