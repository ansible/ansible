import pytest


@pytest.fixture
def access_token(monkeypatch):
    monkeypatch.setenv('LINODE_ACCESS_TOKEN', 'barfoo')


@pytest.fixture
def no_access_token_in_env(monkeypatch):
    try:
        monkeypatch.delenv('LINODE_ACCESS_TOKEN')
    except KeyError:
        pass


@pytest.fixture
def default_args():
    return {'state': 'present', 'label': 'foo'}


@pytest.fixture
def mock_linode():
    class Linode():
        def delete(self, *args, **kwargs):
            pass

        @property
        def _raw_json(self):
            return {
                "alerts": {
                    "cpu": 90,
                    "io": 10000,
                    "network_in": 10,
                    "network_out": 10,
                    "transfer_quota": 80
                },
                "backups": {
                    "enabled": False,
                    "schedule": {
                        "day": None,
                        "window": None,
                    }
                },
                "created": "2018-09-26T08:12:33",
                "group": "Foobar Group",
                "hypervisor": "kvm",
                "id": 10480444,
                "image": "linode/centos7",
                "ipv4": [
                    "130.132.285.233"
                ],
                "ipv6": "2a82:7e00::h03c:46ff:fe04:5cd2/64",
                "label": "lin-foo",
                "region": "eu-west",
                "specs": {
                    "disk": 25600,
                    "memory": 1024,
                    "transfer": 1000,
                    "vcpus": 1
                },
                "status": "running",
                "tags": [],
                "type": "g6-nanode-1",
                "updated": "2018-09-26T10:10:14",
                "watchdog_enabled": True
            }
    return Linode()
