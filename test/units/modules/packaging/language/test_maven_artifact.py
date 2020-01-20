# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import pytest

from ansible.modules.packaging.language import maven_artifact
from ansible.module_utils import basic


pytestmark = pytest.mark.usefixtures('patch_ansible_module')

maven_metadata_example = b"""<?xml version="1.0" encoding="UTF-8"?>
<metadata>
   <groupId>junit</groupId>
   <artifactId>junit</artifactId>
   <versioning>
      <latest>4.13-beta-2</latest>
      <release>4.13-beta-2</release>
      <versions>
         <version>3.7</version>
         <version>3.8</version>
         <version>3.8.1</version>
         <version>3.8.2</version>
         <version>4.0</version>
         <version>4.1</version>
         <version>4.2</version>
         <version>4.3</version>
         <version>4.3.1</version>
         <version>4.4</version>
         <version>4.5</version>
         <version>4.6</version>
         <version>4.7</version>
         <version>4.8</version>
         <version>4.8.1</version>
         <version>4.8.2</version>
         <version>4.9</version>
         <version>4.10</version>
         <version>4.11-beta-1</version>
         <version>4.11</version>
         <version>4.12-beta-1</version>
         <version>4.12-beta-2</version>
         <version>4.12-beta-3</version>
         <version>4.12</version>
         <version>4.13-beta-1</version>
         <version>4.13-beta-2</version>
      </versions>
      <lastUpdated>20190202141051</lastUpdated>
   </versioning>
</metadata>
"""


@pytest.mark.parametrize('patch_ansible_module, version_by_spec, version_choosed', [
    (None, "(,3.9]", "3.8.2"),
    (None, "3.0", "3.8.2"),
    (None, "[3.7]", "3.7"),
    (None, "[4.10, 4.12]", "4.12"),
    (None, "[4.10, 4.12)", "4.11"),
    (None, "[2.0,)", "4.13-beta-2"),
])
def test_find_version_by_spec(mocker, version_by_spec, version_choosed):
    _getContent = mocker.patch('ansible.modules.packaging.language.maven_artifact.MavenDownloader._getContent')
    _getContent.return_value = maven_metadata_example

    artifact = maven_artifact.Artifact("junit", "junit", None, version_by_spec, "jar")
    mvn_downloader = maven_artifact.MavenDownloader(basic.AnsibleModule, "https://repo1.maven.org/maven2")

    assert mvn_downloader.find_version_by_spec(artifact) == version_choosed
