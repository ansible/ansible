# (c) 2017, Ansible by Red Hat, inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os
import copy
import collections

import yaml

from ansible.plugins.lookup import LookupBase
from ansible.module_utils.network_common import to_list, dict_merge
from ansible.module_utils.six import iteritems, string_types
from ansible.module_utils._text import to_bytes, to_text
from ansible.errors import AnsibleError, AnsibleUndefinedVariable

try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()


DOCUMENTATION = """
  lookup: ansible_template
  version_added: "2.5"
  short_description: "Template facts using Ansible directives language"
  description:
    - The ansible-template lookup provides a structure approach to templating
      out host facts to another format.  It is useful when wanting to transform
      fact key/value pairs into another structured test format.
  options:
    _terms:
      description: Relative or absolute path to the template file.
      required: True
    root_fact:
      description: Roots the template values at the root fact if specified to simplify template writing
      type: string
"""


EXAMPLES = """
- name: template global facts
  set_fact:
    configuration: "{{ lookup('ansible_template', 'my_template.yaml') }}"

- name: template global facts using multiple templates
  set_fact:
    configuration: "{{ lookup('ansible_template', 'my_template_1.yaml', 'my_template_2.yaml') }}"

- name: templates can also be passed a list
  set_fact:
    configuration: "{{ lookup('ansible_template', ['my_template_1.yaml', 'my_template_2.yaml']) }}"


- name: template global facts with relative path
  set_fact:
    configuration: "{{ lookup('ansible_template', 'path/to/my_template.yaml') }}"

- name: template subset of host facts
  set_fact:
    configuration: "{{ lookup('ansible_template', 'my_template.yaml', root_fact='interfaces') }}"
"""


RETURN = """
  _raw:
    description:
      - The output of the template
"""


MISSING_KEY_OPTIONS = frozenset(('warn', 'fail', 'ignore'))


VALID_OPTIONS = frozenset((
    'template',
    'block',
    'when',
    'required',
    'indent',
    'missing_key',
    'loop',
    'name',
    'join'
))


class LookupModule(LookupBase):

    def run(self, terms, variables, **kwargs):

        root_fact = kwargs.get('root_fact')

        ret = []

        for items in terms:
            for term in to_list(items):
                display.debug("File lookup term: %s" % term)

                lookupfile = self.find_file_in_search_path(variables, 'templates', term)
                display.vvvvv("File lookup using %s as file" % lookupfile)

                if lookupfile:
                    with open(to_bytes(lookupfile, errors='surrogate_or_strict'), 'rb') as f:
                        template_data = to_text(f.read(), errors='surrogate_or_strict')
                        spec = yaml.safe_load(template_data)

                        if root_fact:
                            template_vars = self.template("{{ %s }}" % root_fact, variables)
                            if not template_vars:
                                raise AnsibleError('specified value for root_fact not found')

                        else:
                            template_vars = variables.copy()

                        ret.extend(self.build(spec, template_vars))

        return [ret]

    def validate_spec_entry(self, spec):
        if set(spec.keys()).difference(VALID_OPTIONS):
            raise AnsibleError('invalid options specified in template')

    def build(self, spec, template_vars):
        config_lines = list()

        for item in spec:
            self.validate_spec_entry(item)

            name = item.get('name')
            block = item.get('block')
            when = item.get('when')

            if block:
                when = item.get('when')

                loop = item.get('loop')
                loop_data = None

                loop_control = item.get('loop_control') or {'loop_var': 'item'}

                if loop:
                    loop_data = self.template("{{ %s }}" % loop, template_vars, fail_on_undefined=False)
                    if not loop_data:
                        display.warning("block '%s' skipped due to missing loop var '%s'" % (name, loop))
                        continue

                values = list()

                if isinstance(loop_data, collections.Mapping):
                    for item_key, item_value in iteritems(loop_data):
                        item_data = template_vars.copy()
                        key = loop_control['loop_var']
                        item_data[key] = {'key': item_key, 'value': item_value}

                        if when:
                            conditional = "{%% if %s %%}True{%% else %%}False{%% endif %%}"
                            if not self.template(conditional % when, item_data, fail_on_undefined=False):
                                display.vvvvv("block '%s' skipped due to conditional check failure" % name)
                                continue

                        for entry in block:
                            if 'template' not in entry:
                                raise AnsibleError("missing required block entry `template`")
                            templated_values = self._process_block(entry, item_data)

                            if templated_values:
                                values.extend(templated_values)

                elif isinstance(loop_data, collections.Iterable):
                    for item_value in loop_data:
                        item_data = template_vars.copy()
                        key = loop_control['loop_var']
                        item_data[key] = item_value

                        if when:
                            conditional = "{%% if %s %%}True{%% else %%}False{%% endif %%}"
                            if not self.template(conditional % when, item_data, fail_on_undefined=False):
                                display.vvvvv("block '%s' skipped due to conditional check failure" % name)
                                continue

                        for entry in block:
                            if 'template' not in entry:
                                raise AnsibleError("missing required block entry `template`")
                            templated_values = self._process_block(entry, item_data)

                            if templated_values:
                                values.extend(templated_values)

                else:
                    for entry in block:
                        if when:
                            conditional = "{%% if %s %%}True{%% else %%}False{%% endif %%}"
                            if not self.template(conditional % when, template_vars, fail_on_undefined=False):
                                display.vvvvv("block '%s' skipped due to conditional check failure" % name)
                                continue

                        if 'template' not in entry:
                            raise AnsibleError("missing required block entry `template`")

                        templated_values = self._process_block(entry, template_vars)

                        if templated_values:
                            values.extend(templated_values)

                if values:
                    config_lines.extend(values)

            else:
                values = self._process_block(item, template_vars)
                if values:
                    config_lines.extend(values)

        return config_lines

    def _template_items(self, block, data):
        name = block.get('name')
        items = to_list(block['template'])

        required = block.get('required')

        join = block.get('join')
        join_delimiter = block.get('join_delimiter') or ' '

        indent = block.get('indent')

        missing_key = block.get('missing_key') or 'warn'
        if missing_key not in MISSING_KEY_OPTIONS:
            raise AnsibleError('option missing_key expected one of %s, got %s' % (', '.join(MISSING_KEY_OPTIONS), missing_key))

        fail_on_undefined = missing_key == 'fail'
        warn_on_missing_key = missing_key == 'warn'

        values = list()

        for item in items:
            templated_value = self.template(item, data, fail_on_undefined=fail_on_undefined)

            if templated_value:
                if '__omit_place_holder__' in templated_value:
                    continue
                if isinstance(templated_value, string_types):
                    values.append(templated_value)
                elif isinstance(templated_value, collections.Iterable):
                    values.extend(templated_value)
            else:
                if required:
                    raise AnsibleError("block '%s' is missing required key" % name)
                elif warn_on_missing_key:
                    display.warning("line '%s' skipped due to missing key" % item)

            if join and values:
                values = [join_delimiter.join(values)]

            if indent:
                values = [(indent * ' ') + line.strip() for line in values]

        return values

    def _process_block(self, block, data):
        name = block.get('name')
        when = block.get('when')

        loop = block.get('loop')
        loop_data = None

        loop_control = block.get('loop_control') or {'loop_var': 'item'}

        values = list()

        if when:
            conditional = "{%% if %s %%}True{%% else %%}False{%% endif %%}"
            if not self.template(conditional % when, data, fail_on_undefined=False):
                display.vvvv("block '%s' skipped due to conditional check failure" % name)
                return values

        if loop:
            loop_data = self.template("{{ %s }}" % loop, data, fail_on_undefined=False)
            if not loop_data:
                display.warning("block '%s' skipped due to missing loop var '%s'" % (name, loop))
                return values

        if isinstance(loop_data, collections.Mapping):
            for item_key, item_value in iteritems(loop_data):
                item_data = data.copy()
                key = loop_control['loop_var']
                item_data[key] = {'key': item_key, 'value': item_value}

                templated_values = self._template_items(block, item_data)

                if templated_values:
                    values.extend(templated_values)

        elif isinstance(loop_data, collections.Iterable):
            for item_value in loop_data:
                item_data = data.copy()
                key = loop_control['loop_var']
                item_data[key] = item_value

                templated_values = self._template_items(block, item_data)

                if templated_values:
                    values.extend(templated_values)

        else:
            values = self._template_items(block, data)

        return values

    def template(self, value, data=None, fail_on_undefined=False):
        try:
            data = data or {}
            self._templar.set_available_variables(data)
            return self._templar.template(value)
        except AnsibleUndefinedVariable:
            if not fail_on_undefined:
                return None
            raise
