from __future__ import annotations as _annotations

import inspect as _inspect
import typing as _t


def caller_frame() -> _inspect.FrameInfo | None:
    """Return the caller stack frame, skipping any marked with the `_skip_stackwalk` local."""
    _skip_stackwalk = True

    return next(iter_stack(), None)


def iter_stack() -> _t.Generator[_inspect.FrameInfo]:
    """Iterate over stack frames, skipping any marked with the `_skip_stackwalk` local."""
    _skip_stackwalk = True

    for frame_info in _inspect.stack():
        if '_skip_stackwalk' in frame_info.frame.f_locals:
            continue

        yield frame_info
