# (c) 2017 Red Hat Inc.
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
            OUTLINE
                    setup:
                        get_object_from_s3
                        setup_pipeline
                    tests:
                        test_define_pipeline
                        test_deactivate_pipeline
                        test_activate_pipeline
                        test_create_pipeline
                        test_create_pipeline_with_tags
                        test_create_pipeline_already_exists
                        test_delete_nonexistent_pipeline
                        test_delete_pipeline
                        test_build_unique_id_different
                        test_build_unique_id_same
                        test_build_unique_id_obj
                        test_format_tags
                        test_format_empty_tags
                        test_pipeline_description
                        test_pipeline_description_nonexistent
                        test_pipeline_field
                        test_check_dp_exists_true
                        test_check_dp_exists_false
                        test_check_dp_status
                    cleanup:
                        tear_down_pipeline
'''

import pytest
import boto3
import os
import json
from . placebo_fixtures import placeboify, maybe_sleep
from ansible.modules.cloud.amazon import data_pipeline as dp
from ansible.modules.cloud.amazon import s3
from ansible.module_utils._text import to_text


class FakeModule(object):
    def __init__(self, **kwargs):
        self.params = kwargs

    def fail_json(self, *args, **kwargs):
        self.exit_args = args
        self.exit_kwargs = kwargs
        raise Exception('FAIL')

    def exit_json(self, *args, **kwargs):
        self.exit_args = args
        self.exit_kwargs = kwargs


def get_object_from_s3():
    if not os.getenv('PLACEBO_RECORD'):
        objects = [{"name": "Every 1 day",
                    "id": "DefaultSchedule",
                    "fields": []},
                   {"name": "Default",
                    "id": "Default",
                    "fields": []}]
        return objects
    else:
        s3 = boto3.client('s3')
        data = s3.get_object(Bucket="ansible-test-datapipeline", Key="pipeline-object/new.json")
        objects = json.loads(to_text(data['Body'].read()))
        return objects


def setup_pipeline(placeboify, description='', objects=[], tags={}):
    connection = placeboify.client('datapipeline')
    params = {'name': 'ansible-test-create-pipeline',
              'description': description,
              'state': 'present',
              'timeout': 300,
              'objects': objects,
              'tags': tags,
              'parameters': [],
              'values': []}
    m = FakeModule(**params)
    changed, result = dp.create_pipeline(connection, m)
    return m, connection, result['data_pipeline']['pipeline_id']


def tear_down_pipeline(connection, module):
    params = {'name': 'ansible-test-create-pipeline',
              'state': 'absent',
              'timeout': 300}
    dp.delete_pipeline(connection, module)


def test_define_pipeline(placeboify, maybe_sleep):
    m, connection, dp_id = setup_pipeline(placeboify, description='ansible-unit-test-1', objects=[], tags={})
    m.params['objects'] = get_object_from_s3()  # get objects to populate the pipeline to define it
    changed, result = dp.define_pipeline(client=connection, module=m, objects=m.params.get('objects'), dp_id=dp_id)
    assert 'has been updated' in result
    tear_down_pipeline(connection, m)


def test_deactivate_pipeline(placeboify, maybe_sleep):
    m, connection, dp_id = setup_pipeline(placeboify, description='ansible-unit-test-2', objects=get_object_from_s3(), tags={})
    changed, result = dp.deactivate_pipeline(connection, m)
    assert "Data Pipeline ansible-test-create-pipeline deactivated" in result['msg']
    tear_down_pipeline(connection, m)


def test_activate_pipeline(placeboify, maybe_sleep):
    objects = get_object_from_s3()
    m, connection, dp_id = setup_pipeline(placeboify, description='ansible-unit-test-3', objects=objects, tags={})
    changed, result = dp.activate_pipeline(connection, m)
    assert changed is True
    tear_down_pipeline(connection, m)


def test_create_pipeline(placeboify, maybe_sleep):
    obj = get_object_from_s3()
    connection = placeboify.client('datapipeline')
    params = {'name': 'ansible-test-create-pipeline',
              'description': 'ansible-unit-test-4',
              'state': 'present',
              'timeout': 300,
              'tags': {}}
    m = FakeModule(**params)
    changed, result = dp.create_pipeline(connection, m)
    assert changed is True
    tear_down_pipeline(connection, m)


def test_create_pipeline_with_tags(placeboify, maybe_sleep):
    obj = get_object_from_s3()
    connection = placeboify.client('datapipeline')
    params = {'name': 'ansible-test-create-pipeline',
              'description': 'ansible-unit-test-5',
              'state': 'present',
              'tags': {'ansible': 'test'},
              'timeout': 300}
    m = FakeModule(**params)
    changed, result = dp.create_pipeline(connection, m)
    assert changed is True
    assert result['msg'] == "Data Pipeline ansible-test-create-pipeline created."
    tear_down_pipeline(connection, m)


def test_create_pipeline_already_exists(placeboify, maybe_sleep):
    m, connection, dp_id = setup_pipeline(placeboify, description='ansible-unit-test-6', objects=[], tags={})
    # create the same pipeline
    changed, result = dp.create_pipeline(connection, m)
    assert changed is False
    assert "Data Pipeline ansible-test-create-pipeline is present" in result['msg']
    tear_down_pipeline(connection, m)


def test_delete_nonexistent_pipeline(placeboify, maybe_sleep):
    connection = placeboify.client('datapipeline')
    params = {'name': 'ansible-test-nonexistent',
              'description': 'ansible-unit-test-7',
              'state': 'absent',
              'objects': [],
              'tags': {'ansible': 'test'},
              'timeout': 300}
    m = FakeModule(**params)
    changed, result = dp.delete_pipeline(connection, m)
    assert changed is False
    tear_down_pipeline(connection, m)


def test_delete_pipeline(placeboify, maybe_sleep):
    m, connection, dp_id = setup_pipeline(placeboify, description='ansible-unit-test-8', objects=[], tags={})
    changed, result = dp.delete_pipeline(connection, m)
    assert changed is True


def test_build_unique_id_different(placeboify, maybe_sleep):
    params1 = {'name': 'ansible-unittest-1', 'description': 'test-unique-id'}
    m = FakeModule(**params1)
    hash1 = dp.build_unique_id(m)
    params2 = {'name': 'ansible-unittest-1', 'description': 'test-unique-id-different'}
    m = FakeModule(**params2)
    hash2 = dp.build_unique_id(m)
    assert hash1 != hash2


def test_build_unique_id_same(placeboify, maybe_sleep):
    params1 = {'name': 'ansible-unittest-1', 'description': 'test-unique-id', 'tags': {'ansible': 'test'}}
    m = FakeModule(**params1)
    hash1 = dp.build_unique_id(m)
    params2 = {'name': 'ansible-unittest-1', 'description': 'test-unique-id', 'tags': {'ansible': 'test'}}
    m = FakeModule(**params2)
    hash2 = dp.build_unique_id(m)
    assert hash1 == hash2


def test_build_unique_id_obj(placeboify, maybe_sleep):
    # check that the object can be different and the unique id should be the same; should be able to modify objects
    params1 = {'name': 'ansible-unittest-1', 'objects': [{'first': 'object'}]}
    m = FakeModule(**params1)
    hash1 = dp.build_unique_id(m)
    params2 = {'name': 'ansible-unittest-1', 'objects': [{'second': 'object'}]}
    m = FakeModule(**params2)
    hash2 = dp.build_unique_id(m)
    assert hash1 == hash2


def test_format_tags(placeboify, maybe_sleep):
    unformatted_tags = {'key1': 'val1', 'key2': 'val2', 'key3': 'val3'}
    formatted_tags = dp.format_tags(unformatted_tags)
    for tag_set in formatted_tags:
        assert unformatted_tags[tag_set['key']] == tag_set['value']


def test_format_empty_tags(placeboify, maybe_sleep):
    unformatted_tags = {}
    formatted_tags = dp.format_tags(unformatted_tags)
    assert formatted_tags == []


def test_pipeline_description(placeboify, maybe_sleep):
    m, connection, dp_id = setup_pipeline(placeboify, description='ansible-unit-test-9', objects=[], tags={})
    pipelines = dp.pipeline_description(connection, dp_id)
    assert dp_id == pipelines['pipelineDescriptionList'][0]['pipelineId']
    tear_down_pipeline(connection, m)


def test_pipeline_description_nonexistent(placeboify, maybe_sleep):
    hypothetical_pipeline_id = "df-015440025PF7YGLDK47C"
    connection = placeboify.client('datapipeline')
    m = FakeModule()
    with pytest.raises(Exception):
        dp.pipeline_description(connection, hypothetical_pipeline_id)


def test_pipeline_field(placeboify, maybe_sleep):
    m, connection, dp_id = setup_pipeline(placeboify, description='ansible-unit-test-10', objects=[], tags={})
    pipeline_field_info = dp.pipeline_field(connection, dp_id, "@pipelineState")
    assert pipeline_field_info == "PENDING"
    tear_down_pipeline(connection, m)


def test_check_dp_exists_true(placeboify, maybe_sleep):
    m, connection, dp_id = setup_pipeline(placeboify, description='ansible-unit-test-11', objects=[], tags={})
    exists = dp.check_dp_exists(connection, dp_id)
    assert exists is True
    tear_down_pipeline(connection, m)


def test_check_dp_exists_false(placeboify, maybe_sleep):
    hypothetical_pipeline_id = "df-015440025PF7YGLDK47C"
    connection = placeboify.client('datapipeline')
    exists = dp.check_dp_exists(connection, hypothetical_pipeline_id)
    assert exists is False


def test_check_dp_status(placeboify, maybe_sleep):
    inactive_states = ['INACTIVE', 'PENDING', 'FINISHED', 'DELETING']
    m, connection, dp_id = setup_pipeline(placeboify, description='ansible-unit-test-12', objects=[], tags={})
    state = dp.check_dp_status(connection, dp_id, inactive_states)
    assert state is True
    tear_down_pipeline(connection, m)
