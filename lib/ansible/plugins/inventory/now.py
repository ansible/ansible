from __future__ import absolute_import, division, print_function
__metaclass__ = type
DOCUMENTATION = r'''
    name: now
    plugin_type: inventory
    author:
      - Will Tome (@willtome)
      - Alex Mittell (@alex_mittell)
    short_description: ServiceNow Inventory Plugin
    version_added: "2.10"
    description:
        - ServiceNow Inventory plugin
    extends_documentation_fragment:
        - constructed
        - inventory_cache
    options:
        plugin:
            description: The name of the ServiceNow Inventory Plugin, this should always be 'now'.
            required: True
            choices: ['now']
        instance:
            description: The ServiceNow instance URI. The URI should be the fully-qualified domain name, e.g. 'your-instance.servicenow.com'.
            type: string
            required: True
            env:
                - name: SN_INSTANCE
        username:
            description: The ServiceNow user acount, it should have rights to read cmdb_ci_server (default), or table specified by SN_TABLE
            type: string
            required: True
            env:
                - name: SN_USERNAME
        password:
            description: The ServiceNow instance user password.
            type: string
            secret: true
            env:
                - name: SN_PASSWORD
        table:
            description: The ServiceNow table to query
            type: string
            default: cmdb_ci_server
        fields:
            description: Comma seperated string providing additional table columns to add as host vars to each inventory host.
            type: list
            default: [host_name,fqdn,ip_address,sys_class_name]
        selection_order:
            description: Comma seperated string providing ability to define selection preference order.
            type: list
            default: 'host_name,fqdn,ip_address'
        filter_results:
            description: Filter results with sysparm_query encoded query string syntax. Complete list of operators available for filters and queries.
            type: string
            default: ''
        proxy:
            description: Proxy server to use for requests to ServiceNow.
            type: string
            default: ''
'''

EXAMPLES = r'''
plugin: now
instance: demo.service-now.com
username: admin
password: password
keyed_groups:
  - key: sn_sys_class_name | lower
    prefix: ''
    separator: ''

plugin: now
instance: demo.service-now.com
username: admin
password: password
fields: [name,host_name,fqdn,ip_address,sys_class_name, install_status, classification,vendor]
keyed_groups:
  - key: sn_classification | lower
    prefix: 'env'
  - key: sn_vendor | lower
    prefix: ''
    separator: ''
  - key: sn_sys_class_name | lower
    prefix: ''
    separator: ''
  - key: sn_install_status | lower
    prefix: 'status'

plugin: now
instance: demo.service-now.com
username: admin
password: password
fields:
  - name
  - sys_tags
compose:
  sn_tags: sn_sys_tags.replace(" ", "").split(',')
  ansible_host: sn_ip_address
keyed_groups:
  - key: sn_tags | lower
    prefix: 'tag'
'''

from ansible.plugins.inventory import BaseInventoryPlugin, Constructable, Cacheable
from ansible.errors import AnsibleError, AnsibleParserError
try:
    import requests
    HAS_REQUESTS = True 
except ImportError: 
    HAS_REQUESTS = False 
import sys


class InventoryModule(BaseInventoryPlugin, Constructable, Cacheable):

    NAME = 'now'

    def invoke(self, verb, path, data):
        auth = requests.auth.HTTPBasicAuth(self.get_option('username'),
                                           self.get_option('password'))
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        proxy = self.get_option('proxy')

        # build url
        self.url = "https://%s/%s" % (self.get_option('instance'), path)
        url = self.url
        results = []
        
        if not self.update_cache:
            try:    
                results = self._cache[self.cache_key][self.url]
            except KeyError:
                pass

        if not results:
            if self.cache_key not in self._cache:
                self._cache[self.cache_key] = {self.url: ''}

            session = requests.Session()

            while url:
                # perform REST operation, accumulating page results
                response = session.get(url,
                                       auth=auth,
                                       headers=headers,
                                       proxies={
                                           'http': proxy,
                                           'https': proxy
                                       })
                if response.status_code != 200:
                    raise AnsibleError("http error (%s): %s" %
                                       (response.status_code, response.text))
                results += response.json()['result']
                next_link = response.links.get('next', {})
                url = next_link.get('url', None)

            self._cache[self.cache_key] = {self.url: results}

        results = {'result': results}
        return results

    def parse(self, inventory, loader, path,
              cache=True):  # Plugin interface (2)
        super(InventoryModule, self).parse(inventory, loader, path)

        if not HAS_REQUESTS:
            raise AnsibleParserError('Please install "requests" Python module as this is required'
                                     ' for ServiceNow dynamic inventory plugin.')

        self._read_config_data(path)
        self.cache_key = self.get_cache_key(path)

        self.use_cache = self.get_option('cache') and cache
        self.update_cache = self.get_option('cache') and not cache

        selection = self.get_option('selection_order')
        fields = self.get_option('fields')
        table = self.get_option('table')
        filter_results = self.get_option('filter_results')

        options = "?sysparm_exclude_reference_link=true&sysparm_display_value=true"

        path = '/api/now/table/' + table + options + \
            "&sysparm_fields=" + ','.join(fields) + \
            "&sysparm_query=" + filter_results

        content = self.invoke('GET', path, None)
        strict = self.get_option('strict')

        for record in content['result']:

            target = None

            for k in selection:
                if k in record:
                    if record[k] != '':
                        target = record[k]
            if target is None:
                continue

            host_name = self.inventory.add_host(target)

            for k in record.keys():
                self.inventory.set_variable(host_name, 'sn_%s' % k, record[k])

            self._set_composite_vars(
                self.get_option('compose'),
                self.inventory.get_host(host_name).get_vars(), host_name,
                strict)
            self._add_host_to_composed_groups(self.get_option('groups'),
                                              dict(), host_name, strict)
            self._add_host_to_keyed_groups(self.get_option('keyed_groups'),
                                           dict(), host_name, strict)