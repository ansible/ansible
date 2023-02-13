"""Logic for filtering out integration test targets which are unsupported for the currently provided arguments and available hosts."""
from __future__ import annotations

import abc
import typing as t

from ...config import (
    IntegrationConfig,
)

from ...util import (
    cache,
    detect_architecture,
    display,
    get_type_map,
)

from ...target import (
    IntegrationTarget,
)

from ...host_configs import (
    ControllerConfig,
    DockerConfig,
    FallbackReason,
    HostConfig,
    NetworkInventoryConfig,
    NetworkRemoteConfig,
    OriginConfig,
    PosixConfig,
    PosixRemoteConfig,
    PosixSshConfig,
    RemoteConfig,
    WindowsInventoryConfig,
    WindowsRemoteConfig,
)

from ...host_profiles import (
    HostProfile,
)

THostConfig = t.TypeVar('THostConfig', bound=HostConfig)
TPosixConfig = t.TypeVar('TPosixConfig', bound=PosixConfig)
TRemoteConfig = t.TypeVar('TRemoteConfig', bound=RemoteConfig)
THostProfile = t.TypeVar('THostProfile', bound=HostProfile)


class TargetFilter(t.Generic[THostConfig], metaclass=abc.ABCMeta):
    """Base class for target filters."""

    def __init__(self, args: IntegrationConfig, configs: list[THostConfig], controller: bool) -> None:
        self.args = args
        self.configs = configs
        self.controller = controller
        self.host_type = 'controller' if controller else 'target'

        # values which are not host specific
        self.include_targets = args.include
        self.allow_root = args.allow_root
        self.allow_destructive = args.allow_destructive

    @property
    def config(self) -> THostConfig:
        """The configuration to filter. Only valid when there is a single config."""
        if len(self.configs) != 1:
            raise Exception()

        return self.configs[0]

    def skip(
        self,
        skip: str,
        reason: str,
        targets: list[IntegrationTarget],
        exclude: set[str],
        override: t.Optional[list[str]] = None,
    ) -> None:
        """Apply the specified skip rule to the given targets by updating the provided exclude list."""
        if skip.startswith('skip/'):
            skipped = [target.name for target in targets if skip in target.skips and (not override or target.name not in override)]
        else:
            skipped = [target.name for target in targets if f'{skip}/' in target.aliases and (not override or target.name not in override)]

        self.apply_skip(f'"{skip}"', reason, skipped, exclude)

    def apply_skip(self, marked: str, reason: str, skipped: list[str], exclude: set[str]) -> None:
        """Apply the provided skips to the given exclude list."""
        if not skipped:
            return

        exclude.update(skipped)
        display.warning(f'Excluding {self.host_type} tests marked {marked} {reason}: {", ".join(skipped)}')

    def filter_profiles(self, profiles: list[THostProfile], target: IntegrationTarget) -> list[THostProfile]:
        """Filter the list of profiles, returning only those which are not skipped for the given target."""
        del target
        return profiles

    def filter_targets(self, targets: list[IntegrationTarget], exclude: set[str]) -> None:
        """Filter the list of targets, adding any which this host profile cannot support to the provided exclude list."""
        if self.controller and self.args.host_settings.controller_fallback and targets:
            affected_targets = [target.name for target in targets]
            reason = self.args.host_settings.controller_fallback.reason

            if reason == FallbackReason.ENVIRONMENT:
                exclude.update(affected_targets)
                display.warning(f'Excluding {self.host_type} tests since a fallback controller is in use: {", ".join(affected_targets)}')
            elif reason == FallbackReason.PYTHON:
                display.warning(f'Some {self.host_type} tests may be redundant since a fallback python is in use: {", ".join(affected_targets)}')

        if not self.allow_destructive and not self.config.is_managed:
            override_destructive = set(target for target in self.include_targets if target.startswith('destructive/'))
            override = [target.name for target in targets if override_destructive & set(target.aliases)]

            self.skip('destructive', 'which require --allow-destructive or prefixing with "destructive/" to run on unmanaged hosts', targets, exclude, override)

        if not self.args.allow_disabled:
            override_disabled = set(target for target in self.args.include if target.startswith('disabled/'))
            override = [target.name for target in targets if override_disabled & set(target.aliases)]

            self.skip('disabled', 'which require --allow-disabled or prefixing with "disabled/"', targets, exclude, override)

        if not self.args.allow_unsupported:
            override_unsupported = set(target for target in self.args.include if target.startswith('unsupported/'))
            override = [target.name for target in targets if override_unsupported & set(target.aliases)]

            self.skip('unsupported', 'which require --allow-unsupported or prefixing with "unsupported/"', targets, exclude, override)

        if not self.args.allow_unstable:
            override_unstable = set(target for target in self.args.include if target.startswith('unstable/'))

            if self.args.allow_unstable_changed:
                override_unstable |= set(self.args.metadata.change_description.focused_targets or [])

            override = [target.name for target in targets if override_unstable & set(target.aliases)]

            self.skip('unstable', 'which require --allow-unstable or prefixing with "unstable/"', targets, exclude, override)


class PosixTargetFilter(TargetFilter[TPosixConfig]):
    """Target filter for POSIX hosts."""

    def filter_targets(self, targets: list[IntegrationTarget], exclude: set[str]) -> None:
        """Filter the list of targets, adding any which this host profile cannot support to the provided exclude list."""
        super().filter_targets(targets, exclude)

        if not self.allow_root and not self.config.have_root:
            self.skip('needs/root', 'which require --allow-root or running as root', targets, exclude)

        self.skip(f'skip/python{self.config.python.version}', f'which are not supported by Python {self.config.python.version}', targets, exclude)
        self.skip(f'skip/python{self.config.python.major_version}', f'which are not supported by Python {self.config.python.major_version}', targets, exclude)


class DockerTargetFilter(PosixTargetFilter[DockerConfig]):
    """Target filter for docker hosts."""

    def filter_targets(self, targets: list[IntegrationTarget], exclude: set[str]) -> None:
        """Filter the list of targets, adding any which this host profile cannot support to the provided exclude list."""
        super().filter_targets(targets, exclude)

        self.skip('skip/docker', 'which cannot run under docker', targets, exclude)

        if not self.config.privileged:
            self.skip('needs/privileged', 'which require --docker-privileged to run under docker', targets, exclude)


class PosixSshTargetFilter(PosixTargetFilter[PosixSshConfig]):
    """Target filter for POSIX SSH hosts."""


class RemoteTargetFilter(TargetFilter[TRemoteConfig]):
    """Target filter for remote Ansible Core CI managed hosts."""

    def filter_profiles(self, profiles: list[THostProfile], target: IntegrationTarget) -> list[THostProfile]:
        """Filter the list of profiles, returning only those which are not skipped for the given target."""
        profiles = super().filter_profiles(profiles, target)

        skipped_profiles = [profile for profile in profiles if any(skip in target.skips for skip in get_remote_skip_aliases(profile.config))]

        if skipped_profiles:
            configs: list[TRemoteConfig] = [profile.config for profile in skipped_profiles]
            display.warning(f'Excluding skipped hosts from inventory: {", ".join(config.name for config in configs)}')

        profiles = [profile for profile in profiles if profile not in skipped_profiles]

        return profiles

    def filter_targets(self, targets: list[IntegrationTarget], exclude: set[str]) -> None:
        """Filter the list of targets, adding any which this host profile cannot support to the provided exclude list."""
        super().filter_targets(targets, exclude)

        if len(self.configs) > 1:
            host_skips = {host.name: get_remote_skip_aliases(host) for host in self.configs}

            # Skip only targets which skip all hosts.
            # Targets that skip only some hosts will be handled during inventory generation.
            skipped = [target.name for target in targets if all(any(skip in target.skips for skip in skips) for skips in host_skips.values())]

            if skipped:
                exclude.update(skipped)
                display.warning(f'Excluding tests which do not support {", ".join(host_skips.keys())}: {", ".join(skipped)}')
        else:
            skips = get_remote_skip_aliases(self.config)

            for skip, reason in skips.items():
                self.skip(skip, reason, targets, exclude)


class PosixRemoteTargetFilter(PosixTargetFilter[PosixRemoteConfig], RemoteTargetFilter[PosixRemoteConfig]):
    """Target filter for POSIX remote hosts."""


class WindowsRemoteTargetFilter(RemoteTargetFilter[WindowsRemoteConfig]):
    """Target filter for remote Windows hosts."""


class WindowsInventoryTargetFilter(TargetFilter[WindowsInventoryConfig]):
    """Target filter for Windows inventory."""


class NetworkRemoteTargetFilter(RemoteTargetFilter[NetworkRemoteConfig]):
    """Target filter for remote network hosts."""


class NetworkInventoryTargetFilter(TargetFilter[NetworkInventoryConfig]):
    """Target filter for network inventory."""


class OriginTargetFilter(PosixTargetFilter[OriginConfig]):
    """Target filter for localhost."""

    def filter_targets(self, targets: list[IntegrationTarget], exclude: set[str]) -> None:
        """Filter the list of targets, adding any which this host profile cannot support to the provided exclude list."""
        super().filter_targets(targets, exclude)

        arch = detect_architecture(self.config.python.path)

        if arch:
            self.skip(f'skip/{arch}', f'which are not supported by {arch}', targets, exclude)


@cache
def get_host_target_type_map() -> dict[t.Type[HostConfig], t.Type[TargetFilter]]:
    """Create and return a mapping of HostConfig types to TargetFilter types."""
    return get_type_map(TargetFilter, HostConfig)


def get_target_filter(args: IntegrationConfig, configs: list[HostConfig], controller: bool) -> TargetFilter:
    """Return an integration test target filter instance for the provided host configurations."""
    target_type = type(configs[0])

    if issubclass(target_type, ControllerConfig):
        target_type = type(args.controller)
        configs = [args.controller]

    filter_type = get_host_target_type_map()[target_type]
    filter_instance = filter_type(args, configs, controller)

    return filter_instance


def get_remote_skip_aliases(config: RemoteConfig) -> dict[str, str]:
    """Return a dictionary of skip aliases and the reason why they apply."""
    return get_platform_skip_aliases(config.platform, config.version, config.arch)


def get_platform_skip_aliases(platform: str, version: str, arch: t.Optional[str]) -> dict[str, str]:
    """Return a dictionary of skip aliases and the reason why they apply."""
    skips = {
        f'skip/{platform}': platform,
        f'skip/{platform}/{version}': f'{platform} {version}',
        f'skip/{platform}{version}': f'{platform} {version}',  # legacy syntax, use above format
    }

    if arch:
        skips.update({
            f'skip/{arch}': arch,
            f'skip/{arch}/{platform}': f'{platform} on {arch}',
            f'skip/{arch}/{platform}/{version}': f'{platform} {version} on {arch}',
        })

    skips = {alias: f'which are not supported by {description}' for alias, description in skips.items()}

    return skips
