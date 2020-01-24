# Copyright (c) 2019 Matt Martz <matt@sivel.net>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import multiprocessing

# Explicit multiprocessing context using the fork start method
# This exists as a compat layer now that Python3.8 has changed the default
# start method for macOS to ``spawn`` which is incompatible with our
# code base currently
#
# This exists in utils to allow it to be easily imported into various places
# without causing circular import or dependency problems
try:
    context = multiprocessing.get_context('fork')
except AttributeError:
    # Py2 has no context functionality, and only supports fork
    context = multiprocessing
