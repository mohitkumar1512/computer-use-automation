"""Surfaces: how cua perceives and acts on a user interface."""

from cua.surface.actions import Action, Click, Fill, Navigate, Target
from cua.surface.browser import WebSurface, launch_page
from cua.surface.errors import AmbiguousTarget, SurfaceError, TargetNotFound
from cua.surface.observation import Observation, Surface

__all__ = [
    "Action",
    "AmbiguousTarget",
    "Click",
    "Fill",
    "Navigate",
    "Observation",
    "Surface",
    "SurfaceError",
    "Target",
    "TargetNotFound",
    "WebSurface",
    "launch_page",
]
