#!/usr/bin/env python

import os
import yaml
import argparse

try:
    import pyrax
    HAS_PYRAX = True
except ImportError:
    HAS_PYRAX = False


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-y', '--yes', action='store_true', dest='assumeyes',
                        default=False, help="Don't prompt for confirmation")
    parser.add_argument('--match', dest='match_re',
                        default='^ansible-testing',
                        help='Regular expression used to find resources '
                             '(default: %(default)s)')

    return parser.parse_args()


def authenticate():
    try:
        with open(os.path.realpath('./credentials.yml')) as f:
            credentials = yaml.load(f)
    except Exception as e:
        raise SystemExit(e)

    try:
        pyrax.set_credentials(credentials.get('rackspace_username'),
                              credentials.get('rackspace_api_key'))
    except Exception as e:
        raise SystemExit(e)


def prompt_and_delete(item, prompt, assumeyes):
    if not assumeyes:
        assumeyes = raw_input(prompt).lower() == 'y'
    assert (hasattr(item, 'delete') or hasattr(item, 'terminate'),
            "Class <%s> has no delete or terminate attribute" % item.__class__)
    if assumeyes:
        if hasattr(item, 'delete'):
            item.delete()
            print ("Deleted %s" % item)
        if hasattr(item, 'terminate'):
            item.terminate()
            print ("Terminated %s" % item)


def delete_rax(args):
    """Function for deleting CloudServers"""
    for region in pyrax.identity.services.compute.regions:
        cs = pyrax.connect_to_cloudservers(region=region)
        servers = cs.servers.list(search_opts=dict(name='^%s' % args.match_re))
        for server in servers:
            prompt_and_delete(server,
                              'Delete matching %s? [y/n]: ' % server,
                              args.assumeyes)


def main():
    if not HAS_PYRAX:
        raise SystemExit('The pyrax python module is required for this script')

    args = parse_args()
    authenticate()
    delete_rax(args)


if __name__ == '__main__':
    main()
