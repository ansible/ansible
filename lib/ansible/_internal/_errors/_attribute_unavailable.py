from __future__ import annotations


class AttributeUnavailableError(Exception):
    """
    This AttributeError-equivalent exception can be raised by custom Jinja-injected objects (e.g. CurrentTask) when an attribute is not yet available.
    It does not extend AttributeError to allow the exception message to be included on the resulting undefined object.
    """
