"""Functions for disk IO."""
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import errno
import json
import os

from . import types as t

from .util import (
    to_bytes,
)


def make_dirs(path):  # type: (str) -> None
    """Create a directory at path, including any necessary parent directories."""
    try:
        os.makedirs(to_bytes(path))
    except OSError as ex:
        if ex.errno != errno.EEXIST:
            raise


def write_json_file(path, content, create_directories=False):  # type: (str, t.Union[t.List[t.Any], t.Dict[str, t.Any]], bool) -> None
    """Write the given json content to the specified path, optionally creating missing directories."""
    text_content = json.dumps(content, sort_keys=True, indent=4) + '\n'
    write_text_file(path, text_content, create_directories=create_directories)


def write_text_file(path, content, create_directories=False):  # type: (str, str, bool) -> None
    """Write the given text content to the specified path, optionally creating missing directories."""
    if create_directories:
        make_dirs(os.path.dirname(path))

    with open(to_bytes(path), 'wb') as file:
        file.write(to_bytes(content))
