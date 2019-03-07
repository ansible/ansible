# -*- coding: utf-8 -*-
#
# Copyright: (c) 2019, Rob Huelga (@RobW3LGA)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


import pytest

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.aci.aci import ACIModule, aci_argument_spec


@pytest.mark.usefixtures('setup')
class TestReference_AnsibleModule_Construct_Url_1(object):

    @pytest.fixture(scope='class')
    def params(self):

        return {
            'tenant': None,
            'descr': None,
            'state': 'query'
        }

    def testRootP01(self, setup, params):

        params['state'] = 'present'
        module = setup
        module.params.update(params)
        sut = ACIModule(module)
        tenant = 'Test-Tenant'

        sut.construct_url(
            root_class=dict(
                aci_class='fvTenant',
                aci_rn='tn-{0}'.format(tenant),
                target_filter={'name': tenant},
                module_object=tenant
            )
        )

        assert 'https://local.host.local:443/api/mo/uni/tn-Test-Tenant.json' == sut.url
        assert '?rsp-prop-include=config-only' == sut.filter_string

    def testRootA01(self, setup, params):

        params['state'] = 'absent'
        module = setup
        module.params.update(params)
        sut = ACIModule(module)
        tenant = 'Test-Tenant'

        sut.construct_url(
            root_class=dict(
                aci_class='fvTenant',
                aci_rn='tn-{0}'.format(tenant),
                target_filter={'name': tenant},
                module_object=tenant
            )
        )

        assert 'https://local.host.local:443/api/mo/uni/tn-Test-Tenant.json' == sut.url
        assert '?rsp-prop-include=config-only' == sut.filter_string

    def testRootQ01(self, setup, params):

        params['state'] = 'query'
        module = setup
        module.params.update(params)
        sut = ACIModule(module)
        tenant = None

        sut.construct_url(
            root_class=dict(
                aci_class='fvTenant',
                aci_rn='tn-{0}'.format(tenant),
                target_filter={'name': tenant},
                module_object=tenant
            )
        )

        assert 'https://local.host.local:443/api/class/fvTenant.json' == sut.url
        assert '' == sut.filter_string

    def testRootQ02(self, setup, params):

        params['state'] = 'query'
        module = setup
        module.params.update(params)
        sut = ACIModule(module)
        tenant = 'Test-Tenant'

        sut.construct_url(
            root_class=dict(
                aci_class='fvTenant',
                aci_rn='tn-{0}'.format(tenant),
                target_filter={'name': tenant},
                module_object=tenant
            )
        )

        assert 'https://local.host.local:443/api/mo/uni/tn-Test-Tenant.json' == sut.url
        assert '' == sut.filter_string


@pytest.mark.usefixtures('setup')
class TestReference_AnsibleModule_Construct_Url_2(object):

    @pytest.fixture(scope='class')
    def params(self):

        return {
            'tenant': None,
            'ap': None,
            'descr': None,
            'state': 'query'
        }

    def testChildP01(self, setup, params):

        params['state'] = 'present'
        module = setup
        module.params.update(params)
        sut = ACIModule(module)
        tenant = 'Test-Tenant'
        ap = 'Test-Ap'

        sut.construct_url(
            root_class=dict(
                aci_class='fvTenant',
                aci_rn='tn-{0}'.format(tenant),
                target_filter={'name': tenant},
                module_object=tenant
            ),
            subclass_1=dict(
                aci_class='fvAp',
                aci_rn='ap-{0}'.format(ap),
                target_filter={'name': ap},
                module_object=ap
            )
        )

        assert 'https://local.host.local:443/api/mo/uni/tn-Test-Tenant/ap-Test-Ap.json' == sut.url
        assert '?rsp-prop-include=config-only' == sut.filter_string

    def testChildA01(self, setup, params):

        params['state'] = 'absent'
        module = setup
        module.params.update(params)
        sut = ACIModule(module)
        tenant = 'Test-Tenant'
        ap = 'Test-Ap'

        sut.construct_url(
            root_class=dict(
                aci_class='fvTenant',
                aci_rn='tn-{0}'.format(tenant),
                target_filter={'name': tenant},
                module_object=tenant
            ),
            subclass_1=dict(
                aci_class='fvAp',
                aci_rn='ap-{0}'.format(ap),
                target_filter={'name': ap},
                module_object=ap
            )
        )

        assert 'https://local.host.local:443/api/mo/uni/tn-Test-Tenant/ap-Test-Ap.json' == sut.url
        assert '?rsp-prop-include=config-only' == sut.filter_string

    def testChildQ01(self, setup, params):

        params['state'] = 'query'
        module = setup
        module.params.update(params)
        sut = ACIModule(module)
        tenant = None
        ap = None

        sut.construct_url(
            root_class=dict(
                aci_class='fvTenant',
                aci_rn='tn-{0}'.format(tenant),
                target_filter={'name': tenant},
                module_object=tenant
            ),
            subclass_1=dict(
                aci_class='fvAp',
                aci_rn='ap-{0}'.format(ap),
                target_filter={'name': ap},
                module_object=ap
            )
        )

        assert 'https://local.host.local:443/api/class/fvAp.json' == sut.url
        assert '' == sut.filter_string

    def testChildQ02(self, setup, params):

        params['state'] = 'query'
        module = setup
        module.params.update(params)
        sut = ACIModule(module)
        tenant = 'Test-Tenant'
        ap = None

        sut.construct_url(
            root_class=dict(
                aci_class='fvTenant',
                aci_rn='tn-{0}'.format(tenant),
                target_filter={'name': tenant},
                module_object=tenant
            ),
            subclass_1=dict(
                aci_class='fvAp',
                aci_rn='ap-{0}'.format(ap),
                target_filter={'name': ap},
                module_object=ap
            )
        )

        assert 'https://local.host.local:443/api/mo/uni/tn-Test-Tenant.json' == sut.url
        assert '?rsp-subtree=full&rsp-subtree-class=fvAp' == sut.filter_string

    def testChildQ03(self, setup, params):

        params['state'] = 'query'
        module = setup
        module.params.update(params)
        sut = ACIModule(module)
        tenant = None
        ap = 'Test-Ap'

        sut.construct_url(
            root_class=dict(
                aci_class='fvTenant',
                aci_rn='tn-{0}'.format(tenant),
                target_filter={'name': tenant},
                module_object=tenant
            ),
            subclass_1=dict(
                aci_class='fvAp',
                aci_rn='ap-{0}'.format(ap),
                target_filter={'name': ap},
                module_object=ap
            )
        )

        assert 'https://local.host.local:443/api/class/fvAp.json' == sut.url
        assert '?query-target-filter=eq%28fvAp.name%2C+%22Test-Ap%22%29' == sut.filter_string

        sut = None

    def testChildQ04(self, setup, params):

        params['state'] = 'query'
        module = setup
        module.params.update(params)
        sut = ACIModule(module)
        tenant = 'Test-Tenant'
        ap = 'Test-Ap'

        sut.construct_url(
            root_class=dict(
                aci_class='fvTenant',
                aci_rn='tn-{0}'.format(tenant),
                target_filter={'name': tenant},
                module_object=tenant
            ),
            subclass_1=dict(
                aci_class='fvAp',
                aci_rn='ap-{0}'.format(ap),
                target_filter={'name': ap},
                module_object=ap
            )
        )

        assert 'https://local.host.local:443/api/mo/uni/tn-Test-Tenant/ap-Test-Ap.json' == sut.url
        assert '' == sut.filter_string


@pytest.mark.usefixtures('setup')
class TestReference_AnsibleModule_Construct_Url_3(object):

    @pytest.fixture(scope='class')
    def params(self):

        return {
            'tenant': None,
            'descr': None,
            'state': 'query'
        }

    def testGrandChildP01(self, setup, params):

        params['state'] = 'present'
        module = setup
        module.params.update(params)
        sut = ACIModule(module)
        tenant = 'Test-Tenant'
        ap = 'Test-Ap'
        aepg = 'Test-Epg'

        sut.construct_url(
            root_class=dict(
                aci_class='fvTenant',
                aci_rn='tn-{0}'.format(tenant),
                target_filter={'name': tenant},
                module_object=tenant
            ),
            subclass_1=dict(
                aci_class='fvAp',
                aci_rn='ap-{0}'.format(ap),
                target_filter={'name': ap},
                module_object=ap
            ),
            subclass_2=dict(
                aci_class='fvAEPg',
                aci_rn='epg-{0}'.format(aepg),
                target_filter={'name': aepg},
                module_object=aepg
            ),
            child_classes=['fvRsBd']
        )

        assert 'https://local.host.local:443/api/mo/uni/tn-Test-Tenant/ap-Test-Ap/epg-Test-Epg.json' == sut.url
        assert '?rsp-prop-include=config-only&rsp-subtree=full&rsp-subtree-class=fvRsBd' == sut.filter_string

    def testGrandChildA01(self, setup, params):

        params['state'] = 'absent'
        module = setup
        module.params.update(params)
        sut = ACIModule(module)
        tenant = 'Test-Tenant'
        ap = 'Test-Ap'
        aepg = 'Test-Epg'

        sut.construct_url(
            root_class=dict(
                aci_class='fvTenant',
                aci_rn='tn-{0}'.format(tenant),
                target_filter={'name': tenant},
                module_object=tenant
            ),
            subclass_1=dict(
                aci_class='fvAp',
                aci_rn='ap-{0}'.format(ap),
                target_filter={'name': ap},
                module_object=ap
            ),
            subclass_2=dict(
                aci_class='fvAEPg',
                aci_rn='epg-{0}'.format(aepg),
                target_filter={'name': aepg},
                module_object=aepg
            ),
            child_classes=['fvRsBd']
        )

        assert 'https://local.host.local:443/api/mo/uni/tn-Test-Tenant/ap-Test-Ap/epg-Test-Epg.json' == sut.url
        assert '?rsp-prop-include=config-only&rsp-subtree=full&rsp-subtree-class=fvRsBd' == sut.filter_string

    def testGrandChildQ01(self, setup, params):

        params['state'] = 'query'
        module = setup
        module.params.update(params)
        sut = ACIModule(module)
        tenant = None
        ap = None
        aepg = None

        sut.construct_url(
            root_class=dict(
                aci_class='fvTenant',
                aci_rn='tn-{0}'.format(tenant),
                target_filter={'name': tenant},
                module_object=tenant
            ),
            subclass_1=dict(
                aci_class='fvAp',
                aci_rn='ap-{0}'.format(ap),
                target_filter={'name': ap},
                module_object=ap
            ),
            subclass_2=dict(
                aci_class='fvAEPg',
                aci_rn='epg-{0}'.format(aepg),
                target_filter={'name': aepg},
                module_object=aepg
            ),
            child_classes=['fvRsBd']
        )

        assert 'https://local.host.local:443/api/class/fvAEPg.json' == sut.url
        assert '?rsp-subtree=full&rsp-subtree-class=fvRsBd' == sut.filter_string

    def testGrandChildQ02(self, setup, params):

        params['state'] = 'query'
        module = setup
        module.params.update(params)
        sut = ACIModule(module)
        tenant = 'Test-Tenant'
        ap = None
        aepg = None

        sut.construct_url(
            root_class=dict(
                aci_class='fvTenant',
                aci_rn='tn-{0}'.format(tenant),
                target_filter={'name': tenant},
                module_object=tenant
            ),
            subclass_1=dict(
                aci_class='fvAp',
                aci_rn='ap-{0}'.format(ap),
                target_filter={'name': ap},
                module_object=ap
            ),
            subclass_2=dict(
                aci_class='fvAEPg',
                aci_rn='epg-{0}'.format(aepg),
                target_filter={'name': aepg},
                module_object=aepg
            ),
            child_classes=['fvRsBd']
        )

        assert 'https://local.host.local:443/api/mo/uni/tn-Test-Tenant.json' == sut.url
        assert '?rsp-subtree=full&rsp-subtree-class=fvAEPg%2CfvAp%2CfvRsBd' == sut.filter_string

    def testGrandChildQ03(self, setup, params):

        params['state'] = 'query'
        module = setup
        module.params.update(params)
        sut = ACIModule(module)
        tenant = 'Test-Tenant'
        ap = 'Test-Ap'
        aepg = None

        sut.construct_url(
            root_class=dict(
                aci_class='fvTenant',
                aci_rn='tn-{0}'.format(tenant),
                target_filter={'name': tenant},
                module_object=tenant
            ),
            subclass_1=dict(
                aci_class='fvAp',
                aci_rn='ap-{0}'.format(ap),
                target_filter={'name': ap},
                module_object=ap
            ),
            subclass_2=dict(
                aci_class='fvAEPg',
                aci_rn='epg-{0}'.format(aepg),
                target_filter={'name': aepg},
                module_object=aepg
            ),
            child_classes=['fvRsBd']
        )

        assert 'https://local.host.local:443/api/mo/uni/tn-Test-Tenant/ap-Test-Ap.json' == sut.url
        assert '?rsp-subtree=full&rsp-subtree-class=fvAEPg%2CfvRsBd' == sut.filter_string

    def testGrandChildQ04(self, setup, params):

        params['state'] = 'query'
        module = setup
        module.params.update(params)
        sut = ACIModule(module)
        tenant = 'Test-Tenant'
        ap = 'Test-Ap'
        aepg = 'Test-Epg'

        sut.construct_url(
            root_class=dict(
                aci_class='fvTenant',
                aci_rn='tn-{0}'.format(tenant),
                target_filter={'name': tenant},
                module_object=tenant
            ),
            subclass_1=dict(
                aci_class='fvAp',
                aci_rn='ap-{0}'.format(ap),
                target_filter={'name': ap},
                module_object=ap
            ),
            subclass_2=dict(
                aci_class='fvAEPg',
                aci_rn='epg-{0}'.format(aepg),
                target_filter={'name': aepg},
                module_object=aepg
            ),
            child_classes=['fvRsBd']
        )

        assert 'https://local.host.local:443/api/mo/uni/tn-Test-Tenant/ap-Test-Ap/epg-Test-Epg.json' == sut.url
        assert '?rsp-subtree=full&rsp-subtree-class=fvRsBd' == sut.filter_string

    def testGrandChildQ05(self, setup, params):

        params['state'] = 'query'
        module = setup
        module.params.update(params)
        sut = ACIModule(module)
        tenant = None
        ap = 'Test-Ap'
        aepg = 'Test-Epg'

        sut.construct_url(
            root_class=dict(
                aci_class='fvTenant',
                aci_rn='tn-{0}'.format(tenant),
                target_filter={'name': tenant},
                module_object=tenant
            ),
            subclass_1=dict(
                aci_class='fvAp',
                aci_rn='ap-{0}'.format(ap),
                target_filter={'name': ap},
                module_object=ap
            ),
            subclass_2=dict(
                aci_class='fvAEPg',
                aci_rn='epg-{0}'.format(aepg),
                target_filter={'name': aepg},
                module_object=aepg
            ),
            child_classes=['fvRsBd']
        )

        assert 'https://local.host.local:443/api/class/fvAp.json' == sut.url
        assert '?query-target-filter=eq%28fvAp.name%2C+%22Test-Ap%22%29&rsp-subtree-filter=eq%28fvAEPg.name%2C+%22Test-Epg%22%29', \
            '&rsp-subtree=full&rsp-subtree-class=fvAEPg%2CfvRsBd' == sut.filter_string

    def testGrandChildQ06(self, setup, params):

        params['state'] = 'query'
        module = setup
        module.params.update(params)
        sut = ACIModule(module)
        tenant = None
        ap = None
        aepg = 'Test-Epg'

        sut.construct_url(
            root_class=dict(
                aci_class='fvTenant',
                aci_rn='tn-{0}'.format(tenant),
                target_filter={'name': tenant},
                module_object=tenant
            ),
            subclass_1=dict(
                aci_class='fvAp',
                aci_rn='ap-{0}'.format(ap),
                target_filter={'name': ap},
                module_object=ap
            ),
            subclass_2=dict(
                aci_class='fvAEPg',
                aci_rn='epg-{0}'.format(aepg),
                target_filter={'name': aepg},
                module_object=aepg
            ),
            child_classes=['fvRsBd']
        )

        assert 'https://local.host.local:443/api/class/fvAEPg.json' == sut.url
        assert '?query-target-filter=eq%28fvAEPg.name%2C+%22Test-Epg%22%29&rsp-subtree=full&rsp-subtree-class=fvRsBd' == sut.filter_string

    def testGrandChildQ07(self, setup, params):

        params['state'] = 'query'
        module = setup
        module.params.update(params)
        sut = ACIModule(module)
        tenant = 'Test-Tenant'
        ap = None
        aepg = 'Test-Epg'

        sut.construct_url(
            root_class=dict(
                aci_class='fvTenant',
                aci_rn='tn-{0}'.format(tenant),
                target_filter={'name': tenant},
                module_object=tenant
            ),
            subclass_1=dict(
                aci_class='fvAp',
                aci_rn='ap-{0}'.format(ap),
                target_filter={'name': ap},
                module_object=ap
            ),
            subclass_2=dict(
                aci_class='fvAEPg',
                aci_rn='epg-{0}'.format(aepg),
                target_filter={'name': aepg},
                module_object=aepg
            ),
            child_classes=['fvRsBd']
        )

        assert 'https://local.host.local:443/api/mo/uni/tn-Test-Tenant.json' == sut.url
        assert '?rsp-subtree-filter=eq%28fvAEPg.name%2C+%22Test-Epg%22%29&rsp-subtree=full&rsp-subtree-class=fvAEPg%2CfvRsBd' == sut.filter_string


@pytest.mark.usefixtures('setup')
class TestReference_AnsibleModule_Construct_Url_4(object):

    @pytest.fixture(scope='class')
    def params(self):

        return {
            'tenant': None,
            'out': None,
            'lnodep': None,
            'lifp': None,
            'state': 'query'
        }

    def testGreatGrandChildP01(self, setup, params):

        params['state'] = 'present'
        module = setup
        module.params.update(params)
        sut = ACIModule(module)
        tenant = 'Test-Tenant'
        out = 'Test-L3Out'
        lnodep = 'Test-NodeProfile'
        lifp = 'Test-InterfaceProfile'

        sut.construct_url(
            root_class=dict(
                parent_class='uni',
                aci_class='fvTenant',
                aci_rn='tn-{0}'.format(tenant),
                target_filter={'name': tenant},
                module_object=tenant
            ),
            subclass_1=dict(
                parent_class='fvTenant',
                aci_class='l3extOut',
                aci_rn='out-{0}'.format(out),
                target_filter={'name': out},
                module_object=out
            ),
            subclass_2=dict(
                parent_class='l3extOut',
                aci_class='l3extLNodeP',
                aci_rn='lnodep-{0}'.format(lnodep),
                target_filter={'name': lnodep},
                module_object=lnodep
            ),
            subclass_3=dict(
                parent_class='l3extLNodeP',
                aci_class='l3extLIfP',
                aci_rn='lifp-{0}'.format(lifp),
                target_filter={'name': lifp},
                module_object=lifp
            )
        )

        assert 'https://local.host.local:443/api/mo/uni/tn-Test-Tenant/out-Test-L3Out/lnodep-Test-NodeProfile/lifp-Test-InterfaceProfile.json' == sut.url
        assert '?rsp-prop-include=config-only' == sut.filter_string

    def testGreatGrandChildA01(self, setup, params):

        params['state'] = 'absent'
        module = setup
        module.params.update(params)
        sut = ACIModule(module)
        tenant = 'Test-Tenant'
        out = 'Test-L3Out'
        lnodep = 'Test-NodeProfile'
        lifp = 'Test-InterfaceProfile'

        sut.construct_url(
            root_class=dict(
                parent_class='uni',
                aci_class='fvTenant',
                aci_rn='tn-{0}'.format(tenant),
                target_filter={'name': tenant},
                module_object=tenant
            ),
            subclass_1=dict(
                parent_class='fvTenant',
                aci_class='l3extOut',
                aci_rn='out-{0}'.format(out),
                target_filter={'name': out},
                module_object=out
            ),
            subclass_2=dict(
                parent_class='l3extOut',
                aci_class='l3extLNodeP',
                aci_rn='lnodep-{0}'.format(lnodep),
                target_filter={'name': lnodep},
                module_object=lnodep
            ),
            subclass_3=dict(
                parent_class='l3extLNodeP',
                aci_class='l3extLIfP',
                aci_rn='lifp-{0}'.format(lifp),
                target_filter={'name': lifp},
                module_object=lifp
            )
        )

        assert 'https://local.host.local:443/api/mo/uni/tn-Test-Tenant/out-Test-L3Out/lnodep-Test-NodeProfile/lifp-Test-InterfaceProfile.json' == sut.url
        assert '?rsp-prop-include=config-only' == sut.filter_string

    def testGreatGrandChildQ01(self, setup, params):

        params['state'] = 'query'
        module = setup
        module.params.update(params)
        sut = ACIModule(module)
        tenant = None
        out = None
        lnodep = None
        lifp = None

        sut.construct_url(
            root_class=dict(
                parent_class='uni',
                aci_class='fvTenant',
                aci_rn='tn-{0}'.format(tenant),
                target_filter={'name': tenant},
                module_object=tenant
            ),
            subclass_1=dict(
                parent_class='fvTenant',
                aci_class='l3extOut',
                aci_rn='out-{0}'.format(out),
                target_filter={'name': out},
                module_object=out
            ),
            subclass_2=dict(
                parent_class='l3extOut',
                aci_class='l3extLNodeP',
                aci_rn='lnodep-{0}'.format(lnodep),
                target_filter={'name': lnodep},
                module_object=lnodep
            ),
            subclass_3=dict(
                parent_class='l3extLNodeP',
                aci_class='l3extLIfP',
                aci_rn='lifp-{0}'.format(lifp),
                target_filter={'name': lifp},
                module_object=lifp
            )
        )

        assert 'https://local.host.local:443/api/class/l3extLIfP.json' == sut.url
        assert '?rsp-subtree=full&rsp-subtree-class=l3extLIfP' == sut.filter_string

    def testGreatGrandChildQ02(self, setup, params):

        params['state'] = 'query'
        module = setup
        module.params.update(params)
        sut = ACIModule(module)
        tenant = 'Test-Tenant'
        out = None
        lnodep = None
        lifp = None

        sut.construct_url(
            root_class=dict(
                parent_class='uni',
                aci_class='fvTenant',
                aci_rn='tn-{0}'.format(tenant),
                target_filter={'name': tenant},
                module_object=tenant
            ),
            subclass_1=dict(
                parent_class='fvTenant',
                aci_class='l3extOut',
                aci_rn='out-{0}'.format(out),
                target_filter={'name': out},
                module_object=out
            ),
            subclass_2=dict(
                parent_class='l3extOut',
                aci_class='l3extLNodeP',
                aci_rn='lnodep-{0}'.format(lnodep),
                target_filter={'name': lnodep},
                module_object=lnodep
            ),
            subclass_3=dict(
                parent_class='l3extLNodeP',
                aci_class='l3extLIfP',
                aci_rn='lifp-{0}'.format(lifp),
                target_filter={'name': lifp},
                module_object=lifp
            )
        )

        assert 'https://local.host.local:443/api/mo/uni/tn-Test-Tenant.json' == sut.url
        assert '?rsp-subtree=full&rsp-subtree-class=l3extLIfP' == sut.filter_string

    def testGreatGrandChildQ03(self, setup, params):

        params['state'] = 'query'
        module = setup
        module.params.update(params)
        sut = ACIModule(module)
        tenant = 'Test-Tenant'
        out = 'Test-L3Out'
        lnodep = None
        lifp = None

        sut.construct_url(
            root_class=dict(
                parent_class='uni',
                aci_class='fvTenant',
                aci_rn='tn-{0}'.format(tenant),
                target_filter={'name': tenant},
                module_object=tenant
            ),
            subclass_1=dict(
                parent_class='fvTenant',
                aci_class='l3extOut',
                aci_rn='out-{0}'.format(out),
                target_filter={'name': out},
                module_object=out
            ),
            subclass_2=dict(
                parent_class='l3extOut',
                aci_class='l3extLNodeP',
                aci_rn='lnodep-{0}'.format(lnodep),
                target_filter={'name': lnodep},
                module_object=lnodep
            ),
            subclass_3=dict(
                parent_class='l3extLNodeP',
                aci_class='l3extLIfP',
                aci_rn='lifp-{0}'.format(lifp),
                target_filter={'name': lifp},
                module_object=lifp
            )
        )

        assert 'https://local.host.local:443/api/mo/uni/tn-Test-Tenant/out-Test-L3Out.json' == sut.url
        assert '?rsp-subtree=full&rsp-subtree-class=l3extLIfP' == sut.filter_string

    def testGreatGrandChildQ04(self, setup, params):

        params['state'] = 'query'
        module = setup
        module.params.update(params)
        sut = ACIModule(module)
        tenant = 'Test-Tenant'
        out = 'Test-L3Out'
        lnodep = 'Test-NodeProfile'
        lifp = None

        sut.construct_url(
            root_class=dict(
                parent_class='uni',
                aci_class='fvTenant',
                aci_rn='tn-{0}'.format(tenant),
                target_filter={'name': tenant},
                module_object=tenant
            ),
            subclass_1=dict(
                parent_class='fvTenant',
                aci_class='l3extOut',
                aci_rn='out-{0}'.format(out),
                target_filter={'name': out},
                module_object=out
            ),
            subclass_2=dict(
                parent_class='l3extOut',
                aci_class='l3extLNodeP',
                aci_rn='lnodep-{0}'.format(lnodep),
                target_filter={'name': lnodep},
                module_object=lnodep
            ),
            subclass_3=dict(
                parent_class='l3extLNodeP',
                aci_class='l3extLIfP',
                aci_rn='lifp-{0}'.format(lifp),
                target_filter={'name': lifp},
                module_object=lifp
            )
        )

        assert 'https://local.host.local:443/api/mo/uni/tn-Test-Tenant/out-Test-L3Out/lnodep-Test-NodeProfile.json' == sut.url
        assert '?rsp-subtree=full&rsp-subtree-class=l3extLIfP' == sut.filter_string

    def testGreatGrandChildQ05(self, setup, params):

        params['state'] = 'query'
        module = setup
        module.params.update(params)
        sut = ACIModule(module)
        tenant = 'Test-Tenant'
        out = 'Test-L3Out'
        lnodep = 'Test-NodeProfile'
        lifp = 'Test-InterfaceProfile'

        sut.construct_url(
            root_class=dict(
                parent_class='uni',
                aci_class='fvTenant',
                aci_rn='tn-{0}'.format(tenant),
                target_filter={'name': tenant},
                module_object=tenant
            ),
            subclass_1=dict(
                parent_class='fvTenant',
                aci_class='l3extOut',
                aci_rn='out-{0}'.format(out),
                target_filter={'name': out},
                module_object=out
            ),
            subclass_2=dict(
                parent_class='l3extOut',
                aci_class='l3extLNodeP',
                aci_rn='lnodep-{0}'.format(lnodep),
                target_filter={'name': lnodep},
                module_object=lnodep
            ),
            subclass_3=dict(
                parent_class='l3extLNodeP',
                aci_class='l3extLIfP',
                aci_rn='lifp-{0}'.format(lifp),
                target_filter={'name': lifp},
                module_object=lifp
            )
        )

        assert 'https://local.host.local:443/api/mo/uni/tn-Test-Tenant/out-Test-L3Out/lnodep-Test-NodeProfile/lifp-Test-InterfaceProfile.json' == sut.url
        assert '' == sut.filter_string

    def testGreatGrandChildQ06(self, setup, params):

        params['state'] = 'query'
        module = setup
        module.params.update(params)
        sut = ACIModule(module)
        tenant = None
        out = 'Test-L3Out'
        lnodep = 'Test-NodeProfile'
        lifp = 'Test-InterfaceProfile'

        sut.construct_url(
            root_class=dict(
                parent_class='uni',
                aci_class='fvTenant',
                aci_rn='tn-{0}'.format(tenant),
                target_filter={'name': tenant},
                module_object=tenant
            ),
            subclass_1=dict(
                parent_class='fvTenant',
                aci_class='l3extOut',
                aci_rn='out-{0}'.format(out),
                target_filter={'name': out},
                module_object=out
            ),
            subclass_2=dict(
                parent_class='l3extOut',
                aci_class='l3extLNodeP',
                aci_rn='lnodep-{0}'.format(lnodep),
                target_filter={'name': lnodep},
                module_object=lnodep
            ),
            subclass_3=dict(
                parent_class='l3extLNodeP',
                aci_class='l3extLIfP',
                aci_rn='lifp-{0}'.format(lifp),
                target_filter={'name': lifp},
                module_object=lifp
            )
        )

        assert 'https://local.host.local:443/api/class/l3extLIfP.json' == sut.url
        assert '?query-target-filter=eq%28l3extLIfP.name%2C+%22Test-InterfaceProfile%22%29&rsp-subtree=full&rsp-subtree-class=l3extLIfP' == sut.filter_string

    def testGreatGrandChildQ07(self, setup, params):

        params['state'] = 'query'
        module = setup
        module.params.update(params)
        sut = ACIModule(module)
        tenant = None
        out = None
        lnodep = 'Test-NodeProfile'
        lifp = 'Test-InterfaceProfile'

        sut.construct_url(
            root_class=dict(
                parent_class='uni',
                aci_class='fvTenant',
                aci_rn='tn-{0}'.format(tenant),
                target_filter={'name': tenant},
                module_object=tenant
            ),
            subclass_1=dict(
                parent_class='fvTenant',
                aci_class='l3extOut',
                aci_rn='out-{0}'.format(out),
                target_filter={'name': out},
                module_object=out
            ),
            subclass_2=dict(
                parent_class='l3extOut',
                aci_class='l3extLNodeP',
                aci_rn='lnodep-{0}'.format(lnodep),
                target_filter={'name': lnodep},
                module_object=lnodep
            ),
            subclass_3=dict(
                parent_class='l3extLNodeP',
                aci_class='l3extLIfP',
                aci_rn='lifp-{0}'.format(lifp),
                target_filter={'name': lifp},
                module_object=lifp
            )
        )

        assert 'https://local.host.local:443/api/class/l3extLIfP.json' == sut.url
        assert '?query-target-filter=eq%28l3extLIfP.name%2C+%22Test-InterfaceProfile%22%29&rsp-subtree=full&rsp-subtree-class=l3extLIfP' == sut.filter_string

    def testGreatGrandChildQ08(self, setup, params):

        params['state'] = 'query'
        module = setup
        module.params.update(params)
        sut = ACIModule(module)
        tenant = None
        out = None
        lnodep = None
        lifp = 'Test-InterfaceProfile'

        sut.construct_url(
            root_class=dict(
                parent_class='uni',
                aci_class='fvTenant',
                aci_rn='tn-{0}'.format(tenant),
                target_filter={'name': tenant},
                module_object=tenant
            ),
            subclass_1=dict(
                parent_class='fvTenant',
                aci_class='l3extOut',
                aci_rn='out-{0}'.format(out),
                target_filter={'name': out},
                module_object=out
            ),
            subclass_2=dict(
                parent_class='l3extOut',
                aci_class='l3extLNodeP',
                aci_rn='lnodep-{0}'.format(lnodep),
                target_filter={'name': lnodep},
                module_object=lnodep
            ),
            subclass_3=dict(
                parent_class='l3extLNodeP',
                aci_class='l3extLIfP',
                aci_rn='lifp-{0}'.format(lifp),
                target_filter={'name': lifp},
                module_object=lifp
            )
        )

        assert 'https://local.host.local:443/api/class/l3extLIfP.json' == sut.url
        assert '?query-target-filter=eq%28l3extLIfP.name%2C+%22Test-InterfaceProfile%22%29&rsp-subtree=full&rsp-subtree-class=l3extLIfP' == sut.filter_string

    def testGreatGrandChildQ09(self, setup, params):

        params['state'] = 'query'
        module = setup
        module.params.update(params)
        sut = ACIModule(module)
        tenant = 'Test-Tenant'
        out = None
        lnodep = None
        lifp = 'Test-InterfaceProfile'

        sut.construct_url(
            root_class=dict(
                parent_class='uni',
                aci_class='fvTenant',
                aci_rn='tn-{0}'.format(tenant),
                target_filter={'name': tenant},
                module_object=tenant
            ),
            subclass_1=dict(
                parent_class='fvTenant',
                aci_class='l3extOut',
                aci_rn='out-{0}'.format(out),
                target_filter={'name': out},
                module_object=out
            ),
            subclass_2=dict(
                parent_class='l3extOut',
                aci_class='l3extLNodeP',
                aci_rn='lnodep-{0}'.format(lnodep),
                target_filter={'name': lnodep},
                module_object=lnodep
            ),
            subclass_3=dict(
                parent_class='l3extLNodeP',
                aci_class='l3extLIfP',
                aci_rn='lifp-{0}'.format(lifp),
                target_filter={'name': lifp},
                module_object=lifp
            )
        )

        assert 'https://local.host.local:443/api/mo/uni/tn-Test-Tenant.json' == sut.url
        assert '?rsp-subtree-filter=eq%28l3extLIfP.name%2C+%22Test-InterfaceProfile%22%29&rsp-subtree=full&rsp-subtree-class=l3extLIfP' == sut.filter_string

    def testGreatGrandChildQ10(self, setup, params):

        params['state'] = 'query'
        module = setup
        module.params.update(params)
        sut = ACIModule(module)
        tenant = 'Test-Tenant'
        out = 'Test-L3Out'
        lnodep = None
        lifp = 'Test-InterfaceProfile'

        sut.construct_url(
            root_class=dict(
                parent_class='uni',
                aci_class='fvTenant',
                aci_rn='tn-{0}'.format(tenant),
                target_filter={'name': tenant},
                module_object=tenant
            ),
            subclass_1=dict(
                parent_class='fvTenant',
                aci_class='l3extOut',
                aci_rn='out-{0}'.format(out),
                target_filter={'name': out},
                module_object=out
            ),
            subclass_2=dict(
                parent_class='l3extOut',
                aci_class='l3extLNodeP',
                aci_rn='lnodep-{0}'.format(lnodep),
                target_filter={'name': lnodep},
                module_object=lnodep
            ),
            subclass_3=dict(
                parent_class='l3extLNodeP',
                aci_class='l3extLIfP',
                aci_rn='lifp-{0}'.format(lifp),
                target_filter={'name': lifp},
                module_object=lifp
            )
        )

        assert 'https://local.host.local:443/api/mo/uni/tn-Test-Tenant/out-Test-L3Out.json' == sut.url
        assert '?rsp-subtree-filter=eq%28l3extLIfP.name%2C+%22Test-InterfaceProfile%22%29&rsp-subtree=full&rsp-subtree-class=l3extLIfP' == sut.filter_string

    def testGreatGrandChildQ11(self, setup, params):

        params['state'] = 'query'
        module = setup
        module.params.update(params)
        sut = ACIModule(module)
        tenant = 'Test-Tenant'
        out = None
        lnodep = 'Test-NodeProfile'
        lifp = 'Test-InterfaceProfile'

        sut.construct_url(
            root_class=dict(
                parent_class='uni',
                aci_class='fvTenant',
                aci_rn='tn-{0}'.format(tenant),
                target_filter={'name': tenant},
                module_object=tenant
            ),
            subclass_1=dict(
                parent_class='fvTenant',
                aci_class='l3extOut',
                aci_rn='out-{0}'.format(out),
                target_filter={'name': out},
                module_object=out
            ),
            subclass_2=dict(
                parent_class='l3extOut',
                aci_class='l3extLNodeP',
                aci_rn='lnodep-{0}'.format(lnodep),
                target_filter={'name': lnodep},
                module_object=lnodep
            ),
            subclass_3=dict(
                parent_class='l3extLNodeP',
                aci_class='l3extLIfP',
                aci_rn='lifp-{0}'.format(lifp),
                target_filter={'name': lifp},
                module_object=lifp
            )
        )

        assert 'https://local.host.local:443/api/mo/uni/tn-Test-Tenant.json' == sut.url
        assert '?rsp-subtree-filter=eq%28l3extLIfP.name%2C+%22Test-InterfaceProfile%22%29&rsp-subtree=full&rsp-subtree-class=l3extLIfP' == sut.filter_string

    def testGreatGrandChildQ12(self, setup, params):

        params['state'] = 'query'
        module = setup
        module.params.update(params)
        sut = ACIModule(module)
        tenant = None
        out = 'Test-L3Out'
        lnodep = None
        lifp = 'Test-InterfaceProfile'

        sut.construct_url(
            root_class=dict(
                parent_class='uni',
                aci_class='fvTenant',
                aci_rn='tn-{0}'.format(tenant),
                target_filter={'name': tenant},
                module_object=tenant
            ),
            subclass_1=dict(
                parent_class='fvTenant',
                aci_class='l3extOut',
                aci_rn='out-{0}'.format(out),
                target_filter={'name': out},
                module_object=out
            ),
            subclass_2=dict(
                parent_class='l3extOut',
                aci_class='l3extLNodeP',
                aci_rn='lnodep-{0}'.format(lnodep),
                target_filter={'name': lnodep},
                module_object=lnodep
            ),
            subclass_3=dict(
                parent_class='l3extLNodeP',
                aci_class='l3extLIfP',
                aci_rn='lifp-{0}'.format(lifp),
                target_filter={'name': lifp},
                module_object=lifp
            )
        )

        assert 'https://local.host.local:443/api/class/l3extLIfP.json' == sut.url
        assert '?query-target-filter=eq%28l3extLIfP.name%2C+%22Test-InterfaceProfile%22%29&rsp-subtree=full&rsp-subtree-class=l3extLIfP' == sut.filter_string
