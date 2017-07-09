'''
Create GCE resources for use in integration tests.

Takes a prefix as a command-line argument and creates two persistent disks named
${prefix}-base and ${prefix}-extra and a snapshot of the base disk named
${prefix}-snapshot. prefix will be forced to lowercase, to ensure the names are
legal GCE resource names.
'''

import gce_credentials
import optparse
import sys


def parse_args():
    parser = optparse.OptionParser(
        usage="%s [options] <prefix>" % (sys.argv[0],), description=__doc__
    )
    gce_credentials.add_credentials_options(parser)
    parser.add_option(
        "--prefix",
        action="store",
        dest="prefix",
        help="String used to prefix GCE resource names (default: %default)"
    )

    (opts, args) = parser.parse_args()
    gce_credentials.check_required(opts, parser)
    if not args:
        parser.error("Missing required argument: name prefix")
    return (opts, args)


if __name__ == '__main__':

    (opts, args) = parse_args()
    gce = gce_credentials.get_gce_driver(opts)
    prefix = args[0].lower()
    try:
        base_volume = gce.create_volume(
            size=10, name=prefix + '-base', location='us-central1-a')
        gce.create_volume_snapshot(base_volume, name=prefix + '-snapshot')
        gce.create_volume(size=10, name=prefix + '-extra', location='us-central1-a')
    except KeyboardInterrupt as e:
        print("\nExiting on user command.")
