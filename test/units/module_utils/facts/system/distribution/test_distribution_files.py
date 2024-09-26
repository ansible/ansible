# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import tempfile


from ansible.module_utils.facts.system.distribution import DistributionFiles


def test_distribution_files(mock_module):
    d = DistributionFiles(mock_module)
    temp_dir = tempfile.TemporaryDirectory()
    dist_file, dist_file_content = d._get_dist_file_content(temp_dir.name)
    assert not dist_file
    assert dist_file_content is None
