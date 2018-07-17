# This code is part of Ansible, but is an independent component.
# This particular file snippet, and this file snippet only, is BSD licensed.
# Modules you write using this snippet, which is embedded dynamically by
# Ansible still belong to the author of the module, and may assign their own
# license to the complete work.
#
# Copyright (C) 2018 Western Telematic Inc.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#  * Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
#  * Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#
# Contains utility methods
# WTI Networking
#
from __future__ import absolute_import, division, print_function
__metaclass__ = type

import base64, json, codecs

from ansible.module_utils._text import to_text, to_bytes
from ansible.module_utils.urls import fetch_url

def request(wtimodule, url, user, passwd, timeout, data=None, method=None):
    auth = to_text(base64.b64encode(to_bytes('{0}:{1}'.format(user, passwd), errors='surrogate_or_strict')))

    response, info = fetch_url(wtimodule, url, data=data, method=method, timeout=timeout, headers={'Content-Type': 'application/json', 'Authorization': "Basic %s" % auth})

    if info['status'] not in (200, 201, 204):
        wtimodule.fail_json(msg=info['msg'])

    # Search for body in both http body and http data
    if response is not None:
        body = codecs.decode(response.read(), 'utf-8')
    elif 'body' in info:
        body = codecs.decode(info['body'], 'utf-8')
        del info['body']
    else:
        body = ''

    if body:
        return body
    else:
        return {}
