'''
Find and delete AWS resources matching the provided --match string.  Unless
--yes|-y is provided, the prompt for confirmation prior to deleting resources.
Please use caution, you can easily delete you're *ENTIRE* EC2 infrastructure.
'''

import os
import re
import sys
import boto
import optparse
import yaml

def delete_aws_resources(get_func, attr, opts):
    for item in get_func():
        val = getattr(item, attr)
        if re.search(opts.match_re, val):
            prompt_and_delete(item, "Delete matching %s? [y/n]: " % (item,), opts.assumeyes)

def prompt_and_delete(item, prompt, assumeyes):
    if not assumeyes:
        assumeyes = raw_input(prompt).lower() == 'y'
    assert hasattr(item, 'delete'), "Class <%s> has no delete attribute" % item.__class__
    if assumeyes:
        item.delete()
        print ("Deleted %s" % item)

def parse_args():
    # Load details from credentials.yml
    default_aws_access_key = os.environ.get('AWS_ACCESS_KEY', None)
    default_aws_secret_key = os.environ.get('AWS_SECRET_KEY', None)
    if os.path.isfile('credentials.yml'):
        credentials = yaml.load(open('credentials.yml', 'r'))

        if default_aws_access_key is None:
            default_aws_access_key = credentials['ec2_access_key']
        if default_aws_secret_key is None:
            default_aws_secret_key = credentials['ec2_secret_key']

    parser = optparse.OptionParser(usage="%s [options]" % (sys.argv[0],),
                description=__doc__)
    parser.add_option("--access",
        action="store", dest="ec2_access_key",
        default=default_aws_access_key,
        help="Amazon ec2 access id.  Can use EC2_ACCESS_KEY environment variable, or a values from credentials.yml.")
    parser.add_option("--secret",
        action="store", dest="ec2_secret_key",
        default=default_aws_secret_key,
        help="Amazon ec2 secret key.  Can use EC2_SECRET_KEY environment variable, or a values from credentials.yml.")
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
        help="Regular expression used to find AWS resources (default: %default)")

    (opts, args) = parser.parse_args()
    for required in ['ec2_access_key', 'ec2_secret_key']:
        if getattr(opts, required) is None:
            parser.error("Missing required parameter: --%s" % required)

    return (opts, args)

if __name__ == '__main__':

    (opts, args) = parse_args()

    # Connect to AWS
    aws = boto.connect_ec2(aws_access_key_id=opts.ec2_access_key,
            aws_secret_access_key=opts.ec2_secret_key)

    try:
        # Delete matching keys
        delete_aws_resources(aws.get_all_key_pairs, 'name', opts)

        # Delete matching groups
        delete_aws_resources(aws.get_all_security_groups, 'name', opts)
    except KeyboardInterrupt, e:
        print "\nExiting on user command."
