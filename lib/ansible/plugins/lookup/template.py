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
            - Whether to convert YAML into data. If V(False), strings that are YAML will be left untouched.
            - Mutually exclusive with the O(jinja2_native) option.
        default: true
        deprecated:
          why: This option is no longer used in the Ansible Core code base.
          version: "2.23"
          alternatives: Jinja2 native mode is now the default and only option, which is mutually exclusive with this option.
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
            - It is off by default even if global O(jinja2_native) is V(True).
            - Has no effect if global O(jinja2_native) is V(False).
            - This offers more flexibility than the template module which does not use Jinja2 native types at all.
        default: True
        version_added: '2.11'
        type: bool
        deprecated:
          why: This option is no longer used in the Ansible Core code base.
          version: "2.23"
          alternatives: Jinja2 native mode is now the default and only option.
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
      trim_blocks:
        description:
        - Determine when newlines should be removed from blocks.
        - When set to V(yes) the first newline after a block is removed (block, not variable tag!).
        type: bool
        default: yes
        version_added: '2.19'
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

- name: show templating results with trim_blocks
  ansible.builtin.debug:
    msg: "{{ lookup('ansible.builtin.template', './some_template.j2', trim_blocks=True) }}"

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
from ansible.template import trust_as_template
from ansible._internal._templating import _template_vars
from ansible._internal._templating._engine import TemplateOptions, TemplateOverrides
from ansible.utils.display import Display


display = Display()


class LookupModule(LookupBase):

    def run(self, terms, variables=None, **kwargs):

        ret = []

        self.set_options(var_options=variables, direct=kwargs)

        # capture options
        lookup_template_vars = self.get_option('template_vars')
        variable_start_string = self.get_option('variable_start_string')
        variable_end_string = self.get_option('variable_end_string')
        comment_start_string = self.get_option('comment_start_string')
        comment_end_string = self.get_option('comment_end_string')
        trim_blocks = self.get_option('trim_blocks')

        templar = self._templar

        for term in terms:
            display.debug("File lookup term: %s" % term)

            lookupfile = self.find_file_in_search_path(variables, 'templates', term)
            display.vvvv("File lookup using %s as file" % lookupfile)
            if lookupfile:
                template_data = trust_as_template(self._loader.get_text_file_contents(lookupfile))

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
                # FIXME: why isn't this a chainmap with a sacrificial bottom layer?
                vars = deepcopy(variables)
                vars.update(_template_vars.generate_ansible_template_vars(
                    path=term,
                    fullpath=lookupfile,
                    include_ansible_managed='ansible_managed' not in vars,  # do not clobber ansible_managed when set by the user
                ))
                vars.update(lookup_template_vars)

                overrides = dict(
                    variable_start_string=variable_start_string,
                    variable_end_string=variable_end_string,
                    comment_start_string=comment_start_string,
                    comment_end_string=comment_end_string,
                    trim_blocks=trim_blocks,
                )

                data_templar = templar.copy_with_new_env(available_variables=vars, searchpath=searchpath)
                # use the internal template API to avoid forced top-level finalization behavior imposed by the public API
                res = data_templar._engine.template(template_data, options=TemplateOptions(
                    escape_backslashes=False,
                    overrides=TemplateOverrides.from_kwargs(overrides),
                ))

                ret.append(res)
            else:
                raise AnsibleError("the template file %s could not be found for the lookup" % term)

        return ret
