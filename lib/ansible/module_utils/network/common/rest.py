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

from ansible.module_utils.connection import Connection, ConnectionError
from ansible.module_utils._text import to_bytes, to_text
import q

class RestApi(object):
    def __init__(self, socket_path, idempotency_support=True):
        self.socket_path = socket_path
        # If server supports Idempotency we will skip the check
        # in client
        self.idempotency_support = idempotency_support

    def _diff_resource(self, old, new, primary_keys=None):
        if primary_keys is not None:
           want = dict()
           for keys in primary_keys:
               want.update({keys: new.get(keys, {})})
        else:
            want = dict(new)

        if isinstance(old, list):
            for resource in old:
                if compare_json_resources(resource, want):
                    return resource
        else:
             if compare_json_resources(old, want):
                 return old
                    
        return None

    def _replace_resource_content(self, have, want):
        if not isinstance(have, dict) and not isinstance(want, dict):
            raise ValueError("content should be in dict format")

        if self._diff_resource(have, want) is not None:
            return False

        for key in want:
           if key in have:
               have[key] = want[key]

        return True

    def getResource(self, url_path, query_params=None):
        conn = Connection(self.socket_path)
        
        try:
            response = conn.send_request(
                url_path=url_path,
                http_method='GET',
                query_params=query_params)
        except ConnectionError as e:
            raise e
        return (True, response.get('items', {}))


    def addResource(self, url_path, content=None, primary_keys=None,
                   query_params=None):
        conn = Connection(self.socket_path)
        q(content, primary_keys, query_params)
        
        # To support idempotency we will have to check if we already
        # have object with same primary key or content in case of no pk
        if self.idempotency_support is False:
            try:
                (changed, old_obj_list) = self.getResource(url_path, query_params)
            except ConnectionError as e:
                raise e
            if primary_keys is None:
                if self._diff_resource(old_obj_list, content) is not None:
                    return (False, None)
            elif self._diff_resource(old_obj_list, content,
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

    def editResource(self, url_path, content=None, query_params=None):
        conn = Connection(self.socket_path)
       
        # In case of edit, if old resource have same content then
        # we don't need to send new PUT
        if self.idempotency_support is False:
            try:
                (changed, old_obj) = self.getResource(url_path, query_params)
            except ConnectionError as e:
                raise e
            try:
                if not self._replace_resource_content(old_obj, content):
                    # Old object has same content, nothing to change
                    return (False, None)
            except Exception as exc:
                 raise exc

        try:
            response =  conn.send_request(
                url_path=url_path,
                http_method='PUT',
                body_params=old_obj
            )
        except ConnectionError as e:
            raise e
        return (True, response)

    def deleteResource(self, url_path, body_params=None, query_params=None):
        conn = Connection(self.socket_path)

        try:
            response =  conn.send_request(
                url_path=url_path,
                http_method='DELETE',
                body_params=body_params,
                query_params=query_params
            )
        except ConnectionError as e:
            raise e
        return (True, response)

# Function to compare if 'want' dict is subset/copy of 'have'
# It supports comparing dicts with mutable objects
def compare_json_resources(have, want):
    if set(have.keys()) & set(want.keys()) != set(want.keys()):
        return False

    have_subset = dict()
    for keys in want:
        have_subset.update({keys: have.get(keys, {})})

    have_str = json.dumps(have_subset, sort_keys=True)
    want_str = json.dumps(want, sort_keys=True)

    if have_str == want_str:
        return True
    else:
        return False
