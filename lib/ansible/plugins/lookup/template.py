# Copyright: (c) 2012, Michael DeHaan <michael.dehaan@gmail.com>
# Copyright: (c) 2012-17, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = """
    lookup: template
    author: Michael DeHaan <michael.dehaan@gmail.com>
    version_added: "0.9"
    short_description: retrieve contents of file after templating with Jinja2
    description:
      - Returns a list of strings; for each template in the list of templates you pass in, returns a string containing the results of processing that template.
    options:
      _terms:
        description: list of files to template
      convert_data:
        type: bool
        description: whether to convert YAML into data. If False, strings that are YAML will be left untouched.
      variable_start_string:
        description: The string marking the beginning of a print statement.
        default: '{{'
        version_added: '2.8'
        type: str
      variable_end_string:
        description: The string marking the end of a print statement.
        default: '}}'
        version_added: '2.8'
        type: str
"""

EXAMPLES = """
- name: show templating results
  debug:
    msg: "{{ lookup('template', './some_template.j2') }}"

- name: show templating results with different variable start and end string
  debug:
    msg: "{{ lookup('template', './some_template.j2', variable_start_string='[%', variable_end_string='%]') }}"
"""

RETURN = """
_raw:
   description: file(s) content after templating
"""

from copy import deepcopy
import os

from ansible.errors import AnsibleError
from ansible.plugins.lookup import LookupBase
from ansible.module_utils._text import to_bytes, to_text
from ansible.template import generate_ansible_template_vars
from ansible.utils.display import Display

display = Display()


class LookupModule(LookupBase):

    def run(self, terms, variables, **kwargs):

        convert_data_p = kwargs.get('convert_data', True)
        lookup_template_vars = kwargs.get('template_vars', {})
        ret = []

        variable_start_string = kwargs.get('variable_start_string', None)
        variable_end_string = kwargs.get('variable_end_string', None)

        old_vars = self._templar.available_variables

        for term in terms:
            display.debug("File lookup term: %s" % term)

            lookupfile = self.find_file_in_search_path(variables, 'templates', term)
            display.vvvv("File lookup using %s as file" % lookupfile)
            if lookupfile:
                b_template_data, show_data = self._loader._get_file_contents(lookupfile)
                template_data = to_text(b_template_data, errors='surrogate_or_strict')

                # set jinja2 internal search path for includes
                searchpath = variables.get('ansible_search_path', [])
                if searchpath:
                    # our search paths aren't actually the proper ones for jinja includes.
                    # We want to search into the 'templates' subdir of each search path in
                    # addition to our original search paths.
                    newsearchpath = []
                    for p in searchpath:
                        newsearchpath.append(os.path.join(p, 'templates'))
                        newsearchpath.append(p)
                    searchpath = newsearchpath
                searchpath.insert(0, os.path.dirname(lookupfile))

                self._templar.environment.loader.searchpath = searchpath
                if variable_start_string is not None:
                    self._templar.environment.variable_start_string = variable_start_string
                if variable_end_string is not None:
                    self._templar.environment.variable_end_string = variable_end_string

                # The template will have access to all existing variables,
                # plus some added by ansible (e.g., template_{path,mtime}),
                # plus anything passed to the lookup with the template_vars=
                # argument.
                vars = deepcopy(variables)
                vars.update(generate_ansible_template_vars(lookupfile))
                vars.update(lookup_template_vars)
                self._templar.available_variables = vars

                # do the templating
                res = self._templar.template(template_data, preserve_trailing_newlines=True,
                                             convert_data=convert_data_p, escape_backslashes=False)

                ret.append(res)
            else:
                raise AnsibleError("the template file %s could not be found for the lookup" % term)

        # restore old variables
        self._templar.available_variables = old_vars

        return ret
