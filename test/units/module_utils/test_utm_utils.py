# This code is part of Ansible, but is an independent component.
# This particular file snippet, and this file snippet only, is BSD licensed.
# Modules you write using this snippet, which is embedded dynamically by Ansible
# still belong to the author of the module, and may assign their own license
# to the complete work.
#
# Copyright: (c) 2018, Johannes Brunswicker <johannes.brunswicker@gmail.com>
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

from ansible.module_utils.utm_utils import UTM


class FakeModule:
    def __init__(self, params):
        self.params = params


def test_combine_headers_returns_only_default():
    expected = {"Accept": "application/json", "Content-type": "application/json"}
    module = FakeModule(
        params={'utm_protocol': 'utm_protocol', 'utm_host': 'utm_host', 'utm_port': 1234, 'utm_token': 'utm_token',
                'name': 'FakeName', 'headers': {}})
    result = UTM(module, "endpoint", [])._combine_headers()
    assert result == expected


def test_combine_headers_returns_only_default2():
    expected = {"Accept": "application/json", "Content-type": "application/json"}
    module = FakeModule(
        params={'utm_protocol': 'utm_protocol', 'utm_host': 'utm_host', 'utm_port': 1234, 'utm_token': 'utm_token',
                'name': 'FakeName'})
    result = UTM(module, "endpoint", [])._combine_headers()
    assert result == expected


def test_combine_headers_returns_combined():
    expected = {"Accept": "application/json", "Content-type": "application/json",
                "extraHeader": "extraHeaderValue"}
    module = FakeModule(params={'utm_protocol': 'utm_protocol', 'utm_host': 'utm_host', 'utm_port': 1234,
                                'utm_token': 'utm_token', 'name': 'FakeName',
                                "headers": {"extraHeader": "extraHeaderValue"}})
    result = UTM(module, "endpoint", [])._combine_headers()
    assert result == expected
