"""Sanity test for symlinks in the bin directory."""
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os

from .. import types as t

from ..sanity import (
    SanityVersionNeutral,
    SanityMessage,
    SanityFailure,
    SanitySuccess,
)

from ..config import (
    SanityConfig,
)

from ..data import (
    data_context,
)

from ..payload import (
    ANSIBLE_BIN_SYMLINK_MAP,
    __file__ as symlink_map_full_path,
)

from ..util import (
    ANSIBLE_BIN_PATH,
    ANSIBLE_TEST_DATA_ROOT,
)


class BinSymlinksTest(SanityVersionNeutral):
    """Sanity test for symlinks in the bin directory."""
    ansible_only = True

    @property
    def can_ignore(self):  # type: () -> bool
        """True if the test supports ignore entries."""
        return False

    @property
    def no_targets(self):  # type: () -> bool
        """True if the test does not use test targets. Mutually exclusive with all_targets."""
        return True

    # noinspection PyUnusedLocal
    def test(self, args, targets):  # pylint: disable=locally-disabled, unused-argument
        """
        :type args: SanityConfig
        :type targets: SanityTargets
        :rtype: TestResult
        """
        bin_root = ANSIBLE_BIN_PATH
        bin_names = os.listdir(bin_root)
        bin_paths = sorted(os.path.join(bin_root, path) for path in bin_names)

        injector_root = os.path.join(ANSIBLE_TEST_DATA_ROOT, 'injector')
        injector_names = os.listdir(injector_root)

        errors = []  # type: t.List[t.Tuple[str, str]]

        symlink_map_path = os.path.relpath(symlink_map_full_path, data_context().content.root)

        for bin_path in bin_paths:
            if not os.path.islink(bin_path):
                errors.append((bin_path, 'not a symbolic link'))
                continue

            dest = os.readlink(bin_path)

            if not os.path.exists(bin_path):
                errors.append((bin_path, 'points to non-existent path "%s"' % dest))
                continue

            if not os.path.isfile(bin_path):
                errors.append((bin_path, 'points to non-file "%s"' % dest))
                continue

            map_dest = ANSIBLE_BIN_SYMLINK_MAP.get(os.path.basename(bin_path))

            if not map_dest:
                errors.append((bin_path, 'missing from ANSIBLE_BIN_SYMLINK_MAP in file "%s"' % symlink_map_path))
                continue

            if dest != map_dest:
                errors.append((bin_path, 'points to "%s" instead of "%s" from ANSIBLE_BIN_SYMLINK_MAP in file "%s"' % (dest, map_dest, symlink_map_path)))
                continue

            if not os.access(bin_path, os.X_OK):
                errors.append((bin_path, 'points to non-executable file "%s"' % dest))
                continue

        for bin_name, dest in ANSIBLE_BIN_SYMLINK_MAP.items():
            if bin_name not in bin_names:
                bin_path = os.path.join(bin_root, bin_name)
                errors.append((bin_path, 'missing symlink to "%s" defined in ANSIBLE_BIN_SYMLINK_MAP in file "%s"' % (dest, symlink_map_path)))

            if bin_name not in injector_names:
                injector_path = os.path.join(injector_root, bin_name)
                errors.append((injector_path, 'missing symlink to "python.py"'))

        messages = [SanityMessage(message=message, path=os.path.relpath(path, data_context().content.root), confidence=100) for path, message in errors]

        if errors:
            return SanityFailure(self.name, messages=messages)

        return SanitySuccess(self.name)
