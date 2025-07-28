import inspect

from ansible.module_utils.common import warnings


def deprecate(importable_name, *args):
    """Inject import-time deprecation warnings."""
    parent__name__ = inspect.stack()[1].frame.f_globals['__name__']

    if importable_name in args:
        import importlib
        importable = getattr(
            importlib.import_module("ansible.module_utils.six"),
            importable_name
        )
    else:
        raise AttributeError(f"module {parent__name__!r} has no attribute {importable_name!r}")

    # TODO Inspect and remove all calls to this function in 2.24
    warnings.deprecate(
        msg=f"Importing {importable_name!r} from {parent__name__!r} is deprecated.",
        version="2.24",
    )

    return importable
