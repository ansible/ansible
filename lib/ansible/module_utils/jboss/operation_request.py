# -*- coding: utf-8 -*-

# (c) 2017, Ansible by Red Hat, inc
#
# This file is part of Ansible by Red Hat
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


class OperationRequestBuilder(object):

    def __init__(self):
        self.detyped_request = dict(address=[])

    def read(self):
        self.detyped_request['operation'] = 'read-resource'

    def add(self):
        self.detyped_request['operation'] = 'add'

    def remove(self):
        self.detyped_request['operation'] = 'remove'

    def write(self, attribute, value):
        self.detyped_request['operation'] = 'write-attribute'
        self.detyped_request['name'] = attribute
        self.detyped_request['value'] = value

    def _no_target(self):
        return self.detyped_request['address'] == []

    def operation(self, name):
        self.detyped_request['operation'] = name

    def deploy(self):
        self.operation('deploy' if self._no_target() else 'add')

    def undeploy(self):
        self.operation('undeploy' if self._no_target() else 'remove')

    def composite(self, operations):
        self.detyped_request['operation'] = 'composite'
        self.detyped_request['steps'] = operations

    def content(self, src):
        self.detyped_request['content'] = [dict(url='file:' + src)]

    def content_reference(self, bytes_value):
        self.detyped_request['content'] = [
            {'hash': {'BYTES_VALUE': bytes_value}}]

    def address_from(self, path):
        if path is not None:
            # Use regex: /node-type=node-name (/node-type=node-name)*
            tokens = path.split('/')

            address = []

            for token in tokens[1:]:
                node_type, node_name = token.split('=')
                address.append({node_type: node_name})

            self.detyped_request['address'] = address

    def deployment(self, name):
        self.detyped_request['address'].append(dict(deployment=name))

    def target(self, server_group):
        if server_group is not None:
            self.detyped_request['address'].append(
                {'server-group': server_group})

    def payload(self, attributes):
        self.detyped_request.update(attributes)

    def build(self):
        return self.detyped_request


def execute(operation, parameters, path):
    builder = OperationRequestBuilder()
    builder.address_from(path)
    builder.payload(parameters)
    builder.operation(operation)
    return builder.build()


def read(path):
    builder = OperationRequestBuilder()
    builder.address_from(path)
    builder.read()
    return builder.build()


def add(path, attributes):
    builder = OperationRequestBuilder()
    builder.address_from(path)
    builder.add()
    builder.payload(attributes)
    return builder.build()


def remove(path):
    builder = OperationRequestBuilder()
    builder.address_from(path)
    builder.remove()
    return builder.build()


def write_attribute(path, name, value):
    builder = OperationRequestBuilder()
    builder.address_from(path)
    builder.write(name, value)
    return builder.build()


def composite(operations):
    builder = OperationRequestBuilder()
    builder.composite(operations)
    return builder.build()


def deploy(name, src, server_group):
    add_builder = OperationRequestBuilder()
    add_builder.deployment(name)
    add_builder.content(src)
    add_builder.add()
    add_content = add_builder.build()

    deploy_builder = OperationRequestBuilder()
    deploy_builder.target(server_group)
    deploy_builder.deploy()
    deploy_builder.deployment(name)
    deploy_operation = deploy_builder.build()

    return [add_content, deploy_operation]


def deploy_only(name, bytes_value, server_group):
    builder = OperationRequestBuilder()
    builder.content_reference(bytes_value)
    builder.target(server_group)
    builder.add()
    builder.payload(dict(enabled=True))
    builder.deployment(name)
    return builder.build()


def undeploy(name, server_group):
    builder = OperationRequestBuilder()
    builder.deployment(name)
    builder.remove()
    remove_content = builder.build()

    builder = OperationRequestBuilder()
    builder.target(server_group)
    builder.undeploy()
    builder.deployment(name)
    undeploy_operation = builder.build()

    return [undeploy_operation, remove_content]
