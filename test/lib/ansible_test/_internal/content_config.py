"""Content configuration."""
from __future__ import annotations

import os
import pickle
import typing as t

from .constants import (
    CONTROLLER_PYTHON_VERSIONS,
    SUPPORTED_PYTHON_VERSIONS,
)

from .compat.packaging import (
    PACKAGING_IMPORT_ERROR,
    SpecifierSet,
    Version,
)

from .compat.yaml import (
    YAML_IMPORT_ERROR,
    yaml_load,
)

from .io import (
    open_binary_file,
    read_text_file,
)

from .util import (
    ApplicationError,
    display,
    str_to_version,
)

from .data import (
    data_context,
)

from .config import (
    EnvironmentConfig,
    ContentConfig,
    ModulesConfig,
)

MISSING = object()


def parse_modules_config(data: t.Any) -> ModulesConfig:
    """Parse the given dictionary as module config and return it."""
    if not isinstance(data, dict):
        raise Exception('config must be type `dict` not `%s`' % type(data))

    python_requires = data.get('python_requires', MISSING)

    if python_requires == MISSING:
        raise KeyError('python_requires is required')

    return ModulesConfig(
        python_requires=python_requires,
        python_versions=parse_python_requires(python_requires),
        controller_only=python_requires == 'controller',
    )


def parse_content_config(data: t.Any) -> ContentConfig:
    """Parse the given dictionary as content config and return it."""
    if not isinstance(data, dict):
        raise Exception('config must be type `dict` not `%s`' % type(data))

    # Configuration specific to modules/module_utils.
    modules = parse_modules_config(data.get('modules', {}))

    # Python versions supported by the controller, combined with Python versions supported by modules/module_utils.
    # Mainly used for display purposes and to limit the Python versions used for sanity tests.
    python_versions = tuple(version for version in SUPPORTED_PYTHON_VERSIONS
                            if version in CONTROLLER_PYTHON_VERSIONS or version in modules.python_versions)

    # True if Python 2.x is supported.
    py2_support = any(version for version in python_versions if str_to_version(version)[0] == 2)

    return ContentConfig(
        modules=modules,
        python_versions=python_versions,
        py2_support=py2_support,
    )


def load_config(path: str) -> t.Optional[ContentConfig]:
    """Load and parse the specified config file and return the result or None if loading/parsing failed."""
    if YAML_IMPORT_ERROR:
        raise ApplicationError('The "PyYAML" module is required to parse config: %s' % YAML_IMPORT_ERROR)

    if PACKAGING_IMPORT_ERROR:
        raise ApplicationError('The "packaging" module is required to parse config: %s' % PACKAGING_IMPORT_ERROR)

    value = read_text_file(path)

    try:
        yaml_value = yaml_load(value)
    except Exception as ex:  # pylint: disable=broad-except
        display.warning('Ignoring config "%s" due to a YAML parsing error: %s' % (path, ex))
        return None

    try:
        config = parse_content_config(yaml_value)
    except Exception as ex:  # pylint: disable=broad-except
        display.warning('Ignoring config "%s" due a config parsing error: %s' % (path, ex))
        return None

    display.info('Loaded configuration: %s' % path, verbosity=1)

    return config


def get_content_config(args: EnvironmentConfig) -> ContentConfig:
    """
    Parse and return the content configuration (if any) for the current collection.
    For ansible-core, a default configuration is used.
    Results are cached.
    """
    if args.host_path:
        args.content_config = deserialize_content_config(os.path.join(args.host_path, 'config.dat'))

    if args.content_config:
        return args.content_config

    collection_config_path = 'tests/config.yml'

    config = None

    if data_context().content.collection and os.path.exists(collection_config_path):
        config = load_config(collection_config_path)

    if not config:
        config = parse_content_config(dict(
            modules=dict(
                python_requires='default',
            ),
        ))

    if not config.modules.python_versions:
        raise ApplicationError('This collection does not declare support for modules/module_utils on any known Python version.\n'
                               'Ansible supports modules/module_utils on Python versions: %s\n'
                               'This collection provides the Python requirement: %s' % (
                                   ', '.join(SUPPORTED_PYTHON_VERSIONS), config.modules.python_requires))

    args.content_config = config

    return config


def parse_python_requires(value: t.Any) -> tuple[str, ...]:
    """Parse the given 'python_requires' version specifier and return the matching Python versions."""
    if not isinstance(value, str):
        raise ValueError('python_requires must must be of type `str` not type `%s`' % type(value))

    versions: tuple[str, ...]

    if value == 'default':
        versions = SUPPORTED_PYTHON_VERSIONS
    elif value == 'controller':
        versions = CONTROLLER_PYTHON_VERSIONS
    else:
        specifier_set = SpecifierSet(value)
        versions = tuple(version for version in SUPPORTED_PYTHON_VERSIONS if specifier_set.contains(Version(version)))

    return versions


def serialize_content_config(args: EnvironmentConfig, path: str) -> None:
    """Serialize the content config to the given path. If the config has not been loaded, an empty config will be serialized."""
    with open_binary_file(path, 'wb') as config_file:
        pickle.dump(args.content_config, config_file)


def deserialize_content_config(path: str) -> ContentConfig:
    """Deserialize content config from the path."""
    with open_binary_file(path) as config_file:
        return pickle.load(config_file)
