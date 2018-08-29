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

from ansible.compat.tests import mock
from ansible.compat.tests.mock import call, patch
from ansible.module_utils.network.ftd.configuration import iterate_over_pageable_resource, BaseConfigurationResource


class TestBaseConfigurationResource(object):

    @patch.object(BaseConfigurationResource, 'send_request')
    def test_get_objects_by_filter_with_multiple_filters(self, send_request_mock):
        objects = [
            {'name': 'obj1', 'type': 1, 'foo': {'bar': 'buzz'}},
            {'name': 'obj2', 'type': 1, 'foo': {'bar': 'buz'}},
            {'name': 'obj3', 'type': 2, 'foo': {'bar': 'buzz'}}
        ]
        resource = BaseConfigurationResource(None)

        send_request_mock.side_effect = [{'items': objects}, {'items': []}]
        assert objects == resource.get_objects_by_filter('/objects', {})

        send_request_mock.side_effect = [{'items': objects}, {'items': []}]
        assert [objects[0]] == resource.get_objects_by_filter('/objects', {'name': 'obj1'})

        send_request_mock.side_effect = [{'items': objects}, {'items': []}]
        assert [objects[1]] == resource.get_objects_by_filter('/objects',
                                                              {'type': 1, 'foo': {'bar': 'buz'}})

    @patch.object(BaseConfigurationResource, 'send_request')
    def test_get_objects_by_filter_with_multiple_responses(self, send_request_mock):
        send_request_mock.side_effect = [
            {'items': [
                {'name': 'obj1', 'type': 'foo'},
                {'name': 'obj2', 'type': 'bar'}
            ]},
            {'items': [
                {'name': 'obj3', 'type': 'foo'}
            ]},
            {'items': []}
        ]

        resource = BaseConfigurationResource(None)

        assert [{'name': 'obj1', 'type': 'foo'}, {'name': 'obj3', 'type': 'foo'}] == resource.get_objects_by_filter(
            '/objects', {'type': 'foo'})


class TestIterateOverPageableResource(object):

    def test_iterate_over_pageable_resource_with_no_items(self):
        resource_func = mock.Mock(return_value={'items': []})

        items = iterate_over_pageable_resource(resource_func)

        assert [] == list(items)

    def test_iterate_over_pageable_resource_with_one_page(self):
        resource_func = mock.Mock(side_effect=[
            {'items': ['foo', 'bar']},
            {'items': []},
        ])

        items = iterate_over_pageable_resource(resource_func)

        assert ['foo', 'bar'] == list(items)
        resource_func.assert_has_calls([
            call(query_params={'offset': 0, 'limit': 10}),
            call(query_params={'offset': 10, 'limit': 10})
        ])

    def test_iterate_over_pageable_resource_with_multiple_pages(self):
        resource_func = mock.Mock(side_effect=[
            {'items': ['foo']},
            {'items': ['bar']},
            {'items': ['buzz']},
            {'items': []},
        ])

        items = iterate_over_pageable_resource(resource_func)

        assert ['foo', 'bar', 'buzz'] == list(items)

    def test_iterate_over_pageable_resource_should_preserve_query_params(self):
        resource_func = mock.Mock(return_value={'items': []})

        items = iterate_over_pageable_resource(resource_func, {'filter': 'name:123'})

        assert [] == list(items)
        resource_func.assert_called_once_with(query_params={'filter': 'name:123', 'offset': 0, 'limit': 10})

    def test_iterate_over_pageable_resource_should_preserve_limit(self):
        resource_func = mock.Mock(side_effect=[
            {'items': ['foo']},
            {'items': []},
        ])

        items = iterate_over_pageable_resource(resource_func, {'limit': 1})

        assert ['foo'] == list(items)
        resource_func.assert_has_calls([
            call(query_params={'offset': 0, 'limit': 1}),
            call(query_params={'offset': 1, 'limit': 1})
        ])

    def test_iterate_over_pageable_resource_should_preserve_offset(self):
        resource_func = mock.Mock(side_effect=[
            {'items': ['foo']},
            {'items': []},
        ])

        items = iterate_over_pageable_resource(resource_func, {'offset': 3})

        assert ['foo'] == list(items)
        resource_func.assert_has_calls([
            call(query_params={'offset': 3, 'limit': 10}),
            call(query_params={'offset': 13, 'limit': 10})
        ])

    def test_iterate_over_pageable_resource_should_pass_with_string_offset_and_limit(self):
        resource_func = mock.Mock(side_effect=[
            {'items': ['foo']},
            {'items': []},
        ])

        items = iterate_over_pageable_resource(resource_func, {'offset': '1', 'limit': '1'})

        assert ['foo'] == list(items)
        resource_func.assert_has_calls([
            call(query_params={'offset': '1', 'limit': '1'}),
            call(query_params={'offset': 2, 'limit': '1'})
        ])
