#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2018, Matt Martz <matt@sivel.net>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = '''
author: Matt Martz (@sivel)
description:
  - Tests internet bandwidth using speedtest.net
short_description: Tests internet bandwidth using speedtest.net
module: speedtest
notes: []
options:
    download:
        default: true
        description:
          - Perform download test
        type: bool
    exclude:
        default: []
        description:
          - List of servers to exclude from testing
        required: false
    pre_allocate:
        default: true
        description:
          - Pre-allocate upload data. This option improves performance of
            upload testing, but comes at the cost of higher memory use
        type: bool
    secure:
        default: True
        description:
          - Use HTTPS instead of HTTP when communicating with
            speedtest.net operated servers
        type: bool
    servers:
        default: []
        description:
          - List of servers to limit for testing
        required: false
    share:
        default: false
        description:
          - Generate and provide a URL to the speedtest.net share
            results image
        type: bool
    source:
        description:
          - Source IP address to bind to
        required: false
    timeout:
        default: 10
        description:
          - HTTP timeout in seconds
    upload:
        default: true
        description:
          - Perform upload test
        type: bool
requirements:
  - speedtest-cli>=2.0.0
version_added: 2.8
'''

EXAMPLES = '''
- speedtest:
    share: yes
    servers:
      - 1234

- speedtest:
    share: yes
    source: "{{ ansible_eth1.ipv4.address }}"
'''

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

RETURN = '''
bytes_received:
    description: bytes recevied during download testing
    returned: always
    type: int
    sample: 315786858
bytes_sent:
    description: bytes sent during upload testing
    returned: always
    type: int
    sample: 105914368
client:
    description: information about local client
    returned: always
    type: dict
download:
    description: download speed in bytes per second
    returned: always
    type: float
    sample: 252432440.16133374
ping:
    description: latency to chosen server
    returned: always
    type: float
    sample: 5.491
server:
    description: information about the remote test server
    returned: always
    type: dict
share:
    description: URL to speedtest.net share image, will be null if share=False
    returned: always
    type: str
    sample: http://www.speedtest.net/result/1234.png
timestamp:
    description: ISO8601 timestamp recorded at the start of the test
    returned: always
    type: str
    sample: "2018-04-02T16:00:20.036880Z"
upload:
    description: upload speed in bytes per second
    returned: always
    type: float
    sample: 81690942.203669
'''

import traceback

try:
    import speedtest
    HAS_SPEEDTEST = True
except ImportError:
    HAS_SPEEDTEST = False

from ansible.module_utils.basic import AnsibleModule


def run_speedtest(module):
    s = speedtest.Speedtest(
        source_address=module.params['source'],
        secure=module.params['secure'],
        timeout=int(module.params['timeout']),
    )

    s.get_servers(
        module.params['servers'],
        module.params['exclude']
    )
    s.get_best_server()

    if module.params['download']:
        s.download()
    if module.params['upload']:
        s.upload(pre_allocate=module.params['pre_allocate'])
    if module.params['share']:
        s.results.share()

    module.exit_json(**s.results.dict())


def main():
    module = AnsibleModule(
        argument_spec=dict(
            servers=dict(required=False, type='list', elements='int', default=[]),
            exclude=dict(required=False, type='list', elements='int', default=[]),
            download=dict(type='bool', default=True),
            upload=dict(type='bool', default=True),
            share=dict(type='bool', default=False),
            source=dict(required=False, type='str'),
            secure=dict(type='bool', default=True),
            timeout=dict(type='int', default=10),
            pre_allocate=dict(type='bool', default=True),
        ),
    )

    if HAS_SPEEDTEST:
        version_tuple = tuple((int(n) for n in speedtest.__version__.split('.')))

    if not HAS_SPEEDTEST or not version_tuple or version_tuple < (2, 0, 0):
        module.fail_json(msg='speedtest-cli>=2.0.0 python module required for this '
                             'module')

    if not all((module.params['download'], module.params['upload'])):
        module.fail_json(msg='At least one of download or upload must be set to True')

    try:
        run_speedtest(module)
    except speedtest.NoMatchedServers:
        module.fail_json(msg='No matched servers: %s' % ', '.join('%s' % s for s in module.params['servers']))
    except (speedtest.ConfigRetrievalError,) + speedtest.HTTP_ERRORS:
        module.fail_json(msg='Cannot retrieve speedtest configuration', exception=traceback.format_exc())
    except (speedtest.ServersRetrievalError,) + speedtest.HTTP_ERRORS:
        module.fail_json(msg='Cannot retrieve speedtest server list', exception=traceback.format_exc())
    except speedtest.SpeedtestException as e:
        msg = '%s' % e
        if not msg:
            msg = '%r' % e
        module.fail_json(msg=msg)


if __name__ == '__main__':
    main()
