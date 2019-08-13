# (c) 2018, NetApp Inc.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from ansible.modules.storage.netapp.netapp_e_iscsi_interface import IscsiInterface
from units.modules.utils import AnsibleExitJson, AnsibleFailJson, ModuleTestCase, set_module_args

__metaclass__ = type
import mock


class IscsiInterfaceTest(ModuleTestCase):
    REQUIRED_PARAMS = {
        'api_username': 'rw',
        'api_password': 'password',
        'api_url': 'http://localhost',
        'ssid': '1',
        'state': 'disabled',
        'name': 1,
        'controller': 'A',
    }
    REQ_FUNC = 'ansible.modules.storage.netapp.netapp_e_iscsi_interface.request'

    def _set_args(self, args=None):
        module_args = self.REQUIRED_PARAMS.copy()
        if args is not None:
            module_args.update(args)
        set_module_args(module_args)

    def test_validate_params(self):
        """Ensure we can pass valid parameters to the module"""
        # Provide a range of valid values for each
        for controller in ['A', 'B']:
            for i in range(1, 10):
                for mtu in [1500, 2500, 9000]:
                    self._set_args(dict(
                        state='disabled',
                        name=i,
                        controller=controller,
                        mtu=mtu,
                    ))
            iface = IscsiInterface()

    def test_invalid_params(self):
        """Ensure that our input validation catches invalid parameters"""

        # Currently a 'C' controller is invalid
        self._set_args(dict(
            state='disabled',
            name=1,
            controller="C",
        ))
        with self.assertRaises(AnsibleFailJson) as result:
            iface = IscsiInterface()

        # Each of these mtu values are invalid
        for mtu in [500, 1499, 9001]:
            self._set_args({
                'state': 'disabled',
                'name': 1,
                'controller': 'A',
                'mtu': mtu
            })
        with self.assertRaises(AnsibleFailJson) as result:
            iface = IscsiInterface()

    def test_interfaces(self):
        """Validate that we are processing the interface list properly"""
        self._set_args()

        interfaces = [
            dict(interfaceType='iscsi',
                 iscsi=dict()),
            dict(interfaceType='iscsi',
                 iscsi=dict()),
            dict(interfaceType='fc', )
        ]

        # Ensure we filter out anything without an interfaceType of iscsi
        expected = [iface['iscsi'] for iface in interfaces if iface['interfaceType'] == 'iscsi']

        # We expect a single call to the API: retrieve the list of interfaces from the objectGraph.
        with mock.patch(self.REQ_FUNC, return_value=(200, interfaces)):
            iface = IscsiInterface()
            interfaces = iface.interfaces
            self.assertEquals(interfaces, expected)

    def test_interfaces_fail(self):
        """Ensure we fail gracefully on an error to retrieve the interfaces"""
        self._set_args()

        with self.assertRaises(AnsibleFailJson) as result:
            # Simulate a failed call to the API
            with mock.patch(self.REQ_FUNC, side_effect=Exception("Failure")):
                iface = IscsiInterface()
                interfaces = iface.interfaces

    def test_fetch_target_interface_bad_channel(self):
        """Ensure we fail correctly when a bad channel is provided"""
        self._set_args()

        interfaces = list(dict(channel=1, controllerId='1'))

        with self.assertRaisesRegexp(AnsibleFailJson, r".*?channels include.*"):
            with mock.patch.object(IscsiInterface, 'interfaces', return_value=interfaces):
                iface = IscsiInterface()
                interfaces = iface.fetch_target_interface()

    def test_make_update_body_dhcp(self):
        """Ensure the update body generates correctly for a transition from static to dhcp"""
        self._set_args(dict(state='enabled',
                            config_method='dhcp')
                       )

        iface = dict(id='1',
                     ipv4Enabled=False,
                     ipv4Data=dict(ipv4AddressData=dict(ipv4Address="0.0.0.0",
                                                        ipv4SubnetMask="0.0.0.0",
                                                        ipv4GatewayAddress="0.0.0.0", ),
                                   ipv4AddressConfigMethod='configStatic', ),
                     interfaceData=dict(ethernetData=dict(maximumFramePayloadSize=1500, ), ),
                     )

        # Test a transition from static to dhcp
        inst = IscsiInterface()
        update, body = inst.make_update_body(iface)
        self.assertTrue(update, msg="An update was expected!")
        self.assertEquals(body['settings']['ipv4Enabled'][0], True)
        self.assertEquals(body['settings']['ipv4AddressConfigMethod'][0], 'configDhcp')

    def test_make_update_body_static(self):
        """Ensure the update body generates correctly for a transition from dhcp to static"""
        iface = dict(id='1',
                     ipv4Enabled=False,
                     ipv4Data=dict(ipv4AddressConfigMethod='configDhcp',
                                   ipv4AddressData=dict(ipv4Address="0.0.0.0",
                                                        ipv4SubnetMask="0.0.0.0",
                                                        ipv4GatewayAddress="0.0.0.0", ), ),
                     interfaceData=dict(ethernetData=dict(maximumFramePayloadSize=1500, ), ), )

        self._set_args(dict(state='enabled',
                            config_method='static',
                            address='10.10.10.10',
                            subnet_mask='255.255.255.0',
                            gateway='1.1.1.1'))

        inst = IscsiInterface()
        update, body = inst.make_update_body(iface)
        self.assertTrue(update, msg="An update was expected!")
        self.assertEquals(body['settings']['ipv4Enabled'][0], True)
        self.assertEquals(body['settings']['ipv4AddressConfigMethod'][0], 'configStatic')
        self.assertEquals(body['settings']['ipv4Address'][0], '10.10.10.10')
        self.assertEquals(body['settings']['ipv4SubnetMask'][0], '255.255.255.0')
        self.assertEquals(body['settings']['ipv4GatewayAddress'][0], '1.1.1.1')

    CONTROLLERS = dict(A='1', B='2')

    def test_update_bad_controller(self):
        """Ensure a bad controller fails gracefully"""
        self._set_args(dict(controller='B'))

        inst = IscsiInterface()
        with self.assertRaises(AnsibleFailJson) as result:
            with mock.patch.object(inst, 'get_controllers', return_value=dict(A='1')) as get_controllers:
                inst()

    @mock.patch.object(IscsiInterface, 'get_controllers', return_value=CONTROLLERS)
    def test_update(self, get_controllers):
        """Validate the good path"""
        self._set_args()

        inst = IscsiInterface()
        with self.assertRaises(AnsibleExitJson):
            with mock.patch(self.REQ_FUNC, return_value=(200, "")) as request:
                with mock.patch.object(inst, 'fetch_target_interface', side_effect=[{}, mock.MagicMock()]):
                    with mock.patch.object(inst, 'make_update_body', return_value=(True, {})):
                        inst()
        request.assert_called_once()

    @mock.patch.object(IscsiInterface, 'get_controllers', return_value=CONTROLLERS)
    def test_update_not_required(self, get_controllers):
        """Ensure we don't trigger the update if one isn't required or if check mode is enabled"""
        self._set_args()

        # make_update_body will report that no change is required, so we should see no call to the API.
        inst = IscsiInterface()
        with self.assertRaises(AnsibleExitJson) as result:
            with mock.patch(self.REQ_FUNC, return_value=(200, "")) as request:
                with mock.patch.object(inst, 'fetch_target_interface', side_effect=[{}, mock.MagicMock()]):
                    with mock.patch.object(inst, 'make_update_body', return_value=(False, {})):
                        inst()
        request.assert_not_called()
        self.assertFalse(result.exception.args[0]['changed'], msg="No change was expected.")

        # Since check_mode is enabled, we will run everything normally, but not make a request to the API
        #  to perform the actual change.
        inst = IscsiInterface()
        inst.check_mode = True
        with self.assertRaises(AnsibleExitJson) as result:
            with mock.patch(self.REQ_FUNC, return_value=(200, "")) as request:
                with mock.patch.object(inst, 'fetch_target_interface', side_effect=[{}, mock.MagicMock()]):
                    with mock.patch.object(inst, 'make_update_body', return_value=(True, {})):
                        inst()
        request.assert_not_called()
        self.assertTrue(result.exception.args[0]['changed'], msg="A change was expected.")

    @mock.patch.object(IscsiInterface, 'get_controllers', return_value=CONTROLLERS)
    def test_update_fail_busy(self, get_controllers):
        """Ensure we fail correctly on receiving a busy response from the API."""
        self._set_args()

        inst = IscsiInterface()
        with self.assertRaisesRegexp(AnsibleFailJson, r".*?busy.*") as result:
            with mock.patch(self.REQ_FUNC, return_value=(422, dict(retcode="3"))) as request:
                with mock.patch.object(inst, 'fetch_target_interface', side_effect=[{}, mock.MagicMock()]):
                    with mock.patch.object(inst, 'make_update_body', return_value=(True, {})):
                        inst()
        request.assert_called_once()

    @mock.patch.object(IscsiInterface, 'get_controllers', return_value=CONTROLLERS)
    @mock.patch.object(IscsiInterface, 'make_update_body', return_value=(True, {}))
    def test_update_fail(self, get_controllers, make_body):
        """Ensure we fail correctly on receiving a normal failure from the API."""
        self._set_args()

        inst = IscsiInterface()
        # Test a 422 error with a non-busy status
        with self.assertRaisesRegexp(AnsibleFailJson, r".*?Failed to modify.*") as result:
            with mock.patch(self.REQ_FUNC, return_value=(422, mock.MagicMock())) as request:
                with mock.patch.object(inst, 'fetch_target_interface', side_effect=[{}, mock.MagicMock()]):
                    inst()
        request.assert_called_once()

        # Test a 401 (authentication) error
        with self.assertRaisesRegexp(AnsibleFailJson, r".*?Failed to modify.*") as result:
            with mock.patch(self.REQ_FUNC, return_value=(401, mock.MagicMock())) as request:
                with mock.patch.object(inst, 'fetch_target_interface', side_effect=[{}, mock.MagicMock()]):
                    inst()
        request.assert_called_once()

        # Test with a connection failure
        with self.assertRaisesRegexp(AnsibleFailJson, r".*?Connection failure.*") as result:
            with mock.patch(self.REQ_FUNC, side_effect=Exception()) as request:
                with mock.patch.object(inst, 'fetch_target_interface', side_effect=[{}, mock.MagicMock()]):
                    inst()
        request.assert_called_once()
