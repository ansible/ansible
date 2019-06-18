import ansible.module_utils.semodule as semodule
import pytest

SEMODULE_OUTPUT = '''unconfined\t3.5.0
unconfineduser\t1.0.0
unlabelednet\t1.0.0
unprivuser\t2.4.0
updfstab\t1.6.0
usbmodules\t1.3.0
usbmuxd\t1.2.0
userdomain\t4.9.1
userhelper\t1.8.1
usermanage\t1.19.0
usernetctl\t1.7.0
'''
SEMODULE_OUTPUT_NO_VER = '''unconfined
unconfineduser
unlabelednet
unprivuser
updfstab
usbmodules
usbmuxd
userdomain
userhelper
usermanage
usernetctl
'''


@pytest.mark.parametrize('output', [
    (SEMODULE_OUTPUT),
    (SEMODULE_OUTPUT_NO_VER)]
)
def test_parse_pol_info(output):
    cur_pol = semodule.parse_pol_info('usbmuxd', SEMODULE_OUTPUT)
    assert cur_pol['name'] == 'usbmuxd'
