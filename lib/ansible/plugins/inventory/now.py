DOCUMENTATION = r'''
    name: now
    plugin_type: inventory
    author:
      - Will Tome (@willtome)
    short_description: ServiceNow Inventory Plugin
    version_added: "2.10"
    description:
        - ServiceNow Inventory plugin
    extends_documentation_fragment:
        - constructed
    options:
        instance:
            description: The ServiceNow instance URI. The URI should be the fully-qualified domain name, e.g. 'your-instance.servicenow.com'.
            type: string
            required: True
            env:
                - name: SN_INSTANCE
        username:
            description: The ServiceNow instance user name. The user acount should have enough rights to read the cmdb_ci_server table (default), or the table specified by SN_TABLE
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
            default: []
        groups:
            description: Comma seperated string providing additional table columns to use as groups. Groups can overlap with fields
            type: list
            default: []
        selection_order:
            description: Comma seperated string providing ability to define selection preference order.
            type: string
            default: 'host_name,fqdn,ip_address,name'
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
plugin: servicenow
instance: demo.service-now.com
'''

from ansible.plugins.inventory import BaseInventoryPlugin, Constructable
import requests
import sys


class InventoryModule(BaseInventoryPlugin, Constructable):

    NAME = 'now'

    def invoke(self, verb, path, data):
        auth = requests.auth.HTTPBasicAuth(self.get_option('username'), self.get_option('password'))
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        proxy = self.get_option('proxy')


        # build url
        url = "https://%s/%s" % (self.get_option('instance'), path)
        results = []

        session = requests.Session()

        while url:
          # perform REST operation, accumulating page results
          response = session.get(
              url, auth=auth, headers=headers, proxies={
                  'http': proxy, 'https': proxy})
          if response.status_code != 200:
              print >> sys.stderr, "http error (%s): %s" % (response.status_code, response.text)
          results += response.json()['result']
          next_link = response.links.get('next', {})
          url =  next_link.get('url', None)

        result = { 'result': results }
        return result

    def parse(self, inventory, loader, path, cache=True):  # Plugin interface (2)
        super(InventoryModule, self).parse(inventory, loader, path)
        self._read_config_data(path)

        selection = self.get_option('selection_order').split(',')
        groups = self.get_option('groups')
        fields = self.get_option('fields')
        table = self.get_option('table')
        filter_results = self.get_option('filter_results')

        base_fields = [u'name', u'host_name', u'fqdn', u'ip_address', u'sys_class_name']
        base_groups = [u'sys_class_name']
        groups = base_groups + groups
        options = "?sysparm_exclude_reference_link=true&sysparm_display_value=true"

        columns = list(
            set(base_fields + base_groups + fields + groups))
        path = '/api/now/table/' + table + options + \
            "&sysparm_fields=" + ','.join(columns) + \
            "&sysparm_query=" + filter_results

        content = self.invoke('GET', path, None)

        target = None
        strict=self.get_option('strict')

        for record in content['result']:

            for k in selection:
                if k in record:
                    if record[k] != '':
                        target = record[k]

            host_name = self.inventory.add_host(target)

            for k in record.keys():
                self.inventory.set_variable(host_name, 'sn_%s' % k, record[k])

            for k in groups:
                if k == "sys_tags" and record[k] != None:
                    for y in [x.strip() for x in record[k].split(',')]:
                        group_name = self.inventory.add_group(y)
                        self.inventory.add_child(host_name, group_name)
                else:
                    group_name = self.inventory.add_group(record[k])
                    self.inventory.add_child(group_name, host_name)

            self._set_composite_vars(self.get_option('compose'), self.inventory.get_host(host_name).get_vars(), host_name, strict)
            self._add_host_to_composed_groups(self.get_option('groups'), dict(), host_name, strict)
            self._add_host_to_keyed_groups(self.get_option('keyed_groups'), dict(), host_name, strict)