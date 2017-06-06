# (c) 2015, Stephen Granger <stephen(at)trinimbus.com>
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible.errors import AnsibleError
from ansible.plugins.lookup import LookupBase
import os
import sys
import time
import pickle

try:
    import boto.ec2
    import boto.cloudformation
except ImportError:
    raise errors.AnsibleError(
        "Can't LOOKUP(cf_resource): module boto is not installed")

from distutils.version import LooseVersion
from ansible import __version__ as __ansible_version__

# region/stack/param
class LookupModule(LookupBase):
    def __init__(self, basedir=None, **kwargs):
        self.basedir = basedir
        self.cache_dir = os.path.join(os.getenv('HOME',''),'.stack_resources')
        self.cache_time = 60.0

    def check_cache(self, file):
        now = time.time()
        data = []
        if os.path.isfile(file):
            # check time stamp of file
            if ( now - os.path.getmtime(file) ) < self.cache_time:
                fh = open(file, 'r')
                data = pickle.load(fh)

        return data

    def get_regions(self):
        regions_cache = os.path.join(self.cache_dir, 'regions')
        regions = self.check_cache(regions_cache)
        if not regions:
            try:
                regions = boto.ec2.regions()
                regions = [ r.name for r in regions ]
                fh = open(regions_cache, 'w')
                pickle.dump(regions, fh)
            except:
                raise AnsibleError('Couldn\'t retrieve aws regions')

        return regions

    def get_stack_info(self, region, stack_name):
        stack_cache = os.path.join(self.cache_dir, region + '-' + stack_name)
        resources = self.check_cache(stack_cache)
        if not resources:
            try:
                conn = boto.cloudformation.connect_to_region(region)
                stack = conn.list_stack_resources(stack_name_or_id=stack_name)
                next_token = stack.next_token
                while next_token:
                    next_stack = conn.list_stack_resources(stack_name_or_id=stack_name, next_token=next_token)
                    next_token = next_stack.next_token
                    stack = stack + next_stack
                fh = open(stack_cache, 'w')
                resources = stack
                pickle.dump(resources, fh)
            except:
                resources = []

        return resources

    def run(self, terms, inject=None, **kwargs):
        if not os.path.isdir(self.cache_dir):
            os.makedirs(self.cache_dir)

        regions = self.get_regions()

        if len(terms) == 1:
            args = terms[0].split('/')
        else:
            args = terms

        if args[0] in regions:
            region = args[0]
            stack_name = args[1]
            keys = args[2:]
        else:
            region = os.getenv('AWS_REGION')
            if region:
                if not region in regions:
                    raise AnsibleError('%s is not a valid aws region' % region)
                stack_name = args[0]
                keys = args[1:]
            else:
                raise AnsibleError('aws region not found in argument or AWS_REGION env var')

        resources = self.get_stack_info(region, stack_name)
        return_val = []

        if resources:
            resources = sorted(resources, key=lambda x: x.logical_resource_id)
            for obj in resources:
                if obj.logical_resource_id in keys:
                    return_val.append(obj.physical_resource_id)

        if not return_val:
            raise AnsibleError('Nothing was retured by lookup')

        return return_val
