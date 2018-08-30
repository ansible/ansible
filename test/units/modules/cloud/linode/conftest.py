import pytest


@pytest.fixture
def api_key(monkeypatch):
    monkeypatch.setenv('LINODE_API_KEY', 'foobar')


@pytest.fixture
def auth(monkeypatch):
    def patched_test_echo(dummy):
        return []
    monkeypatch.setattr('linode.api.Api.test_echo', patched_test_echo)
