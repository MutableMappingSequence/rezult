"""A Rust-inspired ``Option`` type for values that may be absent.

``Option[T]`` represents either a present value (``Some``) or no value
(``Nothing``), replacing ad-hoc ``None`` checks with an explicit type.
"""

from __future__ import annotations

from collections.abc import Callable
from functools import wraps
from inspect import iscoroutinefunction
from typing import TYPE_CHECKING, Any, ClassVar, Final, Never, Self, final

from .result import Err, Ok, UnwrapError

if TYPE_CHECKING:
    from .result import Result


def _any_some(anything: Any) -> Some[Any]:
    return anything


_UNSUPPORTED = NotImplementedError("Unsupported option type")


class Option[T]:
    """An optional value: either ``Some`` or ``Nothing``.

    ``Option`` is an abstract base class; every instance is either ``Some`` or
    ``Nothing``. ``Nothing`` is a singleton, so it can be checked with ``is``.

    Example:
        >>> match Some(1):
        ...     case Some(value):
        ...         print(value)
        ...     case Nothing():
        ...         print("empty")
        1
    """

    def __init__(self) -> None:
        """Initialize an option variant.

        ``Option`` is abstract; instantiate ``Some`` or ``Nothing`` instead.

        Raises:
            NotImplementedError: Always, when called on ``Option`` directly.
        """
        raise NotImplementedError("You should implement __init__ for the variant first.")

    # ==========
    # Assertions
    # ==========

    def is_some(self) -> bool:
        """Return whether the option contains a value.

        Returns:
            ``True`` if this is ``Some``, ``False`` if it is ``Nothing``.
        """
        return isinstance(self, Some)

    def is_some_and(self, f: Callable[[T], bool]) -> bool:
        """Return whether the option is ``Some`` and its value satisfies ``f``.

        Args:
            f: Predicate applied to the contained value.

        Returns:
            The predicate's result when this is ``Some``, otherwise ``False``.
        """
        match self:
            case Some(value):
                return f(value)
            case Nothing():
                return False
            case _:
                raise _UNSUPPORTED

    def is_none(self) -> bool:
        """Return whether the option is ``Nothing``.

        Returns:
            ``True`` if this is ``Nothing``, ``False`` if it is ``Some``.
        """
        return not self.is_some()

    def is_none_or(self, f: Callable[[T], bool]) -> bool:
        """Return whether the option is ``Nothing`` or its value satisfies ``f``.

        Args:
            f: Predicate applied to the contained value.

        Returns:
            The predicate's result when this is ``Some``, otherwise ``True``.
        """
        match self:
            case Some(value):
                return f(value)
            case Nothing():
                return True
            case _:
                raise _UNSUPPORTED

    # ========
    # Castings
    # ========

    def ok_or[E](self, err: E) -> Result[T, E]:
        """Convert to a ``Result`` using the given error.

        Args:
            err: Error value used when this is ``Nothing``.

        Returns:
            ``Ok`` with the contained value, or ``Err(err)``.
        """
        match self:
            case Some(value):
                return Ok(value)
            case Nothing():
                return Err(err)
            case _:
                raise _UNSUPPORTED

    def ok_or_else[E](self, op: Callable[[], E]) -> Result[T, E]:
        """Convert to a ``Result``, computing the error lazily.

        Args:
            op: Zero-argument callable producing the error when this is
                ``Nothing``.

        Returns:
            ``Ok`` with the contained value, or ``Err`` with the produced
            error.
        """
        match self:
            case Some(value):
                return Ok(value)
            case Nothing():
                return Err(op())
            case _:
                raise _UNSUPPORTED

    # ========
    # Mappings
    # ========

    def map[U](self, op: Callable[[T], U]) -> Option[U]:
        """Apply ``op`` to the contained value.

        Args:
            op: Function applied to the ``Some`` value.

        Returns:
            ``Some`` with the mapped value, or ``Nothing``.
        """
        match self:
            case Some(value):
                return Some(op(value))
            case Nothing():
                return Nothing()
            case _:
                raise _UNSUPPORTED

    def map_or[U](self, default: U, f: Callable[[T], U]) -> U:
        """Return the mapped contained value, or ``default``.

        Args:
            default: Value returned when this is ``Nothing``.
            f: Function applied to the ``Some`` value.

        Returns:
            The mapped value or ``default``.
        """
        match self:
            case Some(value):
                return f(value)
            case Nothing():
                return default
            case _:
                raise _UNSUPPORTED

    def map_or_else[U](self, default: Callable[[], U], f: Callable[[T], U]) -> U:
        """Return the mapped contained value, or compute a default.

        Args:
            default: Zero-argument callable producing the value for
                ``Nothing``.
            f: Function applied to the ``Some`` value.

        Returns:
            The mapped value or the value produced by ``default``.
        """
        match self:
            case Some(value):
                return f(value)
            case Nothing():
                return default()
            case _:
                raise _UNSUPPORTED

    # ===========
    # Inspectings
    # ===========

    def inspect(self, f: Callable[[T], None]) -> Self:
        """Run ``f`` on the contained value for its side effects.

        Args:
            f: Function called with the ``Some`` value.

        Returns:
            The same option, unchanged.
        """
        if isinstance(self, Some):
            f(self.value)
        return self

    # ==========
    # Unwrapping
    # ==========

    def unwrap(self) -> T:
        """Return the contained value.

        Returns:
            The ``Some`` value.

        Raises:
            UnwrapError: If this is ``Nothing``.
        """
        match self:
            case Some(value):
                return value
            case Nothing():
                raise UnwrapError("Called unwrap on a Nothing value")
            case _:
                raise _UNSUPPORTED

    def unwrap_or(self, default: T) -> T:
        """Return the contained value or ``default``.

        Args:
            default: Value returned when this is ``Nothing``.

        Returns:
            The ``Some`` value or ``default``.
        """
        match self:
            case Some(value):
                return value
            case Nothing():
                return default
            case _:
                raise _UNSUPPORTED

    def unwrap_or_else(self, op: Callable[[], T]) -> T:
        """Return the contained value or compute one.

        Args:
            op: Zero-argument callable producing the value when this is
                ``Nothing``.

        Returns:
            The ``Some`` value or the value produced by ``op``.
        """
        match self:
            case Some(value):
                return value
            case Nothing():
                return op()
            case _:
                raise _UNSUPPORTED

    def expect(self, msg: str) -> T:
        """Return the contained value, raising with ``msg`` on ``Nothing``.

        Args:
            msg: Message used for the raised exception.

        Returns:
            The ``Some`` value.

        Raises:
            UnwrapError: If this is ``Nothing``.
        """
        match self:
            case Some(value):
                return value
            case Nothing():
                raise UnwrapError(msg)
            case _:
                raise _UNSUPPORTED

    # =========
    # Filtering
    # =========

    def filter(self, predicate: Callable[[T], bool]) -> Option[T]:
        """Keep the value only if it satisfies ``predicate``.

        Args:
            predicate: Function applied to the ``Some`` value.

        Returns:
            This option when the predicate holds, otherwise ``Nothing``.
        """
        match self:
            case Some(value):
                return self if predicate(value) else Nothing()
            case Nothing():
                return self
            case _:
                raise _UNSUPPORTED

    # =========
    # Operating
    # =========

    def and_opt[U](self, opt: Option[U]) -> Option[U]:
        """Return ``opt`` if this is ``Some``, otherwise ``Nothing``.

        Args:
            opt: Option returned when this is ``Some``.

        Returns:
            ``opt`` when this is ``Some``, otherwise ``Nothing``.
        """
        match self:
            case Some():
                return opt
            case Nothing():
                return Nothing()
            case _:
                raise _UNSUPPORTED

    def and_then_opt[U](self, op: Callable[[T], Option[U]]) -> Option[U]:
        """Chain another optional operation.

        Args:
            op: Function called with the ``Some`` value; it must return an
                ``Option``.

        Returns:
            The result of ``op`` when this is ``Some``, otherwise ``Nothing``.
        """
        match self:
            case Some(value):
                return op(value)
            case Nothing():
                return Nothing()
            case _:
                raise _UNSUPPORTED

    def or_opt(self, opt: Option[T]) -> Option[T]:
        """Return this option if it is ``Some``, otherwise ``opt``.

        Args:
            opt: Option returned when this is ``Nothing``.

        Returns:
            This option when it is ``Some``, otherwise ``opt``.
        """
        match self:
            case Some():
                return self
            case Nothing():
                return opt
            case _:
                raise _UNSUPPORTED

    def or_else_opt(self, op: Callable[[], Option[T]]) -> Option[T]:
        """Return this option if it is ``Some``, otherwise call ``op``.

        Args:
            op: Zero-argument callable returning an ``Option`` when this is
                ``Nothing``.

        Returns:
            This option when it is ``Some``, otherwise the result of ``op``.
        """
        match self:
            case Some():
                return self
            case Nothing():
                return op()
            case _:
                raise _UNSUPPORTED

    def xor(self, opt: Option[T]) -> Option[T]:
        """Return the value from exactly one of the two options.

        Args:
            opt: The other option.

        Returns:
            The ``Some`` value when exactly one option is ``Some``, otherwise
            ``Nothing``.
        """
        match (self, opt):
            case (Some(_) as some, Nothing()):
                return some
            case (Nothing(), Some(_) as some):
                return some
            case (Some(_), Some(_)) | (Nothing(), Nothing()):
                return Nothing()
            case _:
                raise _UNSUPPORTED

    def zip[U](self, other: Option[U]) -> Option[tuple[T, U]]:
        """Combine two options into a tuple.

        Args:
            other: The option to pair with.

        Returns:
            ``Some((left, right))`` when both are ``Some``, otherwise
            ``Nothing``.
        """
        match (self, other):
            case (Some(left), Some(right)):
                return Some((left, right))
            case (Some(_), Nothing()) | (Nothing(), Some(_)) | (Nothing(), Nothing()):
                return Nothing()
            case _:
                raise _UNSUPPORTED

    # =============
    # Transformings
    # =============

    @classmethod
    def flatten(cls, option: Option[Option[T]]) -> Option[T]:
        """Flatten a nested ``Option``.

        Args:
            option: An ``Option`` whose value is another ``Option``.

        Returns:
            The inner option.

        Example:
            >>> Option.flatten(Some(Some(1)))
            Some(1)
            >>> Option.flatten(Some(Nothing()))
            Nothing
        """
        match option:
            case Some(inner):
                return inner
            case Nothing():
                return Nothing()
            case _:
                raise _UNSUPPORTED

    @classmethod
    def transpose[E](cls, option: Option[Result[T, E]]) -> Result[Option[T], E]:
        """Swap ``Option`` and ``Result`` nesting.

        Args:
            option: An ``Option`` whose value may be a ``Result``.

        Returns:
            ``Ok(Some(value))`` for ``Some(Ok(value))``, ``Err(error)`` for
            ``Some(Err(error))``, and ``Ok(Nothing())`` for ``Nothing()``.

        Example:
            >>> Option.transpose(Some(Ok(1)))
            Ok(Some(1))
            >>> Option.transpose(Nothing())
            Ok(Nothing)
        """
        match option:
            case Some(Ok(value)):
                return Ok(Some(value))
            case Some(Err(value)):
                return Err(value)
            case Nothing():
                return Ok(Nothing())
            case _:
                raise _UNSUPPORTED


class Some[T](Option[T]):
    """The variant of ``Option`` that contains a value.

    Args:
        value: The contained value.

    Attributes:
        value: The contained value.
    """

    __slots__ = ("value",)
    __match_args__ = ("value",)

    def __init__(self, value: T) -> None:
        """Initialize the variant with a value.

        Args:
            value: The contained value.
        """
        self.value: Final = value

    def __repr__(self) -> str:
        return f"Some({self.value!r})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Some) or type(self) is not type(_any_some(other)):
            return NotImplemented
        return self.value == _any_some(other).value

    def __hash__(self) -> int:
        return hash((Some, self.value))


@final
class Nothing(Option[Any]):
    """The empty variant of ``Option``.

    ``Nothing`` is a singleton: every call to ``Nothing()`` returns the same
    instance, and instances compare equal only to themselves. The class cannot
    be subclassed.

    Example:
        >>> Nothing() is Nothing()
        True
        >>> repr(Nothing())
        'Nothing'
    """

    __slots__ = ()
    __match_args__ = ()

    _instance: ClassVar[Nothing | None] = None

    def __new__(cls) -> Nothing:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init_subclass__(cls, **kwargs: Any) -> Never:
        raise TypeError("Nothing cannot be subclassed")

    def __init__(self) -> None:
        """Do nothing; the singleton instance is created in ``__new__``."""

    def __repr__(self) -> str:
        return "Nothing"

    def __eq__(self, other: object) -> bool:
        return self is other

    def __hash__(self) -> int:
        return hash(Nothing)

    def __copy__(self) -> Self:
        return self

    def __deepcopy__(self, memo: dict[int, Any]) -> Self:
        return self

    def __reduce__(self) -> tuple[Any, ...]:
        return (Nothing, ())


def option_eval[**P, T](expr: Callable[P, T | None], *args: P.args, **kwargs: P.kwargs) -> Option[T]:
    """Evaluate ``expr`` eagerly, converting ``None`` into ``Nothing``.

    Args:
        expr: Callable to evaluate.
        *args: Positional arguments forwarded to ``expr``.
        **kwargs: Keyword arguments forwarded to ``expr``.

    Returns:
        ``Some`` with the returned value, or ``Nothing`` when it returns
        ``None``.

    Example:
        >>> option_eval(lambda: 1)
        Some(1)
        >>> option_eval(lambda: None)
        Nothing
        >>> option_eval(lambda a: a, None)
        Nothing
    """
    value = expr(*args, **kwargs)
    return Nothing() if value is None else Some(value)


def optionally[**P, R](func: Callable[P, R | None]) -> Callable[P, Option[R]]:
    """Decorate a function so a ``None`` return value becomes ``Nothing``.

    Args:
        func: Function whose return value may be ``None``.

    Returns:
        A wrapper that returns ``Some`` for non-``None`` results and
        ``Nothing`` for ``None``.

    Raises:
        TypeError: If ``func`` is an async function.

    Example:
        >>> @optionally
        ... def head(items: list[int]) -> int | None:
        ...     return items[0] if items else None
        ...
        >>> head([1, 2])
        Some(1)
        >>> head([])
        Nothing
    """
    if iscoroutinefunction(func):
        raise TypeError("optionally() cannot decorate async functions")

    @wraps(func)
    def new(*args: P.args, **kwargs: P.kwargs) -> Option[R]:
        value = func(*args, **kwargs)
        return Nothing() if value is None else Some(value)

    return new
