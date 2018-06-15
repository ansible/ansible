#!/usr/bin/python
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: gce_instance_template
version_added: "2.3"
short_description: create or destroy instance templates of Compute Engine of GCP.
description:
     - Creates or destroy Google instance templates
       of Compute Engine of Google Cloud Platform.
options:
  state:
    description:
      - The desired state for the instance template.
    default: "present"
    choices: ["present", "absent"]
  name:
    description:
      - The name of the GCE instance template.
  size:
    description:
      - The desired machine type for the instance template.
    default: "f1-micro"
  source:
    description:
      - A source disk to attach to the instance.
        Cannot specify both I(image) and I(source).
  image:
    description:
      - The image to use to create the instance.
        Cannot specify both both I(image) and I(source).
  image_family:
    description:
      - The image family to use to create the instance.
        If I(image) has been used I(image_family) is ignored.
        Cannot specify both I(image) and I(source).
  disk_type:
    description:
      - Specify a C(pd-standard) disk or C(pd-ssd)
        for an SSD disk.
    default: pd-standard
  disk_auto_delete:
    description:
      - Indicate that the boot disk should be
        deleted when the Node is deleted.
    default: true
  network:
    description:
      - The network to associate with the instance.
    default: "default"
  subnetwork:
    description:
      - The Subnetwork resource name for this instance.
  can_ip_forward:
    description:
      - Set to C(yes) to allow instance to
        send/receive non-matching src/dst packets.
    type: bool
    default: 'no'
  external_ip:
    description:
      - The external IP address to use.
        If C(ephemeral), a new non-static address will be
        used.  If C(None), then no external address will
        be used.  To use an existing static IP address
        specify address name.
    default: "ephemeral"
  service_account_email:
    description:
      - service account email
  service_account_permissions:
    description:
      - service account permissions (see
        U(https://cloud.google.com/sdk/gcloud/reference/compute/instances/create),
        --scopes section for detailed information)
    choices: [
      "bigquery", "cloud-platform", "compute-ro", "compute-rw",
      "useraccounts-ro", "useraccounts-rw", "datastore", "logging-write",
      "monitoring", "sql-admin", "storage-full", "storage-ro",
      "storage-rw", "taskqueue", "userinfo-email"
    ]
  automatic_restart:
    description:
      - Defines whether the instance should be
        automatically restarted when it is
        terminated by Compute Engine.
  preemptible:
    description:
      - Defines whether the instance is preemptible.
  tags:
    description:
      - a comma-separated list of tags to associate with the instance
  metadata:
    description:
      - a hash/dictionary of custom data for the instance;
        '{"key":"value", ...}'
  description:
    description:
      - description of instance template
  disks:
    description:
      - a list of persistent disks to attach to the instance; a string value
        gives the name of the disk; alternatively, a dictionary value can
        define 'name' and 'mode' ('READ_ONLY' or 'READ_WRITE'). The first entry
        will be the boot disk (which must be READ_WRITE).
  nic_gce_struct:
    description:
      - Support passing in the GCE-specific
        formatted networkInterfaces[] structure.
  disks_gce_struct:
    description:
      - Support passing in the GCE-specific
        formatted formatted disks[] structure. Case sensitive.
        see U(https://cloud.google.com/compute/docs/reference/latest/instanceTemplates#resource) for detailed information
    version_added: "2.4"
  project_id:
    description:
      - your GCE project ID
  pem_file:
    description:
      - path to the pem file associated with the service account email
        This option is deprecated. Use 'credentials_file'.
  credentials_file:
    description:
      - path to the JSON file associated with the service account email
  subnetwork_region:
    version_added: "2.4"
    description:
      - Region that subnetwork resides in. (Required for subnetwork to successfully complete)
requirements:
    - "python >= 2.6"
    - "apache-libcloud >= 0.13.3, >= 0.17.0 if using JSON credentials,
      >= 0.20.0 if using preemptible option"
notes:
  - JSON credentials strongly preferred.
author: "Gwenael Pellen (@GwenaelPellenArkeup) <gwenael.pellen@arkeup.com>"
'''

EXAMPLES = '''
# Usage
- name: create instance template named foo
  gce_instance_template:
    name: foo
    size: n1-standard-1
    image_family: ubuntu-1604-lts
    state: present
    project_id: "your-project-name"
    credentials_file: "/path/to/your-key.json"
    service_account_email: "your-sa@your-project-name.iam.gserviceaccount.com"

# Example Playbook
- name: Compute Engine Instance Template Examples
  hosts: localhost
  vars:
    service_account_email: "your-sa@your-project-name.iam.gserviceaccount.com"
    credentials_file: "/path/to/your-key.json"
    project_id: "your-project-name"
  tasks:
    - name: create instance template
      gce_instance_template:
        name: my-test-instance-template
        size: n1-standard-1
        image_family: ubuntu-1604-lts
        state: present
        project_id: "{{ project_id }}"
        credentials_file: "{{ credentials_file }}"
        service_account_email: "{{ service_account_email }}"
    - name: delete instance template
      gce_instance_template:
        name: my-test-instance-template
        size: n1-standard-1
        image_family: ubuntu-1604-lts
        state: absent
        project_id: "{{ project_id }}"
        credentials_file: "{{ credentials_file }}"
        service_account_email: "{{ service_account_email }}"

# Example playbook using disks_gce_struct
- name: Compute Engine Instance Template Examples
  hosts: localhost
  vars:
    service_account_email: "your-sa@your-project-name.iam.gserviceaccount.com"
    credentials_file: "/path/to/your-key.json"
    project_id: "your-project-name"
  tasks:
    - name: create instance template
      gce_instance_template:
        name: foo
        size: n1-standard-1
        state: present
        project_id: "{{ project_id }}"
        credentials_file: "{{ credentials_file }}"
        service_account_email: "{{ service_account_email }}"
        disks_gce_struct:
          - device_name: /dev/sda
            boot: true
            autoDelete: true
            initializeParams:
              diskSizeGb: 30
              diskType: pd-ssd
              sourceImage: projects/debian-cloud/global/images/family/debian-8

'''

RETURN = '''
'''

import traceback
try:
    from ast import literal_eval
    HAS_PYTHON26 = True
except ImportError:
    HAS_PYTHON26 = False

try:
    import libcloud
    from libcloud.compute.types import Provider
    from libcloud.compute.providers import get_driver
    from libcloud.common.google import GoogleBaseError, QuotaExceededError, \
        ResourceExistsError, ResourceInUseError, ResourceNotFoundError
    from libcloud.compute.drivers.gce import GCEAddress
    _ = Provider.GCE
    HAS_LIBCLOUD = True
except ImportError:
    HAS_LIBCLOUD = False

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.gce import gce_connect
from ansible.module_utils._text import to_native


def get_info(inst):
    """Retrieves instance template information
    """
    return({
        'name': inst.name,
        'extra': inst.extra,
    })


def create_instance_template(module, gce):
    """Create an instance template
    module : AnsibleModule object
    gce: authenticated GCE libcloud driver
    Returns:
        instance template information
    """
    # get info from module
    name = module.params.get('name')
    size = module.params.get('size')
    source = module.params.get('source')
    image = module.params.get('image')
    image_family = module.params.get('image_family')
    disk_type = module.params.get('disk_type')
    disk_auto_delete = module.params.get('disk_auto_delete')
    network = module.params.get('network')
    subnetwork = module.params.get('subnetwork')
    subnetwork_region = module.params.get('subnetwork_region')
    can_ip_forward = module.params.get('can_ip_forward')
    external_ip = module.params.get('external_ip')
    service_account_permissions = module.params.get(
        'service_account_permissions')
    service_account_email = module.params.get('service_account_email')
    on_host_maintenance = module.params.get('on_host_maintenance')
    automatic_restart = module.params.get('automatic_restart')
    preemptible = module.params.get('preemptible')
    tags = module.params.get('tags')
    metadata = module.params.get('metadata')
    description = module.params.get('description')
    disks_gce_struct = module.params.get('disks_gce_struct')
    changed = False

    # args of ex_create_instancetemplate
    gce_args = dict(
        name="instance",
        size="f1-micro",
        source=None,
        image=None,
        disk_type='pd-standard',
        disk_auto_delete=True,
        network='default',
        subnetwork=None,
        can_ip_forward=None,
        external_ip='ephemeral',
        service_accounts=None,
        on_host_maintenance=None,
        automatic_restart=None,
        preemptible=None,
        tags=None,
        metadata=None,
        description=None,
        disks_gce_struct=None,
        nic_gce_struct=None
    )

    gce_args['name'] = name
    gce_args['size'] = size

    if source is not None:
        gce_args['source'] = source

    if image:
        gce_args['image'] = image
    else:
        if image_family:
            image = gce.ex_get_image_from_family(image_family)
            gce_args['image'] = image
        else:
            gce_args['image'] = "debian-8"

    gce_args['disk_type'] = disk_type
    gce_args['disk_auto_delete'] = disk_auto_delete

    gce_network = gce.ex_get_network(network)
    gce_args['network'] = gce_network

    if subnetwork is not None:
        gce_args['subnetwork'] = gce.ex_get_subnetwork(subnetwork, region=subnetwork_region)

    if can_ip_forward is not None:
        gce_args['can_ip_forward'] = can_ip_forward

    if external_ip == "ephemeral":
        instance_external_ip = external_ip
    elif external_ip == "none":
        instance_external_ip = None
    else:
        try:
            instance_external_ip = gce.ex_get_address(external_ip)
        except GoogleBaseError as err:
            # external_ip is name ?
            instance_external_ip = external_ip
    gce_args['external_ip'] = instance_external_ip

    ex_sa_perms = []
    bad_perms = []
    if service_account_permissions:
        for perm in service_account_permissions:
            if perm not in gce.SA_SCOPES_MAP:
                bad_perms.append(perm)
        if len(bad_perms) > 0:
            module.fail_json(msg='bad permissions: %s' % str(bad_perms))
        if service_account_email is not None:
            ex_sa_perms.append({'email': str(service_account_email)})
        else:
            ex_sa_perms.append({'email': "default"})
        ex_sa_perms[0]['scopes'] = service_account_permissions
    gce_args['service_accounts'] = ex_sa_perms

    if on_host_maintenance is not None:
        gce_args['on_host_maintenance'] = on_host_maintenance

    if automatic_restart is not None:
        gce_args['automatic_restart'] = automatic_restart

    if preemptible is not None:
        gce_args['preemptible'] = preemptible

    if tags is not None:
        gce_args['tags'] = tags

    if disks_gce_struct is not None:
        gce_args['disks_gce_struct'] = disks_gce_struct

    # Try to convert the user's metadata value into the format expected
    # by GCE.  First try to ensure user has proper quoting of a
    # dictionary-like syntax using 'literal_eval', then convert the python
    # dict into a python list of 'key' / 'value' dicts.  Should end up
    # with:
    # [ {'key': key1, 'value': value1}, {'key': key2, 'value': value2}, ...]
    if metadata:
        if isinstance(metadata, dict):
            md = metadata
        else:
            try:
                md = literal_eval(str(metadata))
                if not isinstance(md, dict):
                    raise ValueError('metadata must be a dict')
            except ValueError as e:
                module.fail_json(msg='bad metadata: %s' % str(e))
            except SyntaxError as e:
                module.fail_json(msg='bad metadata syntax')

        if hasattr(libcloud, '__version__') and libcloud.__version__ < '0.15':
            items = []
            for k, v in md.items():
                items.append({"key": k, "value": v})
            metadata = {'items': items}
        else:
            metadata = md
    gce_args['metadata'] = metadata

    if description is not None:
        gce_args['description'] = description

    instance = None
    try:
        instance = gce.ex_get_instancetemplate(name)
    except ResourceNotFoundError:
        try:
            instance = gce.ex_create_instancetemplate(**gce_args)
            changed = True
        except GoogleBaseError as err:
            module.fail_json(
                msg='Unexpected error attempting to create instance {}, error: {}'
                .format(
                    instance,
                    err.value
                )
            )

    if instance:
        json_data = get_info(instance)
    else:
        module.fail_json(msg="no instance template!")

    return (changed, json_data, name)


def delete_instance_template(module, gce):
    """ Delete instance template.
    module : AnsibleModule object
    gce: authenticated GCE libcloud driver
    Returns:
        instance template information
    """
    name = module.params.get('name')
    current_state = "absent"
    changed = False

    # get instance template
    instance = None
    try:
        instance = gce.ex_get_instancetemplate(name)
        current_state = "present"
    except GoogleBaseError as e:
        json_data = dict(msg='instance template not exists: %s' % to_native(e),
                         exception=traceback.format_exc())

    if current_state == "present":
        rc = instance.destroy()
        if rc:
            changed = True
        else:
            module.fail_json(
                msg='instance template destroy failed'
            )

    json_data = {}
    return (changed, json_data, name)


def module_controller(module, gce):
    ''' Control module state parameter.
    module : AnsibleModule object
    gce: authenticated GCE libcloud driver
    Returns:
        nothing
    Exit:
        AnsibleModule object exit with json data.
    '''
    json_output = dict()
    state = module.params.get("state")
    if state == "present":
        (changed, output, name) = create_instance_template(module, gce)
        json_output['changed'] = changed
        json_output['msg'] = output
    elif state == "absent":
        (changed, output, name) = delete_instance_template(module, gce)
        json_output['changed'] = changed
        json_output['msg'] = output

    module.exit_json(**json_output)


def check_if_system_state_would_be_changed(module, gce):
    ''' check_if_system_state_would_be_changed !
    module : AnsibleModule object
    gce: authenticated GCE libcloud driver
    Returns:
        system_state changed
    '''
    changed = False
    current_state = "absent"

    state = module.params.get("state")
    name = module.params.get("name")

    try:
        gce.ex_get_instancetemplate(name)
        current_state = "present"
    except GoogleBaseError as e:
        module.fail_json(msg='GCE get instancetemplate problem: %s' % to_native(e),
                         exception=traceback.format_exc())

    if current_state != state:
        changed = True

    if current_state == "absent":
        if changed:
            output = 'instance template {0} will be created'.format(name)
        else:
            output = 'nothing to do for instance template {0} '.format(name)
    if current_state == "present":
        if changed:
            output = 'instance template {0} will be destroyed'.format(name)
        else:
            output = 'nothing to do for instance template {0} '.format(name)

    return (changed, output)


def main():
    module = AnsibleModule(
        argument_spec=dict(
            state=dict(choices=['present', 'absent'], default='present'),
            name=dict(require=True, aliases=['base_name']),
            size=dict(default='f1-micro'),
            source=dict(),
            image=dict(),
            image_family=dict(default='debian-8'),
            disk_type=dict(choices=['pd-standard', 'pd-ssd'], default='pd-standard', type='str'),
            disk_auto_delete=dict(type='bool', default=True),
            network=dict(default='default'),
            subnetwork=dict(),
            can_ip_forward=dict(type='bool', default=False),
            external_ip=dict(default='ephemeral'),
            service_account_email=dict(),
            service_account_permissions=dict(type='list'),
            automatic_restart=dict(type='bool', default=None),
            preemptible=dict(type='bool', default=None),
            tags=dict(type='list'),
            metadata=dict(),
            description=dict(),
            disks=dict(type='list'),
            nic_gce_struct=dict(type='list'),
            project_id=dict(),
            pem_file=dict(type='path'),
            credentials_file=dict(type='path'),
            subnetwork_region=dict(),
            disks_gce_struct=dict(type='list')
        ),
        mutually_exclusive=[['source', 'image']],
        required_one_of=[['image', 'image_family']],
        supports_check_mode=True
    )

    if not HAS_PYTHON26:
        module.fail_json(
            msg="GCE module requires python's 'ast' module, python v2.6+")
    if not HAS_LIBCLOUD:
        module.fail_json(
            msg='libcloud with GCE support (0.17.0+) required for this module')

    try:
        gce = gce_connect(module)
    except GoogleBaseError as e:
        module.fail_json(msg='GCE Connexion failed %s' % to_native(e), exception=traceback.format_exc())

    if module.check_mode:
        (changed, output) = check_if_system_state_would_be_changed(module, gce)
        module.exit_json(
            changed=changed,
            msg=output
        )
    else:
        module_controller(module, gce)


if __name__ == '__main__':
    main()
