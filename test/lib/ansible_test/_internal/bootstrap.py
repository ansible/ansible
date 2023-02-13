"""Bootstrapping for test hosts."""
from __future__ import annotations

import dataclasses
import os
import typing as t

from .io import (
    read_text_file,
)

from .util import (
    ANSIBLE_TEST_TARGET_ROOT,
)

from .util_common import (
    ShellScriptTemplate,
    set_shebang,
)

from .core_ci import (
    SshKey,
)


@dataclasses.dataclass
class Bootstrap:
    """Base class for bootstrapping systems."""

    controller: bool
    python_versions: list[str]
    ssh_key: SshKey

    @property
    def bootstrap_type(self) -> str:
        """The bootstrap type to pass to the bootstrapping script."""
        return self.__class__.__name__.replace('Bootstrap', '').lower()

    def get_variables(self) -> dict[str, t.Union[str, list[str]]]:
        """The variables to template in the bootstrapping script."""
        return dict(
            bootstrap_type=self.bootstrap_type,
            controller='yes' if self.controller else '',
            python_versions=self.python_versions,
            ssh_key_type=self.ssh_key.KEY_TYPE,
            ssh_private_key=self.ssh_key.key_contents,
            ssh_public_key=self.ssh_key.pub_contents,
        )

    def get_script(self) -> str:
        """Return a shell script to bootstrap the specified host."""
        path = os.path.join(ANSIBLE_TEST_TARGET_ROOT, 'setup', 'bootstrap.sh')

        content = read_text_file(path)
        content = set_shebang(content, '/bin/sh')

        template = ShellScriptTemplate(content)

        variables = self.get_variables()

        script = template.substitute(**variables)

        return script


@dataclasses.dataclass
class BootstrapDocker(Bootstrap):
    """Bootstrap docker instances."""

    def get_variables(self) -> dict[str, t.Union[str, list[str]]]:
        """The variables to template in the bootstrapping script."""
        variables = super().get_variables()

        variables.update(
            platform='',
            platform_version='',
        )

        return variables


@dataclasses.dataclass
class BootstrapRemote(Bootstrap):
    """Bootstrap remote instances."""

    platform: str
    platform_version: str

    def get_variables(self) -> dict[str, t.Union[str, list[str]]]:
        """The variables to template in the bootstrapping script."""
        variables = super().get_variables()

        variables.update(
            platform=self.platform,
            platform_version=self.platform_version,
        )

        return variables
