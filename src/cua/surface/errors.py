"""Errors raised when a surface cannot carry out an action. The full taxonomy arrives in M12."""


class SurfaceError(Exception):
    """An action could not be performed on the surface."""


class TargetNotFound(SurfaceError):
    """No element matched the action's target within the timeout."""


class AmbiguousTarget(SurfaceError):
    """Several elements matched the target; acting on any one of them would be a guess."""
