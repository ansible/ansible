#!/usr/bin/env python
from __future__ import annotations

import subprocess
import unittest


class OptionsTest(unittest.TestCase):
    options = (
        'unsupported',
        'disabled',
        'unstable',
        'destructive',
    )

    def test_options(self):
        for option in self.options:
            with self.subTest(option=option):
                try:
                    command = ['ansible-test', 'integration', '--list-targets']

                    skip_all = subprocess.run([*command, f'{option}_a', f'{option}_b'], text=True, capture_output=True, check=True)
                    allow_all = subprocess.run([*command, f'--allow-{option}', f'{option}_a', f'{option}_b'], text=True, capture_output=True, check=True)
                    allow_first = subprocess.run([*command, f'{option}/{option}_a', f'{option}_b'], text=True, capture_output=True, check=True)
                    allow_last = subprocess.run([*command, f'{option}_a', f'{option}/{option}_b'], text=True, capture_output=True, check=True)

                    self.assertEqual(skip_all.stdout.splitlines(), [])
                    self.assertEqual(allow_all.stdout.splitlines(), [f'{option}_a', f'{option}_b'])
                    self.assertEqual(allow_first.stdout.splitlines(), [f'{option}_a'])
                    self.assertEqual(allow_last.stdout.splitlines(), [f'{option}_b'])
                except subprocess.CalledProcessError as ex:
                    raise Exception(f'{ex}:\n>>> Standard Output:\n{ex.stdout}\n>>> Standard Error:\n{ex.stderr}') from ex


class PrefixesTest(unittest.TestCase):
    def test_prefixes(self):
        try:
            command = ['ansible-test', 'integration', '--list-targets']

            something = subprocess.run([*command, 'something/'], text=True, capture_output=True, check=True)

            self.assertEqual(something.stdout.splitlines(), ['one-part_test', 'two_part_test'])
        except subprocess.CalledProcessError as ex:
            raise Exception(f'{ex}:\n>>> Standard Output:\n{ex.stdout}\n>>> Standard Error:\n{ex.stderr}') from ex


if __name__ == '__main__':
    unittest.main()
