"""Test metadata for passing data to delegated tests."""
from __future__ import absolute_import, print_function

import json

from lib.util import (
    display,
    is_shippable,
)

from lib.diff import (
    parse_diff,
)


class Metadata(object):
    """Metadata object for passing data to delegated tests."""
    def __init__(self):
        """Initialize metadata."""
        self.changes = {}  # type: dict [str, tuple[tuple[int, int]]
        self.cloud_config = None  # type: dict [str, str]

        if is_shippable():
            self.ci_provider = 'shippable'
        else:
            self.ci_provider = ''

    def populate_changes(self, diff):
        """
        :type diff: list[str] | None
        """
        patches = parse_diff(diff)
        patches = sorted(patches, key=lambda k: k.new.path)  # type: list [FileDiff]

        self.changes = dict((patch.new.path, tuple(patch.new.ranges)) for patch in patches)

        renames = [patch.old.path for patch in patches if patch.old.path != patch.new.path and patch.old.exists and patch.new.exists]
        deletes = [patch.old.path for patch in patches if not patch.new.exists]

        # make sure old paths which were renamed or deleted are registered in changes
        for path in renames + deletes:
            if path in self.changes:
                # old path was replaced with another file
                continue

            # failed tests involving deleted files should be using line 0 since there is no content remaining
            self.changes[path] = ((0, 0),)

    def to_dict(self):
        """
        :rtype: dict[str, any]
        """
        return dict(
            changes=self.changes,
            cloud_config=self.cloud_config,
            ci_provider=self.ci_provider,
        )

    def to_file(self, path):
        """
        :type path: path
        """
        data = self.to_dict()

        display.info('>>> Metadata: %s\n%s' % (path, data), verbosity=3)

        with open(path, 'w') as data_fd:
            json.dump(data, data_fd, sort_keys=True, indent=4)

    @staticmethod
    def from_file(path):
        """
        :type path: str
        :rtype: Metadata
        """
        with open(path, 'r') as data_fd:
            data = json.load(data_fd)

        return Metadata.from_dict(data)

    @staticmethod
    def from_dict(data):
        """
        :type data: dict[str, any]
        :rtype: Metadata
        """
        metadata = Metadata()
        metadata.changes = data['changes']
        metadata.cloud_config = data['cloud_config']
        metadata.ci_provider = data['ci_provider']

        return metadata
