# (c) 2014, Ryuzo Yamamoto <ryuzo.yamamoto(at)gmail.com>
#
# This file is part of Ansible
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

from ansible import utils, errors

HAVE_BOTO = False
try:
    import boto
    HAVE_BOTO = True
except ImportError:
    pass

import os

class LookupModule(object):

    def __init__(self, basedir=None, **kwargs):
        self.basedir = basedir;

        if HAVE_BOTO == False:
            raise errors.AnsibleError("Can't LOOKUP(s3): module boto is not installed")

    def run(self, terms, inject=None, **kwargs):
        terms = utils.listify_lookup_plugin_terms(terms, self.basedir, inject)

        ret = []
        for term in terms:

            params = term.split()
            paramvals = {
                'bucket': None,
                'object': None,
                'aws_access_key': None,
                'aws_secret_key': None,
            }
            try:
                for param in params:
                    name, value = param.split('=')
                    assert(name in paramvals)
                    paramvals[name] = value
            except (ValueError, AssertionError), e:
                raise errors.AnsibleError(e)

            try:
                s3 = boto.connect_s3(paramvals['aws_access_key'], paramvals['aws_secret_key'])
            except boto.exception.NoAuthHandlerFound, e:
                raise errors.AnsibleError(e)

            var = self.get_s3_content(s3, paramvals['bucket'], paramvals['object'])
            if var is not None:
                ret.append(var)

        return ret
            
    def get_s3_content(self, s3, bucket, obj):
        try:
            bucket = s3.lookup(bucket)
            key = bucket.lookup(obj)
            return key.get_contents_as_string()
        except s3.provider.storage_copy_error, e:
            raise errors.AnsibleError(e)
