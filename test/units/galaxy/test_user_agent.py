import sys

from ansible import release
from ansible.galaxy import user_agent


def test_user_agent():
    res = user_agent.user_agent()
    assert res.startswith('ansible-galaxy/%s' % release.__version__)
    assert sys.platform in res
    assert 'python:' in res
    assert 'ansible-galaxy' in res
