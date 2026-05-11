from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

try:
    from .observability import observe_adapter_call
    from .settings import get_setting
except ImportError:  # pragma: no cover
    from observability import observe_adapter_call  # type: ignore[no-redef]
    from settings import get_setting  # type: ignore[no-redef]


@dataclass
class GenerationResult:
    provider: str
    output: str


class ModelAdapter(Protocol):
    provider_name: str

    def generate(self, prompt: str, context: str | None = None) -> GenerationResult:
        raise NotImplementedError


class EchoModelAdapter:
    provider_name = "echo"

    def generate(self, prompt: str, context: str | None = None) -> GenerationResult:
        parts = [f"Prompt: {prompt.strip()}"]
        if context:
            parts.append(f"Context: {context.strip()}")
        parts.append("Response: This is a local, deterministic placeholder output.")
        observe_adapter_call(self.provider_name)
        return GenerationResult(provider=self.provider_name, output="\n".join(parts))


class TemplateModelAdapter:
    provider_name = "template"

    def generate(self, prompt: str, context: str | None = None) -> GenerationResult:
        content = prompt if context is None else f"{prompt}\n{context}"
        observe_adapter_call(self.provider_name)
        return GenerationResult(provider=self.provider_name, output=content.upper())


def get_default_adapter() -> ModelAdapter:
    provider = get_setting("INTELLECTIVE_AI_MODEL_PROVIDER", "echo").strip().lower()
    if provider == "template":
        return TemplateModelAdapter()
    return EchoModelAdapter()
