"""What a surface sees, and the interface every surface (web, legacy web, desktop) implements."""

from dataclasses import dataclass, field
from typing import Protocol

from cua.surface.actions import Action


@dataclass(frozen=True)
class Observation:
    """One snapshot of the UI at a moment in time.

    The accessibility snapshot is the primary perception channel; the screenshot is supporting
    evidence for humans and for cases the accessibility tree cannot describe. Both can contain
    sensitive data, so neither appears in repr() — keeping them out of logs until redaction (M6).
    """

    url: str
    title: str
    aria_snapshot: str = field(repr=False)  # YAML-like accessibility tree: roles, names, values
    screenshot: bytes = field(repr=False)  # PNG


class Surface(Protocol):
    """The seam between the automation system and a concrete UI."""

    async def perceive(self) -> Observation: ...

    async def act(self, action: Action) -> None:
        """Perform one action; raises a SurfaceError if its target can't be resolved."""
        ...
