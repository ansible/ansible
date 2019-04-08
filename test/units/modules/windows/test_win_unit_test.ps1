# Copyright: (c) 2019, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Load the win_unit_test module functions
.(Find-AnsibleModule -Name $MyInvocation.MyCommand.Name.Substring(5))

Describe "Testing win_unit_test" {
    It "Gets correct result" {
        $actual = Test-Function
        $actual | Should -Be "abc"
    }
}
