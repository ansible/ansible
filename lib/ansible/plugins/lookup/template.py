# Copyright: (c) 2012, Michael DeHaan <michael.dehaan@gmail.com>
# Copyright: (c) 2012-17, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = """
    name: template
    author: Michael DeHaan
    version_added: "0.9"
    short_description: retrieve contents of file after templating with Jinja2
    description:
      - Returns a list of strings; for each template in the list of templates you pass in, returns a string containing the results of processing that template.
    options:
      _terms:
        description: list of files to template
      convert_data:
        type: bool
        description:
            - Whether to convert YAML into data. If False, strings that are YAML will be left untouched.
            - Mutually exclusive with the jinja2_native option.
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
      jinja2_native:
        description:
            - Controls whether to use Jinja2 native types.
            - It is off by default even if global jinja2_native is True.
            - Has no effect if global jinja2_native is False.
            - This offers more flexibility than the template module which does not use Jinja2 native types at all.
            - Mutually exclusive with the convert_data option.
        default: False
        version_added: '2.11'
        type: bool
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
   type: list
   elements: raw
"""

from copy import deepcopy
import os

from ansible.errors import AnsibleError
from ansible.plugins.lookup import LookupBase
from ansible.module_utils._text import to_bytes, to_text
from ansible.template import generate_ansible_template_vars, AnsibleEnvironment, USE_JINJA2_NATIVE
from ansible.utils.display import Display

if USE_JINJA2_NATIVE:
    from ansible.utils.native_jinja import NativeJinjaText


display = Display()


class LookupModule(LookupBase):

    def run(self, terms, variables, **kwargs):
        convert_data_p = kwargs.get('convert_data', True)
        lookup_template_vars = kwargs.get('template_vars', {})
        jinja2_native = kwargs.get('jinja2_native', False)
        ret = []

        variable_start_string = kwargs.get('variable_start_string', None)
        variable_end_string = kwargs.get('variable_end_string', None)

        if USE_JINJA2_NATIVE and not jinja2_native:
            templar = self._templar.copy_with_new_env(environment_class=AnsibleEnvironment)
        else:
            templar = self._templar

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

                # The template will have access to all existing variables,
                # plus some added by ansible (e.g., template_{path,mtime}),
                # plus anything passed to the lookup with the template_vars=
                # argument.
                vars = deepcopy(variables)
                vars.update(generate_ansible_template_vars(term, lookupfile))
                vars.update(lookup_template_vars)

                with templar.set_temporary_context(variable_start_string=variable_start_string,
                                                   variable_end_string=variable_end_string,
                                                   available_variables=vars, searchpath=searchpath):
                    res = templar.template(template_data, preserve_trailing_newlines=True,
                                           convert_data=convert_data_p, escape_backslashes=False)

                if USE_JINJA2_NATIVE and not jinja2_native:
                    # jinja2_native is true globally but off for the lookup, we need this text
                    # not to be processed by literal_eval anywhere in Ansible
                    res = NativeJinjaText(res)

                ret.append(res)
            else:
                raise AnsibleError("the template file %s could not be found for the lookup" % term)

        return ret
