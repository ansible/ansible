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

from ansible.module_utils.connection import Connection
from ansible.module_utils._text import to_bytes

DEFAULT_PAGE_SIZE = 10

class RestApi(object):
    def __init__(self, socket_path, idempotency_support=True):
        self.socket_path = socket_path
        # If server supports Idempotency we will skip the check
        # in client
        self.idempotency_support = idempotency_support

    def _iterate_resource_by_id(self, resource_list, content=None, pk_id=None):
        q(resource_list)
        for resource in resource_list:
            for k, v in resource.get('items', {}):
                if pk_id is not None:
                    if pk_id == k and v == content[pk_id]:
                       return resource
                else:
                    for k_new, v_new in content:
                        if k_new == k and v_new == v:
                            return resource
                    
        return None

    def getResourceList(self, url_path, query_filters=None):
        conn = Connection(self.socket_path)
        
        try:
            response = conn.send_request(
                url_path=url_path,
                http_method='GET',
                query_params=query_filters)
            response = to_bytes(response, errors='surrogate_or_strict')
        except ConnectionError as e:
            raise e
        return response


    def addResource(self, url_path, content=None, primary_key=None):
        conn = Connection(self.socket_path)
        
        # To support idempotent we will have to check if we already
        # have object with same primary key or content in case of no pk
        if self.idempotency_support is False:
            try:
                old_obj_list = conn.send_request(
                    url_path=url_path,
                    http_method='GET')
            except ConnectionError as e:
                raise e
            if primary_key is None:
                if self._iterate_resource_by_id(old_obj_list, content) is not None:
                    return False
            else:
                if self._iterate_resource_by_id(old_obj_list, content,
                                          pk_id=primary_key) is not None:
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
