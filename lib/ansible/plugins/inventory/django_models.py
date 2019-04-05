# (c) 2019, Ali Aqrabawi <aaqrabaw@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)

__metaclass__ = type

DOCUMENTATION = r'''
    name: django_models
    plugin_type: inventory
    author:
      - "Ali Aqrabawi (@aaqrabaw)"
    short_description: Django models inventory source
    description:
        - Get inventory hosts and groups from database using django models.
        - Uses Django settings file and project path, example:project_path=/path/to/django_project/my_site,setting_module=my_site.setting
        - the database should have three tables:
            - ansible_network_groups (for network devices groups)
            - ansible_aws_groups (for aws  groups)
            - ansible_inventory_hosts (for  hosts)
            
        - table's fields like follow:        
            - ansible_network_groups:
                  - name: CharField(max_length=100)
                  - ansible_connection: CharField(max_length=100)
                  - ansible_network_os: CharField(max_length=100)
                  - parent_group: ForeignKey('self', on_delete=models.DO_NOTHING, related_name='child_group',null=True)
                  - ansible_become: BooleanField(default=False)
                  - arent_group: ForeignKey('self', on_delete=models.DO_NOTHING, related_name='child_group',null=True)                                                   
    
    
            - ansible_aws_groups:
                  
                  - ami: CharField(max_length=100)
                  - region: CharField(max_length=100)
                  - type: models.CharField(max_length=100)
                  - sshkey: models.CharField(max_length=100)
                  - vpcid: models.CharField(max_length=100)
    

            - ansible_inventory_hosts:
                  - host: CharField(max_length=100)
                  - ansible_ssh_host: GenericIPAddressField()
                  - ansible_user: models.CharField(max_length=100)
                  - ansible_ssh_pass: models.CharField(max_length=100)
                  - ansible_become_pass: models.CharField(max_length=100)
                  - group: ForeignKey(ansible_network_groups, on_delete=models.DO_NOTHING)

'''

EXAMPLES = r'''
# django setting.py file.
# Example command line: ansible-inventory --graph -i "project_path=/home/aaqrabaw/PycharmProjects/dj_ansible, setting_module=dj_ansible.settings"
# @all:
#   |--@site_1:
#   |  |--@site1_firewalls:
#   |  |  |--fw1
#   |  |  |--fw2
#   |  |--@site1_ios_switches:
#   |  |  |--ios_switch1
#   |--@ungrouped:

plugin: django_models
'''
from ansible.plugins.inventory import BaseInventoryPlugin
from ansible.errors import AnsibleError
import os

try:
    import django
    from django.db import models
except ImportError:
    raise AnsibleError("Django Must be installed in order to use django_models inventory plugin")

ANSIBLE_CONNECTION_CHOICES = (
    ('network_cli', 'network_cli'),
    ('paramiko_ssh', 'paramiko'),
    ('chroot', 'chroot'),
    ('docker', 'docker'),
    ('httpapi', 'httpapi'),
    ('netconf', 'netconf'),
    ('winrm', 'winrm')
)

ANSIBLE_NETWORK_OS_CHOICES = (
    ('a10', 'a10'),
    ('aci', 'aci'),
    ('aireos', 'aireos'),
    ('aos', 'aos'),
    ('aruba', 'aruba'),
    ('asa', 'asa'),
    ('f5', 'f5'),
    ('ios', 'ios'),
    ('iosxr', 'iosxr'),
    ('nxos', 'nxos')

)


class InventoryModule(BaseInventoryPlugin):
    name = 'django_models'

    def __init__(self):
        self._dj_project_path = None
        self._dj_setting_module = None
        super(InventoryModule, self).__init__()

    def _setup_django(self):
        # add project to python search path
        import sys
        sys.path += [self._dj_project_path]

        os.environ['DJANGO_SETTINGS_MODULE'] = self._dj_setting_module
        try:
            django.setup()
        except ImportError as e:
            raise AnsibleError("Failed to setup Django! reason = " + str(e))

    def _setup_models(self):
        class AnsibleGroupBase(models.Model):
            name = models.CharField(max_length=100)
            ansible_connection = models.CharField(choices=ANSIBLE_CONNECTION_CHOICES, max_length=100)

            class Meta:
                abstract = True

        class AnsibleDeviceGroups(AnsibleGroupBase):
            ansible_become = models.BooleanField(default=False)

            class Meta:
                abstract = True

        class AnsibleNetworkGroups(AnsibleDeviceGroups):
            ansible_network_os = models.CharField(choices=ANSIBLE_NETWORK_OS_CHOICES, max_length=100)
            parent_group = models.ForeignKey('self', on_delete=models.DO_NOTHING, related_name='child_group',
                                             null=True, blank=True)

            class Meta:
                db_table = 'ansible_network_groups'
                app_label = 'django_ansible_inv_plugin'

        class AnsibleAWSGroups(AnsibleGroupBase):
            ami = models.CharField(max_length=100)
            region = models.CharField(max_length=100)
            type = models.CharField(max_length=100)
            sshkey = models.CharField(max_length=100)
            vpcid = models.CharField(max_length=100)
            parent_group = models.ForeignKey('self', on_delete=models.DO_NOTHING, related_name='child_group',
                                             null=True, blank=True)

            class Meta:
                db_table = 'ansible_aws_groups'
                app_label = 'django_ansible_inv_plugin'

        class AnsibleHosts(models.Model):
            host = models.CharField(max_length=100)
            ansible_ssh_host = models.GenericIPAddressField()
            ansible_user = models.CharField(max_length=100)
            ansible_ssh_pass = models.CharField(max_length=100)
            ansible_become_pass = models.CharField(max_length=100)
            group = models.ForeignKey(AnsibleNetworkGroups, on_delete=models.DO_NOTHING)

            class Meta:
                db_table = 'ansible_inventory_hosts'
                app_label = 'django_ansible_inv_plugin'

        self.network_group_model = AnsibleNetworkGroups
        self.aws_group_model = AnsibleAWSGroups
        self.host_model = AnsibleHosts

    def verify_file(self, path):
        if 'project_path' not in path or 'setting_module' not in path:
            return False
        try:
            self._dj_project_path, self._dj_setting_module = path.replace('project_path=', '').replace(
                'setting_module=',
                '').split(',')
        except ValueError:
            raise AnsibleError('invalid django_ansible source path, path=%r ' % path)
        return True

    def _add_group_childes(self, group):
        if group.parent_group:
            self.inventory.add_child(group.parent_group.name, group.name)
            self._add_group_childes(group.parent_group)

    def parse(self, inventory, loader, path, cache=True):

        super(InventoryModule, self).parse(inventory, loader, path)
        self._setup_django()
        self._setup_models()

        groups = self.network_group_model.objects.all()

        try:
            for group in groups:
                self.inventory.add_group(group.name)
                for field in group._meta.fields:
                    field_name = field.name
                    if field_name == 'parent_group':
                        continue
                    value = getattr(group, field.name)
                    if value:
                        self.inventory.set_variable(group.name, field_name, value)
                self._add_group_childes(group)

            hosts = self.host_model.objects.all()
            for host in hosts:
                self.inventory.add_host(host.host, group=host.group.name)
                for field in host._meta.fields:
                    field_name = field.name
                    value = getattr(host, field.name)
                    if value:
                        self.inventory.set_variable(host.host, field_name, value)
        except Exception as e:
            raise AnsibleError(str(e))
