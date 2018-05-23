# (c) 2016, Josh Bradley <jbradley(at)digitalocean.com>
# (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = """
    lookup: chef_databag
    version_added: "2.3"
    short_description: fetches data from a Chef Databag
    description:
       - "This is a lookup plugin to provide access to chef data bags using the pychef package.
         It interfaces with the chef server api using the same methods to find a knife or chef-client config file to load parameters from,
         starting from either the given base path or the current working directory.
         The lookup order mirrors the one from Chef, all folders in the base path are walked back looking for the following configuration
         file in order : .chef/knife.rb, ~/.chef/knife.rb, /etc/chef/client.rb"
    requirements:
        - "pychef (python library https://pychef.readthedocs.io `pip install pychef`"
    options:
        name:
          description:
            - Name of the databag
          required: True
        item:
          description:
            - Item to fetch
          required: True
"""

EXAMPLES = """
    - debug:
        msg: "{{ lookup('chef_databag', 'name=data_bag_name item=data_bag_item') }}"
"""

RETURN = """
  _raw:
    description:
      - The value from the databag
"""

from ansible.errors import AnsibleError
from ansible.plugins.lookup import LookupBase
from ansible.parsing.splitter import parse_kv

try:
    import chef
    HAS_CHEF = True
except ImportError as missing_module:
    HAS_CHEF = False


class LookupModule(LookupBase):
    """
    Chef data bag lookup module
    """
    def __init__(self, loader=None, templar=None, **kwargs):

        super(LookupModule, self).__init__(loader, templar, **kwargs)

        # setup vars for data bag name and data bag item
        self.name = None
        self.item = None

    def parse_kv_args(self, args):
        """
        parse key-value style arguments
        """

        for arg in ["name", "item"]:
            try:
                arg_raw = args.pop(arg, None)
                if arg_raw is None:
                    continue
                parsed = str(arg_raw)
                setattr(self, arg, parsed)
            except ValueError:
                raise AnsibleError(
                    "can't parse arg {0}={1} as string".format(arg, arg_raw)
                )
        if args:
            raise AnsibleError(
                "unrecognized arguments to with_sequence: %r" % args.keys()
            )

    def run(self, terms, variables=None, **kwargs):
        # Ensure pychef has been loaded
        if not HAS_CHEF:
            raise AnsibleError('PyChef needed for lookup plugin, try `pip install pychef`')

        for term in terms:
            self.parse_kv_args(parse_kv(term))

        api_object = chef.autoconfigure()

        if not isinstance(api_object, chef.api.ChefAPI):
            raise AnsibleError('Unable to connect to Chef Server API.')

        data_bag_object = chef.DataBag(self.name)

        data_bag_item = data_bag_object[self.item]

        return [dict(data_bag_item)]
