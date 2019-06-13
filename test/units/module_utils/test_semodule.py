import ansible.module_utils.semodule as semodule

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

def test_parse_pol_info():
    cur_pol = semodule.parse_pol_info('usbmuxd', SEMODULE_OUTPUT)
    assert cur_pol['name'] == 'usbmuxd'
    assert cur_pol['version'] == '1.2.0'
