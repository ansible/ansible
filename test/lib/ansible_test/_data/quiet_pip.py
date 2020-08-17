"""Custom entry-point for pip that filters out unwanted logging and warnings."""
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import logging
import re
import runpy
import warnings

BUILTIN_FILTERER_FILTER = logging.Filterer.filter

LOGGING_MESSAGE_FILTER = re.compile("^("
                                    ".*Running pip install with root privileges is generally not a good idea.*|"  # custom Fedora patch [1]
                                    "DEPRECATION: Python 2.7 will reach the end of its life .*|"  # pip 19.2.3
                                    "Ignoring .*: markers .* don't match your environment|"
                                    "Requirement already satisfied.*"
                                    ")$")

# [1] https://src.fedoraproject.org/rpms/python-pip/blob/master/f/emit-a-warning-when-running-with-root-privileges.patch

WARNING_MESSAGE_FILTERS = (
    # DEPRECATION: Python 2.6 is no longer supported by the Python core team, please upgrade your Python.
    # A future version of pip will drop support for Python 2.6
    'Python 2.6 is no longer supported by the Python core team, ',

    # {path}/python2.6/lib/python2.6/site-packages/pip/_vendor/urllib3/util/ssl_.py:137: InsecurePlatformWarning:
    # A true SSLContext object is not available. This prevents urllib3 from configuring SSL appropriately and may cause certain SSL connections to fail.
    # You can upgrade to a newer version of Python to solve this.
    # For more information, see https://urllib3.readthedocs.io/en/latest/advanced-usage.html#ssl-warnings
    'A true SSLContext object is not available. ',

    # {path}/python2.6/lib/python2.6/site-packages/pip/_vendor/urllib3/util/ssl_.py:339: SNIMissingWarning:
    # An HTTPS request has been made, but the SNI (Subject Name Indication) extension to TLS is not available on this platform.
    # This may cause the server to present an incorrect TLS certificate, which can cause validation failures.
    # You can upgrade to a newer version of Python to solve this.
    # For more information, see https://urllib3.readthedocs.io/en/latest/advanced-usage.html#ssl-warnings
    'An HTTPS request has been made, but the SNI ',

    # DEPRECATION: Python 2.7 reached the end of its life on January 1st, 2020. Please upgrade your Python as Python 2.7 is no longer maintained.
    # pip 21.0 will drop support for Python 2.7 in January 2021.
    # More details about Python 2 support in pip, can be found at https://pip.pypa.io/en/latest/development/release-process/#python-2-support
    'DEPRECATION: Python 2.7 reached the end of its life ',
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
        #   Python 2.6 does not support the PYTHONWARNINGS environment variable. It does support the -W option.
        #   Python 2.7 cannot use the -W option to match warning text after a colon. This makes it impossible to match specific warning messages.
        warnings.filterwarnings('ignore', message_filter)

    runpy.run_module('pip.__main__', run_name='__main__', alter_sys=True)


if __name__ == '__main__':
    main()
