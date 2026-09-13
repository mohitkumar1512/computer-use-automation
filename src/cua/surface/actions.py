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
    sensitive: bool = False  # never show the text, even to an operator (e.g. passwords)


Action = Navigate | Click | Fill

MASK = "••••••"


def describe(action: Action) -> str:
    """One human-readable line for an action, safe to display: sensitive text is masked."""
    match action:
        case Navigate(url=url):
            return f"Open {url}"
        case Click(target=target):
            return f'Click {target.role} "{target.name}"'
        case Fill(target=target, text=text, sensitive=sensitive):
            shown = MASK if sensitive else f'"{text}"'
            return f'Type {shown} into {target.role} "{target.name}"'
    raise TypeError(f"Unsupported action: {action!r}")
