# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import annotations

from ansible.module_utils.facts.network.base import NetworkCollector
from ansible.module_utils.facts.network.generic_bsd import GenericBsdIfconfigNetwork


class DarwinNetwork(GenericBsdIfconfigNetwork):
    """
    This is the Mac macOS Darwin Network Class.
    It uses the GenericBsdIfconfigNetwork unchanged
    """
    platform = 'Darwin'

    # media line is different to the default FreeBSD one
    def parse_media_line(self, words, current_if, ips):
        # not sure if this is useful - we also drop information
        current_if['media'] = 'Unknown'  # Mac does not give us this
        current_if['media_select'] = words[1]
        if len(words) > 2:
            # MacOSX sets the media to '<unknown type>' for bridge interface
            # and parsing splits this into two words; this if/else helps
            if words[1] == '<unknown' and words[2] == 'type>':
                current_if['media_select'] = 'Unknown'
                current_if['media_type'] = 'unknown type'
            else:
                current_if['media_type'] = words[2][1:-1]
        if len(words) > 3:
            current_if['media_options'] = self.get_options(words[3])


class DarwinNetworkCollector(NetworkCollector):
    _fact_class = DarwinNetwork
    _platform = 'Darwin'
