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
import boto.ec2
import boto.cloudformation
import os
import sys
import time
import pickle

# region/stack/param
class LookupModule(LookupBase):
    def __init__(self, basedir=None, **kwargs):
        self.basedir = basedir
        self.cache_dir = os.path.join(os.getenv('HOME',''),'.stack_outputs')
        self.cache_time = 60.0

    def check_cache(self, file):
        now = time.time()
        data = []
        if os.path.isfile(file):
            # check time stamp of file
            if ( now - os.path.getmtime(file) ) < self.cache_time:
                fh = open(file, 'r')
                data = pickle.load(fh)

        # returns a list of strings
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
        outputs = self.check_cache(stack_cache)
        if not outputs:
          try:
            conn = boto.cloudformation.connect_to_region(region)
            stack = conn.describe_stacks(stack_name_or_id=stack_name)[0]
            fh = open(stack_cache, 'w')
            outputs = stack.outputs
            pickle.dump(outputs, fh)
          except:
            outputs = []

        return outputs

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

        stack_outputs = self.get_stack_info(region, stack_name)
        outputs = []

        if stack_outputs:
            for obj in stack_outputs:
                if obj.key in keys:
                    outputs.append(obj.value)

        if len(outputs) == 0:
            raise AnsibleError('Nothing was retured by lookup')

        return outputs
