from __future__ import annotations

from ansible.parsing.vault import EncryptedString
from ansible.plugins.inventory import BaseInventoryPlugin, Cacheable

DOCUMENTATION = """
    inventory: vaulted_test_plugin
    short_description: Mocks a plugin returning vaulted data
    description: Test caching of EncryptedString and bytes.
    extends_documentation_fragment:
      - inventory_cache
    options:
      plugin:
        required: true
        description: name of the plugin
"""


class InventoryModule(BaseInventoryPlugin, Cacheable):
    NAME = 'vaulted_test_plugin'

    def verify_file(self, path):
        return path.endswith('vaulted.yml')

    def parse(self, inventory, loader, path, cache=None):
        super(InventoryModule, self).parse(inventory, loader, path)
        self._read_config_data(path)

        cache_key = self.get_cache_key(path)
        use_cache = self.get_option('cache') and cache

        if use_cache and cache_key in self._cache:
            data = self._cache[cache_key]
        else:
            ciphertext = (
                "$ANSIBLE_VAULT;1.1;AES256\n"
                "35393234323236393339316632363836366236353936663633653463663662366166636362633036\n"
                "3030663765353535646139626266393563313936306536310a316535336333346433303036323533\n"
                "35326566613337373030313161323864393638383363373866383437633230623666616661393631\n"
                "6664326533316164620a653463653133643733353434316230613865623032336338356161666531\n"
                "3633"
            )

            data = {
                'vaulted_host': {
                    'my_secret': EncryptedString(ciphertext=ciphertext),
                    'my_bytes': b'byte_string',
                }
            }

            if self.get_option('cache'):
                self._cache[cache_key] = data

        for hostname, variables in data.items():
            self.inventory.add_host(hostname)
            for k, v in variables.items():
                self.inventory.set_variable(hostname, k, v)
