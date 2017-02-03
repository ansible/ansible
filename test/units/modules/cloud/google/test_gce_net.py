#!/usr/bin/env python

import unittest

from ansible.modules.cloud.google.gce_net import format_allowed_section, format_allowed, sorted_allowed_list


class TestGCENet(unittest.TestCase):
    """Unit test for gce_net module."""
    str_sample_input_section = ('tcp:80,22', 'icmp', 'udp:8080')
    str_sample_input = ';'.join(str_sample_input_section)
    obj_sample_output = [{'IPProtocol': 'tcp', 'ports': ['80', '22']},
                         {'IPProtocol': 'icmp'},
                         {'IPProtocol': 'udp', 'ports': ['8080']}]
    obj_sample_output_sorted = [{'IPProtocol': 'icmp'},
                                {'IPProtocol': 'tcp', 'ports': ['22', '80']},
                                {'IPProtocol': 'udp', 'ports': ['8080']}]

    def test_format_allowed_section(self):
        """
        Split protocol:port sections, which are divided by semicolon (;)
        """
        want = self.obj_sample_output[0]
        got = format_allowed_section(self.str_sample_input_section[0])
        self.assertDictEqual(want, got)

        want = self.obj_sample_output[1]
        got = format_allowed_section(self.str_sample_input_section[1])
        self.assertDictEqual(want, got)

        want = self.obj_sample_output[2]
        got = format_allowed_section(self.str_sample_input_section[2])
        self.assertDictEqual(want, got)

    def test_format_allowed(self):
        """
        Find and extract protocol and port from the splitted allowed protocol string
        """
        want = self.obj_sample_output
        got = format_allowed(self.str_sample_input)
        self.assertEqual(want, got)

    def test_sorted_allowed_list(self):
        """
        Sort the well-formed allowed protocol and port string
        """
        want = self.obj_sample_output_sorted
        got = sorted_allowed_list(format_allowed(self.str_sample_input))
        self.assertEqual(want, got)

if __name__ == "__main__":
    unittest.main()
