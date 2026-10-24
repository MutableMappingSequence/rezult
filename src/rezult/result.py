"""A Rust-inspired ``Result`` type for explicit error handling.

``Result[T, E]`` represents either success (``Ok``) or failure (``Err``),
making error handling visible in the type signature.
"""

from __future__ import annotations

from collections.abc import Callable
from functools import wraps
from inspect import iscoroutinefunction
from typing import TYPE_CHECKING
from typing import Any
from typing import Final
from typing import Protocol
from typing import Self
from typing import cast
from typing import overload


if TYPE_CHECKING:
    from .option import Option


def _any_ok(anything: Any) -> Ok[Any]:
    return anything


def _any_err(anything: Any) -> Err[Any]:
    return anything


_UNSUPPORTED = NotImplementedError("Unsupported result type")


class UnwrapError(Exception):
    """Raised when unwrapping a ``Result`` with the wrong variant.

    The exception argument is either the contained ``Err`` value (for
    ``unwrap`` and ``unwrap_err``) or the message supplied to ``expect`` and
    ``expect_err``.
    """


class Result[T, E]:
    """The outcome of an operation that can fail.

    ``Result`` is an abstract base class; every instance is either ``Ok`` or
    ``Err``. Branch on the variant with pattern matching or with the
    ``is_ok``/``is_err`` helpers.

    Example:
        >>> match Ok(1):
        ...     case Ok(value):
        ...         print(value)
        ...     case Err(error):
        ...         print(error)
        1
    """

    def __init__(self) -> None:
        """Initialize a result variant.

        ``Result`` is abstract; instantiate ``Ok`` or ``Err`` instead.

        Raises:
            NotImplementedError: Always, when called on ``Result`` directly.
        """
        raise NotImplementedError(
            "You should implement __init__ for the variant first."
        )

    # ==========
    # Assertions
    # ==========

    def is_ok(self) -> bool:
        """Return whether the result is ``Ok``.

        Returns:
            ``True`` if this is ``Ok``, ``False`` if it is ``Err``.
        """
        return isinstance(self, Ok)

    def is_ok_and(self, f: Callable[[T], bool]) -> bool:
        """Return whether the result is ``Ok`` and its value satisfies ``f``.

        Args:
            f: Predicate applied to the contained value.

        Returns:
            The predicate's result when this is ``Ok``, otherwise ``False``.
        """
        match self:
            case Ok(value):
                return f(value)
            case Err():
                return False
            case _:
                raise _UNSUPPORTED

    def is_err(self) -> bool:
        """Return whether the result is ``Err``.

        Returns:
            ``True`` if this is ``Err``, ``False`` if it is ``Ok``.
        """
        return not self.is_ok()

    def is_err_and(self, f: Callable[[E], bool]) -> bool:
        """Return whether the result is ``Err`` and its value satisfies ``f``.

        Args:
            f: Predicate applied to the contained error.

        Returns:
            The predicate's result when this is ``Err``, otherwise ``False``.
        """
        match self:
            case Ok():
                return False
            case Err(value):
                return f(value)
            case _:
                raise _UNSUPPORTED

    # ========
    # Castings
    # ========

    def ok(self) -> Option[T]:
        """Convert to an ``Option``, discarding the error.

        Returns:
            ``Some`` containing the success value, or ``Nothing`` for ``Err``.
        """
        from .option import Nothing
        from .option import Some

        match self:
            case Ok(value):
                return Some(value)
            case Err():
                return Nothing()
            case _:
                raise _UNSUPPORTED

    def err(self) -> Option[E]:
        """Convert to an ``Option``, discarding the success value.

        Returns:
            ``Some`` containing the error, or ``Nothing`` for ``Ok``.
        """
        from .option import Nothing
        from .option import Some

        match self:
            case Ok():
                return Nothing()
            case Err(value):
                return Some(value)
            case _:
                raise _UNSUPPORTED

    # ========
    # Mappings
    # ========

    def map[U](self, op: Callable[[T], U]) -> Result[U, E]:
        """Apply ``op`` to the success value, leaving ``Err`` untouched.

        Args:
            op: Function applied to the ``Ok`` value.

        Returns:
            A new ``Result`` with the mapped value, or the original error.
        """
        match self:
            case Ok(value):
                return Ok(op(value))
            case Err(value):
                return Err(value)
            case _:
                raise _UNSUPPORTED

    def map_or[U](self, default: U, f: Callable[[T], U]) -> U:
        """Return the mapped success value, or ``default`` for ``Err``.

        Args:
            default: Value returned when this is ``Err``.
            f: Function applied to the ``Ok`` value.

        Returns:
            The mapped value or ``default``.
        """
        match self:
            case Ok(value):
                return f(value)
            case Err():
                return default
            case _:
                raise _UNSUPPORTED

    def map_err[F](self, op: Callable[[E], F]) -> Result[T, F]:
        """Apply ``op`` to the error value, leaving ``Ok`` untouched.

        Args:
            op: Function applied to the ``Err`` value.

        Returns:
            A new ``Result`` with the mapped error, or the original success.
        """
        match self:
            case Ok(value):
                return Ok(value)
            case Err(value):
                return Err(op(value))
            case _:
                raise _UNSUPPORTED

    # ===========
    # Inspectings
    # ===========

    def inspect(self, f: Callable[[T], None]) -> Self:
        """Run ``f`` on the success value for its side effects.

        Args:
            f: Function called with the ``Ok`` value.

        Returns:
            The same result, unchanged.
        """
        if isinstance(self, Ok):
            f(self.value)
        return self

    def inspect_err(self, f: Callable[[E], None]) -> Self:
        """Run ``f`` on the error value for its side effects.

        Args:
            f: Function called with the ``Err`` value.

        Returns:
            The same result, unchanged.
        """
        if isinstance(self, Err):
            f(self.value)
        return self

    # ==========
    # Unwrapping
    # ==========

    def unwrap(self) -> T:
        """Return the success value.

        Returns:
            The contained ``Ok`` value.

        Raises:
            UnwrapError: If this is ``Err``; the error value becomes the
                exception argument.
        """
        match self:
            case Ok(value):
                return value
            case Err(value):
                raise UnwrapError(value)
            case _:
                raise _UNSUPPORTED

    def unwrap_or(self, default: T) -> T:
        """Return the success value or ``default``.

        Args:
            default: Value returned when this is ``Err``.

        Returns:
            The ``Ok`` value or ``default``.
        """
        match self:
            case Ok(value):
                return value
            case Err():
                return default
            case _:
                raise _UNSUPPORTED

    def unwrap_or_else(self, op: Callable[[E], T]) -> T:
        """Return the success value or compute one from the error.

        Args:
            op: Function called with the ``Err`` value when this is ``Err``.

        Returns:
            The ``Ok`` value or the value produced by ``op``.
        """
        match self:
            case Ok(value):
                return value
            case Err(value):
                return op(value)
            case _:
                raise _UNSUPPORTED

    def expect(self, msg: str) -> T:
        """Return the success value, raising with ``msg`` on ``Err``.

        Args:
            msg: Message used for the raised exception.

        Returns:
            The contained ``Ok`` value.

        Raises:
            UnwrapError: If this is ``Err``.
        """
        match self:
            case Ok(value):
                return value
            case Err():
                raise UnwrapError(msg)
            case _:
                raise _UNSUPPORTED

    def unwrap_err(self) -> E:
        """Return the error value.

        Returns:
            The contained ``Err`` value.

        Raises:
            UnwrapError: If this is ``Ok``; the success value becomes the
                exception argument.
        """
        match self:
            case Ok(value):
                raise UnwrapError(value)
            case Err(value):
                return value
            case _:
                raise _UNSUPPORTED

    def expect_err(self, msg: str) -> E:
        """Return the error value, raising with ``msg`` on ``Ok``.

        Args:
            msg: Message used for the raised exception.

        Returns:
            The contained ``Err`` value.

        Raises:
            UnwrapError: If this is ``Ok``.
        """
        match self:
            case Ok():
                raise UnwrapError(msg)
            case Err(value):
                return value
            case _:
                raise _UNSUPPORTED

    # =========
    # Operating
    # =========

    def and_res[U](self, res: Result[U, E]) -> Result[U, E]:
        """Return ``res`` if this is ``Ok``, otherwise propagate the error.

        Args:
            res: Result returned when this is ``Ok``.

        Returns:
            ``res`` when this is ``Ok``, otherwise a new ``Err`` holding the
            same error.
        """
        match self:
            case Ok():
                return res
            case Err(value):
                return Err(value)
            case _:
                raise _UNSUPPORTED

    def and_then_res[U](self, op: Callable[[T], Result[U, E]]) -> Result[U, E]:
        """Chain another fallible operation.

        Args:
            op: Function called with the ``Ok`` value; it must return a
                ``Result``.

        Returns:
            The result of ``op`` when this is ``Ok``, otherwise the original
            error.
        """
        match self:
            case Ok(value):
                return op(value)
            case Err(value):
                return Err(value)
            case _:
                raise _UNSUPPORTED

    def or_res[F](self, res: Result[T, F]) -> Result[T, F]:
        """Return this result if it is ``Ok``, otherwise ``res``.

        Args:
            res: Result returned when this is ``Err``.

        Returns:
            This result when it is ``Ok``, otherwise ``res``.
        """
        match self:
            case Ok(value):
                return Ok(value)
            case Err():
                return res
            case _:
                raise _UNSUPPORTED

    def or_else_res[F](self, op: Callable[[E], Result[T, F]]) -> Result[T, F]:
        """Return this result if it is ``Ok``, otherwise call ``op``.

        Args:
            op: Function called with the ``Err`` value; it must return a
                ``Result``.

        Returns:
            This result when it is ``Ok``, otherwise the result of ``op``.
        """
        match self:
            case Ok(value):
                return Ok(value)
            case Err(value):
                return op(value)
            case _:
                raise _UNSUPPORTED

    @classmethod
    def transpose(cls, result: Result[Option[T], E]) -> Option[Result[T, E]]:
        """Swap ``Result`` and ``Option`` nesting.

        Args:
            result: A ``Result`` whose success value may be an ``Option``.

        Returns:
            ``Some(Ok(value))`` for ``Ok(Some(value))``, ``Nothing`` for
            ``Ok(Nothing())``, and ``Some(Err(error))`` for ``Err(error)``.

        Example:
            >>> from rezult.option import Nothing, Some
            >>> Result.transpose(Ok(Some(1)))
            Some(Ok(1))
            >>> Result.transpose(Ok(Nothing()))
            Nothing
        """
        from .option import Nothing
        from .option import Some

        match result:
            case Ok(Some(value)):
                return Some(Ok(value))
            case Ok(Nothing()):
                return Nothing()
            case Err(value):
                return Some(Err(value))
            case _:
                raise _UNSUPPORTED

    @classmethod
    def flatten(cls, result: Result[Result[T, E], E]) -> Result[T, E]:
        """Flatten a nested ``Result``.

        Args:
            result: A ``Result`` whose success value is another ``Result``.

        Returns:
            The inner result, or the outer error.

        Example:
            >>> Result.flatten(Ok(Ok(1)))
            Ok(1)
        """
        match result:
            case Ok(inner):
                return inner
            case Err(value):
                return Err(value)
            case _:
                raise _UNSUPPORTED


class Ok[T](Result[T, Any]):
    """The success variant of ``Result``.

    Args:
        value: The success value.

    Attributes:
        value: The contained success value.
    """

    __slots__ = ("value",)
    __match_args__ = ("value",)

    def __init__(self, value: T) -> None:
        """Initialize the success variant.

        Args:
            value: The success value.
        """
        self.value: Final = value

    def __repr__(self) -> str:
        return f"Ok({self.value!r})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Ok) or type(self) is not type(_any_ok(other)):
            return NotImplemented
        return self.value == _any_ok(other).value

    def __hash__(self) -> int:
        return hash((Ok, self.value))


class Err[E](Result[Any, E]):
    """The failure variant of ``Result``.

    Args:
        value: The error value.

    Attributes:
        value: The contained error value.
    """

    __slots__ = ("value",)
    __match_args__ = ("value",)

    def __init__(self, value: E) -> None:
        """Initialize the failure variant.

        Args:
            value: The error value.
        """
        self.value: Final = value

    def __repr__(self) -> str:
        return f"Err({self.value!r})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Err) or type(self) is not type(_any_err(other)):
            return NotImplemented
        return self.value == _any_err(other).value

    def __hash__(self) -> int:
        return hash((Err, self.value))


def result_eval[T](expr: Callable[[], T]) -> Result[T, Exception]:
    """Evaluate ``expr`` eagerly, capturing any ``Exception`` as ``Err``.

    Args:
        expr: Zero-argument callable to evaluate.

    Returns:
        ``Ok`` with the returned value, or ``Err`` with the raised exception.

    Example:
        >>> result_eval(lambda: 1 + 1)
        Ok(2)
        >>> result_eval(lambda: 1 / 0)
        Err(ZeroDivisionError('division by zero'))
    """
    try:
        return Ok(expr())
    except Exception as e:
        return Err(e)


class _ResultDecorator[E: BaseException](Protocol):
    def __call__[**P, R](self, func: Callable[P, R]) -> Callable[P, Result[R, E]]: ...


def _catch[E: BaseException](*exceptions: type[E]) -> _ResultDecorator[E]:
    def wrapper[**P, R](func: Callable[P, R]) -> Callable[P, Result[R, E]]:
        if iscoroutinefunction(func):
            raise TypeError("resulty() cannot decorate async functions")

        @wraps(func)
        def new(*args: P.args, **kwargs: P.kwargs) -> Result[R, E]:
            try:
                return Ok(func(*args, **kwargs))
            except exceptions as e:
                return Err(e)

        return new

    return cast(_ResultDecorator[E], wrapper)


@overload
def resulty() -> _ResultDecorator[Exception]: ...


@overload
def resulty[E: BaseException](
    catch: type[E], *catches: type[E]
) -> _ResultDecorator[E]: ...


def resulty(catch: Any = None, *catches: Any) -> Any:
    """Decorate a function so raised exceptions become ``Err`` values.

    The decorated function returns ``Ok`` with its normal return value, or
    ``Err`` with the first exception matching the configured types.

    Args:
        catch: First exception type to catch. When omitted, ``Exception`` is
            used.
        *catches: Additional exception types to catch.

    Returns:
        A decorator that wraps the target function.

    Raises:
        TypeError: If ``catch`` is not an exception type, or if the decorated
            function is async.

    Example:
        >>> @resulty()
        ... def half(value: int) -> int:
        ...     if value % 2:
        ...         raise ValueError("odd")
        ...     return value // 2
        ...
        >>> half(4)
        Ok(2)
        >>> half(3)
        Err(ValueError('odd'))
    """
    if catch is None:
        return _catch(Exception)

    if not (isinstance(catch, type) and issubclass(catch, BaseException)):
        raise TypeError(
            "resulty() expects exception types; write @resulty() or @resulty(SomeError)"
        )

    return _catch(catch, *catches)
