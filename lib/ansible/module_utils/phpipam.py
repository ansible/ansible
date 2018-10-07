# -*- coding: utf-8 -*-
# Copyright: (c) 2018, Carson Anderson <rcanderson23@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import ansible.module_utils.urls as urls
import json
import urllib


class PhpIpamWrapper(urls.Request):
    def __init__(self, username, password, url):
        urls.Request.__init__(self)
        self.username = username
        self.password = password
        self.url = url
        self.auth_header = {'Authorization':
                            urls.basic_auth_header(self.username, self.password)}

    # Create and authenticates a session against phpipam server
    def create_session(self):
        url = self.url + 'user/'
        auth = json.load(self.post(url, headers=self.auth_header))
        token = auth['data']['token']
        self.headers.update({'token': '%s' % token})

    # Retrieves subnet information in json
    def get_subnet(self, subnet, section):
        url = self.url + 'subnets/cidr/%s/' % subnet
        subnet_response = json.load(self.get(url))
        section_id = self.get_section_id(section)
        try:
            for subnets in subnet_response['data']:
                if subnets['sectionId'] == section_id:
                    return subnets
        except KeyError:
            return None

    def get_section(self, section):
        url = self.url + 'sections/%s/' % section
        url = url.replace(" ", "%20")
        try:
            section_response = json.load(self.get(url))
            return section_response['data']
        except:
            return None

    def get_vlan(self, vlan):
        url = self.url + 'vlan/'
        vlan_response = json.load(self.get(url))
        for vlans in vlan_response['data']:
            if vlans['number'] == vlan:
                return vlans
        return None

    def get_subnet_id(self, subnet, section):
        subnet_response = self.get_subnet(subnet, section)
        try:
            section_id = self.get_section_id(section)
        except KeyError:
            return None
        if subnet_response['sectionId'] == section_id:
            return subnet_response['id']
        else:
            return None

    def get_section_id(self, section):
        section_response = self.get_section(section)
        try:
            return section_response['id']
        except KeyError:
            return None
        except TypeError:
            return None

    def get_vlan_id(self, vlan):
        vlans = self.get_vlan(vlan)
        try:
            if vlans['number'] == vlan:
                return vlans['vlanId']
        except TypeError:
            return None

    def create(self, session, url, **kwargs):
        payload = urllib.urlencode(dict(**kwargs))
        result = json.load(session.post(url, data=payload))
        return result

    def modify(self, session, url, **kwargs):
        payload = urllib.urlencode(dict(**kwargs))
        result = json.load(session.patch(url, data=payload))
        return result

    def remove(self, session, url, id):
        payload = urllib.urlencode({'id': id})
        result = json.load(session.delete(url, data=payload))
        return result
