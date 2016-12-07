import collections
import os
import unittest

from ansible.modules.cloud.docker._docker import get_split_image_tag

class DockerSplitImageTagTestCase(unittest.TestCase):

    def test_trivial(self):
        self.assertEqual(get_split_image_tag('test'), ('test', 'latest'))

    def test_with_org_name(self):
        self.assertEqual(get_split_image_tag('ansible/centos7-ansible'), ('ansible/centos7-ansible', 'latest'))

    def test_with_tag(self):
        self.assertEqual(get_split_image_tag('test:devel'), ('test', 'devel'))

    def test_with_tag_and_org_name(self):
        self.assertEqual(get_split_image_tag('ansible/centos7-ansible:devel'), ('ansible/centos7-ansible', 'devel'))
