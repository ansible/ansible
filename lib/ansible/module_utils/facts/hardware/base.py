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

from __future__ import annotations

import typing as t

from ansible.module_utils.facts.collector import BaseFactCollector


class Hardware:
    platform = 'Generic'

    # FIXME: remove load_on_init when we can
    def __init__(self, module, load_on_init=False):
        self.module = module

    def populate(self, collected_facts=None):
        return {}


class HardwareCollector(BaseFactCollector):
    name = 'hardware'
    _fact_ids = set(['processor',
                     'processor_cores',
                     'processor_count',
                     # TODO: mounts isn't exactly hardware
                     'mounts',
                     'devices'])  # type: t.Set[str]
    _fact_class = Hardware

    def collect(self, module=None, collected_facts=None):
        collected_facts = collected_facts or {}
        if not module:
            return {}

        # Network munges cached_facts by side effect, so give it a copy
        facts_obj = self._fact_class(module)

        facts_dict = facts_obj.populate(collected_facts=collected_facts)

        return facts_dict
