from dataclasses import dataclass


@dataclass(slots=True)
class Ok[T]:
    result: T


@dataclass(slots=True)
class Error[E]:
    error: E


type Result[T, E] = Ok[T] | Error[E]
