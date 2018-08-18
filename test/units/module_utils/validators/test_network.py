# Copyright: 2018, Adam Stevko <adam.stevko@gmail.com>
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause )

import unittest

from ansible.module_utils.validators.network import (
    check_type_port,
    check_type_l3_proto,
    check_type_l4_proto,
    check_type_l7_proto,
    check_type_ipaddr,
)


class NetworkValidatorTest(unittest.TestCase):

    def test_port(self):
        self.assertTrue(check_type_port(0), 0)
        self.assertTrue(check_type_port(22), 22)

        self.assertRaises(ValueError, check_type_port(-123))
        self.assertRaises(ValueError, check_type_port(-123.0))
        self.assertRaises(ValueError, check_type_port(70000))
        self.assertRaises(ValueError, check_type_port(123.0))
        self.assertRaises(ValueError, check_type_port("123"))
        self.assertRaises(ValueError, check_type_port("invalid_input"))

    def test_ipaddr(self):
        # IPv4
        self.assertTrue(check_type_ipaddr("127.0.0.1"), "127.0.0.1")
        self.assertTrue(check_type_ipaddr("127.0.0.1/255.0.0.0"), "127.0.0.1")
        self.assertTrue(check_type_ipaddr("127.0.0.1/8"), "127.0.0.1")

        self.assertRaises(ValueError, check_type_ipaddr("267.0.0.1"))
        self.assertRaises(ValueError, check_type_ipaddr("127.0.0.1/256.0.0.0"))
        self.assertRaises(ValueError, check_type_ipaddr("127.0.0.1/64"))
        self.assertRaises(ValueError, check_type_ipaddr("invalid_input"))

        # IPv6
        self.assertTrue(check_type_ipaddr("::1"), "::1")
        self.assertTrue(check_type_ipaddr("::1/128"), "::1")

        self.assertRaises(ValueError, check_type_ipaddr("fg80::1"))
        self.assertRaises(ValueError, check_type_ipaddr("fe80::1/129"))

    def test_l3_proto(self):
        self.assertTrue(check_type_l3_proto("ip"), "ip")

        self.assertRaises(ValueError, check_type_l3_proto("IP"))
        self.assertRaises(ValueError, check_type_l3_proto(6))

    def test_l4_proto(self):
        self.assertTrue(check_type_l4_proto("tpp"), "tcp")

        self.assertRaises(ValueError, check_type_l4_proto("tcpa"))
        self.assertRaises(ValueError, check_type_l4_proto(6))

    def test_l7_proto(self):
        self.assertTrue(check_type_l7_proto("domain"), "domain")

        self.assertRaises(ValueError, check_type_l7_proto("DOMAIN"))
        self.assertRaises(ValueError, check_type_l7_proto(53))
