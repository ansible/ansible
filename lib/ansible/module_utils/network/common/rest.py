#!/usr/bin/python
#
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
#
import json
import q

from ansible.module_utils.connection import Connection, ConnectionError
from ansible.module_utils._text import to_bytes, to_text

DEFAULT_PAGE_SIZE = 10

class RestApi(object):
    def __init__(self, socket_path, idempotency_support=True):
        self.socket_path = socket_path
        # If server supports Idempotency we will skip the check
        # in client
        self.idempotency_support = idempotency_support

    def _iterate_resource_by_id(self, resource_list, content=None, primary_keys=None):
        if primary_keys is not None:
           want_config = dict()
           for keys in primary_keys:
               want_config.update({keys: content.get(keys, {})})
        else:
            want_config = dict(content)

        for resource in resource_list:
            if compare_json_resources(resource, want_config):
                return resource
                    
        return None

    def getResourceList(self, url_path, query_filters=None):
        conn = Connection(self.socket_path)
        
        try:
            response = conn.send_request(
                url_path=url_path,
                http_method='GET',
                query_params=query_filters)
        except ConnectionError as e:
            raise e
        return response.get('items', {})


    def addResource(self, url_path, content=None, primary_keys=None):
        conn = Connection(self.socket_path)
        
        # To support idempotent we will have to check if we already
        # have object with same primary key or content in case of no pk
        if self.idempotency_support is False:
            try:
                old_obj_list = self.getResourceList(url_path)
            except ConnectionError as e:
                raise e
            if primary_keys is None:
                if self._iterate_resource_by_id(old_obj_list, content) is not None:
                    return (False, None)
            elif self._iterate_resource_by_id(old_obj_list, content,
                                             primary_keys=primary_keys) is not None:
                return (False, None)
        # Could not find existing object with same primary key or content
        try:
            response =  conn.send_request(
                url_path=url_path,
                http_method='POST',
                body_params=content,
            )
        except ConnectionError as e:
            raise e

        return (True, response)

# Function to compare if 'want' dict is subset/copy of 'have'
# It supports comparing dicts with mutable objects
def compare_json_resources(have, want):
    if set(have.keys()) & set(want.keys()) != set(want.keys()):
        return False
    for k in want:
        if k in have:
            if isinstance(have[k], (list, tuple, set)):
                if not isinstance(want[k], (list, tuple, set)):
                    return False
                else:
                    q(want[k], have[k])
                    if len(set(have[k]) - set(want[k])) != 0:
                        return False
            elif isinstance(have[k], dict):
                if not isinstance(want[k], dict):
                    return False
                else:
                    if not compare_json_resources(have[k], want[k]): 
                        return False 
            elif have[k] != want[k]:
                return False
            
        else:
            return False
        
    return True
