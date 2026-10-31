# rezult

Rust-inspired `Result` and `Option` types for Python 3.12+.

`rezult` makes failure and absence part of the type signature. Instead of
throwing exceptions and hoping every caller remembers to catch them, a
function returns `Ok(value)` or `Err(error)`, and callers handle both cases
explicitly with pattern matching or the built-in combinators.

`rezult` is independent, which means it have no extra dependencies. As a result, it is lightweight and fast.

## Why not `try` - `except`?

Exceptions are invisible in a function signature. Nothing stops an error from
escaping several layers up the stack, and the caller has no way to know which
failures are expected without reading the implementation.

```python
def parse_age(text: str) -> int:
    try:
        age = int(text)
    except ValueError as exc:
        raise RuntimeError("invalid age") from exc
    if age < 0:
        raise ValueError("age must be non-negative")
    return age


try:
    age = parse_age("abc")
except RuntimeError as exc:
    print(f"failed: {exc}")
```

With `rezult`, the failure is part of the return type and the caller handles it
in one place:

```python
from rezult import Err, Ok, resulty


@resulty(ValueError)
def parse_age(text: str) -> int:
    age = int(text)
    if age < 0:
        raise ValueError("age must be non-negative")
    return age


match parse_age("abc"):
    case Ok(age):
        print(f"age = {age}")
    case Err(error):
        print(f"failed: {error}")
```

The main differences:

| | `try` / `except` | `rezult` |
| --- | --- | --- |
| Failure visible in the signature | No | Yes |
| Handling failures | Optional, easy to forget | Explicit `match` or `unwrap` |
| Chaining fallible steps | Nested `try` blocks | `map`, `map_err`, `and_then_res`, `or_else_res` |
| Distinguishing "no value" from "error" | `None` and exceptions get mixed up | Separate `Option` and `Result` types |
| Testing | Must assert on exceptions | Compare values directly |

Notice that `rezult` is designed for providing a pratical way to handle exceptions more tersely, but not taking the place for exceptions such as `KeyboardInterrupted` which contain a specified sematic meaning.

## Installation

```bash
# pip
pip install rezult

# uv
uv add rezult

# uv pip
uv pip install rezult
```

or, from a checkout:

```bash
pip install .
```

Requires Python 3.12 or newer.

## Quick start

### Result

```python
from rezult import Err, Ok, Result


def divide(a: float, b: float) -> Result[float, str]:
    if b == 0:
        return Err("division by zero")
    return Ok(a / b)


match divide(10, 2):
    case Ok(value):
        print(f"result: {value}")   # result: 5.0
    case Err(error):
        print(f"error: {error}")


match divide(1, 0):
    case Ok(value):
        print(f"result: {value}")
    case Err(error):
        print(f"error: {error}")    # error: division by zero
```

Results compose without nested `try` blocks:

```python
def validate(age: int) -> Result[int, str]:
    return Ok(age) if age >= 18 else Err("too young")


result = (
    divide(36, 2)
    .map(int)
    .and_then_res(validate)
)
print(result)  # Ok(18)

print(divide(1, 0).map_err(str).unwrap_or(-1))  # -1
```

Other useful methods include `is_ok()`, `is_err()`, `ok()`, `err()`,
`map_or()`, `inspect()`, `unwrap()`, `expect()`, `or_res()`, and
`or_else_res()`.

### Option

`Option[T]` is either `Some(value)` or `Nothing()`. `Nothing()` is a
singleton, so it can be checked with `is`.

```python
from rezult import Nothing, Option, Some


def find_user(user_id: int) -> Option[str]:
    users = {1: "alice", 2: "bob"}
    return Some(users[user_id]) if user_id in users else Nothing()


match find_user(1):
    case Some(name):
        print(f"hello, {name}")     # hello, alice
    case Nothing():
        print("user not found")


print(find_user(3).unwrap_or("anonymous"))  # anonymous
```

Options chain in the same way:

```python
from functools import partial
from operator import ne

find_user(1).map(str.upper)                 # Some('ALICE')
find_user(1).filter(partial(ne, "alice"))   # Nothing
find_user(3).or_opt(Some("guest"))          # Some('guest')
```

Other useful methods include `is_some()`, `is_none()`, `ok_or()`,
`map_or()`, `map_or_else()`, `and_then_opt()`, `or_else_opt()`, `xor()`,
`zip()`, and `unwrap()`.

### Decorators

`resulty` turns raised exceptions into `Err` values:

```python
from pathlib import Path

from rezult import resulty


@resulty()
def load(path: str) -> str:
    return Path(path).read_text()


@resulty(ValueError, KeyError)
def lookup(data: dict[str, int], key: str) -> int:
    return data[key]


load("missing.txt")          # Err(FileNotFoundError(...))
lookup({"a": 1}, "b")        # Err(KeyError('b'))
```

`optionally` turns a `None` return value into `Nothing()`:

```python
from rezult import optionally


@optionally
def first(items: list[int]) -> int | None:
    return items[0] if items else None


first([1, 2])  # Some(1)
first([])      # Nothing
```

Both decorators preserve the wrapped function's metadata. They raise
`TypeError` for async functions instead of silently returning an un-awaited
coroutine.

### Evaluating expressions

If you already have a callable, use `result_eval` or
`option_eval`:

```python
from rezult import option_eval, result_eval

result_eval(lambda: 1 / 0)      # Err(ZeroDivisionError('division by zero'))
result_eval(int, "42")          # Ok(42)
option_eval(lambda: None)       # Nothing
option_eval(lambda: "value")    # Some('value')
```

## API at a glance

| Export | Description |
| --- | --- |
| `Ok(value)` | Successful `Result` variant |
| `Err(error)` | Failed `Result` variant |
| `Some(value)` | Non-empty `Option` variant |
| `Nothing()` | Empty `Option` variant (singleton) |
| `Result` | Base class and combinators for fallible values |
| `Option` | Base class and combinators for optional values |
| `UnwrapError` | Raised by `unwrap`, `expect`, `unwrap_err`, and `expect_err` |
| `resulty(...)` | Decorator: exceptions become `Err` |
| `optionally` | Decorator: `None` becomes `Nothing()` |
| `result_eval(expr, *args, **kwargs)` | Evaluate a callable, capturing exceptions as `Err` |
| `option_eval(expr, *args, **kwargs)` | Evaluate a callable, converting `None` to `Nothing()` |

Both types support structural pattern matching, equality by variant and
contained value, and hashing.

## Contributing

We allow all kinds of contributions, except for fully AI generated code and contributions that only contain a little human thinking.

## License

MIT
