# (c) 2020 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os
import pkgutil
import sys
import warnings

# This package exists to host vendored top-level Python packages for downstream packaging. Any Python packages
# installed beneath this one will be masked from the Ansible loader, and available from the front of sys.path.
# It is expected that the vendored packages will be loaded very early, so a warning will be fired on import of
# the top-level ansible package if any packages beneath this are already loaded at that point.
#
# Python packages may be installed here during downstream packaging using something like:
# pip install --upgrade -t (path to this dir) cryptography pyyaml packaging jinja2

# mask vendored content below this package from being accessed as an ansible subpackage
__path__ = []


def _ensure_vendored_path_entry():
    """
    Ensure that any downstream-bundled content beneath this package is available at the top of sys.path
    """
    # patch our vendored dir onto sys.path
    vendored_path_entry = os.path.dirname(__file__)
    vendored_module_names = set(m[1] for m in pkgutil.iter_modules([vendored_path_entry], ''))  # m[1] == m.name

    if vendored_module_names:
        # patch us early to load vendored deps transparently
        if vendored_path_entry in sys.path:
            # handle reload case by removing the existing entry, wherever it might be
            sys.path.remove(vendored_path_entry)
        sys.path.insert(0, vendored_path_entry)

        already_loaded_vendored_modules = set(sys.modules.keys()).intersection(vendored_module_names)

        if already_loaded_vendored_modules:
            warnings.warn('One or more Python packages bundled by this ansible-core distribution were already '
                          'loaded ({0}). This may result in undefined behavior.'.format(', '.join(sorted(already_loaded_vendored_modules))))


_ensure_vendored_path_entry()
