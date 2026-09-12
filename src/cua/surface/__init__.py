"""Surfaces: how cua perceives (and, from M3, acts on) a user interface."""

from cua.surface.browser import WebSurface, launch_page
from cua.surface.observation import Observation, Surface

__all__ = ["Observation", "Surface", "WebSurface", "launch_page"]
