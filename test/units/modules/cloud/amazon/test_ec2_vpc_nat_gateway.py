import pytest
import unittest

import ansible.modules.cloud.amazon.ec2_vpc_nat_gateway as ng


boto3 = pytest.importorskip("boto3")
botocore = pytest.importorskip("botocore")

aws_region = 'us-west-2'


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
