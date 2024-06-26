"""Test metadata for passing data to delegated tests."""
from __future__ import annotations
import typing as t

from .util import (
    display,
    generate_name,
)

from .io import (
    write_json_file,
    read_json_file,
)

from .diff import (
    parse_diff,
    FileDiff,
)


class Metadata:
    """Metadata object for passing data to delegated tests."""

    def __init__(self) -> None:
        """Initialize metadata."""
        self.changes: dict[str, tuple[tuple[int, int], ...]] = {}
        self.cloud_config: t.Optional[dict[str, dict[str, t.Union[int, str, bool]]]] = None
        self.change_description: t.Optional[ChangeDescription] = None
        self.ci_provider: t.Optional[str] = None
        self.session_id = generate_name()

    def populate_changes(self, diff: t.Optional[list[str]]) -> None:
        """Populate the changeset using the given diff."""
        patches = parse_diff(diff)
        patches: list[FileDiff] = sorted(patches, key=lambda k: k.new.path)

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

    def to_dict(self) -> dict[str, t.Any]:
        """Return a dictionary representation of the metadata."""
        return dict(
            changes=self.changes,
            cloud_config=self.cloud_config,
            ci_provider=self.ci_provider,
            change_description=self.change_description.to_dict(),
            session_id=self.session_id,
        )

    def to_file(self, path: str) -> None:
        """Write the metadata to the specified file."""
        data = self.to_dict()

        display.info('>>> Metadata: %s\n%s' % (path, data), verbosity=3)

        write_json_file(path, data)

    @staticmethod
    def from_file(path: str) -> Metadata:
        """Return metadata loaded from the specified file."""
        data = read_json_file(path)
        return Metadata.from_dict(data)

    @staticmethod
    def from_dict(data: dict[str, t.Any]) -> Metadata:
        """Return metadata loaded from the specified dictionary."""
        metadata = Metadata()
        metadata.changes = data['changes']
        metadata.cloud_config = data['cloud_config']
        metadata.ci_provider = data['ci_provider']
        metadata.change_description = ChangeDescription.from_dict(data['change_description'])
        metadata.session_id = data['session_id']

        return metadata


class ChangeDescription:
    """Description of changes."""

    def __init__(self) -> None:
        self.command: str = ''
        self.changed_paths: list[str] = []
        self.deleted_paths: list[str] = []
        self.regular_command_targets: dict[str, list[str]] = {}
        self.focused_command_targets: dict[str, list[str]] = {}
        self.no_integration_paths: list[str] = []

    @property
    def targets(self) -> t.Optional[list[str]]:
        """Optional list of target names."""
        return self.regular_command_targets.get(self.command)

    @property
    def focused_targets(self) -> t.Optional[list[str]]:
        """Optional list of focused target names."""
        return self.focused_command_targets.get(self.command)

    def to_dict(self) -> dict[str, t.Any]:
        """Return a dictionary representation of the change description."""
        return dict(
            command=self.command,
            changed_paths=self.changed_paths,
            deleted_paths=self.deleted_paths,
            regular_command_targets=self.regular_command_targets,
            focused_command_targets=self.focused_command_targets,
            no_integration_paths=self.no_integration_paths,
        )

    @staticmethod
    def from_dict(data: dict[str, t.Any]) -> ChangeDescription:
        """Return a change description loaded from the given dictionary."""
        changes = ChangeDescription()
        changes.command = data['command']
        changes.changed_paths = data['changed_paths']
        changes.deleted_paths = data['deleted_paths']
        changes.regular_command_targets = data['regular_command_targets']
        changes.focused_command_targets = data['focused_command_targets']
        changes.no_integration_paths = data['no_integration_paths']

        return changes
