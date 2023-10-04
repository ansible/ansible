# Copyright: (c) 2012, Michael DeHaan <michael.dehaan@gmail.com>
# Copyright: (c) 2012-17, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

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
        default: true
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
      template_vars:
        description: A dictionary, the keys become additional variables available for templating.
        default: {}
        version_added: '2.3'
        type: dict
      comment_start_string:
        description: The string marking the beginning of a comment statement.
        version_added: '2.12'
        type: str
        default: '{#'
      comment_end_string:
        description: The string marking the end of a comment statement.
        version_added: '2.12'
        type: str
        default: '#}'
    seealso:
      - ref: playbook_task_paths
        description: Search paths used for relative templates.
"""

EXAMPLES = """
- name: show templating results
  ansible.builtin.debug:
    msg: "{{ lookup('ansible.builtin.template', './some_template.j2') }}"

- name: show templating results with different variable start and end string
  ansible.builtin.debug:
    msg: "{{ lookup('ansible.builtin.template', './some_template.j2', variable_start_string='[%', variable_end_string='%]') }}"

- name: show templating results with different comment start and end string
  ansible.builtin.debug:
    msg: "{{ lookup('ansible.builtin.template', './some_template.j2', comment_start_string='[#', comment_end_string='#]') }}"
"""

RETURN = """
_raw:
   description: file(s) content after templating
   type: list
   elements: raw
"""

from copy import deepcopy
import os

import ansible.constants as C

from ansible.errors import AnsibleError
from ansible.plugins.lookup import LookupBase
from ansible.module_utils.common.text.converters import to_text
from ansible.template import generate_ansible_template_vars, AnsibleEnvironment
from ansible.utils.display import Display
from ansible.utils.native_jinja import NativeJinjaText


display = Display()


class LookupModule(LookupBase):

    def run(self, terms, variables, **kwargs):

        ret = []

        self.set_options(var_options=variables, direct=kwargs)

        # capture options
        convert_data_p = self.get_option('convert_data')
        lookup_template_vars = self.get_option('template_vars')
        jinja2_native = self.get_option('jinja2_native') and C.DEFAULT_JINJA2_NATIVE
        variable_start_string = self.get_option('variable_start_string')
        variable_end_string = self.get_option('variable_end_string')
        comment_start_string = self.get_option('comment_start_string')
        comment_end_string = self.get_option('comment_end_string')

        if jinja2_native:
            templar = self._templar
        else:
            templar = self._templar.copy_with_new_env(environment_class=AnsibleEnvironment)

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

                with templar.set_temporary_context(available_variables=vars, searchpath=searchpath):
                    overrides = dict(
                        variable_start_string=variable_start_string,
                        variable_end_string=variable_end_string,
                        comment_start_string=comment_start_string,
                        comment_end_string=comment_end_string
                    )
                    res = templar.template(template_data, preserve_trailing_newlines=True,
                                           convert_data=convert_data_p, escape_backslashes=False,
                                           overrides=overrides)

                if (C.DEFAULT_JINJA2_NATIVE and not jinja2_native) or not convert_data_p:
                    # jinja2_native is true globally but off for the lookup, we need this text
                    # not to be processed by literal_eval anywhere in Ansible
                    res = NativeJinjaText(res)

                ret.append(res)
            else:
                raise AnsibleError("the template file %s could not be found for the lookup" % term)

        return ret
