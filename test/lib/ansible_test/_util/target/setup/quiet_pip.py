"""Custom entry-point for pip that filters out unwanted logging and warnings."""
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import logging
import os
import re
import runpy
import sys
import warnings

BUILTIN_FILTERER_FILTER = logging.Filterer.filter

LOGGING_MESSAGE_FILTER = re.compile("^("
                                    ".*Running pip install with root privileges is generally not a good idea.*|"  # custom Fedora patch [1]
                                    ".*Running pip as the 'root' user can result in broken permissions .*|"  # pip 21.1
                                    "DEPRECATION: Python 2.7 will reach the end of its life .*|"  # pip 19.2.3
                                    "Ignoring .*: markers .* don't match your environment|"
                                    "Looking in indexes: .*|"  # pypi-test-container
                                    "Requirement already satisfied.*"
                                    ")$")

# [1] https://src.fedoraproject.org/rpms/python-pip/blob/f34/f/emit-a-warning-when-running-with-root-privileges.patch

WARNING_MESSAGE_FILTERS = (
    # DEPRECATION: Python 2.7 reached the end of its life on January 1st, 2020. Please upgrade your Python as Python 2.7 is no longer maintained.
    # pip 21.0 will drop support for Python 2.7 in January 2021.
    # More details about Python 2 support in pip, can be found at https://pip.pypa.io/en/latest/development/release-process/#python-2-support
    'DEPRECATION: Python 2.7 reached the end of its life ',

    # DEPRECATION: Python 3.5 reached the end of its life on September 13th, 2020. Please upgrade your Python as Python 3.5 is no longer maintained.
    # pip 21.0 will drop support for Python 3.5 in January 2021. pip 21.0 will remove support for this functionality.
    'DEPRECATION: Python 3.5 reached the end of its life ',
)


def custom_filterer_filter(self, record):
    """Globally omit logging of unwanted messages."""
    if LOGGING_MESSAGE_FILTER.search(record.getMessage()):
        return 0

    return BUILTIN_FILTERER_FILTER(self, record)


def main():
    """Main program entry point."""
    # Filtering logging output globally avoids having to intercept stdout/stderr.
    # It also avoids problems with loss of color output and mixing up the order of stdout/stderr messages.
    logging.Filterer.filter = custom_filterer_filter

    for message_filter in WARNING_MESSAGE_FILTERS:
        # Setting filterwarnings in code is necessary because of the following:
        #   Python 2.7 cannot use the -W option to match warning text after a colon. This makes it impossible to match specific warning messages.
        warnings.filterwarnings('ignore', message_filter)

    get_pip = os.environ.get('GET_PIP')

    try:
        if get_pip:
            directory, filename = os.path.split(get_pip)
            module = os.path.splitext(filename)[0]
            sys.path.insert(0, directory)
            runpy.run_module(module, run_name='__main__', alter_sys=True)
        else:
            runpy.run_module('pip.__main__', run_name='__main__', alter_sys=True)
    except ImportError as ex:
        print('pip is unavailable: %s' % ex)
        sys.exit(1)


if __name__ == '__main__':
    main()
