# (c) 2016, Marcos Diez <marcos@unitron.com.br>
# https://github.com/marcosdiez/
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
'''
DOCUMENTATION:
    author: 'Marcos Diez <marcos (at) unitron.com.br>'
    lookup: mongodb
    version_added: "2.3"
    short_description: lookup info from MongoDB
    description:
        - 'The ``MongoDB`` lookup runs the *find()* command on a given *collection* on a given *MongoDB* server.'
        - 'The result is a list of jsons, so slightly different from what PyMongo returns. In particular, *timestamps* are converted to epoch integers.'
    options:
        connect_string:
            description:
                - Can be any valid MongoDB connection string, supporting authentication, replicasets, etc.
                - "More info at https://docs.mongodb.org/manual/reference/connection-string/"
            default: "mongodb://localhost/"
        database:
            description:
                - Name of the database which the query will be made
            required: True
        collection:
            description:
                - Name of the collection which the query will be made
            required: True
        filter:
            description:
                - Criteria of the output
            type: 'dict'
            default: '{}'
        projection:
            description:
                - Fields you want returned
            type: dict
            default: "{}"
        skip:
            description:
                - How many results should be skept
            type: integer
        limit:
            description:
                - How many results should be shown
            type: integer
        sort:
            description:
                - Sorting rules. Please notice the constats are replaced by strings.
            type: list
            default: "[]"
    notes:
        - "Please check https://api.mongodb.org/python/current/api/pymongo/collection.html?highlight=find#pymongo.collection.Collection.find for more detais."
    requirements:
        - pymongo >= 2.4
EXAMPLES:
- hosts: all
  gather_facts: false
  vars:
    mongodb_parameters:
      #mandatory parameters
      database: 'local'
      #optional
      collection: "startup_log"
      connection_string: "mongodb://localhost/"
      extra_connection_parameters: { "ssl" : True , "ssl_certfile": /etc/self_signed_certificate.pem" }
      #optional query  parameters, we accept any parameter from the normal mongodb query.
      filter:  { "hostname": "batman" }
      projection: { "pid": True    , "_id" : False , "hostname" : True }
      skip: 0
      limit: 1
      sort:  [ [ "startTime" , "ASCENDING" ] , [ "age", "DESCENDING" ] ]
  tasks:
    - debug: msg="Mongo has already started with the following PID [{{ item.pid }}]"
      with_mongodb: "{{mongodb_parameters}}"
'''

from __future__ import (absolute_import, division, print_function)
from __future__ import unicode_literals
from ansible.module_utils.six import string_types, integer_types
import datetime

__metaclass__ = type

try:
    from pymongo import ASCENDING, DESCENDING
    from pymongo.errors import ConnectionFailure
    from pymongo import MongoClient
except ImportError:
    try:  # for older PyMongo 2.2
        from pymongo import Connection as MongoClient
    except ImportError:
        pymongo_found = False
    else:
        pymongo_found = True
else:
    pymongo_found = True


from ansible.errors import AnsibleError
from ansible.plugins.lookup import LookupBase


class LookupModule(LookupBase):

    def _fix_sort_parameter(self, sort_parameter):
        if sort_parameter is None:
            return sort_parameter

        if not isinstance(sort_parameter, list):
            raise AnsibleError("Error. Sort parameters must be a list, not [ {} ]".format(sort_parameter))

        for item in sort_parameter:
            self._convert_sort_string_to_constant(item)

        return sort_parameter

    def _convert_sort_string_to_constant(self, item):
        original_sort_order = item[1]
        sort_order = original_sort_order.upper()
        if sort_order == "ASCENDING":
            item[1] = ASCENDING
        elif sort_order == "DESCENDING":
            item[1] = DESCENDING
        # else the user knows what s/he is doing and we won't predict. PyMongo will return an error if necessary

    def convert_mongo_result_to_valid_json(self, result):
        if result is None:
            return result
        if isinstance(result, integer_types + (float, bool)):
            return result
        if isinstance(result, string_types):
            return result
        elif isinstance(result, list):
            new_list = []
            for elem in result:
                new_list.append(self.convert_mongo_result_to_valid_json(elem))
            return new_list
        elif isinstance(result, dict):
            new_dict = {}
            for key in result.keys():
                value = result[key]  # python2 and 3 compatible....
                new_dict[key] = self.convert_mongo_result_to_valid_json(value)
            return new_dict
        elif isinstance(result, datetime.datetime):
            # epoch
            return (result - datetime.datetime(1970, 1, 1)). total_seconds()
        else:
            # failsafe
            return "{}".format(result)

    def run(self, terms, variables, **kwargs):

        ret = []
        for term in terms:
            '''
            Makes a MongoDB query and returns the output as a valid list of json.
            Timestamps are converted to epoch integers/longs.

            Here is a sample playbook that uses it:

-------------------------------------------------------------------------------
- hosts: all
  gather_facts: false

  vars:
    mongodb_parameters:
      #optional parameter, default = "mongodb://localhost/"
      # connection_string: "mongodb://localhost/"

      #mandatory parameters
      database: 'local'
      collection: "startup_log"

      #optional query  parameters
      #we accept any parameter from the normal mongodb query.
      # the official documentation is here
      # https://api.mongodb.org/python/current/api/pymongo/collection.html?highlight=find#pymongo.collection.Collection.find
      #   filter:  { "hostname": "batman" }
      #   projection: { "pid": True    , "_id" : False , "hostname" : True }
      #   skip: 0
      #   limit: 1
      #   sort:  [ [ "startTime" , "ASCENDING" ] , [ "age", "DESCENDING" ] ]
      #   extra_connection_parameters = { }

      # dictionary with extra parameters like ssl, ssl_keyfile, maxPoolSize etc...
      # the full list is available here. It varies from PyMongo version
      # https://api.mongodb.org/python/current/api/pymongo/mongo_client.html#pymongo.mongo_client.MongoClient

  tasks:
    - debug: msg="Mongo has already started with the following PID [{{ item.pid }}] - full_data {{ item }} "
      with_items:
      - "{{ lookup('mongodb', mongodb_parameters) }}"
-------------------------------------------------------------------------------
            '''

            connection_string = term.get('connection_string', "mongodb://localhost")
            database = term["database"]
            collection = term['collection']
            extra_connection_parameters = term.get('extra_connection_parameters', {})

            if "extra_connection_parameters" in term:
                del term["extra_connection_parameters"]
            if "connection_string" in term:
                del term["connection_string"]
            del term["database"]
            del term["collection"]

            if "sort" in term:
                term["sort"] = self._fix_sort_parameter(term["sort"])

            # all other parameters are sent to mongo, so we are future and past proof

            try:
                client = MongoClient(connection_string, **extra_connection_parameters)
                results = client[database][collection].find(**term)

                for result in results:
                    result = self.convert_mongo_result_to_valid_json(result)
                    ret.append(result)

            except ConnectionFailure as e:
                raise AnsibleError('unable to connect to database: %s' % str(e))

        return ret
