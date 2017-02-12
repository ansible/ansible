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

from ncclient.xml_ import new_ele, sub_ele, to_xml, to_ele

from ansible.module_utils.connection import exec_command

def send_request(module, obj, check_rc=True):
    request = to_xml(obj)
    rc, out, err = exec_command(module, request)
    if rc != 0:
        if check_rc:
            module.fail_json(msg=str(err))
        return to_ele(err)
    return to_ele(out)

def children(root, iterable):
    for item in iterable:
        try:
            ele = sub_ele(ele, item)
        except NameError:
            ele = sub_ele(root, item)

def lock(module, target='candidate'):
    obj = new_ele('lock')
    children(obj, ('target', target))
    return send_request(module, obj)

def unlock(module, target='candidate'):
    obj = new_ele('unlock')
    children(obj, ('target', target))
    return send_request(module, obj)

def commit(module):
    return send_request(module, new_ele('commit'))

def discard_changes(module):
    return send_request(module, new_ele('discard-changes'))

def validate(module):
    obj = new_ele('validate')
    children(obj, ('source', 'candidate'))
    return send_request(module, obj)

def get_config(module, source='running', filter=None):
    obj = new_ele('get-config')
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
