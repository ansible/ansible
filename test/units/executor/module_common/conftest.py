import pytest


@pytest.fixture
def templar():
    class FakeTemplar:
        def template(self, template_string, *args, **kwargs):
            return template_string

    return FakeTemplar()
