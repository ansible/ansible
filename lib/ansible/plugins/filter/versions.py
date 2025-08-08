# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

from functools import partial
import typing as t

from ansible import errors
from ansible.module_utils.common.text.converters import to_text
from ansible.module_utils.compat.version import LooseVersion, StrictVersion
from ansible.utils.version import SemanticVersion

try:
    from packaging.version import Version as PEP440Version
    HAS_PACKAGING = True
except ImportError:
    HAS_PACKAGING = False


VERSION_TYPE_MAP: dict[str, t.Union[LooseVersion, StrictVersion, SemanticVersion, PEP440Version]] = {
    'loose': LooseVersion,
    'strict': StrictVersion,
    'semver': SemanticVersion,
    'semantic': SemanticVersion,
    'pep440': None,
}
if HAS_PACKAGING:
    VERSION_TYPE_MAP['pep440'] = PEP440Version


def _version(name: str, value: str) -> t.Union[LooseVersion, StrictVersion, SemanticVersion, PEP440Version]:
    """
    Convert a string to a version object.
    :param name: The version type to convert to.
    :param value: The version string to convert.
    :return: A version object.
    :raises: AnsibleFilterError: If the version string cannot be parsed.
    :raises: AnsibleFilterError: If the version is PEP440 and packaging is not installed.
    :raises: AnsibleFilterError: If the version string does not resolve to callable method.
    """

    try:
        method = VERSION_TYPE_MAP[name]
    except KeyError as exc:
        if name == 'pep440' and not HAS_PACKAGING:
            raise errors.AnsibleTemplatePluginError("The pep440_version filter requires the Python 'packaging' library") from exc
        raise

    if not callable(method):
        raise errors.AnsibleTemplatePluginError(f'Invalid version type: {name}')

    try:
        return method(to_text(value))
    except Exception as e:
        raise errors.AnsibleTemplatePluginError(f'Cannot parse version: {e}')


class FilterModule:
    def filters(self) -> dict[str, t.Callable[..., t.Any]]:
        return {
            'loose_version': partial(_version, 'loose'),
            'strict_version': partial(_version, 'strict'),
            'semver_version': partial(_version, 'semver'),
            'semantic_version': partial(_version, 'semantic'),
            'pep440_version': partial(_version, 'pep440'),
        }
