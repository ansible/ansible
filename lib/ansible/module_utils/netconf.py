# This code is part of Ansible, but is an independent component.
# This particular file snippet, and this file snippet only, is BSD licensed.
# Modules you write using this snippet, which is embedded dynamically by Ansible
# still belong to the author of the module, and may assign their own license
# to the complete work.
#
# (c) 2017 Red Hat Inc.
#
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
#
#    * Redistributions of source code must retain the above copyright
#      notice, this list of conditions and the following disclaimer.
#    * Redistributions in binary form must reproduce the above copyright notice,
#      this list of conditions and the following disclaimer in the documentation
#      and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
# IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE
# USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
from contextlib import contextmanager

from ansible.module_utils.connection import exec_command

try:
    from lxml.etree import Element, SubElement, fromstring, tostring
except ImportError:
    from xml.etree.ElementTree import Element, SubElement, fromstring, tostring

NS_MAP = {'nc': "urn:ietf:params:xml:ns:netconf:base:1.0"}


def send_request(module, obj, check_rc=True, ignore_warning=True):
    request = tostring(obj)
    rc, out, err = exec_command(module, request)
    if rc != 0 and check_rc:
        error_root = fromstring(err)
        fake_parent = Element('root')
        fake_parent.append(error_root)

        error_list = fake_parent.findall('.//nc:rpc-error', NS_MAP)
        if not error_list:
            module.fail_json(msg=str(err))

        warnings = []
        for rpc_error in error_list:
            message = rpc_error.find('./nc:error-message', NS_MAP).text
            severity = rpc_error.find('./nc:error-severity', NS_MAP).text

            if severity == 'warning' and ignore_warning:
                warnings.append(message)
            else:
                module.fail_json(msg=str(err))
        return warnings
    return fromstring(out)


def children(root, iterable):
    for item in iterable:
        try:
            ele = SubElement(ele, item)
        except NameError:
            ele = SubElement(root, item)


def lock(module, target='candidate'):
    obj = Element('lock')
    children(obj, ('target', target))
    return send_request(module, obj)


def unlock(module, target='candidate'):
    obj = Element('unlock')
    children(obj, ('target', target))
    return send_request(module, obj)


def commit(module):
    return send_request(module, Element('commit'))


def discard_changes(module):
    return send_request(module, Element('discard-changes'))


def validate(module):
    obj = Element('validate')
    children(obj, ('source', 'candidate'))
    return send_request(module, obj)


def get_config(module, source='running', filter=None):
    obj = Element('get-config')
    children(obj, ('source', source))
    children(obj, ('filter', filter))
    return send_request(module, obj)


@contextmanager
def locked_config(module):
    try:
        lock(module)
        yield
    finally:
        unlock(module)
