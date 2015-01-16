#!/usr/bin/env python

import os
import re
import yaml
import argparse

try:
    import pyrax
    HAS_PYRAX = True
except ImportError:
    HAS_PYRAX = False


def rax_list_iterator(svc, *args, **kwargs):
    method = kwargs.pop('method', 'list')
    items = getattr(svc, method)(*args, **kwargs)
    while items:
        retrieved = getattr(svc, method)(*args, marker=items[-1].id, **kwargs)
        if items and retrieved and items[-1].id == retrieved[0].id:
            del items[-1]
        items.extend(retrieved)
        if len(retrieved) < 2:
            break
    return items


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
    print ("--- Cleaning CloudServers matching '%s'" % args.match_re)
    search_opts = dict(name='^%s' % args.match_re)
    for region in pyrax.identity.services.compute.regions:
        cs = pyrax.connect_to_cloudservers(region=region)
        servers = rax_list_iterator(cs.servers, search_opts=search_opts)
        for server in servers:
            prompt_and_delete(server,
                              'Delete matching %s? [y/n]: ' % server,
                              args.assumeyes)


def delete_rax_clb(args):
    """Function for deleting Cloud Load Balancers"""
    print ("--- Cleaning Cloud Load Balancers matching '%s'" % args.match_re)
    for region in pyrax.identity.services.load_balancer.regions:
        clb = pyrax.connect_to_cloud_loadbalancers(region=region)
        for lb in rax_list_iterator(clb):
            if re.search(args.match_re, lb.name):
                prompt_and_delete(lb,
                                  'Delete matching %s? [y/n]: ' % lb,
                                  args.assumeyes)


def main():
    if not HAS_PYRAX:
        raise SystemExit('The pyrax python module is required for this script')

    args = parse_args()
    authenticate()
    delete_rax(args)
    delete_rax_clb(args)


if __name__ == '__main__':
    main()
