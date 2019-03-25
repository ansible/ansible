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

import os
import json
import collections

import pytest
from units.utils.amazon_placebo_fixtures import placeboify, maybe_sleep

from ansible.modules.cloud.amazon import data_pipeline
from ansible.module_utils._text import to_text

# test_api_gateway.py requires the `boto3` and `botocore` modules
boto3 = pytest.importorskip('boto3')


@pytest.fixture(scope='module')
def dp_setup():
    """
    Yield a FakeModule object, data pipeline id of a vanilla data pipeline, and data pipeline objects

    This fixture is module-scoped, since this can be reused for multiple tests.
    """
    Dependencies = collections.namedtuple("Dependencies", ["module", "data_pipeline_id", "objects"])

    # get objects to use to test populating and activating the data pipeline
    if not os.getenv('PLACEBO_RECORD'):
        objects = [{"name": "Every 1 day",
                    "id": "DefaultSchedule",
                    "fields": []},
                   {"name": "Default",
                    "id": "Default",
                    "fields": []}]
    else:
        s3 = boto3.client('s3')
        data = s3.get_object(Bucket="ansible-test-datapipeline", Key="pipeline-object/new.json")
        objects = json.loads(to_text(data['Body'].read()))

    # create a module with vanilla data pipeline parameters
    params = {'name': 'ansible-test-create-pipeline',
              'description': 'ansible-datapipeline-unit-test',
              'state': 'present',
              'timeout': 300,
              'objects': [],
              'tags': {},
              'parameters': [],
              'values': []}
    module = FakeModule(**params)

    # yield a module, the data pipeline id, and the data pipeline objects (that are not yet defining the vanilla data pipeline)
    if not os.getenv('PLACEBO_RECORD'):
        yield Dependencies(module=module, data_pipeline_id='df-0590406117G8DPQZY2HA', objects=objects)
    else:
        connection = boto3.client('datapipeline')
        changed, result = data_pipeline.create_pipeline(connection, module)
        data_pipeline_id = result['data_pipeline']['pipeline_id']
        yield Dependencies(module=module, data_pipeline_id=data_pipeline_id, objects=objects)

    # remove data pipeline
    if os.getenv('PLACEBO_RECORD'):
        module.params.update(state='absent')
        data_pipeline.delete_pipeline(connection, module)


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


def test_create_pipeline_already_exists(placeboify, maybe_sleep, dp_setup):
    connection = placeboify.client('datapipeline')
    changed, result = data_pipeline.create_pipeline(connection, dp_setup.module)
    assert changed is False
    assert "Data Pipeline ansible-test-create-pipeline is present" in result['msg']


def test_pipeline_field(placeboify, maybe_sleep, dp_setup):
    connection = placeboify.client('datapipeline')
    pipeline_field_info = data_pipeline.pipeline_field(connection, dp_setup.data_pipeline_id, "@pipelineState")
    assert pipeline_field_info == "PENDING"


def test_define_pipeline(placeboify, maybe_sleep, dp_setup):
    connection = placeboify.client('datapipeline')
    changed, result = data_pipeline.define_pipeline(connection, dp_setup.module, dp_setup.objects, dp_setup.data_pipeline_id)
    assert 'has been updated' in result


def test_deactivate_pipeline(placeboify, maybe_sleep, dp_setup):
    connection = placeboify.client('datapipeline')
    changed, result = data_pipeline.deactivate_pipeline(connection, dp_setup.module)
    assert "Data Pipeline ansible-test-create-pipeline deactivated" in result['msg']


def test_activate_without_population(placeboify, maybe_sleep, dp_setup):
    connection = placeboify.client('datapipeline')
    with pytest.raises(Exception) as error_message:
        changed, result = data_pipeline.activate_pipeline(connection, dp_setup.module)
        assert error_message == "You need to populate your pipeline before activation."


def test_create_pipeline(placeboify, maybe_sleep):
    connection = placeboify.client('datapipeline')
    params = {'name': 'ansible-unittest-create-pipeline',
              'description': 'ansible-datapipeline-unit-test',
              'state': 'present',
              'timeout': 300,
              'tags': {}}
    m = FakeModule(**params)
    changed, result = data_pipeline.create_pipeline(connection, m)
    assert changed is True
    assert result['msg'] == "Data Pipeline ansible-unittest-create-pipeline created."

    data_pipeline.delete_pipeline(connection, m)


def test_create_pipeline_with_tags(placeboify, maybe_sleep):
    connection = placeboify.client('datapipeline')
    params = {'name': 'ansible-unittest-create-pipeline_tags',
              'description': 'ansible-datapipeline-unit-test',
              'state': 'present',
              'tags': {'ansible': 'test'},
              'timeout': 300}
    m = FakeModule(**params)
    changed, result = data_pipeline.create_pipeline(connection, m)
    assert changed is True
    assert result['msg'] == "Data Pipeline ansible-unittest-create-pipeline_tags created."

    data_pipeline.delete_pipeline(connection, m)


def test_delete_nonexistent_pipeline(placeboify, maybe_sleep):
    connection = placeboify.client('datapipeline')
    params = {'name': 'ansible-test-nonexistent',
              'description': 'ansible-test-nonexistent',
              'state': 'absent',
              'objects': [],
              'tags': {'ansible': 'test'},
              'timeout': 300}
    m = FakeModule(**params)
    changed, result = data_pipeline.delete_pipeline(connection, m)
    assert changed is False


def test_delete_pipeline(placeboify, maybe_sleep):
    connection = placeboify.client('datapipeline')
    params = {'name': 'ansible-test-nonexistent',
              'description': 'ansible-test-nonexistent',
              'state': 'absent',
              'objects': [],
              'tags': {'ansible': 'test'},
              'timeout': 300}
    m = FakeModule(**params)
    data_pipeline.create_pipeline(connection, m)
    changed, result = data_pipeline.delete_pipeline(connection, m)
    assert changed is True


def test_build_unique_id_different():
    m = FakeModule(**{'name': 'ansible-unittest-1', 'description': 'test-unique-id'})
    m2 = FakeModule(**{'name': 'ansible-unittest-1', 'description': 'test-unique-id-different'})
    assert data_pipeline.build_unique_id(m) != data_pipeline.build_unique_id(m2)


def test_build_unique_id_same():
    m = FakeModule(**{'name': 'ansible-unittest-1', 'description': 'test-unique-id', 'tags': {'ansible': 'test'}})
    m2 = FakeModule(**{'name': 'ansible-unittest-1', 'description': 'test-unique-id', 'tags': {'ansible': 'test'}})
    assert data_pipeline.build_unique_id(m) == data_pipeline.build_unique_id(m2)


def test_build_unique_id_obj():
    # check that the object can be different and the unique id should be the same; should be able to modify objects
    m = FakeModule(**{'name': 'ansible-unittest-1', 'objects': [{'first': 'object'}]})
    m2 = FakeModule(**{'name': 'ansible-unittest-1', 'objects': [{'second': 'object'}]})
    assert data_pipeline.build_unique_id(m) == data_pipeline.build_unique_id(m2)


def test_format_tags():
    unformatted_tags = {'key1': 'val1', 'key2': 'val2', 'key3': 'val3'}
    formatted_tags = data_pipeline.format_tags(unformatted_tags)
    for tag_set in formatted_tags:
        assert unformatted_tags[tag_set['key']] == tag_set['value']


def test_format_empty_tags():
    unformatted_tags = {}
    formatted_tags = data_pipeline.format_tags(unformatted_tags)
    assert formatted_tags == []


def test_pipeline_description(placeboify, maybe_sleep, dp_setup):
    connection = placeboify.client('datapipeline')
    dp_id = dp_setup.data_pipeline_id
    pipelines = data_pipeline.pipeline_description(connection, dp_id)
    assert dp_id == pipelines['pipelineDescriptionList'][0]['pipelineId']


def test_pipeline_description_nonexistent(placeboify, maybe_sleep):
    hypothetical_pipeline_id = "df-015440025PF7YGLDK47C"
    connection = placeboify.client('datapipeline')
    with pytest.raises(Exception) as error:
        data_pipeline.pipeline_description(connection, hypothetical_pipeline_id)
        assert error == data_pipeline.DataPipelineNotFound


def test_check_dp_exists_true(placeboify, maybe_sleep, dp_setup):
    connection = placeboify.client('datapipeline')
    exists = data_pipeline.check_dp_exists(connection, dp_setup.data_pipeline_id)
    assert exists is True


def test_check_dp_exists_false(placeboify, maybe_sleep):
    hypothetical_pipeline_id = "df-015440025PF7YGLDK47C"
    connection = placeboify.client('datapipeline')
    exists = data_pipeline.check_dp_exists(connection, hypothetical_pipeline_id)
    assert exists is False


def test_check_dp_status(placeboify, maybe_sleep, dp_setup):
    inactive_states = ['INACTIVE', 'PENDING', 'FINISHED', 'DELETING']
    connection = placeboify.client('datapipeline')
    state = data_pipeline.check_dp_status(connection, dp_setup.data_pipeline_id, inactive_states)
    assert state is True


def test_activate_pipeline(placeboify, maybe_sleep, dp_setup):
    # use objects to define pipeline before activating
    connection = placeboify.client('datapipeline')
    data_pipeline.define_pipeline(connection,
                                  module=dp_setup.module,
                                  objects=dp_setup.objects,
                                  dp_id=dp_setup.data_pipeline_id)
    changed, result = data_pipeline.activate_pipeline(connection, dp_setup.module)
    assert changed is True
