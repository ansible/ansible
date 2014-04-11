'''
Find and delete GCE resources matching the provided --match string.  Unless
--yes|-y is provided, the prompt for confirmation prior to deleting resources.
Please use caution, you can easily delete your *ENTIRE* GCE infrastructure.
'''

import os
import re
import sys
import optparse
import yaml

try:
    from libcloud.compute.types import Provider
    from libcloud.compute.providers import get_driver
    from libcloud.common.google import GoogleBaseError, QuotaExceededError, \
            ResourceExistsError, ResourceInUseError, ResourceNotFoundError
    _ = Provider.GCE
except ImportError:
    print("failed=True " + \
        "msg='libcloud with GCE support (0.13.3+) required for this module'")
    sys.exit(1)


def delete_gce_resources(get_func, attr, opts):
    for item in get_func():
        val = getattr(item, attr)
        if re.search(opts.match_re, val, re.IGNORECASE):
            prompt_and_delete(item, "Delete matching %s? [y/n]: " % (item,), opts.assumeyes)

def prompt_and_delete(item, prompt, assumeyes):
    if not assumeyes:
        assumeyes = raw_input(prompt).lower() == 'y'
    assert hasattr(item, 'destroy'), "Class <%s> has no delete attribute" % item.__class__
    if assumeyes:
        item.destroy()
        print ("Deleted %s" % item)

def parse_args():
    default_service_account_email = None
    default_pem_file = None
    default_project_id = None

    # Load details from credentials.yml
    if os.path.isfile('credentials.yml'):
        credentials = yaml.load(open('credentials.yml', 'r'))

        if default_service_account_email is None:
            default_service_account_email = credentials['gce_service_account_email']
        if default_pem_file is None:
            default_pem_file = credentials['gce_pem_file']
        if default_project_id is None:
            default_project_id = credentials['gce_project_id']

    parser = optparse.OptionParser(usage="%s [options]" % (sys.argv[0],),
                description=__doc__)
    parser.add_option("--service_account_email",
        action="store", dest="service_account_email",
        default=default_service_account_email,
        help="GCE service account email. Default is loaded from credentials.yml.")
    parser.add_option("--pem_file",
        action="store", dest="pem_file",
        default=default_pem_file,
        help="GCE client key. Default is loaded from credentials.yml.")
    parser.add_option("--project_id",
        action="store", dest="project_id",
        default=default_project_id,
        help="Google Cloud project ID. Default is loaded from credentials.yml.")
    parser.add_option("--credentials", "-c",
        action="store", dest="credential_file",
        default="credentials.yml",
        help="YAML file to read cloud credentials (default: %default)")
    parser.add_option("--yes", "-y",
        action="store_true", dest="assumeyes",
        default=False,
        help="Don't prompt for confirmation")
    parser.add_option("--match",
        action="store", dest="match_re",
        default="^ansible-testing-",
        help="Regular expression used to find GCE resources (default: %default)")

    (opts, args) = parser.parse_args()
    for required in ['service_account_email', 'pem_file', 'project_id']:
        if getattr(opts, required) is None:
            parser.error("Missing required parameter: --%s" % required)

    return (opts, args)

if __name__ == '__main__':

    (opts, args) = parse_args()

    # Connect to GCE
    gce_cls = get_driver(Provider.GCE)
    gce = gce_cls(
        opts.service_account_email, opts.pem_file, project=opts.project_id)

    try:
      # Delete matching instances
      delete_gce_resources(gce.list_nodes, 'name', opts)
      # Delete matching snapshots
      def get_snapshots():
        for volume in gce.list_volumes():
          for snapshot in gce.list_volume_snapshots(volume):
            yield snapshot
      delete_gce_resources(get_snapshots, 'name', opts)
      # Delete matching disks
      delete_gce_resources(gce.list_volumes, 'name', opts)
    except KeyboardInterrupt, e:
        print "\nExiting on user command."
