# This code is part of Ansible, but is an independent component.
# This particular file snippet, and this file snippet only, is BSD licensed.
# Modules you write using this snippet, which is embedded dynamically by Ansible
# still belong to the author of the module, and may assign their own license
# to the complete work.
#
# Copyright (c) 2018 Palo Alto Networks techbizdev, <techbizdev@paloaltonetworks.com>
#
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
#
#    * Redistributions of source code must retain the above copyright
#      notice, this list of conditions and the following disclaimer.
#    * Redistributions in binary form must reproduce the above copyright notice,
#      this list of conditions and the following disclaimer in the documentation
#      and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
# IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE
# USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

from __future__ import absolute_import, division, print_function
__metaclass__ = type


_MIN_VERSION_ERROR = '{0} version ({1}) < minimum version ({2})'
HAS_PANDEVICE = True
try:
    import pandevice
    from pandevice.base import PanDevice
    from pandevice.firewall import Firewall
    from pandevice.panorama import DeviceGroup, Template, TemplateStack
    from pandevice.policies import PreRulebase, PostRulebase, Rulebase
    from pandevice.device import Vsys
    from pandevice.errors import PanDeviceError
except ImportError:
    HAS_PANDEVICE = False


def _vstr(val):
    return '{0}.{1}.{2}'.format(*val)


class ConnectionHelper(object):
    def __init__(self, min_pandevice_version, min_panos_version,
                 panorama_error, firewall_error):
        """Performs connection initialization and determines params."""
        # Params for AnsibleModule.
        self.argument_spec = {}
        self.required_one_of = []

        # Params for pandevice tree construction.
        self.vsys = None
        self.device_group = None
        self.vsys_dg = None
        self.rulebase = None
        self.template = None
        self.template_stack = None
        self.vsys_importable = None
        self.min_pandevice_version = min_pandevice_version
        self.min_panos_version = min_panos_version
        self.panorama_error = panorama_error
        self.firewall_error = firewall_error

        # The PAN-OS device.
        self.device = None

    def get_pandevice_parent(self, module):
        """Builds the pandevice object tree, returning the parent object.

        If pandevice is not installed, then module.fail_json() will be
        invoked.

        Arguments:
            * module(AnsibleModule): the ansible module.

        Returns:
            * The parent pandevice object based on the spec given to
              get_connection().
        """
        # Sanity check.
        if not HAS_PANDEVICE:
            module.fail_json(msg='Missing required library "pandevice".')

        # Verify pandevice minimum version.
        if self.min_pandevice_version is not None:
            pdv = tuple(int(x) for x in pandevice.__version__.split('.'))
            if pdv < self.min_pandevice_version:
                module.fail_json(msg=_MIN_VERSION_ERROR.format(
                    'pandevice', pandevice.__version__,
                    _vstr(self.min_pandevice_version)))

        pan_device_auth, serial_number = None, None
        if module.params['provider'] and module.params['provider']['ip_address']:
            pan_device_auth = (
                module.params['provider']['ip_address'],
                module.params['provider']['username'],
                module.params['provider']['password'],
                module.params['provider']['api_key'],
                module.params['provider']['port'],
            )
            serial_number = module.params['provider']['serial_number']
        elif module.params.get('ip_address', None) is not None:
            pan_device_auth = (
                module.params['ip_address'],
                module.params['username'],
                module.params['password'],
                module.params['api_key'],
                module.params['port'],
            )
            msg = 'Classic provider params are deprecated; use "provider" instead'
            module.deprecate(msg, '2.12')
        else:
            module.fail_json(msg='Provider params are required.')

        # Create the connection object.
        try:
            self.device = PanDevice.create_from_device(*pan_device_auth)
        except PanDeviceError as e:
            module.fail_json(msg='Failed connection: {0}'.format(e))

        # Verify PAN-OS minimum version.
        if self.min_panos_version is not None:
            if self.device._version_info < self.min_panos_version:
                module.fail_json(msg=_MIN_VERSION_ERROR.format(
                    'PAN-OS', _vstr(self.device._version_info),
                    _vstr(self.min_panos_version)))

        # Optional: Firewall via Panorama connectivity specified.
        if hasattr(self.device, 'refresh_devices') and serial_number:
            fw = Firewall(serial=serial_number)
            self.device.add(fw)
            self.device = fw

        parent = self.device
        not_found = '{0} "{1}" is not present.'
        pano_mia_param = 'Param "{0}" is required for Panorama but not specified.'
        ts_error = 'Specify either the template or the template stack{0}.'
        if hasattr(self.device, 'refresh_devices'):
            # Panorama connection.
            # Error if Panorama is not supported.
            if self.panorama_error is not None:
                module.fail_json(msg=self.panorama_error)

            # Spec: template stack.
            tmpl_required = False
            added_template = False
            if self.template_stack is not None:
                name = module.params[self.template_stack]
                if name is not None:
                    stacks = TemplateStack.refreshall(parent, name_only=True)
                    for ts in stacks:
                        if ts.name == name:
                            parent = ts
                            added_template = True
                            break
                    else:
                        module.fail_json(msg=not_found.format(
                            'Template stack', name,
                        ))
                elif self.template is not None:
                    tmpl_required = True
                else:
                    module.fail_json(msg=pano_mia_param.format(self.template_stack))

            # Spec: template.
            if self.template is not None:
                name = module.params[self.template]
                if name is not None:
                    if added_template:
                        module.fail_json(msg=ts_error.format(', not both'))
                    templates = Template.refreshall(parent, name_only=True)
                    for t in templates:
                        if t.name == name:
                            parent = t
                            break
                    else:
                        module.fail_json(msg=not_found.format(
                            'Template', name,
                        ))
                elif tmpl_required:
                    module.fail_json(msg=ts_error.format(''))
                else:
                    module.fail_json(msg=pano_mia_param.format(self.template))

            # Spec: vsys importable.
            vsys_name = self.vsys_importable or self.vsys
            if vsys_name is not None:
                name = module.params[vsys_name]
                if name not in (None, 'shared'):
                    vo = Vsys(name)
                    parent.add(vo)
                    parent = vo

            # Spec: vsys_dg or device_group.
            dg_name = self.vsys_dg or self.device_group
            if dg_name is not None:
                name = module.params[dg_name]
                if name not in (None, 'shared'):
                    groups = DeviceGroup.refreshall(parent, name_only=True)
                    for dg in groups:
                        if dg.name == name:
                            parent = dg
                            break
                    else:
                        module.fail_json(msg=not_found.format(
                            'Device group', name,
                        ))

            # Spec: rulebase.
            if self.rulebase is not None:
                if module.params[self.rulebase] in (None, 'pre-rulebase'):
                    rb = PreRulebase()
                    parent.add(rb)
                    parent = rb
                elif module.params[self.rulebase] == 'rulebase':
                    rb = Rulebase()
                    parent.add(rb)
                    parent = rb
                elif module.params[self.rulebase] == 'post-rulebase':
                    rb = PostRulebase()
                    parent.add(rb)
                    parent = rb
                else:
                    module.fail_json(msg=not_found.format(
                        'Rulebase', module.params[self.rulebase]))
        else:
            # Firewall connection.
            # Error if firewalls are not supported.
            if self.firewall_error is not None:
                module.fail_json(msg=self.firewall_error)

            # Spec: vsys or vsys_dg or vsys_importable.
            vsys_name = self.vsys_dg or self.vsys or self.vsys_importable
            if vsys_name is not None:
                parent.vsys = module.params[vsys_name]

            # Spec: rulebase.
            if self.rulebase is not None:
                rb = Rulebase()
                parent.add(rb)
                parent = rb

        # Done.
        return parent


def get_connection(vsys=None, device_group=None,
                   vsys_dg=None, vsys_importable=None,
                   rulebase=None, template=None, template_stack=None,
                   with_classic_provider_spec=False, with_state=True,
                   argument_spec=None, required_one_of=None,
                   min_pandevice_version=None, min_panos_version=None,
                   panorama_error=None, firewall_error=None):
    """Returns a helper object that handles pandevice object tree init.

    The `vsys`, `device_group`, `vsys_dg`, `vsys_importable`, `rulebase`,
    `template`, and `template_stack` params can be any of the following types:

        * None - do not include this in the spec
        * True - use the default param name
        * string - use this string for the param name

    The `min_pandevice_version` and `min_panos_version` args expect a 3 element
    tuple of ints.  For example, `(0, 6, 0)` or `(8, 1, 0)`.

    If you are including template support (by defining either `template` and/or
    `template_stack`), and the thing the module is enabling the management of is
    an "importable", you should define either `vsys_importable` (whose default
    value is None) or `vsys` (whose default value is 'vsys1').

    Arguments:
        vsys: The vsys (default: 'vsys1').
        device_group: Panorama only - The device group (default: 'shared').
        vsys_dg: The param name if vsys and device_group are a shared param.
        vsys_importable: Either this or `vsys` should be specified.  For:
            - Interfaces
            - VLANs
            - Virtual Wires
            - Virtual Routers
        rulebase: This is a policy of some sort.
        template: Panorama - The template name.
        template_stack: Panorama - The template stack name.
        with_classic_provider_spec(bool): Include the ip_address, username,
            password, api_key, and port params in the base spec, and make the
            "provider" param optional.
        with_state(bool): Include the standard 'state' param.
        argument_spec(dict): The argument spec to mixin with the
            generated spec based on the given parameters.
        required_one_of(list): List of lists to extend into required_one_of.
        min_pandevice_version(tuple): Minimum pandevice version allowed.
        min_panos_version(tuple): Minimum PAN-OS version allowed.
        panorama_error(str): The error message if the device is Panorama.
        firewall_error(str): The error message if the device is a firewall.

    Returns:
        ConnectionHelper
    """
    helper = ConnectionHelper(
        min_pandevice_version, min_panos_version,
        panorama_error, firewall_error)
    req = []
    spec = {
        'provider': {
            'required': True,
            'type': 'dict',
            'required_one_of': [['password', 'api_key'], ],
            'options': {
                'ip_address': {'required': True},
                'username': {'default': 'admin'},
                'password': {'no_log': True},
                'api_key': {'no_log': True},
                'port': {'default': 443, 'type': 'int'},
                'serial_number': {'no_log': True},
            },
        },
    }

    if with_classic_provider_spec:
        spec['provider']['required'] = False
        spec['provider']['options']['ip_address']['required'] = False
        del(spec['provider']['required_one_of'])
        spec.update({
            'ip_address': {'required': False},
            'username': {'default': 'admin'},
            'password': {'no_log': True},
            'api_key': {'no_log': True},
            'port': {'default': 443, 'type': 'int'},
        })
        req.extend([
            ['provider', 'ip_address'],
            ['provider', 'password', 'api_key'],
        ])

    if with_state:
        spec['state'] = {
            'default': 'present',
            'choices': ['present', 'absent'],
        }

    if vsys_dg is not None:
        if isinstance(vsys_dg, bool):
            param = 'vsys_dg'
        else:
            param = vsys_dg
        spec[param] = {}
        helper.vsys_dg = param
    else:
        if vsys is not None:
            if isinstance(vsys, bool):
                param = 'vsys'
            else:
                param = vsys
            spec[param] = {'default': 'vsys1'}
            helper.vsys = param
        if device_group is not None:
            if isinstance(device_group, bool):
                param = 'device_group'
            else:
                param = device_group
            spec[param] = {'default': 'shared'}
            helper.device_group = param
        if vsys_importable is not None:
            if vsys is not None:
                raise KeyError('Define "vsys" or "vsys_importable", not both.')
            if isinstance(vsys_importable, bool):
                param = 'vsys'
            else:
                param = vsys_importable
            spec[param] = {}
            helper.vsys_importable = param

    if rulebase is not None:
        if isinstance(rulebase, bool):
            param = 'rulebase'
        else:
            param = rulebase
        spec[param] = {
            'default': None,
            'choices': ['pre-rulebase', 'rulebase', 'post-rulebase'],
        }
        helper.rulebase = param

    if template is not None:
        if isinstance(template, bool):
            param = 'template'
        else:
            param = template
        spec[param] = {}
        helper.template = param

    if template_stack is not None:
        if isinstance(template_stack, bool):
            param = 'template_stack'
        else:
            param = template_stack
        spec[param] = {}
        helper.template_stack = param

    if argument_spec is not None:
        for k in argument_spec.keys():
            if k in spec:
                raise KeyError('{0}: key used by connection helper.'.format(k))
            spec[k] = argument_spec[k]

    if required_one_of is not None:
        req.extend(required_one_of)

    # Done.
    helper.argument_spec = spec
    helper.required_one_of = req
    return helper
