import pytest
import unittest

from collections import namedtuple
from ansible.parsing.dataloader import DataLoader
from ansible.vars.manager import VariableManager
from ansible.inventory.manager import InventoryManager
from ansible.playbook.play import Play
from ansible.executor.task_queue_manager import TaskQueueManager

import ansible.modules.cloud.amazon.ec2_vpc_nat_gateway as ng


boto3 = pytest.importorskip("boto3")
botocore = pytest.importorskip("botocore")

Options = (
    namedtuple(
        'Options', [
            'connection', 'module_path', 'forks', 'become', 'become_method',
            'become_user', 'remote_user', 'private_key_file', 'ssh_common_args',
            'sftp_extra_args', 'scp_extra_args', 'ssh_extra_args', 'verbosity',
            'check', 'diff'
        ]
    )
)
# initialize needed objects
loader = DataLoader()
variable_manager = VariableManager(loader=loader)
options = (
    Options(
        connection='local',
        module_path='cloud/amazon',
        forks=1, become=None, become_method=None, become_user=None, check=True,
        remote_user=None, private_key_file=None, ssh_common_args=None,
        sftp_extra_args=None, scp_extra_args=None, ssh_extra_args=None,
        verbosity=3, diff=False
    )
)
passwords = dict(vault_pass='')

aws_region = 'us-west-2'

# create inventory and pass to var manager
inventory = InventoryManager(loader=loader)
variable_manager.set_inventory(inventory)


def run(play):
    tqm = None
    results = None
    try:
        tqm = TaskQueueManager(
            inventory=inventory,
            variable_manager=variable_manager,
            loader=loader,
            options=options,
            passwords=passwords,
            stdout_callback='default',
        )
        results = tqm.run(play)
    finally:
        if tqm is not None:
            tqm.cleanup()
    return tqm, results


class AnsibleVpcNatGatewayTasks(unittest.TestCase):

    def test_create_gateway_using_allocation_id(self):
        play_source = dict(
            name="Create new nat gateway with eip allocation-id",
            hosts='localhost',
            gather_facts='no',
            tasks=[
                dict(
                    action=dict(
                        module='ec2_vpc_nat_gateway',
                        args=dict(
                            subnet_id='subnet-12345678',
                            allocation_id='eipalloc-12345678',
                            wait='yes',
                            region=aws_region,
                        )
                    ),
                    register='nat_gateway',
                ),
                dict(
                    action=dict(
                        module='debug',
                        args=dict(
                            msg='{{nat_gateway}}'
                        )
                    )
                )
            ]
        )
        play = Play().load(play_source, variable_manager=variable_manager, loader=loader)
        tqm, results = run(play)
        self.failUnless(tqm._stats.ok['localhost'] == 2)
        self.failUnless(tqm._stats.changed['localhost'] == 1)

    def test_create_gateway_using_allocation_id_idempotent(self):
        play_source = dict(
            name="Create new nat gateway with eip allocation-id",
            hosts='localhost',
            gather_facts='no',
            tasks=[
                dict(
                    action=dict(
                        module='ec2_vpc_nat_gateway',
                        args=dict(
                            subnet_id='subnet-123456789',
                            allocation_id='eipalloc-1234567',
                            wait='yes',
                            region=aws_region,
                        )
                    ),
                    register='nat_gateway',
                ),
                dict(
                    action=dict(
                        module='debug',
                        args=dict(
                            msg='{{nat_gateway}}'
                        )
                    )
                )
            ]
        )
        play = Play().load(play_source, variable_manager=variable_manager, loader=loader)
        tqm, results = run(play)
        self.failUnless(tqm._stats.ok['localhost'] == 2)
        self.assertFalse('localhost' in tqm._stats.changed)

    def test_create_gateway_using_eip_address(self):
        play_source = dict(
            name="Create new nat gateway with eip address",
            hosts='localhost',
            gather_facts='no',
            tasks=[
                dict(
                    action=dict(
                        module='ec2_vpc_nat_gateway',
                        args=dict(
                            subnet_id='subnet-12345678',
                            eip_address='55.55.55.55',
                            wait='yes',
                            region=aws_region,
                        )
                    ),
                    register='nat_gateway',
                ),
                dict(
                    action=dict(
                        module='debug',
                        args=dict(
                            msg='{{nat_gateway}}'
                        )
                    )
                )
            ]
        )
        play = Play().load(play_source, variable_manager=variable_manager, loader=loader)
        tqm, results = run(play)
        self.failUnless(tqm._stats.ok['localhost'] == 2)
        self.failUnless(tqm._stats.changed['localhost'] == 1)

    def test_create_gateway_using_eip_address_idempotent(self):
        play_source = dict(
            name="Create new nat gateway with eip address",
            hosts='localhost',
            gather_facts='no',
            tasks=[
                dict(
                    action=dict(
                        module='ec2_vpc_nat_gateway',
                        args=dict(
                            subnet_id='subnet-123456789',
                            eip_address='55.55.55.55',
                            wait='yes',
                            region=aws_region,
                        )
                    ),
                    register='nat_gateway',
                ),
                dict(
                    action=dict(
                        module='debug',
                        args=dict(
                            msg='{{nat_gateway}}'
                        )
                    )
                )
            ]
        )
        play = Play().load(play_source, variable_manager=variable_manager, loader=loader)
        tqm, results = run(play)
        self.failUnless(tqm._stats.ok['localhost'] == 2)
        self.assertFalse('localhost' in tqm._stats.changed)

    def test_create_gateway_in_subnet_only_if_one_does_not_exist_already(self):
        play_source = dict(
            name="Create new nat gateway only if one does not exist already",
            hosts='localhost',
            gather_facts='no',
            tasks=[
                dict(
                    action=dict(
                        module='ec2_vpc_nat_gateway',
                        args=dict(
                            if_exist_do_not_create='yes',
                            subnet_id='subnet-123456789',
                            wait='yes',
                            region=aws_region,
                        )
                    ),
                    register='nat_gateway',
                ),
                dict(
                    action=dict(
                        module='debug',
                        args=dict(
                            msg='{{nat_gateway}}'
                        )
                    )
                )
            ]
        )
        play = Play().load(play_source, variable_manager=variable_manager, loader=loader)
        tqm, results = run(play)
        self.failUnless(tqm._stats.ok['localhost'] == 2)
        self.assertFalse('localhost' in tqm._stats.changed)

    def test_delete_gateway(self):
        play_source = dict(
            name="Delete Nat Gateway",
            hosts='localhost',
            gather_facts='no',
            tasks=[
                dict(
                    action=dict(
                        module='ec2_vpc_nat_gateway',
                        args=dict(
                            nat_gateway_id='nat-123456789',
                            state='absent',
                            wait='yes',
                            region=aws_region,
                        )
                    ),
                    register='nat_gateway',
                ),
                dict(
                    action=dict(
                        module='debug',
                        args=dict(
                            msg='{{nat_gateway}}'
                        )
                    )
                )
            ]
        )
        play = Play().load(play_source, variable_manager=variable_manager, loader=loader)
        tqm, results = run(play)
        self.failUnless(tqm._stats.ok['localhost'] == 2)
        self.assertTrue('localhost' in tqm._stats.changed)


class AnsibleEc2VpcNatGatewayFunctions(unittest.TestCase):

    def test_get_nat_gateways(self):
        client = boto3.client('ec2', region_name=aws_region)
        success, err_msg, stream = (
            ng.get_nat_gateways(client, 'subnet-123456789', check_mode=True)
        )
        should_return = ng.DRY_RUN_GATEWAYS
        self.assertTrue(success)
        self.assertEqual(stream, should_return)

    def test_get_nat_gateways_no_gateways_found(self):
        client = boto3.client('ec2', region_name=aws_region)
        success, err_msg, stream = (
            ng.get_nat_gateways(client, 'subnet-1234567', check_mode=True)
        )
        self.assertTrue(success)
        self.assertEqual(stream, [])

    def test_wait_for_status(self):
        client = boto3.client('ec2', region_name=aws_region)
        success, err_msg, gws = (
            ng.wait_for_status(
                client, 5, 'nat-123456789', 'available', check_mode=True
            )
        )
        should_return = ng.DRY_RUN_GATEWAYS[0]
        self.assertTrue(success)
        self.assertEqual(gws, should_return)

    def test_wait_for_status_to_timeout(self):
        client = boto3.client('ec2', region_name=aws_region)
        success, err_msg, gws = (
            ng.wait_for_status(
                client, 2, 'nat-12345678', 'available', check_mode=True
            )
        )
        self.assertFalse(success)
        self.assertEqual(gws, {})

    def test_gateway_in_subnet_exists_with_allocation_id(self):
        client = boto3.client('ec2', region_name=aws_region)
        gws, err_msg = (
            ng.gateway_in_subnet_exists(
                client, 'subnet-123456789', 'eipalloc-1234567', check_mode=True
            )
        )
        should_return = ng.DRY_RUN_GATEWAYS
        self.assertEqual(gws, should_return)

    def test_gateway_in_subnet_exists_with_allocation_id_does_not_exist(self):
        client = boto3.client('ec2', region_name=aws_region)
        gws, err_msg = (
            ng.gateway_in_subnet_exists(
                client, 'subnet-123456789', 'eipalloc-123', check_mode=True
            )
        )
        should_return = list()
        self.assertEqual(gws, should_return)

    def test_gateway_in_subnet_exists_without_allocation_id(self):
        client = boto3.client('ec2', region_name=aws_region)
        gws, err_msg = (
            ng.gateway_in_subnet_exists(
                client, 'subnet-123456789', check_mode=True
            )
        )
        should_return = ng.DRY_RUN_GATEWAYS
        self.assertEqual(gws, should_return)

    def test_get_eip_allocation_id_by_address(self):
        client = boto3.client('ec2', region_name=aws_region)
        allocation_id, _ = (
            ng.get_eip_allocation_id_by_address(
                client, '55.55.55.55', check_mode=True
            )
        )
        should_return = 'eipalloc-1234567'
        self.assertEqual(allocation_id, should_return)

    def test_get_eip_allocation_id_by_address_does_not_exist(self):
        client = boto3.client('ec2', region_name=aws_region)
        allocation_id, err_msg = (
            ng.get_eip_allocation_id_by_address(
                client, '52.52.52.52', check_mode=True
            )
        )
        self.assertEqual(err_msg, 'EIP 52.52.52.52 does not exist')
        self.assertTrue(allocation_id is None)

    def test_allocate_eip_address(self):
        client = boto3.client('ec2', region_name=aws_region)
        success, err_msg, eip_id = (
            ng.allocate_eip_address(
                client, check_mode=True
            )
        )
        self.assertTrue(success)

    def test_release_address(self):
        client = boto3.client('ec2', region_name=aws_region)
        success, _ = (
            ng.release_address(
                client, 'eipalloc-1234567', check_mode=True
            )
        )
        self.assertTrue(success)

    def test_create(self):
        client = boto3.client('ec2', region_name=aws_region)
        success, changed, err_msg, results = (
            ng.create(
                client, 'subnet-123456', 'eipalloc-1234567', check_mode=True
            )
        )
        self.assertTrue(success)
        self.assertTrue(changed)

    def test_pre_create(self):
        client = boto3.client('ec2', region_name=aws_region)
        success, changed, err_msg, results = (
            ng.pre_create(
                client, 'subnet-123456', check_mode=True
            )
        )
        self.assertTrue(success)
        self.assertTrue(changed)

    def test_pre_create_idemptotent_with_allocation_id(self):
        client = boto3.client('ec2', region_name=aws_region)
        success, changed, err_msg, results = (
            ng.pre_create(
                client, 'subnet-123456789', allocation_id='eipalloc-1234567', check_mode=True
            )
        )
        self.assertTrue(success)
        self.assertFalse(changed)

    def test_pre_create_idemptotent_with_eip_address(self):
        client = boto3.client('ec2', region_name=aws_region)
        success, changed, err_msg, results = (
            ng.pre_create(
                client, 'subnet-123456789', eip_address='55.55.55.55', check_mode=True
            )
        )
        self.assertTrue(success)
        self.assertFalse(changed)

    def test_pre_create_idemptotent_if_exist_do_not_create(self):
        client = boto3.client('ec2', region_name=aws_region)
        success, changed, err_msg, results = (
            ng.pre_create(
                client, 'subnet-123456789', if_exist_do_not_create=True, check_mode=True
            )
        )
        self.assertTrue(success)
        self.assertFalse(changed)

    def test_delete(self):
        client = boto3.client('ec2', region_name=aws_region)
        success, changed, err_msg, _ = (
            ng.remove(
                client, 'nat-123456789', check_mode=True
            )
        )
        self.assertTrue(success)
        self.assertTrue(changed)

    def test_delete_and_release_ip(self):
        client = boto3.client('ec2', region_name=aws_region)
        success, changed, err_msg, _ = (
            ng.remove(
                client, 'nat-123456789', release_eip=True, check_mode=True
            )
        )
        self.assertTrue(success)
        self.assertTrue(changed)

    def test_delete_if_does_not_exist(self):
        client = boto3.client('ec2', region_name=aws_region)
        success, changed, err_msg, _ = (
            ng.remove(
                client, 'nat-12345', check_mode=True
            )
        )
        self.assertFalse(success)
        self.assertFalse(changed)
