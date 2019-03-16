# Copyright: (c) 2019, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import json

import pytest

from ansible.modules.cloud.misc import terraform
from units.modules.utils import set_module_args


def test_terraform_without_argument(capfd):
    set_module_args({})
    with pytest.raises(SystemExit) as results:
        terraform.main()

    out, err = capfd.readouterr()
    assert not err
    assert json.loads(out)['failed']
    assert 'project_path' in json.loads(out)['msg']



@pytest.fixture
def project_path():
    return "terraform_modules/module_tc_0_0_no_config"


testdataPath = [
    ("/tmp/testplan.tfpalan", "/tmp/testplan.tfpalan"),
    ("testplan.tfpalan", "terraform_modules/module_tc_0_0_no_config/testplan.tfpalan"),

]
@pytest.mark.parametrize("path,expectedOsCheckPath", testdataPath)
def test_file_path_handling(project_path, path, expectedOsCheckPath):
    assert expectedOsCheckPath == terraform.convertOsLookupPath(path, project_path)


testdata = [
    ("1", '"1"'),
    (1, '"1"'),
    ([1], '["1"]'),
    ([1, 2, 3], '["1","2","3"]'),
    (["1", "2", "3"], '["1","2","3"]'),
    ({'content': 'myExample'}, '{ content = "myExample" }'),
    ({'content': 'myExample', 'target_name': '/tmp/test.txt'}, '{ content = "myExample", target_name = "/tmp/test.txt" }')
]
@pytest.mark.parametrize("varValue,expected", testdata)
def test_convert_vars_to_commandline_structure(varValue, expected):
    assert expected == terraform.convertPythonVarValueToTerraformVarCommandlineParameter(varValue)
