"""Actions a surface can perform, and how an action names the element it targets."""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Target:
    """An element identified the way the accessibility tree presents it: role + exact name.

    Names are written as they appear in an Observation's aria_snapshot, colon included —
    e.g. Target("textbox", "Member Number:"). Fallback locators for unlabeled controls: M16.
    """

    role: str
    name: str


@dataclass(frozen=True)
class Navigate:
    url: str


@dataclass(frozen=True)
class Click:
    target: Target


@dataclass(frozen=True)
class Fill:
    target: Target
    text: str = field(repr=False)  # may be a password or PII — kept out of logs until M6


Action = Navigate | Click | Fill
