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

    def testRootP01_moduleObjectValid_returnsObjectUrlAndFilterStringConfigOnly(self, setup, params):

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

    def testRootA01_moduleObjectValid_returnsObjectUrlAndFilterStringConfigOnly(self, setup, params):

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

    def testRootQ01_moduleObjectNone_returnsClassUrlAndFilterStringEmpty(self, setup, params):

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

    def testRootQ02_moduleObjectValid_returnsObjectUrlAndFilterStringEmpty(self, setup, params):

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

    def testChildP01_moduleParentValidChildValid_returnsObjectUrlAndFilterStringConfigOnly(self, setup, params):

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

    def testChildA01_moduleParentValidChildValid_returnsObjectUrlAndFilterStringConfigOnly(self, setup, params):

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

    def testChildQ01_moduleParentNoneChildNone_returnsChildClassUrlAndFilterStringSubtreeClass(self, setup, params):

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

    def testChildQ02_moduleParentValidChildNone_returnsObjectUrlAndFilterStringSubtreeChildClass(self, setup, params):

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

    def testChildQ03_moduleParentNoneChildValid_returnsParentClassUrlAndFilterStringSubtreeClass(self, setup, params):

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

    def testChildQ04_moduleParentValidChildValid_returnsParentClassUrlAndNoFilterString(self, setup, params):

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

    def testGrandChildP01_moduleGrandParentValidParentValidChildValid_returnsObjectUrlAndFilterStringConfigOnlyAndSubtreeClass(self, setup, params):

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

    def testGrandChildA01_moduleGrandParentValidParentValidChildValid_returnsObjectUrlAndFilterStringConfigOnlyAndSubtreeClass(self, setup, params):

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

    def testGrandChildQ01_moduleGrandParentNoneParentNoneChildNone_returnsClassUrlAndFilterStringSubtreeFullAndSubtreeClass(self, setup, params):

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

    def testGrandChildQ02_moduleGrandParentValidParentNoneChildNone_returnsObjectUrlAndFilterStringSubtreeFullAndSubtreeClasses(self, setup, params):

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

    def testGrandChildQ03_moduleGrandParentValidParentValidChildNone_returnsObjectUrlAndFilterStringSubtreeFullAndSubtreeClasses(self, setup, params):

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

    def testGrandChildQ04_moduleGrandParentValidParentValidChildValid_returnsObjectUrlAndFilterStringSubtreeFullAndSubtreeClasses(self, setup, params):

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

    def testGrandChildQ05_moduleGrandParentNoneParentValidChildValid_returnsObjectUrlAndFilterStringSubtreeFullAndSubtreeClasses(self, setup, params):

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
        assert '?query-target-filter=eq%28fvAp.name%2C+%22Test-Ap%22%29&rsp-subtree-filter=eq%28fvAEPg.name%2C+%22Test-Epg%22%29&rsp-subtree=full&rsp-subtree-class=fvAEPg%2CfvRsBd' == sut.filter_string

    def testGrandChildQ06_moduleGrandParentNoneParentNoneChildValid_returnsObjectUrlAndFilterStringSubtreeFullAndSubtreeClasses(self, setup, params):

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

    def testGrandChildQ07_moduleGrandParentNoneParentNoneChildValid_returnsObjectUrlAndFilterStringSubtreeFullAndSubtreeClasses(self, setup, params):

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

    def testGreatGrandChildP01_moduleGreatGrandParentValidGrandParentValidParentValidChildValid_returnsObjectUrlAndFilterStringConfigOnly(self, setup, params):

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

    def testGreatGrandChildA01_moduleGreatGrandParentValidGrandParentValidParentValidChildValid_returnsObjectUrlAndFilterStringConfigOnly(self, setup, params):

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

    def testGreatGrandChildQ01_moduleGreatGrandParentNoneGrandParentNoneParentNoneChildNone_returnsObjectUrlAndFilterStringSubtreeClass(self, setup, params):

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

    def testGreatGrandChildQ02_moduleGreatGrandParentValidGrandParentNoneParentNoneChildNone_returnsObjectUrlAndFilterStringSubtreeClass(self, setup, params):

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

    def testGreatGrandChildQ03_moduleGreatGrandParentValidGrandParentValidParentNoneChildNone_returnsObjectUrlAndFilterStringSubtreeClass(self, setup, params):

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

    def testGreatGrandChildQ04_moduleGreatGrandParentValidGrandParentValidParentValidChildNone_returnsObjectUrlAndFilterStringSubtreeClass(self, setup, params):

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

    def testGreatGrandChildQ05_moduleGreatGrandParentValidGrandParentValidParentValidChildValid_returnsObjectUrlAndFilterStringEmpty(self, setup, params):

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

    def testGreatGrandChildQ06_moduleGreatGrandParentNoneGrandParentValidParentValidChildValid_returnsObjectUrlAndFilterStringTargetFilterAndSubtreeClass(self, setup, params):

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

    def testGreatGrandChildQ07_moduleGreatGrandParentNoneGrandParentNoneParentValidChildValid_returnsObjectUrlAndFilterStringTargetFilterAndSubtreeClass(self, setup, params):

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

    def testGreatGrandChildQ08_moduleGreatGrandParentNoneGrandParentNoneParentNoneChildValid_returnsObjectUrlAndFilterStringTargetFilterAndSubtreeClass(self, setup, params):

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

    def testGreatGrandChildQ09_moduleGreatGrandParentValidGrandParentNoneParentNoneChildValid_returnsObjectUrlAndFilterStringSubtreeFilterAndSubtreeClass(self, setup, params):

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

    def testGreatGrandChildQ10_moduleGreatGrandParentValidGrandParentValidParentNoneChildValid_returnsObjectUrlAndFilterStringSubtreeFilterAndSubtreeClass(self, setup, params):

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

    def testGreatGrandChildQ11_moduleGreatGrandParentValidGrandParentNoneParentValidChildValid_returnsObjectUrlAndFilterStringSubtreeFilterAndSubtreeClass(self, setup, params):

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

    def testGreatGrandChildQ12_moduleGreatGrandParentNoneGrandParentValidParentNoneChildValid_returnsObjectUrlAndFilterStringSubtreeFilterAndSubtreeClass(self, setup, params):

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
