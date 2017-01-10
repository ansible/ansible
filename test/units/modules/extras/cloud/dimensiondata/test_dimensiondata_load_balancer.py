# Make coding more python3-ish
from __future__ import (absolute_import, division)
__metaclass__ = type

import uuid

from libcloud.compute.types import Provider as ComputeProvider
from libcloud.common.dimensiondata import DimensionDataAPIException
from libcloud.loadbalancer.types import Provider as LBProvider

from ansible.compat.tests import unittest
from ansible.compat.tests.mock import call, create_autospec, MagicMock, patch
from ansible.module_utils.basic import AnsibleModule

from ansible.modules.extras.cloud.dimensiondata import \
    dimensiondata_load_balancer as subject


class TestDimensionDataLoadBalancer(unittest.TestCase):

    # ==============
    # SETUP/TEARDOWN
    # ==============

    def setUp(self):
        self.valid_params = dict(
            region='na',
            location='NA12',
            network_domain='ece209803ce2160b58ef3993df3ba44c1a3be250',
            name='lb001',
            port='80',
            protocol='http',
            algorithm='ROUND_ROBIN',
            members=[
                {'name': 'web001', 'port': 8080, 'ip': '192.168.0.11'},
                {'name': 'web002', 'port': 8080, 'ip': '192.168.0.12'}
            ],
            ensure='present',
            verify_ssl_cert=True,
            listener_ip_address='168.0.21.55'
        )

    # =====
    # TESTS
    # =====

    @patch('ansible.modules.extras.cloud.dimensiondata.'
           'dimensiondata_load_balancer.Member', autospec=True)
    def test__create_lb__happy_path(self, member_cls):
        # Mock/Setup
        mod = create_autospec(AnsibleModule)
        lb_drv = create_autospec(subject.get_lb_driver).return_value
        lb_con = lb_drv.return_value

        compute_con = MagicMock()
        net_domain = MagicMock()

        params = self.valid_params

        # Exercise
        changed, msg, lb_dict = subject.create_lb(lb_con=lb_con,
                                                  compute_con=compute_con,
                                                  net_domain=net_domain,
                                                  mod=mod,
                                                  **params)

        # Verify
        self.assertEqual(lb_con.create_balancer.call_count, 1)

        algorithms = getattr(subject.Algorithm, params["algorithm"])
        members = [member_cls(m['name'], m['ip'], m.get('port'))
                   for m in params["members"]]
        ip_address = params["listener_ip_address"]

        self.assertEqual(lb_con.create_balancer.call_args,
                         call(params["name"],
                              params["port"],
                              params["protocol"],
                              algorithms,
                              members,
                              ex_listener_ip_address=ip_address))
        self.assertEqual(changed, True)
        self.assertEqual(type(msg), str)
        self.assertEqual(type(lb_dict), dict)
        self.assertEqual(set(lb_dict.keys()),
                         set(['id', 'name', 'state', 'ip', 'port']))

    def test__delete_lb__happy_path(self):
        # Mock/Setup
        lb_drv = create_autospec(subject.get_lb_driver).return_value
        lb_con = lb_drv.return_value
        lb = lb_con.get_balancer.return_value

        # Exercise
        changed, msg, lb_dict = subject.delete_lb(lb=lb, lb_con=lb_con)

        # Verify
        self.assertEqual(lb_con.destroy_balancer.call_count, 1)
        self.assertEqual(lb_con.destroy_balancer.call_args, call(lb))

        self.assertEqual(changed, True)
        self.assertEqual(type(msg), str)
        self.assertEqual(type(lb_dict), dict)
        self.assertEqual(set(lb_dict.keys()), set(['id', 'name']))

    def test__do_nothing__happy_path(self):
        # Mock/Setup
        lb_drv = create_autospec(subject.get_lb_driver).return_value
        lb_con = lb_drv.return_value
        lb = lb_con.get_balancer.return_value

        # Exercise
        changed, msg, lb_dict = subject.do_nothing(name="lb001",
                                                   ensure="present",
                                                   lb=lb)

        # Verify
        self.assertEqual(changed, False)
        self.assertEqual(type(msg), str)
        self.assertEqual(type(lb_dict), dict)

    def test__get_action__already_absent(self):
        # Exercise
        action = subject.get_action(lb=None, ensure="absent")

        # Assert
        self.assertEqual(action, subject.do_nothing)

    def test__get_action__already_present(self):
        # Mock objects
        lb_drv = create_autospec(subject.get_lb_driver).return_value
        lb_con = lb_drv.return_value

        balancer = lb_con.get_balancer.return_value

        # Exercise
        action = subject.get_action(lb=balancer, ensure="present")

        # Assert
        self.assertEqual(action, subject.do_nothing)

    def test__get_action__create(self):
        # Exercise
        action = subject.get_action(lb=None, ensure="present")

        # Assert
        self.assertEqual(action, subject.create_lb)

    def test__get_action__delete(self):
        # Mock objects
        lb_drv = create_autospec(subject.get_lb_driver).return_value
        lb_con = lb_drv.return_value

        balancer = lb_con.get_balancer.return_value

        # Exercise
        action = subject.get_action(lb=balancer, ensure="absent")

        # Assert
        self.assertEqual(action, subject.delete_lb)

    def test__get_lb_by_id__happy_path(self):
        # Mock objects
        params = self.valid_params
        params["name"] = str(uuid.uuid4())

        lb_drv = create_autospec(subject.get_lb_driver).return_value
        lb_con = lb_drv.return_value

        # Exercise
        lb = subject.get_lb(lb_con=lb_con, **params)

        # Assert
        self.assertEqual(lb_con.get_balancer.call_count, 1)
        self.assertEqual(lb_con.get_balancer.call_args,
                         call(params["name"]))

        self.assertEqual(lb, lb_con.get_balancer.return_value)

    def test__get_lb_by_id__error(self):
        # Mock objects
        params = self.valid_params
        params["name"] = str(uuid.uuid4())

        lb_drv = create_autospec(subject.get_lb_driver).return_value
        lb_con = lb_drv.return_value
        lb_con.get_balancer.side_effect = \
            DimensionDataAPIException(code="SOME OTHER ERROR",
                                      msg="Not found",
                                      driver=lb_drv)

        # Exercise
        with self.assertRaises(subject.GetLoadBalancerError):
            subject.get_lb(lb_con=lb_con, **params)

        # Assert
        self.assertEqual(lb_con.get_balancer.call_count, 1)
        self.assertEqual(lb_con.get_balancer.call_args,
                         call(params["name"]))

    def test__get_lb_by_id__not_found(self):
        # Mock objects
        params = self.valid_params
        params["name"] = str(uuid.uuid4())

        lb_drv = create_autospec(subject.get_lb_driver).return_value
        lb_con = lb_drv.return_value
        lb_con.get_balancer.side_effect = \
            DimensionDataAPIException(code="RESOURCE_NOT_FOUND",
                                      msg="Not found",
                                      driver=lb_drv)

        # Exercise
        lb = subject.get_lb(lb_con=lb_con, **params)

        # Assert
        self.assertEqual(lb_con.get_balancer.call_count, 1)
        self.assertEqual(lb_con.get_balancer.call_args,
                         call(params["name"]))

        self.assertEqual(lb, None)

    def test__get_lb_by_name__happy_path(self):
        # Mock objects
        params = self.valid_params
        params["name"] = "Friendly Name"

        lb_drv = create_autospec(subject.get_lb_driver).return_value
        lb_con = lb_drv.return_value
        balancer = lb_con.get_balancer.return_value
        balancer.name = params["name"]
        lb_con.list_balancers.return_value = [balancer]

        # Exercise
        lb = subject.get_lb(lb_con=lb_con, **params)

        # Assert
        self.assertEqual(lb_con.list_balancers.call_count, 1)

        self.assertEqual(lb_con.get_balancer.call_count, 0)

        self.assertEqual(lb, balancer)

    def test__get_lb_by_name__not_found(self):
        # Mock objects
        params = self.valid_params
        params["name"] = "Friendly Name"

        lb_drv = create_autospec(subject.get_lb_driver).return_value
        lb_con = lb_drv.return_value
        balancer = lb_con.get_balancer.return_value
        balancer.name = "Some other name"
        lb_con.list_balancers.return_value = [balancer]

        # Exercise
        lb = subject.get_lb(lb_con=lb_con, **params)

        # Assert
        self.assertEqual(lb_con.list_balancers.call_count, 1)

        self.assertEqual(lb_con.get_balancer.call_count, 0)

        self.assertEqual(lb, None)

    @patch('ansible.modules.extras.cloud.dimensiondata.'
           'dimensiondata_load_balancer.get_network_domain', autospec=True)
    @patch('ansible.modules.extras.cloud.dimensiondata.'
           'dimensiondata_load_balancer.get_cp_driver', autospec=True)
    @patch('ansible.modules.extras.cloud.dimensiondata.'
           'dimensiondata_load_balancer.get_lb_driver', autospec=True)
    @patch('ansible.modules.extras.cloud.dimensiondata.'
           'dimensiondata_load_balancer.get_credentials', autospec=True)
    def test__initialize__happy_path(self,
                                     get_credentials,
                                     get_lb_driver,
                                     get_cp_driver,
                                     get_network_domain):
        # Mock objects
        params = self.valid_params
        user_id = str(uuid.uuid4())
        key = str(uuid.uuid4())

        get_credentials.return_value = dict(user_id=user_id, key=key)

        lb_drv = get_lb_driver.return_value
        compute_drv = get_cp_driver.return_value

        # Exercise
        lb_con, compute_con, net_domain = subject.initialize(**params)

        # Assert
        self.assertEqual(get_credentials.call_count, 1)

        self.assertEqual(get_cp_driver.call_count, 1)
        self.assertEqual(get_cp_driver.call_args,
                         call(ComputeProvider.DIMENSIONDATA))

        self.assertEqual(compute_drv.call_count, 1)
        region = "dd-%s" % params["region"]
        self.assertEqual(compute_drv.call_args,
                         call(user_id, key, region=region))

        self.assertEqual(compute_con, compute_drv.return_value)

        self.assertEqual(get_network_domain.call_count, 1)

        net_domain_name = params["network_domain"]
        location = params["location"]
        self.assertEqual(get_network_domain.call_args,
                         call(compute_con, net_domain_name, location))

        self.assertEqual(get_lb_driver.call_args,
                         call(LBProvider.DIMENSIONDATA))

        self.assertEqual(lb_drv.call_count, 1)
        self.assertEqual(lb_drv.call_args,
                         call(user_id, key, region=region))
        self.assertEqual(lb_con, lb_drv.return_value)

        self.assertEqual(lb_con.ex_set_current_network_domain.call_count, 1)
        self.assertEqual(lb_con.ex_set_current_network_domain.call_args,
                         call(net_domain.id))

        self.assertEqual(lb_con, lb_drv.return_value)
        self.assertEqual(compute_con, compute_drv.return_value)
        self.assertEqual(net_domain, get_network_domain.return_value)

    @patch('ansible.modules.extras.cloud.dimensiondata'
           '.dimensiondata_load_balancer.AnsibleModule', autospec=True)
    @patch('ansible.modules.extras.cloud.dimensiondata'
           '.dimensiondata_load_balancer.start', autospec=True)
    def test__main__happy_path(self, start, mod_cls):
        # Mock/Setup
        mod = mod_cls.return_value

        # Exercise
        subject.main()

        # Verify
        self.assertEqual(start.call_count, 1)
        self.assertEqual(start.call_args, call(mod))

    @patch('ansible.modules.extras.cloud.dimensiondata'
           '.dimensiondata_load_balancer.create_lb', autospec=True)
    @patch('ansible.modules.extras.cloud.dimensiondata'
           '.dimensiondata_load_balancer.get_action', autospec=True)
    @patch('ansible.modules.extras.cloud.dimensiondata'
           '.dimensiondata_load_balancer.get_lb', autospec=True)
    @patch('ansible.modules.extras.cloud.dimensiondata'
           '.dimensiondata_load_balancer.initialize', autospec=True)
    def test__start__action_create_failure(self,
                                           initialize,
                                           get_lb,
                                           get_action,
                                           create_lb):
        # Mock/Setup
        mod_cls = create_autospec(AnsibleModule)
        mod = mod_cls.return_value
        mod.params = self.valid_params
        mod.params["ensure"] = "present"

        lb_con = MagicMock()
        compute_con = MagicMock()
        net_domain = MagicMock()

        initialize.return_value = (lb_con, compute_con, net_domain)
        balancer = lb_con.get_balancer.return_value
        get_lb.return_value = balancer
        get_action.return_value = create_lb
        create_lb.side_effect = subject.CreateError

        # Exercise
        subject.start(mod)

        # Verify
        self.assertEqual(initialize.call_count, 1)
        self.assertEqual(initialize.call_args, call(**mod.params))

        self.assertEqual(get_lb.call_count, 1)
        self.assertEqual(get_lb.call_args, call(lb_con=lb_con, **mod.params))

        self.assertEqual(get_action.call_count, 1)
        self.assertEqual(get_action.call_args,
                         call(lb=balancer, ensure=mod.params["ensure"]))

        lb = get_lb.return_value
        self.assertEqual(create_lb.call_args, call(lb=lb,
                                                   lb_con=lb_con,
                                                   compute_con=compute_con,
                                                   net_domain=net_domain,
                                                   mod=mod,
                                                   **mod.params))

        self.assertEqual(mod.exit_json.call_count, 0)
        self.assertEqual(mod.fail_json.call_count, 1)

    @patch('ansible.modules.extras.cloud.dimensiondata'
           '.dimensiondata_load_balancer.delete_lb', autospec=True)
    @patch('ansible.modules.extras.cloud.dimensiondata'
           '.dimensiondata_load_balancer.get_action', autospec=True)
    @patch('ansible.modules.extras.cloud.dimensiondata'
           '.dimensiondata_load_balancer.get_lb', autospec=True)
    @patch('ansible.modules.extras.cloud.dimensiondata'
           '.dimensiondata_load_balancer.initialize', autospec=True)
    def test__start__action_delete_failure(self,
                                           initialize,
                                           get_lb,
                                           get_action,
                                           delete_lb):
        # Mock/Setup
        mod_cls = create_autospec(AnsibleModule)
        mod = mod_cls.return_value
        mod.params = self.valid_params
        mod.params["ensure"] = "absent"

        lb_con = MagicMock()
        compute_con = MagicMock()
        net_domain = MagicMock()

        initialize.return_value = (lb_con, compute_con, net_domain)
        balancer = lb_con.get_balancer.return_value
        get_lb.return_value = balancer
        get_action.return_value = delete_lb
        delete_lb.side_effect = subject.DeleteError

        # Exercise
        subject.start(mod)

        # Verify
        self.assertEqual(initialize.call_count, 1)
        self.assertEqual(initialize.call_args, call(**mod.params))

        self.assertEqual(get_lb.call_count, 1)
        self.assertEqual(get_lb.call_args, call(lb_con=lb_con, **mod.params))

        self.assertEqual(get_action.call_count, 1)
        self.assertEqual(get_action.call_args,
                         call(lb=balancer, ensure=mod.params["ensure"]))

        lb = get_lb.return_value
        self.assertEqual(delete_lb.call_args, call(lb=lb,
                                                   lb_con=lb_con,
                                                   compute_con=compute_con,
                                                   net_domain=net_domain,
                                                   mod=mod,
                                                   **mod.params))

        self.assertEqual(mod.exit_json.call_count, 0)
        self.assertEqual(mod.fail_json.call_count, 1)

    @patch('ansible.modules.extras.cloud.dimensiondata'
           '.dimensiondata_load_balancer.get_action', autospec=True)
    @patch('ansible.modules.extras.cloud.dimensiondata'
           '.dimensiondata_load_balancer.get_lb', autospec=True)
    @patch('ansible.modules.extras.cloud.dimensiondata'
           '.dimensiondata_load_balancer.initialize', autospec=True)
    def test__start__get_lb_failure(self, initialize, get_lb, get_action):
        # Mock/Setup
        mod_cls = create_autospec(AnsibleModule)
        mod = mod_cls.return_value
        mod.params = self.valid_params

        lb_con = MagicMock()
        compute_con = MagicMock()
        net_domain = MagicMock()

        initialize.return_value = (lb_con, compute_con, net_domain)
        get_lb.side_effect = subject.GetLoadBalancerError("something")

        # Exercise
        subject.start(mod)

        # Verify
        self.assertEqual(initialize.call_count, 1)
        self.assertEqual(initialize.call_args, call(**mod.params))

        self.assertEqual(get_lb.call_count, 1)
        self.assertEqual(get_lb.call_args, call(lb_con=lb_con, **mod.params))

        self.assertEqual(get_action.call_count, 0)

        self.assertEqual(mod.exit_json.call_count, 0)

        self.assertEqual(mod.fail_json.call_count, 1)

    @patch('ansible.modules.extras.cloud.dimensiondata'
           '.dimensiondata_load_balancer.create_lb', autospec=True)
    @patch('ansible.modules.extras.cloud.dimensiondata'
           '.dimensiondata_load_balancer.get_action', autospec=True)
    @patch('ansible.modules.extras.cloud.dimensiondata'
           '.dimensiondata_load_balancer.get_lb', autospec=True)
    @patch('ansible.modules.extras.cloud.dimensiondata'
           '.dimensiondata_load_balancer.initialize', autospec=True)
    def test__start__happy_path(self,
                                initialize,
                                get_lb,
                                get_action,
                                create_lb):
        # Mock/Setup
        mod_cls = create_autospec(AnsibleModule)
        mod = mod_cls.return_value
        mod.params = self.valid_params

        lb_con = MagicMock()
        compute_con = MagicMock()
        net_domain = MagicMock()

        initialize.return_value = (lb_con, compute_con, net_domain)
        get_action.return_value = create_lb
        create_lb.return_value = (True, "Changed LB", {})

        # Exercise
        subject.start(mod)

        # Verify
        self.assertEqual(initialize.call_count, 1)
        self.assertEqual(initialize.call_args, call(**mod.params))

        self.assertEqual(get_lb.call_count, 1)
        self.assertEqual(get_lb.call_args, call(lb_con=lb_con, **mod.params))

        self.assertEqual(get_action.call_count, 1)
        self.assertEqual(get_action.call_args,
                         call(lb=get_lb.return_value,
                              ensure=mod.params["ensure"]))

        self.assertEqual(create_lb.call_count, 1)
        lb = get_lb.return_value
        self.assertEqual(create_lb.call_args, call(lb=lb,
                                                   lb_con=lb_con,
                                                   compute_con=compute_con,
                                                   net_domain=net_domain,
                                                   mod=mod,
                                                   **mod.params))

        self.assertEqual(mod.exit_json.call_count, 1)
        changed, msg, lb_dict = create_lb.return_value
        self.assertEqual(mod.exit_json.call_args,
                         call(changed=changed, msg=msg, load_balancer=lb_dict))

    @patch('ansible.modules.extras.cloud.dimensiondata'
           '.dimensiondata_load_balancer.get_action', autospec=True)
    @patch('ansible.modules.extras.cloud.dimensiondata'
           '.dimensiondata_load_balancer.get_lb', autospec=True)
    @patch('ansible.modules.extras.cloud.dimensiondata'
           '.dimensiondata_load_balancer.initialize', autospec=True)
    def test__start__initialize_failure(self, initialize, get_lb, get_action):
        # Mock/Setup
        mod_cls = create_autospec(AnsibleModule)
        mod = mod_cls.return_value
        mod.params = self.valid_params

        initialize.side_effect = subject.InitializeError

        # Exercise
        subject.start(mod)

        # Verify
        self.assertEqual(initialize.call_count, 1)
        self.assertEqual(initialize.call_args, call(**mod.params))

        self.assertEqual(get_lb.call_count, 0)

        self.assertEqual(get_action.call_count, 0)

        self.assertEqual(mod.exit_json.call_count, 0)
        self.assertEqual(mod.fail_json.call_count, 1)

    @patch('ansible.modules.extras.cloud.dimensiondata'
           '.dimensiondata_load_balancer.get_action', autospec=True)
    @patch('ansible.modules.extras.cloud.dimensiondata'
           '.dimensiondata_load_balancer.get_lb', autospec=True)
    @patch('ansible.modules.extras.cloud.dimensiondata'
           '.dimensiondata_load_balancer.initialize', autospec=True)
    def test__start__unexpected_failure(self, initialize, get_lb, get_action):
        # Any other exceptions must be thrown by the module so that maintainers
        # can quickly debug and fix the issue.

        # Mock/Setup
        mod_cls = create_autospec(AnsibleModule)
        mod = mod_cls.return_value
        mod.params = self.valid_params

        initialize.side_effect = Exception

        # Exercise
        with self.assertRaises(Exception):
            subject.start(mod)

        # Verify
        self.assertEqual(initialize.call_count, 1)
        self.assertEqual(initialize.call_args, call(**mod.params))

        self.assertEqual(get_lb.call_count, 0)

        self.assertEqual(get_action.call_count, 0)

        self.assertEqual(mod.exit_json.call_count, 0)
        self.assertEqual(mod.fail_json.call_count, 0)
