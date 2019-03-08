# -*- coding: utf-8 -*-

# Copyright: (c) 2019, Matthew Burtless <mburtless@ns1.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Make coding more python3-ish
from __future__ import absolute_import, division, print_function

__metaclass__ = type

from ansible.module_utils.basic import AnsibleModule, missing_required_lib

try:
    from ansible.module_utils.ansible_release import __version__ as ANSIBLE_VERSION
except Exception:
    ANSIBLE_VERSION = 'unknown'

HAS_NS1 = True

try:
    from ns1 import NS1, Config
    from ns1.rest.errors import ResourceException
except ImportError:
    HAS_NS1 = False


NS1_COMMON_ARGS = dict(apiKey=dict(required=True, no_log=True))


class NS1ModuleBase(object):
    def __init__(self, derived_arg_spec, supports_check_mode=False):
        merged_arg_spec = dict()
        merged_arg_spec.update(NS1_COMMON_ARGS)
        if derived_arg_spec:
            merged_arg_spec.update(derived_arg_spec)

        self.module = AnsibleModule(
            argument_spec=merged_arg_spec, supports_check_mode=supports_check_mode
        )

        if not HAS_NS1:
            self.module.fail_json(msg=missing_required_lib("ns1-python"))
        self._build_ns1()

    def _build_ns1(self):
        self.config = Config()
        self.config.createFromAPIKey(self.module.params["apiKey"])
        self.config['transport'] = 'basic'
        self.ns1 = NS1(config=self.config)

    def errback_generator(self):
        def errback(args):
            self.module.fail_json(msg="%s - %s" % (args[0], args[1]))

        return errback
