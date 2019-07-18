#!/usr/bin/env python3.8

from ansible.cli.adhoc import AdHocCLI


def test_simple_command():
    """ Test valid command and its run"""
    adhoc_cli = AdHocCLI(['/bin/ansible', '-m', 'command', 'localhost', '-a', 'echo "hi"'])
    adhoc_cli.parse()
    adhoc_cli.run()


if __name__ == '__main__':
    test_simple_command()
