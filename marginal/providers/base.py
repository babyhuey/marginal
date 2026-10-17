"""The `ModelProvider` interface every concrete provider implements."""

from __future__ import annotations

from collections.abc import AsyncIterator, Awaitable, Callable
from typing import Protocol, runtime_checkable

from pydantic import BaseModel, ValidationError

from marginal.providers.errors import ProviderResponseError


@runtime_checkable
class ModelProvider(Protocol):
    """A callable LLM backend, resolved from one `provider` value in `models:`."""

    async def generate(self, prompt: str, **kwargs: object) -> str:
        """Generate a single text completion for `prompt`."""
        ...

    async def generate_structured(
        self, prompt: str, schema: type[BaseModel], **kwargs: object
    ) -> BaseModel:
        """Generate a completion validated against `schema`."""
        ...

    # Declared without `async` on purpose: concrete implementations are async
    # generator functions (`async def ...: yield ...`), which return an
    # AsyncIterator directly when called rather than a coroutine to await.
    def stream(self, prompt: str, **kwargs: object) -> AsyncIterator[str]:
        """Stream a text completion for `prompt` as it's generated."""
        ...


async def retry_once_on_validation_error(
    provider: str, attempt: Callable[[], Awaitable[BaseModel]]
) -> BaseModel:
    """Await `attempt()`, calling it once more if its output fails schema validation.

    A second `ValidationError` becomes a `ProviderResponseError`; any other
    error from `attempt` propagates on the first try, unretried.
    """
    validation_error: ValidationError | None = None
    for _ in range(2):
        try:
            return await attempt()
        except ValidationError as exc:
            validation_error = exc
    raise ProviderResponseError(
        f"{provider} structured output failed schema validation after retrying once: "
        f"{validation_error}"
    ) from validation_error
