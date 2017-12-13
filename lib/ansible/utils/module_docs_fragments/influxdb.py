# Copyright: (c) 2017, Ansible Project
# Copyright: (c) 2017, Abhijeet Kasurde (akasurde@redhat.com)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


class ModuleDocFragment(object):
    # Parameters for influxdb modules
    DOCUMENTATION = '''
options:
  hostname:
    description:
    - The hostname or IP address on which InfluxDB server is listening
    required: true
  username:
    description:
    - Username that will be used to authenticate against InfluxDB server
    default: root
  password:
    description:
    - Password that will be used to authenticate against InfluxDB server
    default: root
  port:
    description:
    - The port on which InfluxDB server is listening
    default: 8086
  database_name:
    description:
    - Name of the database.
    required: true
  validate_certs:
    description:
    - If set to C(no), the SSL certificates will not be validated.
    - This should only set to C(no) used on personally controlled sites using self-signed certificates.
    default: true
    version_added: "2.5"
  ssl:
    description:
    - Use https instead of http to connect to InfluxDB server.
    default: False
    version_added: "2.5"
  timeout:
    description:
    - Number of seconds Requests will wait for client to establish a connection.
    default: None
    version_added: "2.5"
  retries:
    description:
    - Number of retries client will try before aborting.
    - C(0) indicates try until success.
    default: 3
    version_added: "2.5"
  use_udp:
    description:
    - Use UDP to connect to InfluxDB server.
    default: False
    version_added: "2.5"
  udp_port:
    description:
    - UDP port to connect to InfluxDB server.
    default: 4444
    version_added: "2.5"
  proxies:
    description:
    - HTTP(S) proxy to use for Requests to connect to InfluxDB server.
    default: None
    version_added: "2.5"
'''
