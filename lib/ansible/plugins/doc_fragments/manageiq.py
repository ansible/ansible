# (c) 2017, Daniel Korn <korndaniel1@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


class ModuleDocFragment(object):

    # Standard ManageIQ documentation fragment
    DOCUMENTATION = """
options:
  manageiq_connection:
    required: true
    description:
      - ManageIQ connection configuration information.
    suboptions:
      url:
        required: true
        description:
          - ManageIQ environment url. C(MIQ_URL) env var if set. otherwise, it is required to pass it.
      username:
        description:
          - ManageIQ username. C(MIQ_USERNAME) env var if set. otherwise, required if no token is passed in.
      password:
        description:
          - ManageIQ password. C(MIQ_PASSWORD) env var if set. otherwise, required if no token is passed in.
      token:
        description:
          - ManageIQ token. C(MIQ_TOKEN) env var if set. otherwise, required if no username or password is passed in.
      verify_ssl:
        description:
          - Whether SSL certificates should be verified for HTTPS requests. defaults to True.
        default: true
      ca_bundle_path:
        description:
          - The path to a CA bundle file or directory with certificates. defaults to None.

requirements:
  - 'manageiq-client U(https://github.com/ManageIQ/manageiq-api-client-python/)'
"""
