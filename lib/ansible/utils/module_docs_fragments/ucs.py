# -*- coding: utf-8 -*-

    # Cisco UCS doc fragment
    DOCUMENTATION = '''
options:
  hostname:
    description:
    - IP address or hostname of Cisco UCS Manager.
    type: str
    required: yes
  username:
    description:
    - Username for Cisco UCS Manager authentication.
    type: str
    default: admin
  password:
    description:
    - Password for Cisco UCS Manager authentication.
    type: str
    required: yes
  port:
    description:
    - Port number to be used during connection (by default uses 443 for https and 80 for http connection).
    type: int
  use_ssl:
    description:
    - If C(no), an HTTP connection will be used instead of the default HTTPS connection.
    type: bool
    default: yes
  use_proxy:
    description:
    - If C(no), will not use the proxy as defined by system environment variable.
    type: bool
    default: yes
  proxy:
    description:
    - If use_proxy is no, specfies proxy to be used for connection.
      e.g. 'http://proxy.xy.z:8080'
    type: str
'''
