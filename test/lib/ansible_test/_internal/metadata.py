"""Test metadata for passing data to delegated tests."""
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import json

from . import types as t

from .util import (
    display,
)

from .util_common import (
    write_json_file,
)

from .diff import (
    parse_diff,
    FileDiff,
)


class Metadata:
    """Metadata object for passing data to delegated tests."""
    def __init__(self):
        """Initialize metadata."""
        self.changes = {}  # type: t.Dict[str, t.Tuple[t.Tuple[int, int]]]
        self.cloud_config = None  # type: t.Optional[t.Dict[str, str]]
        self.instance_config = None  # type: t.Optional[t.List[t.Dict[str, str]]]
        self.change_description = None  # type: t.Optional[ChangeDescription]
        self.ci_provider = None  # type: t.Optional[str]

    def populate_changes(self, diff):
        """
        :type diff: list[str] | None
        """
        patches = parse_diff(diff)
        patches = sorted(patches, key=lambda k: k.new.path)  # type: t.List[FileDiff]

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
            instance_config=self.instance_config,
            ci_provider=self.ci_provider,
            change_description=self.change_description.to_dict(),
        )

    def to_file(self, path):
        """
        :type path: path
        """
        data = self.to_dict()

        display.info('>>> Metadata: %s\n%s' % (path, data), verbosity=3)

        write_json_file(path, data)

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
        metadata.instance_config = data['instance_config']
        metadata.ci_provider = data['ci_provider']
        metadata.change_description = ChangeDescription.from_dict(data['change_description'])

        return metadata


class ChangeDescription:
    """Description of changes."""
    def __init__(self):
        self.command = ''  # type: str
        self.changed_paths = []  # type: t.List[str]
        self.deleted_paths = []  # type: t.List[str]
        self.regular_command_targets = {}  # type: t.Dict[str, t.List[str]]
        self.focused_command_targets = {}  # type: t.Dict[str, t.List[str]]
        self.no_integration_paths = []  # type: t.List[str]

    @property
    def targets(self):
        """
        :rtype: list[str] | None
        """
        return self.regular_command_targets.get(self.command)

    @property
    def focused_targets(self):
        """
        :rtype: list[str] | None
        """
        return self.focused_command_targets.get(self.command)

    def to_dict(self):
        """
        :rtype: dict[str, any]
        """
        return dict(
            command=self.command,
            changed_paths=self.changed_paths,
            deleted_paths=self.deleted_paths,
            regular_command_targets=self.regular_command_targets,
            focused_command_targets=self.focused_command_targets,
            no_integration_paths=self.no_integration_paths,
        )

    @staticmethod
    def from_dict(data):
        """
        :param data: dict[str, any]
        :rtype: ChangeDescription
        """
        changes = ChangeDescription()
        changes.command = data['command']
        changes.changed_paths = data['changed_paths']
        changes.deleted_paths = data['deleted_paths']
        changes.regular_command_targets = data['regular_command_targets']
        changes.focused_command_targets = data['focused_command_targets']
        changes.no_integration_paths = data['no_integration_paths']

        return changes
