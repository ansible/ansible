'''
Find and delete GCE resources matching the provided --match string.  Unless
--yes|-y is provided, the prompt for confirmation prior to deleting resources.
Please use caution, you can easily delete your *ENTIRE* GCE infrastructure.
'''

import optparse
import os
import re
import sys
import yaml

try:
    from libcloud.common.google import (
        GoogleBaseError,
        QuotaExceededError,
        ResourceExistsError,
        ResourceInUseError,
        ResourceNotFoundError,
    )
    from libcloud.compute.providers import get_driver
    from libcloud.compute.types import Provider
    _ = Provider.GCE
except ImportError:
    print("failed=True msg='libcloud with GCE support (0.13.3+) required for this module'")
    sys.exit(1)

import gce_credentials

from ansible.module_utils.six.moves import input


def delete_gce_resources(get_func, attr, opts):
    for item in get_func():
        val = getattr(item, attr)
        if re.search(opts.match_re, val, re.IGNORECASE):
            prompt_and_delete(item, "Delete matching %s? [y/n]: " % (item,), opts.assumeyes)


def prompt_and_delete(item, prompt, assumeyes):
    if not assumeyes:
        assumeyes = input(prompt).lower() == 'y'
    assert hasattr(item, 'destroy'), "Class <%s> has no delete attribute" % item.__class__
    if assumeyes:
        item.destroy()
        print("Deleted %s" % item)


def parse_args():
    parser = optparse.OptionParser(
        usage="%s [options]" % sys.argv[0],
        description=__doc__
    )
    gce_credentials.add_credentials_options(parser)
    parser.add_option(
        "--yes", "-y",
        action="store_true", dest="assumeyes",
        default=False,
        help="Don't prompt for confirmation"
    )
    parser.add_option(
        "--match",
        action="store", dest="match_re",
        default="^ansible-testing-",
        help="Regular expression used to find GCE resources (default: %default)"
    )

    (opts, args) = parser.parse_args()
    gce_credentials.check_required(opts, parser)
    return (opts, args)

if __name__ == '__main__':

    (opts, args) = parse_args()

    # Connect to GCE
    gce = gce_credentials.get_gce_driver(opts)

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
    except KeyboardInterrupt as e:
        print("\nExiting on user command.")
