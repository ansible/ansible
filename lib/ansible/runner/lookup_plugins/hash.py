# (c) 2015, Dominique Barton <dbarton@confirm.ch>
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

import os
import hashlib
from ansible import utils, errors


class LookupModule(object):

    '''
    This is an Ansible lookup module to lookup a hash digest from a file, in a
    memory efficient way (buffered). The digest will be returned as hex string.

    By default the lookup module uses the MD5 algorithm for hashing, though you
    can change that be specifying an "algorithm=..." parameter after the
    filename.

    Based on the official hashlib documentation, hash algorithms that
    are always present are md5(), sha1(), sha224(), sha256(), sha384(),
    and sha512(). Additional algorithms may also be available depending upon
    the OpenSSL library that Python uses on your platform.

    For more informations, browse to the official hashlib documentation:
    https://docs.python.org/2/library/hashlib.html
    '''

    def __init__(self, algorithm='md5', basedir=None, **kwargs):
        '''
        Save basedir and selected algorithm in instance vars.
        '''

        self.algorithm = algorithm
        self.basedir = basedir

    def run(self, terms, inject=None, **kwargs):
        '''
        Run method will automatically be invoked by the core, when the lookup
        plugin is executed.
        '''

        # Get the terms and initialize ret list.
        terms = utils.listify_lookup_plugin_terms(terms, self.basedir, inject)
        ret = []

        # If an user passes a string instead of a list, fix it here.
        if not isinstance(terms, list):
            terms = [terms]

        # Loop through each received file path.
        for term in terms:

            # Split parameters and get first argument (aka. file path).
            param_chunks = term.split()
            file_path = param_chunks[0]

            # Set default parameters.
            params = {
                'algorithm': self.algorithm
            }

            # Overwrite  user specific parameters.
            for param in param_chunks[1:]:
                key, value = param.split('=')
                params[key] = value

            # To be convenient to the "file" lookup plugin, we've to handle all
            # special file pathes. This becomes really important when using the
            # plugin in roles. Files should be looked up in the following
            # direction:
            #
            #   - basedir path
            #   - relative path (i.e. the roles' files/ directory)
            #   - playbook path (i.e. relative to the playbooks directory)
            #

            # The basedir path is quite simple and always defined.
            basedir_path = utils.path_dwim(self.basedir, file_path)

            # For the relative file path, we've to use path_dwim_relative().
            if '_original_file' not in inject:
                relative_path = None
            else:
                relative_path = utils.path_dwim_relative(
                    inject['_original_file'], 'files', file_path, self.basedir,
                    check=False
                )

            # The playbook dir is not always defined, so we've to check that
            # first, before we can set the playbook path.
            if 'playbook_dir' not in inject:
                playbook_path = None
            else:
                playbook_path = os.path.join(inject['playbook_dir'], file_path)

            # We've all pathes defined, locate the first matching file.
            for path in (basedir_path, relative_path, playbook_path):
                if path and os.path.exists(path):
                    afile = open(path, 'r')
                    break
            else:
                raise errors.AnsibleError(
                    'Could not locate file "{0}'.format(
                        file_path)
                )

            # Get a new hash object.
            try:
                hasher = getattr(hashlib, params['algorithm'])()
            except AttributeError:
                raise errors.AnsibleError(
                    'Invalid algorithm "{0}" defined'.format(
                        params['algorithm'])
                )

            # Read file in a memory efficient way and updated hash object.
            while True:
                buffer = afile.read(65536)
                if len(buffer) > 0:
                    hasher.update(buffer)
                else:
                    break

            # Append hex digest to ret list.
            ret.append(hasher.hexdigest())

            # Close file.
            afile.close()

        # Return hex digest.
        return ret
