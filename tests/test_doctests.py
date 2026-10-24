import doctest
from types import ModuleType

import pytest

import rezult.option
import rezult.result


@pytest.mark.parametrize(
    "module",
    [rezult.result, rezult.option],
    ids=["result", "option"],
)
def test_module_doctests(module: ModuleType) -> None:
    outcome = doctest.testmod(module, verbose=False)
    assert outcome.failed == 0
    assert outcome.attempted > 0
