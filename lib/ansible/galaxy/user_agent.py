
import sys

from ansible.release import __version__ as ansible_version

# Based on suggestions at https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/User-Agent
USER_AGENT_FORMAT = 'ansible-galaxy/{version} ({platform}; python:{py_major}.{py_minor}.{py_micro})'


def user_agent():
    '''Return a user-agent including mazer version, platform, and python version'''

    user_agent_data = {'version': ansible_version,
                       'platform': sys.platform,
                       'py_major': sys.version_info.major,
                       'py_minor': sys.version_info.minor,
                       'py_micro': sys.version_info.micro}
    return USER_AGENT_FORMAT.format(**user_agent_data)
