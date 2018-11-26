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

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible.module_utils.facts.network.base import NetworkCollector
from ansible.module_utils.facts.network.generic_bsd import GenericBsdIfconfigNetwork


class NetBSDNetwork(GenericBsdIfconfigNetwork):
    """
    This is the NetBSD Network Class.
    It uses the GenericBsdIfconfigNetwork
    """
    platform = 'NetBSD'

    def get_media_select(self, media_string):
        last = media_string.find('(')
        media_select = media_string[:last].rstrip() if last != -1 else media_string
        return media_select

    def get_media_type_and_options(self, media_string):
        first = media_string.find('(') + 1
        media_type_opts = media_string[first::].rstrip(')') if first else ''
        return media_type_opts

    def parse_media_line(self, words, current_if, ips):
        # example of line:
        # $ ifconfig
        # ne0: flags=8863<UP,BROADCAST,NOTRAILERS,RUNNING,SIMPLEX,MULTICAST> mtu 1500
        #    ec_capabilities=1<VLAN_MTU>
        #    ec_enabled=0
        #    address: 00:20:91:45:00:78
        #    media: Ethernet 10baseT full-duplex
        #    inet 192.168.156.29 netmask 0xffffff00 broadcast 192.168.156.255
        #
        # (other possible output for line media:
        #    media: Ethernet autoselect (1000baseT full-duplex)
        current_if['media'] = words[1]

        media_string = ' '.join(words[2:])
        if 'autoselect' in media_string:
            if len(words) > 2:
                current_if['media_select'] = self.get_media_select(media_string)
            if len(words) > 3:
                media_type_opts_list = self.get_media_type_and_options(media_string).split(' ')
                current_if['media_type'] = media_type_opts_list[0]
                if len(media_type_opts_list) > 1:
                    current_if['media_options'] = media_type_opts_list[1].split(',')
        else:
            if len(words) > 2:
                current_if['media_type'] = words[2]
            if len(words) > 3:
                current_if['media_options'] = words[3].split(',')


class NetBSDNetworkCollector(NetworkCollector):
    _fact_class = NetBSDNetwork
    _platform = 'NetBSD'
