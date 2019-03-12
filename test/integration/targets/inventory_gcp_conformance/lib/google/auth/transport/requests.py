from ansible.module_utils.six.moves import http_client


class FakeResponse(object):
    def __init__(self, fr_data):
        self.fr_data = fr_data
        self.status_code = 200

    def json(self):
        return self.fr_data['response_data']

    def raise_for_status(self):
        pass


class AuthorizedSession(object):
    def __init__(self, credentials,
                 refresh_status_codes=(http_client.UNAUTHORIZED,), max_refresh_attempts=2,
                 refresh_timeout=None, auth_request=None):
        pass

    def request(self, method, url, data=None, headers=None, **kwargs):
        pass

    def get(self, url, **kwargs):
        if url == "https://www.googleapis.com/compute/v1/projects/foo/zones/us-east1-d/instances":
            return FakeResponse(
                {
                    'status_code': 200,
                    'response_data': {
                        "kind": "compute#instanceList",
                        "items": [
                            {
                                "kind": "compute#instance",
                                "id": "2114317324400335940",
                                "creationTimestamp": "2017-11-02T15:56:44.318-07:00",
                                "name": "awx",
                                "description": "",
                                "tags": {
                                    "items": [
                                        "http-server"
                                    ]
                                },
                                "machineType": "https://www.googleapis.com/compute/v1/projects/foo/zones/us-east1-d/machineTypes/n1-standard-2",
                                "status": "RUNNING",
                                "zone": "https://www.googleapis.com/compute/v1/projects/foo/zones/us-east1-d",
                                "networkInterfaces": [
                                    {
                                        "kind": "compute#networkInterface",
                                        "network": "https://www.googleapis.com/compute/v1/projects/foo/global/networks/default",
                                        "subnetwork": "https://www.googleapis.com/compute/v1/projects/foo/regions/us-east1/subnetworks/default",
                                        "networkIP": "10.142.0.7",
                                        "name": "nic0",
                                        "accessConfigs": [
                                            {
                                                "kind": "compute#accessConfig",
                                                "type": "ONE_TO_ONE_NAT",
                                                "name": "External NAT",
                                                "natIP": "104.196.66.112",
                                                "networkTier": "PREMIUM"
                                            }
                                        ],
                                        "fingerprint": "bHC-nLDaT_c="
                                    }
                                ],
                                "disks": [
                                    {
                                        "kind": "compute#attachedDisk",
                                        "type": "PERSISTENT",
                                        "mode": "READ_WRITE",
                                        "source": "https://www.googleapis.com/compute/v1/projects/foo/zones/us-east1-d/disks/awx",
                                        "deviceName": "awx",
                                        "index": 0,
                                        "boot": True,
                                        "autoDelete": True,
                                        "licenses": [
                                            "https://www.googleapis.com/compute/v1/projects/centos-cloud/global/licenses/centos-7"
                                        ],
                                        "interface": "SCSI"
                                    }
                                ],
                                "metadata": {},
                                "serviceAccounts": [
                                    {
                                        "scopes": [
                                            "https://www.googleapis.com/auth/devstorage.read_only"
                                        ]
                                    }
                                ],
                                "selfLink": "https://www.googleapis.com/compute/v1/projects/foo/zones/us-east1-d/instances/awx",
                                "scheduling": {
                                    "onHostMaintenance": "MIGRATE",
                                    "automaticRestart": True,
                                    "preemptible": False
                                },
                                "cpuPlatform": "Intel Haswell",
                                "startRestricted": False,
                                "deletionProtection": True
                            },
                            {
                                "kind": "compute#instance",
                                "id": "206498018328856136",
                                "creationTimestamp": "2018-11-27T18:08:40.722-08:00",
                                "name": "gke-devel-default-pool-1b49cc65-lxj4",
                                "description": "",
                                "tags": {
                                    "items": [
                                        "gke-devel-674942a3-node"
                                    ]
                                },
                                "machineType": "https://www.googleapis.com/compute/v1/projects/foo/zones/us-east1-d/machineTypes/n1-standard-8",
                                "status": "RUNNING",
                                "zone": "https://www.googleapis.com/compute/v1/projects/foo/zones/us-east1-d",
                                "canIpForward": True,
                                "networkInterfaces": [
                                    {
                                        "kind": "compute#networkInterface",
                                        "network": "https://www.googleapis.com/compute/v1/projects/foo/global/networks/default",
                                        "subnetwork": "https://www.googleapis.com/compute/v1/projects/foo/regions/us-east1/subnetworks/default",
                                        "networkIP": "10.142.0.6",
                                        "name": "nic0",
                                        "accessConfigs": [
                                            {
                                                "kind": "compute#accessConfig",
                                                "type": "ONE_TO_ONE_NAT",
                                                "name": "external-nat",
                                                "natIP": "35.231.144.241",
                                                "networkTier": "PREMIUM"
                                            }
                                        ]
                                    }
                                ],
                                "disks": [
                                    {
                                        "kind": "compute#attachedDisk",
                                        "type": "PERSISTENT",
                                        "mode": "READ_WRITE",
                                        "source": "https://www.googleapis.com/compute/v1/projects/foo/zones/us-east1-d/disks/gke-devel-default-pool-1b49cc65-lxj4",
                                        "deviceName": "persistent-disk-0",
                                        "index": 0,
                                        "boot": True,
                                        "autoDelete": True,
                                        "licenses": [
                                            "https://www.googleapis.com/compute/v1/projects/cos-cloud/global/licenses/cos"
                                        ],
                                        "interface": "SCSI"
                                    },
                                    {
                                        "kind": "compute#attachedDisk",
                                        "type": "PERSISTENT",
                                        "mode": "READ_WRITE",
                                        "source": "https://www.googleapis.com/compute/v1/projects/foo/zones/us-east1-d/disks/gke-devel-674942a3-dyn-pvc-c643c774-f2b7-11e8-b34a-42010a8e0032",
                                        "deviceName": "gke-devel-674942a3-dyn-pvc-c643c774-f2b7-11e8-b34a-42010a8e0032",
                                        "index": 1,
                                        "boot": False,
                                        "autoDelete": False,
                                        "interface": "SCSI"
                                    }
                                ],
                                "metadata": {},
                                "serviceAccounts": [
                                    {
                                        "scopes": [
                                            "https://www.googleapis.com/auth/devstorage.read_only",
                                            "https://www.googleapis.com/auth/logging.write",
                                            "https://www.googleapis.com/auth/monitoring",
                                            "https://www.googleapis.com/auth/service.management.readonly",
                                            "https://www.googleapis.com/auth/servicecontrol",
                                            "https://www.googleapis.com/auth/trace.append",
                                            "https://www.googleapis.com/auth/compute"
                                        ]
                                    }
                                ],
                                "selfLink": "https://www.googleapis.com/compute/v1/projects/foo/zones/us-east1-d/instances/gke-devel-default-pool-1b49cc65-lxj4",
                                "scheduling": {
                                    "onHostMaintenance": "MIGRATE",
                                    "automaticRestart": True,
                                    "preemptible": False
                                },
                                "cpuPlatform": "Intel Haswell",
                                "labels": {
                                    "goog-gke-node": ""
                                },
                                "startRestricted": False,
                                "deletionProtection": False
                            },
                            {
                                "kind": "compute#instance",
                                "id": "6929072879715680739",
                                "creationTimestamp": "2019-03-20T15:30:37.859-07:00",
                                "name": "gke-tower-qe-default-pool-0aa0f212-745b",
                                "description": "",
                                "tags": {
                                    "items": [
                                        "gke-tower-qe-2647dc41-node"
                                    ]
                                },
                                "machineType": "https://www.googleapis.com/compute/v1/projects/foo/zones/us-east1-d/machineTypes/n1-standard-2",
                                "status": "RUNNING",
                                "zone": "https://www.googleapis.com/compute/v1/projects/foo/zones/us-east1-d",
                                "canIpForward": True,
                                "networkInterfaces": [
                                    {
                                        "kind": "compute#networkInterface",
                                        "network": "https://www.googleapis.com/compute/v1/projects/foo/global/networks/default",
                                        "subnetwork": "https://www.googleapis.com/compute/v1/projects/foo/regions/us-east1/subnetworks/default",
                                        "networkIP": "10.142.0.41",
                                        "name": "nic0",
                                        "accessConfigs": [
                                            {
                                                "kind": "compute#accessConfig",
                                                "type": "ONE_TO_ONE_NAT",
                                                "name": "external-nat",
                                                "natIP": "34.73.239.41",
                                                "networkTier": "PREMIUM"
                                            }
                                        ]
                                    }
                                ],
                                "disks": [
                                    {
                                        "kind": "compute#attachedDisk",
                                        "type": "PERSISTENT",
                                        "mode": "READ_WRITE",
                                        "source": "https://www.googleapis.com/compute/v1/projects/foo/zones/us-east1-d/disks/gke-tower-qe-default-pool-0aa0f212-745b",
                                        "deviceName": "persistent-disk-0",
                                        "index": 0,
                                        "boot": True,
                                        "autoDelete": True,
                                        "licenses": [
                                            "https://www.googleapis.com/compute/v1/projects/cos-cloud/global/licenses/cos",
                                            "https://www.googleapis.com/compute/v1/projects/cos-cloud/global/licenses/cos-pcid",
                                            "https://www.googleapis.com/compute/v1/projects/gke-node-images/global/licenses/gke-node"
                                        ],
                                        "interface": "SCSI"
                                    }
                                ],
                                "metadata": {},
                                "serviceAccounts": [
                                    {
                                        "scopes": [
                                            "https://www.googleapis.com/auth/devstorage.read_only",
                                            "https://www.googleapis.com/auth/logging.write",
                                            "https://www.googleapis.com/auth/monitoring",
                                            "https://www.googleapis.com/auth/servicecontrol",
                                            "https://www.googleapis.com/auth/service.management.readonly",
                                            "https://www.googleapis.com/auth/trace.append"
                                        ]
                                    }
                                ],
                                "selfLink": "https://www.googleapis.com/compute/v1/projects/foo/zones/us-east1-d/instances/gke-tower-qe-default-pool-0aa0f212-745b",
                                "scheduling": {
                                    "onHostMaintenance": "MIGRATE",
                                    "automaticRestart": True,
                                    "preemptible": False
                                },
                                "cpuPlatform": "Intel Haswell",
                                "labels": {
                                    "goog-gke-node": ""
                                },
                                "startRestricted": False,
                                "deletionProtection": False
                            },
                            {
                                "kind": "compute#instance",
                                "id": "3378743296778656512",
                                "creationTimestamp": "2017-05-11T15:30:07.584-07:00",
                                "name": "tower-mockups",
                                "description": "",
                                "tags": {
                                    "items": [
                                        "http-server",
                                        "https-server"
                                    ],
                                    "fingerprint": "6smc4R4d39I="
                                },
                                "machineType": "https://www.googleapis.com/compute/v1/projects/foo/zones/us-east1-d/machineTypes/g1-small",
                                "status": "RUNNING",
                                "zone": "https://www.googleapis.com/compute/v1/projects/foo/zones/us-east1-d",
                                "canIpForward": False,
                                "networkInterfaces": [
                                    {
                                        "kind": "compute#networkInterface",
                                        "network": "https://www.googleapis.com/compute/v1/projects/foo/global/networks/default",
                                        "subnetwork": "https://www.googleapis.com/compute/v1/projects/foo/regions/us-east1/subnetworks/default",
                                        "networkIP": "10.142.0.2",
                                        "name": "nic0",
                                        "accessConfigs": [
                                            {
                                                "kind": "compute#accessConfig",
                                                "type": "ONE_TO_ONE_NAT",
                                                "name": "External NAT",
                                                "natIP": "35.190.146.119",
                                                "networkTier": "PREMIUM"
                                            }
                                        ],
                                        "fingerprint": "yjGZFDMLynE="
                                    }
                                ],
                                "disks": [
                                    {
                                        "kind": "compute#attachedDisk",
                                        "type": "PERSISTENT",
                                        "mode": "READ_WRITE",
                                        "source": "https://www.googleapis.com/compute/v1/projects/foo/zones/us-east1-d/disks/tower-mockups",
                                        "deviceName": "tower-mockups",
                                        "index": 0,
                                        "boot": True,
                                        "autoDelete": True,
                                        "licenses": [
                                            "https://www.googleapis.com/compute/v1/projects/centos-cloud/global/licenses/centos-7"
                                        ],
                                        "interface": "SCSI"
                                    }
                                ],
                                "metadata": {},
                                "serviceAccounts": [
                                    {
                                        "scopes": [
                                            "https://www.googleapis.com/auth/devstorage.read_only",
                                            "https://www.googleapis.com/auth/logging.write",
                                            "https://www.googleapis.com/auth/monitoring.write",
                                            "https://www.googleapis.com/auth/servicecontrol",
                                            "https://www.googleapis.com/auth/service.management.readonly",
                                            "https://www.googleapis.com/auth/trace.append"
                                        ]
                                    }
                                ],
                                "selfLink": "https://www.googleapis.com/compute/v1/projects/foo/zones/us-east1-d/instances/tower-mockups",
                                "scheduling": {
                                    "onHostMaintenance": "MIGRATE",
                                    "automaticRestart": True,
                                    "preemptible": False
                                },
                                "cpuPlatform": "Intel Haswell",
                                "labelFingerprint": "42WmSpB8rSM=",
                                "startRestricted": False,
                                "deletionProtection": True
                            },
                            {
                                "kind": "compute#instance",
                                "id": "1278988980378204978",
                                "creationTimestamp": "2017-09-13T07:51:09.814-07:00",
                                "name": "towerapi-testing",
                                "description": "",
                                "tags": {
                                    "items": [
                                        "http-server",
                                        "https-server"
                                    ],
                                    "fingerprint": "6smc4R4d39I="
                                },
                                "machineType": "https://www.googleapis.com/compute/v1/projects/foo/zones/us-east1-d/machineTypes/n1-standard-2",
                                "status": "RUNNING",
                                "zone": "https://www.googleapis.com/compute/v1/projects/foo/zones/us-east1-d",
                                "networkInterfaces": [
                                    {
                                        "kind": "compute#networkInterface",
                                        "network": "https://www.googleapis.com/compute/v1/projects/foo/global/networks/default",
                                        "subnetwork": "https://www.googleapis.com/compute/v1/projects/foo/regions/us-east1/subnetworks/default",
                                        "networkIP": "10.142.0.12",
                                        "name": "nic0",
                                        "accessConfigs": [
                                            {
                                                "kind": "compute#accessConfig",
                                                "type": "ONE_TO_ONE_NAT",
                                                "name": "External NAT",
                                                "natIP": "35.196.9.30",
                                                "networkTier": "PREMIUM"
                                            }
                                        ],
                                        "fingerprint": "MxZOIpDgSDw="
                                    }
                                ],
                                "disks": [
                                    {
                                        "kind": "compute#attachedDisk",
                                        "type": "PERSISTENT",
                                        "mode": "READ_WRITE",
                                        "source": "https://www.googleapis.com/compute/v1/projects/foo/zones/us-east1-d/disks/towerapi-testing",
                                        "deviceName": "towerapi-testing",
                                        "index": 0,
                                        "boot": True,
                                        "autoDelete": True,
                                        "licenses": [
                                            "https://www.googleapis.com/compute/v1/projects/centos-cloud/global/licenses/centos-7"
                                        ],
                                        "interface": "SCSI"
                                    }
                                ],
                                "metadata": {},
                                "serviceAccounts": [
                                    {
                                        "scopes": [
                                            "https://www.googleapis.com/auth/devstorage.read_only"
                                        ]
                                    }
                                ],
                                "selfLink": "https://www.googleapis.com/compute/v1/projects/foo/zones/us-east1-d/instances/towerapi-testing",
                                "scheduling": {
                                    "onHostMaintenance": "MIGRATE",
                                    "automaticRestart": True,
                                    "preemptible": False
                                },
                                "cpuPlatform": "Intel Haswell",
                                "labelFingerprint": "42WmSpB8rSM=",
                                "startRestricted": False,
                                "deletionProtection": False
                            }
                        ],
                        "id": "projects/foo/zones/us-east1-d/instances",
                        "selfLink": "https://www.googleapis.com/compute/v1/projects/foo/zones/us-east1-d/instances"
                    }
                }
            )

        if url == "https://www.googleapis.com/compute/v1/projects/foo/aggregated/disks":
            return FakeResponse(
                {'status_code': 200,
                'response_data': {
                    "selfLink": "https://www.googleapis.com/compute/v1/projects/foo/aggregated/disks",
                    "items": {
                        "zones/us-east1-d": {
                            "disks": [
                                {
                                    "kind": "compute#disk",
                                    "id": "2567155990073318467",
                                    "name": "awx",
                                    "selfLink": "https://www.googleapis.com/compute/v1/projects/foo/zones/us-east1-d/disks/awx",
                                    "sourceImage": "https://www.googleapis.com/compute/v1/projects/centos-cloud/global/images/centos-7-v20171025",
                                    "sourceImageId": "5631027483984767623",
                                },
                                {
                                    "kind": "compute#disk",
                                    "id": "8859321029010636696",
                                    "name": "gke-devel-674942a3-dyn-pvc-c643c774-f2b7-11e8-b34a-42010a8e0032",
                                    "selfLink": "https://www.googleapis.com/compute/v1/projects/foo/zones/us-east1-d/disks/gke-devel-674942a3-dyn-pvc-c643c774-f2b7-11e8-b34a-42010a8e0032",
                                },
                                {
                                    "kind": "compute#disk",
                                    "id": "5001173527827513827",
                                    "name": "gke-tower-qe-default-pool-0aa0f212-745b",
                                    "selfLink": "https://www.googleapis.com/compute/v1/projects/foo/zones/us-east1-d/disks/gke-tower-qe-default-pool-0aa0f212-745b",
                                    "sourceImage": "https://www.googleapis.com/compute/v1/projects/gke-node-images/global/images/gke-1117-gke12-cos-69-10895-138-0-v190225-pre",
                                    "sourceImageId": "7072096510453341410",
                                },
                                {
                                    "kind": "compute#disk",
                                    "id": "1872548568728427264",
                                    "name": "tower-mockups",
                                    "selfLink": "https://www.googleapis.com/compute/v1/projects/foo/zones/us-east1-d/disks/tower-mockups",
                                    "sourceImage": "https://www.googleapis.com/compute/v1/projects/centos-cloud/global/images/centos-7-v20170426",
                                    "sourceImageId": "5992902547674756879",
                                },
                                {
                                    "kind": "compute#disk",
                                    "id": "6198992417309653810",
                                    "name": "towerapi-testing",
                                    "selfLink": "https://www.googleapis.com/compute/v1/projects/foo/zones/us-east1-d/disks/towerapi-testing",
                                    "sourceImage": "https://www.googleapis.com/compute/v1/projects/centos-cloud/global/images/centos-7-v20170829",
                                    "sourceImageId": "4960063913426897282",
                                },
                                {
                                    "kind": "compute#disk",
                                    "id": "3100958182266127944",
                                    "creationTimestamp": "2018-11-27T18:08:40.729-08:00",
                                    "name": "gke-devel-default-pool-1b49cc65-lxj4",
                                    "selfLink": "https://www.googleapis.com/compute/v1/projects/foo/zones/us-east1-d/disks/gke-devel-default-pool-1b49cc65-lxj4",
                                    "sourceImage": "https://www.googleapis.com/compute/v1/projects/gke-node-images/global/images/gke-197-gke11-cos-stable-65-10323-99-0-p2-v181110-pre",
                                    "sourceImageId": "6765926854811116985",
                                }
                            ]
                        },
                    }
                }
            }
        )
