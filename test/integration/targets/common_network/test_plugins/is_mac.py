# Copyright: (c) 2020, Matt Martz <matt@sivel.net>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

from ansible.module_utils.common.network import is_mac


class TestModule(object):
    def tests(self):
        return {
            'is_mac': is_mac,
        }
