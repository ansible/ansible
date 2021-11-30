"""Content configuration."""
from __future__ import annotations

import os
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
    read_text_file,
)

from .util import (
    ApplicationError,
    display,
    str_to_version,
    cache,
)

from .data import (
    data_context,
)


MISSING = object()


class BaseConfig:
    """Base class for content configuration."""
    def __init__(self, data):  # type: (t.Any) -> None
        if not isinstance(data, dict):
            raise Exception('config must be type `dict` not `%s`' % type(data))


class ModulesConfig(BaseConfig):
    """Configuration for modules."""
    def __init__(self, data):  # type: (t.Any) -> None
        super().__init__(data)

        python_requires = data.get('python_requires', MISSING)

        if python_requires == MISSING:
            raise KeyError('python_requires is required')

        self.python_requires = python_requires
        self.python_versions = parse_python_requires(python_requires)
        self.controller_only = python_requires == 'controller'


class ContentConfig(BaseConfig):
    """Configuration for all content."""
    def __init__(self, data):  # type: (t.Any) -> None
        super().__init__(data)

        # Configuration specific to modules/module_utils.
        self.modules = ModulesConfig(data.get('modules', {}))

        # Python versions supported by the controller, combined with Python versions supported by modules/module_utils.
        # Mainly used for display purposes and to limit the Python versions used for sanity tests.
        self.python_versions = [version for version in SUPPORTED_PYTHON_VERSIONS
                                if version in CONTROLLER_PYTHON_VERSIONS or version in self.modules.python_versions]

        # True if Python 2.x is supported.
        self.py2_support = any(version for version in self.python_versions if str_to_version(version)[0] == 2)


def load_config(path):  # type: (str) -> t.Optional[ContentConfig]
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
        config = ContentConfig(yaml_value)
    except Exception as ex:  # pylint: disable=broad-except
        display.warning('Ignoring config "%s" due a config parsing error: %s' % (path, ex))
        return None

    display.info('Loaded configuration: %s' % path, verbosity=1)

    return config


@cache
def get_content_config():  # type: () -> ContentConfig
    """
    Parse and return the content configuration (if any) for the current collection.
    For ansible-core, a default configuration is used.
    Results are cached.
    """
    collection_config_path = 'tests/config.yml'

    config = None

    if data_context().content.collection and os.path.exists(collection_config_path):
        config = load_config(collection_config_path)

    if not config:
        config = ContentConfig(dict(
            modules=dict(
                python_requires='default',
            ),
        ))

    if not config.modules.python_versions:
        raise ApplicationError('This collection does not declare support for modules/module_utils on any known Python version.\n'
                               'Ansible supports modules/module_utils on Python versions: %s\n'
                               'This collection provides the Python requirement: %s' % (
                                   ', '.join(SUPPORTED_PYTHON_VERSIONS), config.modules.python_requires))

    return config


def parse_python_requires(value):  # type: (t.Any) -> t.List[str]
    """Parse the given 'python_requires' version specifier and return the matching Python versions."""
    if not isinstance(value, str):
        raise ValueError('python_requires must must be of type `str` not type `%s`' % type(value))

    if value == 'default':
        versions = list(SUPPORTED_PYTHON_VERSIONS)
    elif value == 'controller':
        versions = list(CONTROLLER_PYTHON_VERSIONS)
    else:
        specifier_set = SpecifierSet(value)
        versions = [version for version in SUPPORTED_PYTHON_VERSIONS if specifier_set.contains(Version(version))]

    return versions
