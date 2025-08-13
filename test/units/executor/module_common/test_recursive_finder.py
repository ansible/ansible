# -*- coding: utf-8 -*-

# Copyright: (c) 2017, Toshio Kuratomi <tkuratomi@ansible.com>
# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import annotations

import datetime
import os
import pytest
import zipfile

from io import BytesIO

import ansible.errors

from ansible._internal._ansiballz._builder import ExtensionManager
from ansible.executor.module_common import recursive_finder
from ansible.plugins.loader import init_plugin_loader

# These are the modules that are brought in by module_utils/basic.py  This may need to be updated
# when basic.py gains new imports
# We will remove these when we modify AnsiBallZ to store its args in a separate file instead of in
# basic.py

MODULE_UTILS_BASIC_FILES = frozenset(('ansible/__init__.py',
                                      'ansible/module_utils/__init__.py',
                                      'ansible/module_utils/basic.py',
                                      'ansible/module_utils/_internal/__init__.py',
                                      'ansible/module_utils/_internal/_ansiballz/__init__.py',
                                      'ansible/module_utils/_internal/_ansiballz/_loader.py',
                                      'ansible/module_utils/_internal/_dataclass_validation.py',
                                      'ansible/module_utils/_internal/_datatag/__init__.py',
                                      'ansible/module_utils/_internal/_datatag/_tags.py',
                                      'ansible/module_utils/_internal/_debugging.py',
                                      'ansible/module_utils/_internal/_deprecator.py',
                                      'ansible/module_utils/_internal/_errors.py',
                                      'ansible/module_utils/_internal/_event_utils.py',
                                      'ansible/module_utils/_internal/_json/__init__.py',
                                      'ansible/module_utils/_internal/_json/_legacy_encoder.py',
                                      'ansible/module_utils/_internal/_json/_profiles/__init__.py',
                                      'ansible/module_utils/_internal/_json/_profiles/_module_legacy_c2m.py',
                                      'ansible/module_utils/_internal/_json/_profiles/_module_legacy_m2c.py',
                                      'ansible/module_utils/_internal/_json/_profiles/_tagless.py',
                                      'ansible/module_utils/_internal/_traceback.py',
                                      'ansible/module_utils/_internal/_validation.py',
                                      'ansible/module_utils/_internal/_messages.py',
                                      'ansible/module_utils/_internal/_no_six.py',
                                      'ansible/module_utils/_internal/_patches/_dataclass_annotation_patch.py',
                                      'ansible/module_utils/_internal/_patches/_socket_patch.py',
                                      'ansible/module_utils/_internal/_patches/_sys_intern_patch.py',
                                      'ansible/module_utils/_internal/_patches/__init__.py',
                                      'ansible/module_utils/_internal/_plugin_info.py',
                                      'ansible/module_utils/_internal/_stack.py',
                                      'ansible/module_utils/_internal/_text_utils.py',
                                      'ansible/module_utils/common/collections.py',
                                      'ansible/module_utils/common/parameters.py',
                                      'ansible/module_utils/common/warnings.py',
                                      'ansible/module_utils/parsing/convert_bool.py',
                                      'ansible/module_utils/common/__init__.py',
                                      'ansible/module_utils/common/file.py',
                                      'ansible/module_utils/common/json.py',
                                      'ansible/module_utils/common/locale.py',
                                      'ansible/module_utils/common/process.py',
                                      'ansible/module_utils/common/sys_info.py',
                                      'ansible/module_utils/common/text/__init__.py',
                                      'ansible/module_utils/common/text/converters.py',
                                      'ansible/module_utils/common/text/formatters.py',
                                      'ansible/module_utils/common/validation.py',
                                      'ansible/module_utils/common/_utils.py',
                                      'ansible/module_utils/common/arg_spec.py',
                                      'ansible/module_utils/compat/__init__.py',
                                      'ansible/module_utils/compat/selinux.py',
                                      'ansible/module_utils/compat/typing.py',
                                      'ansible/module_utils/datatag.py',
                                      'ansible/module_utils/distro/__init__.py',
                                      'ansible/module_utils/distro/_distro.py',
                                      'ansible/module_utils/errors.py',
                                      'ansible/module_utils/parsing/__init__.py',
                                      'ansible/module_utils/parsing/convert_bool.py',
                                      ))

ONLY_BASIC_FILE = frozenset(('ansible/module_utils/basic.py',))

ANSIBLE_LIB = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 'lib', 'ansible')

NOW = datetime.datetime.now(datetime.timezone.utc)


@pytest.fixture
def zip_file() -> zipfile.ZipFile:
    init_plugin_loader()

    zipoutput = BytesIO()
    zf = zipfile.ZipFile(zipoutput, mode='w', compression=zipfile.ZIP_STORED)

    return zf


def test_no_module_utils(zip_file: zipfile.ZipFile) -> None:
    name = 'ping'
    data = b'#!/usr/bin/python\nreturn \'{\"changed\": false}\''
    recursive_finder(name, os.path.join(ANSIBLE_LIB, 'modules', 'system', 'ping.py'), data, zip_file, NOW, ExtensionManager())
    assert frozenset(zip_file.namelist()) == MODULE_UTILS_BASIC_FILES


def test_module_utils_with_syntax_error(zip_file: zipfile.ZipFile) -> None:
    name = 'fake_module'
    data = b'#!/usr/bin/python\ndef something(:\n   pass\n'
    with pytest.raises(ansible.errors.AnsibleError) as exec_info:
        recursive_finder(name, os.path.join(ANSIBLE_LIB, 'modules', 'system', 'fake_module.py'), data, zip_file, NOW, ExtensionManager())
    assert "Unable to compile 'fake_module': invalid syntax" in str(exec_info.value)


def test_module_utils_with_identation_error(zip_file: zipfile.ZipFile) -> None:
    name = 'fake_module'
    data = b'#!/usr/bin/python\n    def something():\n    pass\n'
    with pytest.raises(ansible.errors.AnsibleError) as exec_info:
        recursive_finder(name, os.path.join(ANSIBLE_LIB, 'modules', 'system', 'fake_module.py'), data, zip_file, NOW, ExtensionManager())
    assert "Unable to compile 'fake_module': unexpected indent" in str(exec_info.value)


def test_from_import_six(zip_file: zipfile.ZipFile) -> None:
    name = 'ping'
    data = b'#!/usr/bin/python\nfrom ansible.module_utils import six'
    recursive_finder(name, os.path.join(ANSIBLE_LIB, 'modules', 'system', 'ping.py'), data, zip_file, NOW, ExtensionManager())
    assert frozenset(zip_file.namelist()) == frozenset(('ansible/module_utils/six/__init__.py', )).union(MODULE_UTILS_BASIC_FILES)


def test_import_six(zip_file: zipfile.ZipFile) -> None:
    name = 'ping'
    data = b'#!/usr/bin/python\nimport ansible.module_utils.six'
    recursive_finder(name, os.path.join(ANSIBLE_LIB, 'modules', 'system', 'ping.py'), data, zip_file, NOW, ExtensionManager())
    assert frozenset(zip_file.namelist()) == frozenset(('ansible/module_utils/six/__init__.py', )).union(MODULE_UTILS_BASIC_FILES)


def test_import_six_from_many_submodules(zip_file: zipfile.ZipFile) -> None:
    name = 'ping'
    data = b'#!/usr/bin/python\nfrom ansible.module_utils.six.moves.urllib.parse import urlparse'
    recursive_finder(name, os.path.join(ANSIBLE_LIB, 'modules', 'system', 'ping.py'), data, zip_file, NOW, ExtensionManager())
    assert frozenset(zip_file.namelist()) == frozenset(('ansible/module_utils/six/__init__.py',)).union(MODULE_UTILS_BASIC_FILES)
