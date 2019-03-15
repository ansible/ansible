#!/usr/bin/python

# Copyright: (c) 2019, Patryk Cichy @PatTheSilent
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: cs_image_store

short_description: Manages CloudStack Image Stores.

version_added: "2.8"

description:
  - Deploy, remove, recreate CloudStack Image Stores.

options:
  url:
    description:
      - The URL for the Image Store.
      - Required when I(state=present).
    type: str
  name:
    description:
      - The ID of the Image Store. Required when deleting a Image Store.
    required: true
    type: str
  zone:
    description:
      - The Zone name for the Image Store.
    required: true
    type: str
  state:
    description:
      - Stage of the Image Store
    choices: [present, absent]
    default: present
    type: str
  provider:
    description:
      - The image store provider name. Required when creating a new Image Store
    type: str
  force_recreate:
    description:
      - Set to C(yes) if you're changing an existing Image Store.
      - This will force the recreation of the Image Store.
      - Recreation might fail if there are snapshots present on the Image Store. Delete them before running the recreation.
    type: bool
    default: no

extends_documentation_fragment: cloudstack

author:
  - Patryk Cichy (@PatTheSilent)
'''

EXAMPLES = '''
- name: Add a Image Store (NFS)
  cs_image_store:
    zone: zone-01
    name: nfs-01
    provider: NFS
    url: nfs://192.168.21.16/exports/secondary
  delegate_to: localhost

# Change the NFS share URL and force a Image Store recreation
- name: Change the NFS url
  cs_image_store:
    zone: zone-01
    name: nfs-01
    provider: NFS
    force_recreate: yes
    url: nfs://192.168.21.10/shares/secondary
  delegate_to: localhost

- name: delete the image store
  cs_image_store:
    name: nfs-01
    zone: zone-01
    state: absent
  delegate_to: localhost

'''

RETURN = '''
id:
  description: the ID of the image store
  type: str
  returned: success
  sample: feb11a84-a093-45eb-b84d-7f680313c40b
name:
  description: the name of the image store
  type: str
  returned: success
  sample: nfs-01
protocol:
  description: the protocol of the image store
  type: str
  returned: success
  sample: nfs
provider_name:
  description: the provider name of the image store
  type: str
  returned: success
  sample: NFS
scope:
  description: the scope of the image store
  type: str
  returned: success
  sample: ZONE
url:
  description: the url of the image store
  type: str
  sample: nfs://192.168.21.16/exports/secondary
  returned: success
zone:
  description: the Zone name of the image store
  type: str
  returned: success
  sample: zone-01
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.cloudstack import AnsibleCloudStack, cs_argument_spec, cs_required_together


class AnsibleCloudstackImageStore(AnsibleCloudStack):

    def __init__(self, module):
        super(AnsibleCloudstackImageStore, self).__init__(module)
        self.returns = {
            'protocol': 'protocol',
            'providername': 'provider_name',
            'scope': 'scope',
            'url': 'url'
        }
        self.image_store = None

    def get_storage_providers(self, storage_type="image"):
        args = {
            'type': storage_type
        }
        storage_provides = self.query_api('listStorageProviders', **args)
        return [provider.get('name') for provider in storage_provides.get('dataStoreProvider')]

    def get_image_store(self):
        if self.image_store:
            return self.image_store
        image_store = self.module.params.get('name')
        args = {
            'name': self.module.params.get('name'),
            'zoneid': self.get_zone(key='id')
        }

        image_stores = self.query_api('listImageStores', **args)
        if image_stores:
            for img_s in image_stores.get('imagestore'):
                if image_store.lower() in [img_s['name'].lower(), img_s['id']]:
                    self.image_store = img_s
                    break

        return self.image_store

    def present_image_store(self):
        provider_list = self.get_storage_providers()
        image_store = self.get_image_store()

        if self.module.params.get('provider') not in provider_list:
            self.module.fail_json(
                msg='Provider %s is not in the provider list (%s). Please specify a correct provider' % (
                    self.module.params.get('provider'), provider_list))
        args = {
            'name': self.module.params.get('name'),
            'url': self.module.params.get('url'),
            'zoneid': self.get_zone(key='id'),
            'provider': self.module.params.get('provider')
        }
        if not image_store:
            self.result['changed'] = True
            if not self.module.check_mode:
                res = self.query_api('addImageStore', **args)
                self.image_store = res.get('imagestore')
        else:
            # Cloudstack API expects 'provider' but returns 'providername'
            args['providername'] = args.pop('provider')
            if self.has_changed(args, image_store):
                if self.module.params.get('force_recreate'):
                    self.absent_image_store()
                    self.image_store = None
                    self.image_store = self.present_image_store()
                else:
                    self.module.warn("Changes to the Image Store won't be applied"
                                     "Use force_recreate=yes to allow the store to be recreated")

        return self.image_store

    def absent_image_store(self):
        image_store = self.get_image_store()
        if image_store:
            self.result['changed'] = True
            if not self.module.check_mode:
                args = {
                    'id': image_store.get('id')
                }
                self.query_api('deleteImageStore', **args)
        return image_store


def main():
    argument_spec = cs_argument_spec()
    argument_spec.update(dict(
        url=dict(),
        name=dict(required=True),
        zone=dict(required=True),
        provider=dict(),
        force_recreate=dict(type='bool', default=False),
        state=dict(choices=['present', 'absent'], default='present'),
    ))

    module = AnsibleModule(
        argument_spec=argument_spec,
        required_together=cs_required_together(),
        required_if=[
            ('state', 'present', ['url', 'provider']),
        ],
        supports_check_mode=True
    )

    acis_do = AnsibleCloudstackImageStore(module)

    state = module.params.get('state')
    if state == "absent":
        image_store = acis_do.absent_image_store()
    else:
        image_store = acis_do.present_image_store()

    result = acis_do.get_result(image_store)
    module.exit_json(**result)


if __name__ == '__main__':
    main()
