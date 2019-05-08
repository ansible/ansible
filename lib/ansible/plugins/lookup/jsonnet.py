# (c) 2018, Stoned Elipot <stoned.elipot@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = """
    lookup: jsonnet
    author: Stoned Elipot <stoned.elipot@gmail.com>
    version_added: "2.9"
    short_description: retrieve file after templating with Jsonnet
    description:
      - The jsonnet lookup returns templated Jsonnet documents. The
        documents are looked up like regular template files.
      - Any Jinja2 expression can be evaluated from the Jsonnet document,
        hence any Ansible variable's value is available, with the provided
        "native" function ```ansible_expr```. It takes one argument,
        a Jinja2 expression, as a string, and returns its evaluation.
        The Jinja2 expression can be a bare string.
    requirements:
      - jsonnet (python library https://pypi.org/project/jsonnet/)
    options:
      _terms:
        description:
          - List of files to process.
      ext_vars:
        description:
          - A mapping for key and string values defining so called
            "external variables" for the Jsonnet processing.
          -  cf. https://jsonnet.org/learning/tutorial.html
      "ext_codes, tla_vars, tla_codes, max_trace, max_stack, gc_min_objects, gc_growth_trigger":
         description:
           - Other keyword arguments supported by Jsonnet Python API.
           - cf. https://jsonnet.org/ref/bindings.html
"""

EXAMPLES = """
- name: show templating results
  debug: msg="{{ lookup('jsonnet', 'some_template.jsonnet') }}"

- name: set facts from json produced by jsonnet
  set_fact: myvar="{{ lookup('jsonnet', 'some_template.jsonnet') }}"

- name: set facts from json produced by jsonnet with external variables provided
  set_fact: myvar="{{ lookup('jsonnet', 'some_template.jsonnet', ext_vars=a_mapping) }}"
  vars:
    a_mapping:
      var1: value1
      var2: value2

# Examples of Jinja2 expression evaluation in Jsonnet document:
#  std.native("ansible_expr")("{{ 1 + 1 }}")
#  std.native("ansible_expr")("ansible_all_ipv4_addresses")
"""

RETURN = """
_raw:
   description: Jsonnet document after processing
"""

from ansible.errors import AnsibleError
from ansible.plugins.lookup import LookupBase
from ansible.template import generate_ansible_template_vars
from ansible.module_utils._text import to_native, to_text
from ansible.utils.display import Display

display = Display()

try:
    import _jsonnet
    HAS_JSONNET = True
except ImportError:
    HAS_JSONNET = False


class LookupModule(LookupBase):

    def run(self, terms, variables, **kwargs):

        if not HAS_JSONNET:
            raise AnsibleError(
                "Requires the _jsonnet Python package. Try `pip install jsonnet`")

        ret = []

        for term in terms:
            display.debug("File lookup term: %s" % term)

            lookupfile = self.find_file_in_search_path(
                variables, 'templates', term)
            display.vvvv("File lookup using %s as file" % lookupfile)
            if lookupfile:
                vars = variables.copy()
                vars.update(generate_ansible_template_vars(lookupfile))
                self._templar.set_available_variables(vars)

                def ansible_expr(expr):
                    return to_native(self._templar.template(expr, convert_bare=True))

                native_callbacks = {
                    'ansible_expr': (('expr',), ansible_expr),
                }

                res = to_text(_jsonnet.evaluate_file(
                    lookupfile,
                    native_callbacks=native_callbacks, **kwargs))
                ret.append(res)
            else:
                raise AnsibleError(
                    "the Jsonnet document file %s could not be found for the lookup" % term)

        return ret
