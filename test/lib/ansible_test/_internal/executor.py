"""Execute Ansible tests."""
from __future__ import annotations

import typing as t

from .io import (
    read_text_file,
)

from .util import (
    ApplicationWarning,
    display,
)

from .ci import (
    get_ci_provider,
)

from .classification import (
    categorize_changes,
)

from .config import (
    TestConfig,
)

from .metadata import (
    ChangeDescription,
)

from .provisioning import (
    HostState,
)


def get_changes_filter(args):  # type: (TestConfig) -> t.List[str]
    """Return a list of targets which should be tested based on the changes made."""
    paths = detect_changes(args)

    if not args.metadata.change_description:
        if paths:
            changes = categorize_changes(args, paths, args.command)
        else:
            changes = ChangeDescription()

        args.metadata.change_description = changes

    if paths is None:
        return []  # change detection not enabled, do not filter targets

    if not paths:
        raise NoChangesDetected()

    if args.metadata.change_description.targets is None:
        raise NoTestsForChanges()

    return args.metadata.change_description.targets


def detect_changes(args):  # type: (TestConfig) -> t.Optional[t.List[str]]
    """Return a list of changed paths."""
    if args.changed:
        paths = get_ci_provider().detect_changes(args)
    elif args.changed_from or args.changed_path:
        paths = args.changed_path or []
        if args.changed_from:
            paths += read_text_file(args.changed_from).splitlines()
    else:
        return None  # change detection not enabled

    if paths is None:
        return None  # act as though change detection not enabled, do not filter targets

    display.info('Detected changes in %d file(s).' % len(paths))

    for path in paths:
        display.info(path, verbosity=1)

    return paths


class NoChangesDetected(ApplicationWarning):
    """Exception when change detection was performed, but no changes were found."""
    def __init__(self):
        super().__init__('No changes detected.')


class NoTestsForChanges(ApplicationWarning):
    """Exception when changes detected, but no tests trigger as a result."""
    def __init__(self):
        super().__init__('No tests found for detected changes.')


class Delegate(Exception):
    """Trigger command delegation."""
    def __init__(self, host_state, exclude=None, require=None):  # type: (HostState, t.List[str], t.List[str]) -> None
        super().__init__()

        self.host_state = host_state
        self.exclude = exclude or []
        self.require = require or []


class ListTargets(Exception):
    """List integration test targets instead of executing them."""
    def __init__(self, target_names):  # type: (t.List[str]) -> None
        super().__init__()

        self.target_names = target_names


class AllTargetsSkipped(ApplicationWarning):
    """All targets skipped."""
    def __init__(self):
        super().__init__('All targets skipped.')
