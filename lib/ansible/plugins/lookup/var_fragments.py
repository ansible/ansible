from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


DOCUMENTATION = """
    lookup: vars
    author: Jiri Tyr
    version_added: "2.10"
    short_description: Compose single variable out of variable fragment files.
    description:
      - Read fragments of variable files and try to compose a single variable
        out of them.
    options:
      dir:
        description:
          - Directory to lookup for file fragments.
          - Relative path, is relative to the directory from which Ansible was
            executed.
        default: .
        type: path
      files:
        description:
          - File to read.
          - The file location is relative to the C(dir) path.
          - Each file can also be absolute path.
        type: list
      extensions:
        description:
          - File extensions to read.
        default:
          - .yaml
          - .yml
        type: list
"""

EXAMPLES = """
- name: Read all *.yaml and *.yml files from the specified directory
  hosts: all
  vars:
    my_var: "{{ lookup('vars_fragments', dir='/path/to/my/dir') }}"
  tasks:
    - debug:
        var: my_var

- name: Read only files with specified extensions
  hosts: all
  vars:
    my_var: "{{
      lookup(
        'vars_fragments',
        dir='/path/to/my/dir'
        extensions=['.vm.yaml', '.vm.yml']) }}"
  tasks:
    - debug:
        var: my_var

- name: Read only specified files from the directory
  hosts: all
  vars:
    my_var: "{{
      lookup(
        'vars_fragments',
        dir='/path/to/my/dir'
        files=['file1.yaml', 'file2.yaml']) }}"
  tasks:
    - debug:
        var: my_var

- name: Read only specified files
  hosts: all
  vars:
    my_var: "{{
      lookup(
        'vars_fragments',
        files=[
          '/path/to/my/dir1/file1.yaml',
          '/path/to/my/dir2/file2.yaml']) }}"
  tasks:
    - debug:
        var: my_var
"""

RETURN = """
_value:
  description:
    - Combined value from all variable fragments.
"""


from ansible.errors import AnsibleError
from ansible.errors import AnsibleParserError
from ansible.errors import AnsibleUndefinedVariable
from ansible.plugins.lookup import LookupBase

import glob
import os
import yaml


class LookupModule(LookupBase):
    def _read_yaml_file(self, path):
        content = ''

        try:
            f = open(path, 'r')
        except IOError as e:
            raise AnsibleError("Cannot open file '%s'.\n%s" % (path, e))

        for line in f.readlines():
            # Ignore the YAML document header
            if not line.startswith('---'):
                content += line

        try:
            f.close()
        except IOError as e:
            raise AnsibleError("Cannot close file '%s'.\n%s" % (path, e))

        return content

    def run(self, terms=None, variables=None, **kwargs):
        if variables is not None:
            self._templar.available_variables = variables

        # Load options
        self.set_options(direct=kwargs)

        dir = self.get_option('dir')
        files = self.get_option('files')
        ext = self.get_option('extensions')

        fpaths = ()

        # Compose a list of unique file paths
        if files is not None:
            for f in files:
                if os.path.isabs(f):
                    fpaths += (f,)
                else:
                    fpaths += (os.path.normpath("%s/%s" % (dir, f)),)
        else:
            for x in ext:
                fpaths += tuple(glob.glob("%s/*%s" % (dir, x)))

        yaml_data = ''

        # Read content of all existing files
        for fp in fpaths:
            if os.path.exists(fp):
                yaml_data += self._read_yaml_file(fp)

                # Make sure each fragment is terminated with a new line
                if yaml_data[-1] != "\n":
                    yaml_data += "\n"

        # Parse the YAML data
        try:
            data = yaml.safe_load(yaml_data)
        except yaml.YAMLError as e:
            raise AnsibleParserError("Unable parse YAML data: %s" % e)

        # Template the file
        try:
            templated = self._templar.template(data, fail_on_undefined=True)
        except AnsibleUndefinedVariable as e:
            raise AnsibleError("Cannot template data: %s" % e)

        # Normalize the return value
        if isinstance(templated, list):
            ret = templated
        else:
            ret = [templated]

        return ret
