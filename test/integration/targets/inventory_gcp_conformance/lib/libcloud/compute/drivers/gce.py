from collections import namedtuple

Node = namedtuple('Node', 'id, uuid, name, state, public_ips, private_ips, driver, image, size, extra')
Zone = namedtuple('Zone', 'name')


class Connection(object):
    def __init__(self):
        self.gce_params = None
        self.user_agent = []

    def user_agent_append(self, ua):
        self.user_agent.append(ua)


class GCENodeDriver(object):
    def __init__(self, user_id, key=None, datacenter=None, project=None,
                 auth_type=None, scopes=None, credential_file=None, **kwargs):
        self.connection = Connection()

    def list_nodes(self):
        zone = 'us-east1-d'
        return [
            Node(
                '2114317324400335940',                              # id
                '13b1d76d263d745c05b2c6e5234b4f51074f1222',         # uuid
                'awx',                                              # name
                'RUNNING',                                          # state
                ['104.196.66.112'],                                 # public_ips
                ['10.142.0.7'],                                     # private_ips
                'Google Compute Engine',                            # driver
                'centos-7-v20171025',                               # image
                'n1-standard-2',                                    # size
                {                                                   # extra (only the fields gce.py cares about)
                    'status': 'RUNNING',
                    'tags': ['http-server'],
                    'zone': Zone(zone),
                    'metadata': {},
                    'description': None,
                    'networkInterfaces': [
                        {
                            'network': 'https://www.googleapis.com/compute/v1/projects/foo/global/networks/default',
                            'subnetwork': 'https://www.googleapis.com/compute/v1/projects/foo/regions/us-east1/subnetworks/default',
                            'networkIP': '10.142.0.7',
                            'name': 'nic0',
                        }
                    ]
                }
            ),
            Node(
                '206498018328856136',
                '65c0b74157bcfb1540ee2e2fee9ffd2ff9288585',
                'gke-devel-default-pool-1b49cc65-lxj4',
                'RUNNING',
                ['35.231.144.241'],
                ['10.142.0.6'],
                'Google Compute Engine',
                'gke-197-gke11-cos-stable-65-10323-99-0-p2-v181110-pre',
                'n1-standard-8',
                {
                    'status': 'RUNNING',
                    'tags': ['gke-devel-674942a3-node'],
                    'zone': Zone(zone),
                    'metadata': {},
                    'description': None,
                    'networkInterfaces': [
                        {
                            'network': 'https://www.googleapis.com/compute/v1/projects/foo/global/networks/default',
                            'subnetwork': 'https://www.googleapis.com/compute/v1/projects/foo/regions/us-east1/subnetworks/default',
                            'networkIP': '10.142.0.6',
                            'name': 'nic0',
                        }
                    ],
                }
            ),
            Node(
                '6929072879715680739',
                '2eecb7ffbd44f3785f86c43593d8a26fffed3ebb',
                'gke-tower-qe-default-pool-0aa0f212-745b',
                'RUNNING',
                ['34.73.239.41'],
                ['10.142.0.41'],
                'Google Compute Engine',
                'gke-1117-gke12-cos-69-10895-138-0-v190225-pre',
                'n1-standard-2',
                {
                    'status': 'RUNNING',
                    'tags': ['gke-tower-qe-2647dc41-node'],
                    'zone': Zone(zone),
                    'metadata': {},
                    'description': None,
                    'networkInterfaces': [
                        {
                            'network': 'https://www.googleapis.com/compute/v1/projects/foo/global/networks/default',
                            'subnetwork': 'https://www.googleapis.com/compute/v1/projects/foo/regions/us-east1/subnetworks/default',
                            'networkIP': '10.142.0.41',
                            'name': 'nic0',
                        }
                    ],
                }
            ),
            Node(
                '3378743296778656512',
                'a72fbe9d2a868f40b20f03e0a2be7fc9d292b083',
                'tower-mockups',
                'RUNNING',
                ['35.190.146.119'],
                ['10.142.0.2'],
                'Google Compute Engine',
                'centos-7-v20170426',
                'g1-small',
                {
                    'status': 'RUNNING',
                    'tags': ['http-server', 'https-server'],
                    'zone': Zone(zone),
                    'metadata': {},
                    'description': None,
                    'networkInterfaces': [
                        {
                            'network': 'https://www.googleapis.com/compute/v1/projects/foo/global/networks/default',
                            'subnetwork': 'https://www.googleapis.com/compute/v1/projects/foo/regions/us-east1/subnetworks/default',
                            'networkIP': '10.142.0.2',
                            'name': 'nic0',
                        }
                    ],
                }
            ),
            Node(
                '1278988980378204978',
                '21b24f2d2708ff8b9c03fc1f1406f4f70e682928',
                'towerapi-testing',
                'RUNNING',
                ['35.196.9.30'],
                ['10.142.0.12'],
                'Google Compute Engine',
                'centos-7-v20170829',
                'n1-standard-2',
                {
                    'status': 'RUNNING',
                    'tags': ['http-server', 'https-server'],
                    'zone': Zone(zone),
                    'metadata': {},
                    'description': None,
                    'networkInterfaces': [
                        {
                            'network': 'https://www.googleapis.com/compute/v1/projects/foo/global/networks/default',
                            'subnetwork': 'https://www.googleapis.com/compute/v1/projects/foo/regions/us-east1/subnetworks/default',
                            'networkIP': '10.142.0.12',
                            'name': 'nic0',
                        }
                    ],
                }
            )
        ]
