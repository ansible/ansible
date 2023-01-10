#!powershell
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#AnsibleRequires -CSharpUtil Ansible.Basic

throw "test inner error message"

$module = [Ansible.Basic.AnsibleModule]::Create($args, @{
        options = @{
            test = @{ type = 'str'; choices = @('foo', 'bar'); default = 'foo' }
        }
    })

$module.Result.test = 'abc'

$module.ExitJson()
