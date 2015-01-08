# This code is part of Ansible, but is an independent component.
# This particular file snippet, and this file snippet only, is BSD licensed.
# Modules you write using this snippet, which is embedded dynamically by Ansible
# still belong to the author of the module, and may assign their own license
# to the complete work.
#
# Copyright (c), Michael DeHaan <michael.dehaan@gmail.com>, 2012-2013
# All rights reserved.
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

AXAPI_PORT_PROTOCOLS = {
    'tcp': 2,
    'udp': 3,
}

AXAPI_VPORT_PROTOCOLS = {
    'tcp': 2,
    'udp': 3,
    'fast-http': 9,
    'http': 11,
    'https': 12,
}

def a10_argument_spec():
    return dict(
        host=dict(type='str', required=True),
        username=dict(type='str', aliases=['user', 'admin'], required=True),
        password=dict(type='str', aliases=['pass', 'pwd'], required=True, no_log=True),
        write_config=dict(type='bool', default=False)
    )

def axapi_failure(result):
    if 'response' in result and result['response'].get('status') == 'fail':
        return True
    return False

def axapi_call(module, url, post=None):
    '''
    Returns a datastructure based on the result of the API call
    '''
    rsp, info = fetch_url(module, url, data=post)
    if not rsp or info['status'] >= 400:
        module.fail_json(msg="failed to connect (status code %s), error was %s" % (info['status'], info.get('msg', 'no error given')))
    try:
        raw_data = rsp.read()
        data = json.loads(raw_data)
    except ValueError:
        # at least one API call (system.action.write_config) returns
        # XML even when JSON is requested, so do some minimal handling
        # here to prevent failing even when the call succeeded
        if 'status="ok"' in raw_data.lower():
            data = {"response": {"status": "OK"}}
        else:
            data = {"response": {"status": "fail", "err": {"msg": raw_data}}}
    except:
        module.fail_json(msg="could not read the result from the host")
    finally:
        rsp.close()
    return data

def axapi_authenticate(module, base_url, username, password):
    url = '%s&method=authenticate&username=%s&password=%s' % (base_url, username, password)
    result = axapi_call(module, url)
    if axapi_failure(result):
        return module.fail_json(msg=result['response']['err']['msg'])
    sessid = result['session_id']
    return base_url + '&session_id=' + sessid

def axapi_enabled_disabled(flag):
    '''
    The axapi uses 0/1 integer values for flags, rather than strings
    or booleans, so convert the given flag to a 0 or 1. For now, params
    are specified as strings only so thats what we check.
    '''
    if flag == 'enabled':
        return 1
    else:
        return 0

def axapi_get_port_protocol(protocol):
    return AXAPI_PORT_PROTOCOLS.get(protocol.lower(), None)

def axapi_get_vport_protocol(protocol):
    return AXAPI_VPORT_PROTOCOLS.get(protocol.lower(), None)

