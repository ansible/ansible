# (c) 2019 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# CAUTION: This implementation of the collection loader is used by ansible-test.
#          Because of this, it must be compatible with all Python versions supported on the controller or remote.

from __future__ import annotations

from collections.abc import Mapping


def _meta_yml_to_dict(yaml_string_data: bytes | str, content_id):
    """
    Converts string YAML dictionary to a Python dictionary. This function may be monkeypatched to another implementation
    by some tools (eg the import sanity test).
    :param yaml_string_data: a bytes-ish YAML dictionary
    :param content_id: a unique ID representing the content to allow other implementations to cache the output
    :return: a Python dictionary representing the YAML dictionary content
    """
    # NB: content_id is passed in, but not used by this implementation

    # Import the `yaml` module only when needed, as it is not available for the module/module_utils import sanity tests.
    # This also avoids use of shared YAML infrastructure to eliminate any Ansible dependencies outside the collection loader itself.
    import yaml

    try:
        from yaml import CBaseLoader as BaseLoader
    except (ImportError, AttributeError):
        from yaml import BaseLoader  # type: ignore[assignment]

    # Using BaseLoader ensures that all scalars are strings.
    # Doing so avoids parsing unquoted versions as floats, dates as datetime.date, etc.
    routing_dict = yaml.load(yaml_string_data, Loader=BaseLoader)
    if not routing_dict:
        routing_dict = {}
    if not isinstance(routing_dict, Mapping):
        raise ValueError('collection metadata must be an instance of Python Mapping')
    return routing_dict
