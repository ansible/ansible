from ansible.compat.tests import unittest

from ansible.modules.files.match import find_from_content


class MatchTestCase(unittest.TestCase):

    def test_no_match(self):
        result = find_from_content(r'[Aa]+rdvark', "nothing here\nshould match\nthe given\nregular expression\n")
        self.assertEqual(result, [])

    def test_no_capture(self):
        result = find_from_content(r'[Aa]+rdvark', "aardvark\nbeetle\ncheetah\ndoormouse\nechidna\n")
        self.assertEqual(result, [{"groups": (), "named_groups": {}}])

    def test_unnamed_groups(self):
        sudoers_file = """
        root    ALL=(ALL:ALL) ALL
        %admin  ALL=(ALL)     ALL
        %sudo   ALL=(ALL:ALL) ALL
        jdoe    ALL=(ALL)     NOPASSWD:ALL
        """

        result = find_from_content(r'^[ \t\f\v]*(\S+)(?:[ \t\f\v]+\S*)+NOPASSWD:ALL', sudoers_file)
        self.assertEqual(result, [{"groups": ("jdoe",), "named_groups": {}}])

    def test_named_groups(self):
        # example of a hosts file
        hosts_file = """
        127.0.0.1\tlocalhost

        # some kinda comment
        ::1\tip6-localhost\tip6-loopback
        fe00::0\tip6-localnet
        ff00::0\tip6-mcastprefix
        ff02::1\tip6-allnodes
        ff02::2\tip6-allrouters
        ff02::3\tip6-allhosts
        127.0.1.1\tlocalhost.localdomain\tlocalhost
        """

        result = find_from_content(r'^[ \t\f\v]*(?P<address>[a-f\d.:]+)[ \t\f\v]*(?P<hostnames>(?:\S+[ \t\f\v]*)+)', hosts_file)
        self.assertEqual(result, [
            {
                "groups": ("127.0.0.1", "localhost"),
                "named_groups": {"address": "127.0.0.1", "hostnames": "localhost"}
            },
            {
                "groups": ("::1", "ip6-localhost\tip6-loopback"),
                "named_groups": {"address": "::1", "hostnames": "ip6-localhost\tip6-loopback"}
            },
            {
                "groups": ("fe00::0", "ip6-localnet"),
                "named_groups": {"address": "fe00::0", "hostnames": "ip6-localnet"}
            },
            {
                "groups": ("ff00::0", "ip6-mcastprefix"),
                "named_groups": {"address": "ff00::0", "hostnames": "ip6-mcastprefix"}
            },
            {
                "groups": ("ff02::1", "ip6-allnodes"),
                "named_groups": {"address": "ff02::1", "hostnames": "ip6-allnodes"}
            },
            {
                "groups": ("ff02::2", "ip6-allrouters"),
                "named_groups": {"address": "ff02::2", "hostnames": "ip6-allrouters"}
            },
            {
                "groups": ("ff02::3", "ip6-allhosts"),
                "named_groups": {"address": "ff02::3", "hostnames": "ip6-allhosts"}
            },
            {
                "groups": ("127.0.1.1", "localhost.localdomain\tlocalhost"),
                "named_groups": {"address": "127.0.1.1", "hostnames": "localhost.localdomain\tlocalhost"}
            }
        ])
