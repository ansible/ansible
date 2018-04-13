import collections
import os
import sys
import yaml

try:
    from libcloud.compute.types import Provider
    from libcloud.compute.providers import get_driver
    _ = Provider.GCE
except ImportError:
    print("failed=True msg='libcloud with GCE support (0.13.3+) required for this module'")
    sys.exit(1)


def add_credentials_options(parser):
    default_service_account_email = None
    default_pem_file = None
    default_project_id = None

    # Load details from credentials.yml
    if os.path.isfile('credentials.yml'):
        credentials = yaml.load(open('credentials.yml', 'r'))
        default_service_account_email = credentials[
            'gce_service_account_email']
        default_pem_file = credentials['gce_pem_file']
        default_project_id = credentials['gce_project_id']

    parser.add_option(
        "--service_account_email", action="store",
        dest="service_account_email", default=default_service_account_email,
        help="GCE service account email. Default is loaded from credentials.yml.")
    parser.add_option(
        "--pem_file", action="store", dest="pem_file",
        default=default_pem_file,
        help="GCE client key. Default is loaded from credentials.yml.")
    parser.add_option(
        "--project_id", action="store", dest="project_id",
        default=default_project_id,
        help="Google Cloud project ID. Default is loaded from credentials.yml.")


def check_required(opts, parser):
    for required in ['service_account_email', 'pem_file', 'project_id']:
        if getattr(opts, required) is None:
            parser.error("Missing required parameter: --%s" % required)


def get_gce_driver(opts):
    # Connect to GCE
    gce_cls = get_driver(Provider.GCE)
    return gce_cls(opts.service_account_email, opts.pem_file,
                   project=opts.project_id)
