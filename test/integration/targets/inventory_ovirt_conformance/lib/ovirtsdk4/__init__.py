from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


class Connection(object):

    def __init__(self, *args, **kwargs):
        self.__system_service = None

    def system_service(self):
        """
        Returns the reference to the root of the services tree.
        The returned value is an instance of the `SystemService` class.
        """

        if self.__system_service is None:
            from ovirtsdk4.services import SystemService
            self.__system_service = SystemService(self, '')
        return self.__system_service

    def follow_link(self, obj):
        if isinstance(obj, list):
            return obj

        links = {
            '/ovirt-engine/api/hosts/3d64646a-2877-41bb-af57-df134c5e73c4': {
                'name': 'host01'
            },
            '/ovirt-engine/api/clusters/848141d1-4385-4ec2-ad51-641bfa77b762': {
                'name': 'cluster01',
                'id': '848141d1-4385-4ec2-ad51-641bfa77b762'
            },
            '/ovirt-engine/api/templates/a39f1b56-e84e-4b5b-83f7-10faee6b5410': {
                'name': 'template01'
            },
            '/ovirt-engine/api/clusters/848141d1-4385-4ec2-ad51-641bfa77b762/affinitygroups/7e80bfd0-c4ea-42f9-8087-d13ae15fe66c': {
                'vms': [FakeStruct({
                    'name': 'vm01'
                })]
            }
        }

        return FakeStruct(links.get(obj.href, {}))


class FakeStruct(object):
    def __init__(self, attr_dict):
        for k, v in attr_dict.items():
            setattr(self, k, v)
