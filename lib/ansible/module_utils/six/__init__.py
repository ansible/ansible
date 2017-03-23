# This code is part of Ansible, but is an independent component.
# This particular file snippet, and this file snippet only, is BSD licensed.
# Modules you write using this snippet, which is embedded dynamically by Ansible
# still belong to the author of the module, and may assign their own license
# to the complete work.
#
# Copyright (c) 2017, Toshio Kuratomi <tkuratomi@ansible.com>
#
# This code is based on code from Astropy and retains their 3-clause BSD license
# reproduced below:
#
# Copyright (c) 2011-2016, Astropy Developers
#
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# * Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.
# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
# * Neither the name of the Astropy Team nor the names of its contributors may
#   be used to endorse or promote products derived from this software without
#   specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
# Astropy License: https://github.com/astropy/astropy/blob/cf3265e42a0db8e00bb90644db37c8150f5ac00c/licenses/LICENSE.rst
# Astropy Code: https://github.com/astropy/astropy/blob/cf3265e42a0db8e00bb90644db37c8150f5ac00c/astropy/extern/six.py

"""
Handle loading six package from system or from the bundled copy
"""
from __future__ import absolute_import

import imp as _imp
import sys as _sys

try:
    from distutils.version import LooseVersion as _LooseVersion
except ImportError:
    # Some platforms *cough*Solaris*cough* don't ship the whole stdlib
    _LooseVersion = None

try:
    import six as _system_six
except ImportError:
    _system_six = None

from . import _six as _bundled_six


def _find_module(name, path=None):
    """Alternative to `imp.find_module` that can also search in subpackages"""
    parts = name.split('.')

    for part in parts:
        if path is not None:
            path = [path]
        fh, path, descr = _imp.find_module(part, path)
    return fh, path, descr


def _get_bundled_six_source():
    # Special import loader (zipimport for instance)
    found = False
    for path in _sys.path:
        importer = _sys.path_importer_cache.get(path)
        if importer:
            try:
                found = importer.find_module('ansible/module_utils/six/_six')
            except ImportError:
                continue
            if found:
                break
    else:
        raise ImportError("Could not find ansible.module_utils.six._six")

    module_source = importer.get_source('ansible/module_utils/six/_six')
    return module_source


def _get_six_source():
    """Import the newest version of the six library that's available"""
    mod_info = None
    try:
        if _system_six and _LooseVersion and \
                _LooseVersion(_system_six.__version__) >= _LooseVersion(_bundled_six.__version__):
            mod_info = _find_module('six')
    except:
        # Any errors finding the system library, use our bundled lib instead
        pass

    if not mod_info:
        try:
            mod_info = _find_module('ansible.module_utils.six._six')
        except ImportError:
            # zipimport
            module_source = _get_bundled_six_source()
            return module_source

    return mod_info[0].read()

source = _get_six_source()
exec(source)
