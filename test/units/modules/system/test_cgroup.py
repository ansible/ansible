from ansible.compat.tests import unittest

from ansible.modules.system.cgroup import parse_config, generate_config_file_content


class CGroupTestCase(unittest.TestCase):

    def test_parse_config_nice_format(self):
        name = 'mycgroup'
        limit = '3G'
        config_to_parse = [
            '# This could be any commentary and should be ignored whichever line it is found in.',
            'cgroup ' + name + ' {',
            '# This could be any commentary and should be ignored whichever line it is found in.',
            '\tmemory {',
            '# This could be any commentary and should be ignored whichever line it is found in.',
            '\t\tmemory.limit_in_bytes = ' + limit + ' ;',
            '# This could be any commentary and should be ignored whichever line it is found in.',
            '\t}',
            '# This could be any commentary and should be ignored whichever line it is found in.',
            '}',
            '# This could be any commentary and should be ignored whichever line it is found in.'
        ]
        expected = {
            name: {
                'memory': {
                    'memory.limit_in_bytes': limit
                }
            }
        }
        actual = parse_config('\n'.join(config_to_parse))
        self.assertEqual(actual, expected)

    def test_parse_config_ugly_format(self):
        name = 'mycgroup'
        limit = '3G'
        config_to_parse = [
            'cgroup ' + name + '{memory{memory.limit_in_bytes=' + limit + ';}}'
        ]
        expected = {
            name: {
                'memory': {
                    'memory.limit_in_bytes': limit
                }
            }
        }
        actual = parse_config('\n'.join(config_to_parse))
        self.assertEqual(actual, expected)
