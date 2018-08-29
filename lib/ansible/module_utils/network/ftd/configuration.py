# Copyright (c) 2018 Cisco and/or its affiliates.
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

from functools import partial

from ansible.module_utils.network.ftd.common import HTTPMethod, equal_objects, copy_identity_properties, \
    FtdConfigurationError, FtdServerError, ResponseParams

DEFAULT_PAGE_SIZE = 10
DEFAULT_OFFSET = 0

UNPROCESSABLE_ENTITY_STATUS = 422
INVALID_UUID_ERROR_MESSAGE = "Validation failed due to an invalid UUID"
DUPLICATE_NAME_ERROR_MESSAGE = "Validation failed due to a duplicate name"


class BaseConfigurationResource(object):
    def __init__(self, conn):
        self._conn = conn
        self.config_changed = False

    def get_object_by_name(self, url_path, name, path_params=None):
        item_generator = iterate_over_pageable_resource(
            partial(self.send_request, url_path=url_path, http_method=HTTPMethod.GET, path_params=path_params),
            {'filter': 'name:%s' % name}
        )
        # not all endpoints support filtering so checking name explicitly
        return next((item for item in item_generator if item['name'] == name), None)

    def get_objects_by_filter(self, url_path, filters, path_params=None, query_params=None):
        def match_filters(obj):
            for k, v in filters.items():
                if k not in obj or obj[k] != v:
                    return False
            return True

        item_generator = iterate_over_pageable_resource(
            partial(self.send_request, url_path=url_path, http_method=HTTPMethod.GET, path_params=path_params),
            query_params
        )
        return [i for i in item_generator if match_filters(i)]

    def add_object(self, url_path, body_params, path_params=None, query_params=None, update_if_exists=False):
        def is_duplicate_name_error(err):
            return err.code == UNPROCESSABLE_ENTITY_STATUS and DUPLICATE_NAME_ERROR_MESSAGE in str(err)

        def update_existing_object(obj):
            new_path_params = {} if path_params is None else path_params
            new_path_params['objId'] = obj['id']
            return self.send_request(url_path=url_path + '/{objId}',
                                     http_method=HTTPMethod.PUT,
                                     body_params=copy_identity_properties(obj, body_params),
                                     path_params=new_path_params,
                                     query_params=query_params)

        try:
            return self.send_request(url_path=url_path, http_method=HTTPMethod.POST, body_params=body_params,
                                     path_params=path_params, query_params=query_params)
        except FtdServerError as e:
            if is_duplicate_name_error(e):
                existing_obj = self.get_object_by_name(url_path, body_params['name'], path_params)
                if equal_objects(existing_obj, body_params):
                    return existing_obj
                elif update_if_exists:
                    return update_existing_object(existing_obj)
                else:
                    raise FtdConfigurationError(
                        'Cannot add new object. An object with the same name but different parameters already exists.')
            else:
                raise e

    def delete_object(self, url_path, path_params):
        def is_invalid_uuid_error(err):
            return err.code == UNPROCESSABLE_ENTITY_STATUS and INVALID_UUID_ERROR_MESSAGE in str(err)

        try:
            return self.send_request(url_path=url_path, http_method=HTTPMethod.DELETE, path_params=path_params)
        except FtdServerError as e:
            if is_invalid_uuid_error(e):
                return {'status': 'Referenced object does not exist'}
            else:
                raise e

    def edit_object(self, url_path, body_params, path_params=None, query_params=None):
        existing_object = self.send_request(url_path=url_path, http_method=HTTPMethod.GET, path_params=path_params)

        if not existing_object:
            raise FtdConfigurationError('Referenced object does not exist')
        elif equal_objects(existing_object, body_params):
            return existing_object
        else:
            return self.send_request(url_path=url_path, http_method=HTTPMethod.PUT, body_params=body_params,
                                     path_params=path_params, query_params=query_params)

    def send_request(self, url_path, http_method, body_params=None, path_params=None, query_params=None):
        def raise_for_failure(resp):
            if not resp[ResponseParams.SUCCESS]:
                raise FtdServerError(resp[ResponseParams.RESPONSE], resp[ResponseParams.STATUS_CODE])

        response = self._conn.send_request(url_path=url_path, http_method=http_method, body_params=body_params,
                                           path_params=path_params, query_params=query_params)
        raise_for_failure(response)
        if http_method != HTTPMethod.GET:
            self.config_changed = True
        return response[ResponseParams.RESPONSE]


def iterate_over_pageable_resource(resource_func, query_params=None):
    """
    A generator function that iterates over a resource that supports pagination and lazily returns present items
    one by one.

    :param resource_func: function that receives `query_params` named argument and returns a page of objects
    :type resource_func: callable
    :param query_params: initial dictionary of query parameters that will be passed to the resource_func
    :type query_params: dict
    :return: an iterator containing returned items
    :rtype: iterator of dict
    """
    query_params = {} if query_params is None else dict(query_params)
    query_params.setdefault('limit', DEFAULT_PAGE_SIZE)
    query_params.setdefault('offset', DEFAULT_OFFSET)

    result = resource_func(query_params=query_params)
    while result['items']:
        for item in result['items']:
            yield item
        # creating a copy not to mutate existing dict
        query_params = dict(query_params)
        query_params['offset'] = int(query_params['offset']) + int(query_params['limit'])
        result = resource_func(query_params=query_params)
