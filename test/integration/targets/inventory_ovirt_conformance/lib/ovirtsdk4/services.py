from __future__ import (absolute_import, division, print_function)
from ovirtsdk4.service import Service
from ovirtsdk4 import FakeStruct
__metaclass__ = type


class SystemService(Service):
    def __init__(self, connection, path):
        super(SystemService, self).__init__(connection, path)

    def clusters_service(self):

        return ClustersService(self._connection, '%s/clusters' % self._path)

    def vms_service(self):

        return VmsService(self._connection, '%s/vms' % self._path)


class VmsService(Service):
    def list(self, *args, **kwargs):
        return [FakeStruct({
            'id': '57f74db3-874f-4449-a353-2f01a48332f0',
            'name': 'vm01',
            'host': FakeStruct({
                'href': '/ovirt-engine/api/hosts/3d64646a-2877-41bb-af57-df134c5e73c4',
            }),
            'cluster': FakeStruct({
                'id': '3d64646a-2877-41bb-af57-df134c5e73c4',
                'href': '/ovirt-engine/api/hosts/3d64646a-2877-41bb-af57-df134c5e73c4',
            }),
            'status': 'UP',
            'description': 'my_vm01',
            'fqdn': 'vm01.local.domain',
            'os': FakeStruct({
                'type': 'rhel_7x64'
            }),
            'template': FakeStruct({
                'href': '/ovirt-engine/api/templates/a39f1b56-e84e-4b5b-83f7-10faee6b5410',
            }),
        })]

    def vm_service(self, id):
        return VmService(self._connection, '%s/%s' % (self._path, id))


class VmService(Service):

    def affinity_labels_service(self):
        """
        List all known affinity labels.

        """
        return AffinityLabelsService(self._connection, '%s/vms' % self._path)

    def reported_devices_service(self):

        return VmReportedDevicesService(self._connection, '%s/reporteddevices' % self._path)

    def statistics_service(self):

        return StatisticsService(self._connection, '%s/statistics' % self._path)

    def tags_service(self):

        return TagsService(self._connection, '%s/tags' % self._path)


class ClustersService(Service):
    def list(self, *args, **kwargs):
        return [FakeStruct(
            {
                'id': '848141d1-4385-4ec2-ad51-641bfa77b762',
                'name': 'cluster01',
            })
        ]

    def cluster_service(self, id):
        """
        A reference to the service that manages a specific cluster.

        """
        return ClusterService(self._connection, '%s/%s' % (self._path, id))


class ClusterService(Service):
    def affinity_groups_service(self):
        """
        A reference to the service that manages affinity groups.

        """
        return AffinityGroupsService(self._connection, '%s/affinitygroups' % self._path)


class AffinityGroupsService(Service):
    def list(self, *args, **kwargs):
        return [FakeStruct({
            'name': 'group01',
            'href': '/ovirt-engine/api/clusters/848141d1-4385-4ec2-ad51-641bfa77b762/affinitygroups/a53fe0d0-ba94-4ae9-b294-7c9f74d7af79/vms',
            'vms': [FakeStruct({
                'href': '/ovirt-engine/api/clusters/848141d1-4385-4ec2-ad51-641bfa77b762/affinitygroups/a53fe0d0-ba94-4ae9-b294-7c9f74d7af79/vms',
                'name': 'vm01',
            })]
        })]


class AffinityLabelsService(Service):
    def list(self, *args, **kwargs):
        return [FakeStruct({
            'name': 'label01'
        })]


class VmReportedDevicesService(Service):
    def list(self, *args, **kwargs):
        return [FakeStruct({
            'name': 'eth0',
            'ips': [
                FakeStruct({
                    'address': '192.168.2.1',
                    'version': 'v4'
                }),
                FakeStruct({
                    'address': '2001:db8:3333:4444:5555:6666:7777:8888',
                    'version': 'v6'
                })
            ]
        })]


class StatisticsService(Service):
    def list(self, *args, **kwargs):
        return [
            FakeStruct({
                'name': 'memory.installed',
                'values': [FakeStruct({
                    'datum': 1234567
                })]
            }),
            FakeStruct({
                'name': 'memory.used',
                'values': [FakeStruct({
                    'datum': 123
                })
                ]
            }),
            FakeStruct({
                'name': 'cpu.current.guest',
                'values': [FakeStruct({
                    'datum': 0.63
                })
                ]
            }),
            FakeStruct({
                'name': 'cpu.current.hypervisor',
                'values': [FakeStruct({
                    'datum': 0.30
                })
                ]
            }),
            FakeStruct({
                'name': 'cpu.current.total',
                'values': [FakeStruct({
                    'datum': 0.63
                })
                ]
            }),
            FakeStruct({
                'name': 'migration.progress',
                'values': [FakeStruct({
                    'datum': 0
                })
                ]
            }),
            FakeStruct({
                'name': 'memory.buffered',
                'values': [FakeStruct({
                    'datum': 0
                })
                ]
            }),
            FakeStruct({
                'name': 'memory.cached',
                'values': [FakeStruct({
                    'datum': 0
                })
                ]
            }),
            FakeStruct({
                'name': 'memory.free',
                'values': [FakeStruct({
                    'datum': 0
                })
                ]
            }),
        ]


class TagsService(Service):
    def list(self, *args, **kwargs):
        return [FakeStruct({
            'name': 'tag01'
        })]
