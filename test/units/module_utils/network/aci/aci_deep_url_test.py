import pytest

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.aci.aci import ACIModule, aci_argument_spec


@pytest.mark.usefixtures('setup')
class Test_AnsibleModule_Construct_Url_Exceptions(object):

    @pytest.fixture(scope='class')
    def params(self):

        return {
            'tenant': None,
            'descr': None,
            'state': 'query'
        }

    def testExceptionE01_moduleParentValidChildParentReferenceInvalid_raisesValueErrorException(self, setup, params):

        params['state'] = 'query'
        module = setup
        module.params.update(params)
        sut = ACIModule(module)
        tenant = 'Test-Tenant'
        ap = 'Test-Ap'

        with pytest.raises(ValueError) as exception_output:
            sut.construct_deep_url(
                parent_objects=[
                    dict(
                        parent_class='uni',
                        aci_class='fvTenant',
                        aci_rn='tn-{0}'.format(tenant),
                        target_filter={'name': tenant},
                        module_object=tenant
                    )
                ],
                target_object=dict(
                    parent_class='nonExistentParent',
                    aci_class='fvAp',
                    aci_rn='ap-{0}'.format(ap),
                    target_filter={'name': ap},
                    module_object=ap
                )
            )

        assert str(exception_output.value) == "There appears to be a break in the URL chain referencing parent_class 'nonExistentParent'. Make sure each parent_class is referencing a valid parent object"


@pytest.mark.usefixtures('setup')
class Test_AnsibleModule_Construct_Url_1(object):

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

        sut.construct_deep_url(
            target_object=dict(
                parent_class='uni',
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

        sut.construct_deep_url(
            target_object=dict(
                parent_class='uni',
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

        sut.construct_deep_url(
            target_object=dict(
                parent_class='uni',
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

        sut.construct_deep_url(
            target_object=dict(
                parent_class='uni',
                aci_class='fvTenant',
                aci_rn='tn-{0}'.format(tenant),
                target_filter={'name': tenant},
                module_object=tenant
            )
        )

        assert 'https://local.host.local:443/api/mo/uni/tn-Test-Tenant.json' == sut.url
        assert '' == sut.filter_string


@pytest.mark.usefixtures('setup')
class Test_AnsibleModule_Construct_Url_2(object):

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

        sut.construct_deep_url(
            parent_objects=[
                dict(
                    parent_class='uni',
                    aci_class='fvTenant',
                    aci_rn='tn-{0}'.format(tenant),
                    target_filter={'name': tenant},
                    module_object=tenant
                )
            ],
            target_object=dict(
                parent_class='fvTenant',
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

        sut.construct_deep_url(
            parent_objects=[
                dict(
                    parent_class='uni',
                    aci_class='fvTenant',
                    aci_rn='tn-{0}'.format(tenant),
                    target_filter={'name': tenant},
                    module_object=tenant
                )
            ],
            target_object=dict(
                parent_class='fvTenant',
                aci_class='fvAp',
                aci_rn='ap-{0}'.format(ap),
                target_filter={'name': ap},
                module_object=ap
            )
        )

        assert 'https://local.host.local:443/api/mo/uni/tn-Test-Tenant/ap-Test-Ap.json' == sut.url
        assert '?rsp-prop-include=config-only' == sut.filter_string

    def testChildQ01_moduleParentNoneChildNone_returnsChildClassUrlAndFilterStringEmpty(self, setup, params):

        params['state'] = 'query'
        module = setup
        module.params.update(params)
        sut = ACIModule(module)
        tenant = None
        ap = None

        sut.construct_deep_url(
            parent_objects=[
                dict(
                    parent_class='uni',
                    aci_class='fvTenant',
                    aci_rn='tn-{0}'.format(tenant),
                    target_filter={'name': tenant},
                    module_object=tenant
                )
            ],
            target_object=dict(
                parent_class='fvTenant',
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

        sut.construct_deep_url(
            parent_objects=[
                dict(
                    parent_class='uni',
                    aci_class='fvTenant',
                    aci_rn='tn-{0}'.format(tenant),
                    target_filter={'name': tenant},
                    module_object=tenant
                )
            ],
            target_object=dict(
                parent_class='fvTenant',
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

        sut.construct_deep_url(
            parent_objects=[
                dict(
                    parent_class='uni',
                    aci_class='fvTenant',
                    aci_rn='tn-{0}'.format(tenant),
                    target_filter={'name': tenant},
                    module_object=tenant
                )
            ],
            target_object=dict(
                parent_class='fvTenant',
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

        sut.construct_deep_url(
            parent_objects=[
                dict(
                    parent_class='uni',
                    aci_class='fvTenant',
                    aci_rn='tn-{0}'.format(tenant),
                    target_filter={'name': tenant},
                    module_object=tenant
                )
            ],
            target_object=dict(
                parent_class='fvTenant',
                aci_class='fvAp',
                aci_rn='ap-{0}'.format(ap),
                target_filter={'name': ap},
                module_object=ap
            )
        )

        assert 'https://local.host.local:443/api/mo/uni/tn-Test-Tenant/ap-Test-Ap.json' == sut.url
        assert '' == sut.filter_string


@pytest.mark.usefixtures('setup')
class Test_AnsibleModule_Construct_Url_3(object):

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

        sut.construct_deep_url(
            parent_objects=[
                dict(
                    parent_class='uni',
                    aci_class='fvTenant',
                    aci_rn='tn-{0}'.format(tenant),
                    target_filter={'name': tenant},
                    module_object=tenant
                ),
                dict(
                    parent_class='fvTenant',
                    aci_class='fvAp',
                    aci_rn='ap-{0}'.format(ap),
                    target_filter={'name': ap},
                    module_object=ap
                )
            ],
            target_object=dict(
                parent_class='fvAp',
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

        sut.construct_deep_url(
            parent_objects=[
                dict(
                    parent_class='uni',
                    aci_class='fvTenant',
                    aci_rn='tn-{0}'.format(tenant),
                    target_filter={'name': tenant},
                    module_object=tenant
                ),
                dict(
                    parent_class='fvTenant',
                    aci_class='fvAp',
                    aci_rn='ap-{0}'.format(ap),
                    target_filter={'name': ap},
                    module_object=ap
                )
            ],
            target_object=dict(
                parent_class='fvAp',
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

        sut.construct_deep_url(
            parent_objects=[
                dict(
                    parent_class='uni',
                    aci_class='fvTenant',
                    aci_rn='tn-{0}'.format(tenant),
                    target_filter={'name': tenant},
                    module_object=tenant
                ),
                dict(
                    parent_class='fvTenant',
                    aci_class='fvAp',
                    aci_rn='ap-{0}'.format(ap),
                    target_filter={'name': ap},
                    module_object=ap
                )
            ],
            target_object=dict(
                parent_class='fvAp',
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

        sut.construct_deep_url(
            parent_objects=[
                dict(
                    parent_class='uni',
                    aci_class='fvTenant',
                    aci_rn='tn-{0}'.format(tenant),
                    target_filter={'name': tenant},
                    module_object=tenant
                ),
                dict(
                    parent_class='fvTenant',
                    aci_class='fvAp',
                    aci_rn='ap-{0}'.format(ap),
                    target_filter={'name': ap},
                    module_object=ap
                )
            ],
            target_object=dict(
                parent_class='fvAp',
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

        sut.construct_deep_url(
            parent_objects=[
                dict(
                    parent_class='uni',
                    aci_class='fvTenant',
                    aci_rn='tn-{0}'.format(tenant),
                    target_filter={'name': tenant},
                    module_object=tenant
                ),
                dict(
                    parent_class='fvTenant',
                    aci_class='fvAp',
                    aci_rn='ap-{0}'.format(ap),
                    target_filter={'name': ap},
                    module_object=ap
                )
            ],
            target_object=dict(
                parent_class='fvAp',
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

        sut.construct_deep_url(
            parent_objects=[
                dict(
                    parent_class='uni',
                    aci_class='fvTenant',
                    aci_rn='tn-{0}'.format(tenant),
                    target_filter={'name': tenant},
                    module_object=tenant
                ),
                dict(
                    parent_class='fvTenant',
                    aci_class='fvAp',
                    aci_rn='ap-{0}'.format(ap),
                    target_filter={'name': ap},
                    module_object=ap
                )
            ],
            target_object=dict(
                parent_class='fvAp',
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

        sut.construct_deep_url(
            parent_objects=[
                dict(
                    parent_class='uni',
                    aci_class='fvTenant',
                    aci_rn='tn-{0}'.format(tenant),
                    target_filter={'name': tenant},
                    module_object=tenant
                ),
                dict(
                    parent_class='fvTenant',
                    aci_class='fvAp',
                    aci_rn='ap-{0}'.format(ap),
                    target_filter={'name': ap},
                    module_object=ap
                )
            ],
            target_object=dict(
                parent_class='fvAp',
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

        sut.construct_deep_url(
            parent_objects=[
                dict(
                    parent_class='uni',
                    aci_class='fvTenant',
                    aci_rn='tn-{0}'.format(tenant),
                    target_filter={'name': tenant},
                    module_object=tenant
                ),
                dict(
                    parent_class='fvTenant',
                    aci_class='fvAp',
                    aci_rn='ap-{0}'.format(ap),
                    target_filter={'name': ap},
                    module_object=ap
                )
            ],
            target_object=dict(
                parent_class='fvAp',
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

        sut.construct_deep_url(
            parent_objects=[
                dict(
                    parent_class='uni',
                    aci_class='fvTenant',
                    aci_rn='tn-{0}'.format(tenant),
                    target_filter={'name': tenant},
                    module_object=tenant
                ),
                dict(
                    parent_class='fvTenant',
                    aci_class='fvAp',
                    aci_rn='ap-{0}'.format(ap),
                    target_filter={'name': ap},
                    module_object=ap
                )
            ],
            target_object=dict(
                parent_class='fvAp',
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
class Test_AnsibleModule_Construct_Url_4(object):

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

        sut.construct_deep_url(
            parent_objects=[
                dict(
                    parent_class='uni',
                    aci_class='fvTenant',
                    aci_rn='tn-{0}'.format(tenant),
                    target_filter={'name': tenant},
                    module_object=tenant
                ),
                dict(
                    parent_class='fvTenant',
                    aci_class='l3extOut',
                    aci_rn='out-{0}'.format(out),
                    target_filter={'name': out},
                    module_object=out
                ),
                dict(
                    parent_class='l3extOut',
                    aci_class='l3extLNodeP',
                    aci_rn='lnodep-{0}'.format(lnodep),
                    target_filter={'name': lnodep},
                    module_object=lnodep
                )
            ],
            target_object=dict(
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

        sut.construct_deep_url(
            parent_objects=[
                dict(
                    parent_class='uni',
                    aci_class='fvTenant',
                    aci_rn='tn-{0}'.format(tenant),
                    target_filter={'name': tenant},
                    module_object=tenant
                ),
                dict(
                    parent_class='fvTenant',
                    aci_class='l3extOut',
                    aci_rn='out-{0}'.format(out),
                    target_filter={'name': out},
                    module_object=out
                ),
                dict(
                    parent_class='l3extOut',
                    aci_class='l3extLNodeP',
                    aci_rn='lnodep-{0}'.format(lnodep),
                    target_filter={'name': lnodep},
                    module_object=lnodep
                )
            ],
            target_object=dict(
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

        sut.construct_deep_url(
            parent_objects=[
                dict(
                    parent_class='uni',
                    aci_class='fvTenant',
                    aci_rn='tn-{0}'.format(tenant),
                    target_filter={'name': tenant},
                    module_object=tenant
                ),
                dict(
                    parent_class='fvTenant',
                    aci_class='l3extOut',
                    aci_rn='out-{0}'.format(out),
                    target_filter={'name': out},
                    module_object=out
                ),
                dict(
                    parent_class='l3extOut',
                    aci_class='l3extLNodeP',
                    aci_rn='lnodep-{0}'.format(lnodep),
                    target_filter={'name': lnodep},
                    module_object=lnodep
                )
            ],
            target_object=dict(
                parent_class='l3extLNodeP',
                aci_class='l3extLIfP',
                aci_rn='lifp-{0}'.format(lifp),
                target_filter={'name': lifp},
                module_object=lifp
            )
        )

        assert 'https://local.host.local:443/api/class/l3extLIfP.json' == sut.url
        #assert '?rsp-subtree=full&rsp-subtree-class=l3extLIfP' == sut.filter_string
        assert '' == sut.filter_string

    def testGreatGrandChildQ02_moduleGreatGrandParentValidGrandParentNoneParentNoneChildNone_returnsObjectUrlAndFilterStringSubtreeClass(self, setup, params):

        params['state'] = 'query'
        module = setup
        module.params.update(params)
        sut = ACIModule(module)
        tenant = 'Test-Tenant'
        out = None
        lnodep = None
        lifp = None

        sut.construct_deep_url(
            parent_objects=[
                dict(
                    parent_class='uni',
                    aci_class='fvTenant',
                    aci_rn='tn-{0}'.format(tenant),
                    target_filter={'name': tenant},
                    module_object=tenant
                ),
                dict(
                    parent_class='fvTenant',
                    aci_class='l3extOut',
                    aci_rn='out-{0}'.format(out),
                    target_filter={'name': out},
                    module_object=out
                ),
                dict(
                    parent_class='l3extOut',
                    aci_class='l3extLNodeP',
                    aci_rn='lnodep-{0}'.format(lnodep),
                    target_filter={'name': lnodep},
                    module_object=lnodep
                )
            ],
            target_object=dict(
                parent_class='l3extLNodeP',
                aci_class='l3extLIfP',
                aci_rn='lifp-{0}'.format(lifp),
                target_filter={'name': lifp},
                module_object=lifp
            )
        )

        assert 'https://local.host.local:443/api/mo/uni/tn-Test-Tenant.json' == sut.url
        #assert '?rsp-subtree=full&rsp-subtree-class=l3extLIfP' == sut.filter_string
        assert '?rsp-subtree=full&rsp-subtree-class=l3extLIfP%2Cl3extLNodeP%2Cl3extOut' == sut.filter_string

    def testGreatGrandChildQ03_moduleGreatGrandParentValidGrandParentValidParentNoneChildNone_returnsObjectUrlAndFilterStringSubtreeClass(self, setup, params):

        params['state'] = 'query'
        module = setup
        module.params.update(params)
        sut = ACIModule(module)
        tenant = 'Test-Tenant'
        out = 'Test-L3Out'
        lnodep = None
        lifp = None

        sut.construct_deep_url(
            parent_objects=[
                dict(
                    parent_class='uni',
                    aci_class='fvTenant',
                    aci_rn='tn-{0}'.format(tenant),
                    target_filter={'name': tenant},
                    module_object=tenant
                ),
                dict(
                    parent_class='fvTenant',
                    aci_class='l3extOut',
                    aci_rn='out-{0}'.format(out),
                    target_filter={'name': out},
                    module_object=out
                ),
                dict(
                    parent_class='l3extOut',
                    aci_class='l3extLNodeP',
                    aci_rn='lnodep-{0}'.format(lnodep),
                    target_filter={'name': lnodep},
                    module_object=lnodep
                )
            ],
            target_object=dict(
                parent_class='l3extLNodeP',
                aci_class='l3extLIfP',
                aci_rn='lifp-{0}'.format(lifp),
                target_filter={'name': lifp},
                module_object=lifp
            )
        )

        assert 'https://local.host.local:443/api/mo/uni/tn-Test-Tenant/out-Test-L3Out.json' == sut.url
        #assert '?rsp-subtree=full&rsp-subtree-class=l3extLIfP' == sut.filter_string
        assert '?rsp-subtree=full&rsp-subtree-class=l3extLIfP%2Cl3extLNodeP%2Cl3extOut' == sut.filter_string

    def testGreatGrandChildQ04_moduleGreatGrandParentValidGrandParentValidParentValidChildNone_returnsObjectUrlAndFilterStringSubtreeClass(self, setup, params):

        params['state'] = 'query'
        module = setup
        module.params.update(params)
        sut = ACIModule(module)
        tenant = 'Test-Tenant'
        out = 'Test-L3Out'
        lnodep = 'Test-NodeProfile'
        lifp = None

        sut.construct_deep_url(
            parent_objects=[
                dict(
                    parent_class='uni',
                    aci_class='fvTenant',
                    aci_rn='tn-{0}'.format(tenant),
                    target_filter={'name': tenant},
                    module_object=tenant
                ),
                dict(
                    parent_class='fvTenant',
                    aci_class='l3extOut',
                    aci_rn='out-{0}'.format(out),
                    target_filter={'name': out},
                    module_object=out
                ),
                dict(
                    parent_class='l3extOut',
                    aci_class='l3extLNodeP',
                    aci_rn='lnodep-{0}'.format(lnodep),
                    target_filter={'name': lnodep},
                    module_object=lnodep
                )
            ],
            target_object=dict(
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

        sut.construct_deep_url(
            parent_objects=[
                dict(
                    parent_class='uni',
                    aci_class='fvTenant',
                    aci_rn='tn-{0}'.format(tenant),
                    target_filter={'name': tenant},
                    module_object=tenant
                ),
                dict(
                    parent_class='fvTenant',
                    aci_class='l3extOut',
                    aci_rn='out-{0}'.format(out),
                    target_filter={'name': out},
                    module_object=out
                ),
                dict(
                    parent_class='l3extOut',
                    aci_class='l3extLNodeP',
                    aci_rn='lnodep-{0}'.format(lnodep),
                    target_filter={'name': lnodep},
                    module_object=lnodep
                )
            ],
            target_object=dict(
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

        sut.construct_deep_url(
            parent_objects=[
                dict(
                    parent_class='uni',
                    aci_class='fvTenant',
                    aci_rn='tn-{0}'.format(tenant),
                    target_filter={'name': tenant},
                    module_object=tenant
                ),
                dict(
                    parent_class='fvTenant',
                    aci_class='l3extOut',
                    aci_rn='out-{0}'.format(out),
                    target_filter={'name': out},
                    module_object=out
                ),
                dict(
                    parent_class='l3extOut',
                    aci_class='l3extLNodeP',
                    aci_rn='lnodep-{0}'.format(lnodep),
                    target_filter={'name': lnodep},
                    module_object=lnodep
                )
            ],
            target_object=dict(
                parent_class='l3extLNodeP',
                aci_class='l3extLIfP',
                aci_rn='lifp-{0}'.format(lifp),
                target_filter={'name': lifp},
                module_object=lifp
            )
        )

        #assert 'https://local.host.local:443/api/class/l3extLIfP.json' == sut.url
        assert 'https://local.host.local:443/api/class/l3extOut.json' == sut.url
        #assert '?query-target-filter=eq%28l3extLIfP.name%2C+%22Test-InterfaceProfile%22%29&rsp-subtree=full&rsp-subtree-class=l3extLIfP' == sut.filter_string
        assert '?query-target-filter=eq%28l3extOut.name%2C+%22Test-L3Out%22%29&rsp-subtree-filter=eq%28l3extLIfP.name%2C+%22Test-InterfaceProfile%22%29&rsp-subtree=full&rsp-subtree-class=l3extLIfP' == sut.filter_string

    def testGreatGrandChildQ07_moduleGreatGrandParentNoneGrandParentNoneParentValidChildValid_returnsObjectUrlAndFilterStringTargetFilterAndSubtreeClass(self, setup, params):

        params['state'] = 'query'
        module = setup
        module.params.update(params)
        sut = ACIModule(module)
        tenant = None
        out = None
        lnodep = 'Test-NodeProfile'
        lifp = 'Test-InterfaceProfile'

        sut.construct_deep_url(
            parent_objects=[
                dict(
                    parent_class='uni',
                    aci_class='fvTenant',
                    aci_rn='tn-{0}'.format(tenant),
                    target_filter={'name': tenant},
                    module_object=tenant
                ),
                dict(
                    parent_class='fvTenant',
                    aci_class='l3extOut',
                    aci_rn='out-{0}'.format(out),
                    target_filter={'name': out},
                    module_object=out
                ),
                dict(
                    parent_class='l3extOut',
                    aci_class='l3extLNodeP',
                    aci_rn='lnodep-{0}'.format(lnodep),
                    target_filter={'name': lnodep},
                    module_object=lnodep
                )
            ],
            target_object=dict(
                parent_class='l3extLNodeP',
                aci_class='l3extLIfP',
                aci_rn='lifp-{0}'.format(lifp),
                target_filter={'name': lifp},
                module_object=lifp
            )
        )

        #assert 'https://local.host.local:443/api/class/l3extLIfP.json' == sut.url
        assert 'https://local.host.local:443/api/class/l3extLNodeP.json' == sut.url
        #assert '?query-target-filter=eq%28l3extLIfP.name%2C+%22Test-InterfaceProfile%22%29&rsp-subtree=full&rsp-subtree-class=l3extLIfP' == sut.filter_string
        assert '?query-target-filter=eq%28l3extLNodeP.name%2C+%22Test-NodeProfile%22%29&rsp-subtree-filter=eq%28l3extLIfP.name%2C+%22Test-InterfaceProfile%22%29&rsp-subtree=full&rsp-subtree-class=l3extLIfP' == sut.filter_string

    def testGreatGrandChildQ08_moduleGreatGrandParentNoneGrandParentNoneParentNoneChildValid_returnsObjectUrlAndFilterStringTargetFilterAndSubtreeClass(self, setup, params):

        params['state'] = 'query'
        module = setup
        module.params.update(params)
        sut = ACIModule(module)
        tenant = None
        out = None
        lnodep = None
        lifp = 'Test-InterfaceProfile'

        sut.construct_deep_url(
            parent_objects=[
                dict(
                    parent_class='uni',
                    aci_class='fvTenant',
                    aci_rn='tn-{0}'.format(tenant),
                    target_filter={'name': tenant},
                    module_object=tenant
                ),
                dict(
                    parent_class='fvTenant',
                    aci_class='l3extOut',
                    aci_rn='out-{0}'.format(out),
                    target_filter={'name': out},
                    module_object=out
                ),
                dict(
                    parent_class='l3extOut',
                    aci_class='l3extLNodeP',
                    aci_rn='lnodep-{0}'.format(lnodep),
                    target_filter={'name': lnodep},
                    module_object=lnodep
                )
            ],
            target_object=dict(
                parent_class='l3extLNodeP',
                aci_class='l3extLIfP',
                aci_rn='lifp-{0}'.format(lifp),
                target_filter={'name': lifp},
                module_object=lifp
            )
        )

        assert 'https://local.host.local:443/api/class/l3extLIfP.json' == sut.url
        #assert '?query-target-filter=eq%28l3extLIfP.name%2C+%22Test-InterfaceProfile%22%29&rsp-subtree=full&rsp-subtree-class=l3extLIfP' == sut.filter_string
        assert '?query-target-filter=eq%28l3extLIfP.name%2C+%22Test-InterfaceProfile%22%29' == sut.filter_string

    def testGreatGrandChildQ09_moduleGreatGrandParentValidGrandParentNoneParentNoneChildValid_returnsObjectUrlAndFilterStringSubtreeFilterAndSubtreeClass(self, setup, params):

        params['state'] = 'query'
        module = setup
        module.params.update(params)
        sut = ACIModule(module)
        tenant = 'Test-Tenant'
        out = None
        lnodep = None
        lifp = 'Test-InterfaceProfile'

        sut.construct_deep_url(
            parent_objects=[
                dict(
                    parent_class='uni',
                    aci_class='fvTenant',
                    aci_rn='tn-{0}'.format(tenant),
                    target_filter={'name': tenant},
                    module_object=tenant
                ),
                dict(
                    parent_class='fvTenant',
                    aci_class='l3extOut',
                    aci_rn='out-{0}'.format(out),
                    target_filter={'name': out},
                    module_object=out
                ),
                dict(
                    parent_class='l3extOut',
                    aci_class='l3extLNodeP',
                    aci_rn='lnodep-{0}'.format(lnodep),
                    target_filter={'name': lnodep},
                    module_object=lnodep
                )
            ],
            target_object=dict(
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

        sut.construct_deep_url(
            parent_objects=[
                dict(
                    parent_class='uni',
                    aci_class='fvTenant',
                    aci_rn='tn-{0}'.format(tenant),
                    target_filter={'name': tenant},
                    module_object=tenant
                ),
                dict(
                    parent_class='fvTenant',
                    aci_class='l3extOut',
                    aci_rn='out-{0}'.format(out),
                    target_filter={'name': out},
                    module_object=out
                ),
                dict(
                    parent_class='l3extOut',
                    aci_class='l3extLNodeP',
                    aci_rn='lnodep-{0}'.format(lnodep),
                    target_filter={'name': lnodep},
                    module_object=lnodep
                )
            ],
            target_object=dict(
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

        sut.construct_deep_url(
            parent_objects=[
                dict(
                    parent_class='uni',
                    aci_class='fvTenant',
                    aci_rn='tn-{0}'.format(tenant),
                    target_filter={'name': tenant},
                    module_object=tenant
                ),
                dict(
                    parent_class='fvTenant',
                    aci_class='l3extOut',
                    aci_rn='out-{0}'.format(out),
                    target_filter={'name': out},
                    module_object=out
                ),
                dict(
                    parent_class='l3extOut',
                    aci_class='l3extLNodeP',
                    aci_rn='lnodep-{0}'.format(lnodep),
                    target_filter={'name': lnodep},
                    module_object=lnodep
                )
            ],
            target_object=dict(
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

        sut.construct_deep_url(
            parent_objects=[
                dict(
                    parent_class='uni',
                    aci_class='fvTenant',
                    aci_rn='tn-{0}'.format(tenant),
                    target_filter={'name': tenant},
                    module_object=tenant
                ),
                dict(
                    parent_class='fvTenant',
                    aci_class='l3extOut',
                    aci_rn='out-{0}'.format(out),
                    target_filter={'name': out},
                    module_object=out
                ),
                dict(
                    parent_class='l3extOut',
                    aci_class='l3extLNodeP',
                    aci_rn='lnodep-{0}'.format(lnodep),
                    target_filter={'name': lnodep},
                    module_object=lnodep
                )
            ],
            target_object=dict(
                parent_class='l3extLNodeP',
                aci_class='l3extLIfP',
                aci_rn='lifp-{0}'.format(lifp),
                target_filter={'name': lifp},
                module_object=lifp
            )
        )

        #assert 'https://local.host.local:443/api/class/l3extLIfP.json' == sut.url
        assert 'https://local.host.local:443/api/class/l3extOut.json' == sut.url
        #assert '?query-target-filter=eq%28l3extLIfP.name%2C+%22Test-InterfaceProfile%22%29&rsp-subtree=full&rsp-subtree-class=l3extLIfP' == sut.filter_string
        assert '?query-target-filter=eq%28l3extOut.name%2C+%22Test-L3Out%22%29&rsp-subtree-filter=eq%28l3extLIfP.name%2C+%22Test-InterfaceProfile%22%29&rsp-subtree=full&rsp-subtree-class=l3extLIfP' == sut.filter_string

    def testGreatGrandChildQ13_moduleGreatGrandParentValidGrandParentNoneParentValidChildNone_returnsObjectUrlAndFilterStringSubtreeFilterAndSubtreeClass(self, setup, params):

        params['state'] = 'query'
        module = setup
        module.params.update(params)
        sut = ACIModule(module)
        tenant = 'Test-Tenant'
        out = None
        lnodep = 'Test-NodeProfile'
        lifp = None

        sut.construct_deep_url(
            parent_objects=[
                dict(
                    parent_class='uni',
                    aci_class='fvTenant',
                    aci_rn='tn-{0}'.format(tenant),
                    target_filter={'name': tenant},
                    module_object=tenant
                ),
                dict(
                    parent_class='fvTenant',
                    aci_class='l3extOut',
                    aci_rn='out-{0}'.format(out),
                    target_filter={'name': out},
                    module_object=out
                ),
                dict(
                    parent_class='l3extOut',
                    aci_class='l3extLNodeP',
                    aci_rn='lnodep-{0}'.format(lnodep),
                    target_filter={'name': lnodep},
                    module_object=lnodep
                )
            ],
            target_object=dict(
                parent_class='l3extLNodeP',
                aci_class='l3extLIfP',
                aci_rn='lifp-{0}'.format(lifp),
                target_filter={'name': lifp},
                module_object=lifp
            )
        )

        assert 'https://local.host.local:443/api/mo/uni/tn-Test-Tenant.json' == sut.url
        assert '?rsp-subtree=full&rsp-subtree-class=l3extLIfP%2Cl3extLNodeP%2Cl3extOut' == sut.filter_string


@pytest.mark.usefixtures('setup')
class Test_AnsibleModule_Construct_Url_5(object):

    @pytest.fixture(scope='class')
    def params(self):

        return {
            'tenant': None,
            'out': None,
            'lnodep': None,
            'lifp': None,
            'ifp': None,
            'bfdRsIfPol': None,
            'state': 'query'
        }

    def testGreatGreatGrandChildP01_moduleGreatGreatGrandParentValid_GreatGrandParentValid_GrandParentValid_ParentValid_ChildValid_returnsObjectUrl_And_FilterStringConfigOnly_And_SubtreeFull_And_SubtreeClass(self, setup, params):

        params['state'] = 'present'
        module = setup
        module.params.update(params)
        sut = ACIModule(module)
        tenant = 'Test-Tenant'
        out = 'Test-L3Out'
        lnodep = 'Test-NodeProfile'
        lifp = 'Test-LogicalInterfaceProfile'
        ifp = 'Test-InterfaceProfile'

        sut.construct_deep_url(
            parent_objects=[
                dict(
                    parent_class='uni',
                    aci_class='fvTenant',
                    aci_rn='tn-{0}'.format(tenant),
                    target_filter={'name': tenant},
                    module_object=tenant
                ),
                dict(
                    parent_class='fvTenant',
                    aci_class='l3extOut',
                    aci_rn='out-{0}'.format(out),
                    target_filter={'name': out},
                    module_object=out
                ),
                dict(
                    parent_class='l3extOut',
                    aci_class='l3extLNodeP',
                    aci_rn='lnodep-{0}'.format(lnodep),
                    target_filter={'name': lnodep},
                    module_object=lnodep
                ),
                dict(
                    parent_class='l3extLNodeP',
                    aci_class='l3extLIfP',
                    aci_rn='lifp-{0}'.format(lifp),
                    target_filter={'name': lifp},
                    module_object=lifp
                )
            ],
            target_object=dict(
                parent_class='l3extLIfP',
                aci_class='bfdIfP',
                aci_rn='bfdIfP-{0}'.format(ifp),
                target_filter={'name': ifp},
                module_object=ifp
            ),
            child_classes=['bfdRsIfPol']
        )

        assert 'https://local.host.local:443/api/mo/uni/tn-Test-Tenant/out-Test-L3Out/lnodep-Test-NodeProfile/lifp-Test-LogicalInterfaceProfile/bfdIfP-Test-InterfaceProfile.json' == sut.url
        assert '?rsp-prop-include=config-only&rsp-subtree=full&rsp-subtree-class=bfdRsIfPol' == sut.filter_string

    def testGreatGreatGrandChildA01_moduleGreatGreatGrandParentValid_GreatGrandParentValid_GrandParentValid_ParentValid_ChildValid_returnsObjectUrl_And_FilterStringConfigOnly_And_SubtreeFull_And_SubtreeClass(self, setup, params):

        params['state'] = 'absent'
        module = setup
        module.params.update(params)
        sut = ACIModule(module)
        tenant = 'Test-Tenant'
        out = 'Test-L3Out'
        lnodep = 'Test-NodeProfile'
        lifp = 'Test-LogicalInterfaceProfile'
        ifp = 'Test-InterfaceProfile'

        sut.construct_deep_url(
            parent_objects=[
                dict(
                    parent_class='uni',
                    aci_class='fvTenant',
                    aci_rn='tn-{0}'.format(tenant),
                    target_filter={'name': tenant},
                    module_object=tenant
                ),
                dict(
                    parent_class='fvTenant',
                    aci_class='l3extOut',
                    aci_rn='out-{0}'.format(out),
                    target_filter={'name': out},
                    module_object=out
                ),
                dict(
                    parent_class='l3extOut',
                    aci_class='l3extLNodeP',
                    aci_rn='lnodep-{0}'.format(lnodep),
                    target_filter={'name': lnodep},
                    module_object=lnodep
                ),
                dict(
                    parent_class='l3extLNodeP',
                    aci_class='l3extLIfP',
                    aci_rn='lifp-{0}'.format(lifp),
                    target_filter={'name': lifp},
                    module_object=lifp
                )
            ],
            target_object=dict(
                parent_class='l3extLIfP',
                aci_class='bfdIfP',
                aci_rn='bfdIfP-{0}'.format(ifp),
                target_filter={'name': ifp},
                module_object=ifp
            ),
            child_classes=['bfdRsIfPol']
        )

        assert 'https://local.host.local:443/api/mo/uni/tn-Test-Tenant/out-Test-L3Out/lnodep-Test-NodeProfile/lifp-Test-LogicalInterfaceProfile/bfdIfP-Test-InterfaceProfile.json' == sut.url
        assert '?rsp-prop-include=config-only&rsp-subtree=full&rsp-subtree-class=bfdRsIfPol' == sut.filter_string

    def testGreatGreatGrandChildQ01_moduleGreatGreatGrandParentNone_GreatGrandParentNone_GrandParentNone_ParentNone_ChildNone_returnsObjectUrl_And_FilterStringSubtreeFull_And_SubtreeClass(self, setup, params):

        params['state'] = 'query'
        module = setup
        module.params.update(params)
        sut = ACIModule(module)
        tenant = None
        out = None
        lnodep = None
        lifp = None
        ifp = None

        sut.construct_deep_url(
            parent_objects=[
                dict(
                    parent_class='uni',
                    aci_class='fvTenant',
                    aci_rn='tn-{0}'.format(tenant),
                    target_filter={'name': tenant},
                    module_object=tenant
                ),
                dict(
                    parent_class='fvTenant',
                    aci_class='l3extOut',
                    aci_rn='out-{0}'.format(out),
                    target_filter={'name': out},
                    module_object=out
                ),
                dict(
                    parent_class='l3extOut',
                    aci_class='l3extLNodeP',
                    aci_rn='lnodep-{0}'.format(lnodep),
                    target_filter={'name': lnodep},
                    module_object=lnodep
                ),
                dict(
                    parent_class='l3extLNodeP',
                    aci_class='l3extLIfP',
                    aci_rn='lifp-{0}'.format(lifp),
                    target_filter={'name': lifp},
                    module_object=lifp
                )
            ],
            target_object=dict(
                parent_class='l3extLIfP',
                aci_class='bfdIfP',
                aci_rn='bfdIfP-{0}'.format(ifp),
                target_filter={'name': ifp},
                module_object=ifp
            ),
            child_classes=['bfdRsIfPol']
        )

        assert 'https://local.host.local:443/api/class/bfdIfP.json' == sut.url
        assert '?rsp-subtree=full&rsp-subtree-class=bfdRsIfPol' == sut.filter_string

    def testGreatGreatGrandChildQ02_moduleGreatGreatGrandParentValid_GreatGrandParentNone_GrandParentNone_ParentNone_ChildNone_returnsObjectUrlAndFilterStringSubtreeFull_And_AllSubtreeClasses(self, setup, params):

        params['state'] = 'query'
        module = setup
        module.params.update(params)
        sut = ACIModule(module)
        tenant = 'Test-Tenant'
        out = None
        lnodep = None
        lifp = None
        ifp = None

        sut.construct_deep_url(
            parent_objects=[
                dict(
                    parent_class='uni',
                    aci_class='fvTenant',
                    aci_rn='tn-{0}'.format(tenant),
                    target_filter={'name': tenant},
                    module_object=tenant
                ),
                dict(
                    parent_class='fvTenant',
                    aci_class='l3extOut',
                    aci_rn='out-{0}'.format(out),
                    target_filter={'name': out},
                    module_object=out
                ),
                dict(
                    parent_class='l3extOut',
                    aci_class='l3extLNodeP',
                    aci_rn='lnodep-{0}'.format(lnodep),
                    target_filter={'name': lnodep},
                    module_object=lnodep
                ),
                dict(
                    parent_class='l3extLNodeP',
                    aci_class='l3extLIfP',
                    aci_rn='lifp-{0}'.format(lifp),
                    target_filter={'name': lifp},
                    module_object=lifp
                )
            ],
            target_object=dict(
                parent_class='l3extLIfP',
                aci_class='bfdIfP',
                aci_rn='bfdIfP-{0}'.format(ifp),
                target_filter={'name': ifp},
                module_object=ifp
            ),
            child_classes=['bfdRsIfPol']
        )

        assert 'https://local.host.local:443/api/mo/uni/tn-Test-Tenant.json' == sut.url
        assert '?rsp-subtree=full&rsp-subtree-class=bfdIfP%2CbfdRsIfPol%2Cl3extLIfP%2Cl3extLNodeP%2Cl3extOut' == sut.filter_string

    def testGreatGreatGrandChildQ03_moduleGreatGreatGrandParentValid_GreatGrandParentValid_GrandParentNone_ParentNone_ChildNone_returnsObjectUrlAndFilterStringSubtreeFull_And_AllSubtreeClasses(self, setup, params):

        params['state'] = 'query'
        module = setup
        module.params.update(params)
        sut = ACIModule(module)
        tenant = 'Test-Tenant'
        out = 'Test-L3Out'
        lnodep = None
        lifp = None
        ifp = None

        sut.construct_deep_url(
            parent_objects=[
                dict(
                    parent_class='uni',
                    aci_class='fvTenant',
                    aci_rn='tn-{0}'.format(tenant),
                    target_filter={'name': tenant},
                    module_object=tenant
                ),
                dict(
                    parent_class='fvTenant',
                    aci_class='l3extOut',
                    aci_rn='out-{0}'.format(out),
                    target_filter={'name': out},
                    module_object=out
                ),
                dict(
                    parent_class='l3extOut',
                    aci_class='l3extLNodeP',
                    aci_rn='lnodep-{0}'.format(lnodep),
                    target_filter={'name': lnodep},
                    module_object=lnodep
                ),
                dict(
                    parent_class='l3extLNodeP',
                    aci_class='l3extLIfP',
                    aci_rn='lifp-{0}'.format(lifp),
                    target_filter={'name': lifp},
                    module_object=lifp
                )
            ],
            target_object=dict(
                parent_class='l3extLIfP',
                aci_class='bfdIfP',
                aci_rn='bfdIfP-{0}'.format(ifp),
                target_filter={'name': ifp},
                module_object=ifp
            ),
            child_classes=['bfdRsIfPol']
        )

        assert 'https://local.host.local:443/api/mo/uni/tn-Test-Tenant/out-Test-L3Out.json' == sut.url
        assert '?rsp-subtree=full&rsp-subtree-class=bfdIfP%2CbfdRsIfPol%2Cl3extLIfP%2Cl3extLNodeP%2Cl3extOut' == sut.filter_string

    def testGreatGreatGrandChildQ04_moduleGreatGreatGrandParentValid_GreatGrandParentValid_GrandParentValid_ParentNone_ChildNone_returnsObjectUrlAndFilterStringSubtreeFull_And_AllSubtreeClasses(self, setup, params):

        params['state'] = 'query'
        module = setup
        module.params.update(params)
        sut = ACIModule(module)
        tenant = 'Test-Tenant'
        out = 'Test-L3Out'
        lnodep = 'Test-NodeProfile'
        lifp = None
        ifp = None

        sut.construct_deep_url(
            parent_objects=[
                dict(
                    parent_class='uni',
                    aci_class='fvTenant',
                    aci_rn='tn-{0}'.format(tenant),
                    target_filter={'name': tenant},
                    module_object=tenant
                ),
                dict(
                    parent_class='fvTenant',
                    aci_class='l3extOut',
                    aci_rn='out-{0}'.format(out),
                    target_filter={'name': out},
                    module_object=out
                ),
                dict(
                    parent_class='l3extOut',
                    aci_class='l3extLNodeP',
                    aci_rn='lnodep-{0}'.format(lnodep),
                    target_filter={'name': lnodep},
                    module_object=lnodep
                ),
                dict(
                    parent_class='l3extLNodeP',
                    aci_class='l3extLIfP',
                    aci_rn='lifp-{0}'.format(lifp),
                    target_filter={'name': lifp},
                    module_object=lifp
                )
            ],
            target_object=dict(
                parent_class='l3extLIfP',
                aci_class='bfdIfP',
                aci_rn='bfdIfP-{0}'.format(ifp),
                target_filter={'name': ifp},
                module_object=ifp
            ),
            child_classes=['bfdRsIfPol']
        )

        assert 'https://local.host.local:443/api/mo/uni/tn-Test-Tenant/out-Test-L3Out/lnodep-Test-NodeProfile.json' == sut.url
        assert '?rsp-subtree=full&rsp-subtree-class=bfdIfP%2CbfdRsIfPol%2Cl3extLIfP%2Cl3extLNodeP%2Cl3extOut' == sut.filter_string

    def testGreatGreatGrandChildQ05_module_GreatGreatGrandParentValid_GreatGrandParentValid_GrandParentValid_ParentValid_ChildNone_returnsObjectUrlAndFilterStringSubtreeFull_And_SubtreeClassesObjectAndChildren(self, setup, params):

        params['state'] = 'query'
        module = setup
        module.params.update(params)
        sut = ACIModule(module)
        tenant = 'Test-Tenant'
        out = 'Test-L3Out'
        lnodep = 'Test-NodeProfile'
        lifp = 'Test-LogicalInterfaceProfile'
        ifp = None

        sut.construct_deep_url(
            parent_objects=[
                dict(
                    parent_class='uni',
                    aci_class='fvTenant',
                    aci_rn='tn-{0}'.format(tenant),
                    target_filter={'name': tenant},
                    module_object=tenant
                ),
                dict(
                    parent_class='fvTenant',
                    aci_class='l3extOut',
                    aci_rn='out-{0}'.format(out),
                    target_filter={'name': out},
                    module_object=out
                ),
                dict(
                    parent_class='l3extOut',
                    aci_class='l3extLNodeP',
                    aci_rn='lnodep-{0}'.format(lnodep),
                    target_filter={'name': lnodep},
                    module_object=lnodep
                ),
                dict(
                    parent_class='l3extLNodeP',
                    aci_class='l3extLIfP',
                    aci_rn='lifp-{0}'.format(lifp),
                    target_filter={'name': lifp},
                    module_object=lifp
                )
            ],
            target_object=dict(
                parent_class='l3extLIfP',
                aci_class='bfdIfP',
                aci_rn='bfdIfP-{0}'.format(ifp),
                target_filter={'name': ifp},
                module_object=ifp
            ),
            child_classes=['bfdRsIfPol']
        )

        assert 'https://local.host.local:443/api/mo/uni/tn-Test-Tenant/out-Test-L3Out/lnodep-Test-NodeProfile/lifp-Test-LogicalInterfaceProfile.json' == sut.url
        assert '?rsp-subtree=full&rsp-subtree-class=bfdIfP%2CbfdRsIfPol' == sut.filter_string

    def testGreatGreatGrandChildQ06_module_GreatGreatGrandParentValid_GreatGrandParentValid_GrandParentValid_ParentValid_ChildValid_returnsObjectUrlAndFilterStringSubtreeFull_And_SubtreeFullAndChildrenClassesOnly(self, setup, params):

        params['state'] = 'query'
        module = setup
        module.params.update(params)
        sut = ACIModule(module)
        tenant = 'Test-Tenant'
        out = 'Test-L3Out'
        lnodep = 'Test-NodeProfile'
        lifp = 'Test-LogicalInterfaceProfile'
        ifp = 'Test-InterfaceProfile'

        sut.construct_deep_url(
            parent_objects=[
                dict(
                    parent_class='uni',
                    aci_class='fvTenant',
                    aci_rn='tn-{0}'.format(tenant),
                    target_filter={'name': tenant},
                    module_object=tenant
                ),
                dict(
                    parent_class='fvTenant',
                    aci_class='l3extOut',
                    aci_rn='out-{0}'.format(out),
                    target_filter={'name': out},
                    module_object=out
                ),
                dict(
                    parent_class='l3extOut',
                    aci_class='l3extLNodeP',
                    aci_rn='lnodep-{0}'.format(lnodep),
                    target_filter={'name': lnodep},
                    module_object=lnodep
                ),
                dict(
                    parent_class='l3extLNodeP',
                    aci_class='l3extLIfP',
                    aci_rn='lifp-{0}'.format(lifp),
                    target_filter={'name': lifp},
                    module_object=lifp
                )
            ],
            target_object=dict(
                parent_class='l3extLIfP',
                aci_class='bfdIfP',
                aci_rn='bfdIfP',
                target_filter={'name': None},
                module_object=ifp
            ),
            child_classes=['bfdRsIfPol']
        )

        assert 'https://local.host.local:443/api/mo/uni/tn-Test-Tenant/out-Test-L3Out/lnodep-Test-NodeProfile/lifp-Test-LogicalInterfaceProfile/bfdIfP.json' == sut.url
        assert '?rsp-subtree=full&rsp-subtree-class=bfdRsIfPol' == sut.filter_string

    def testGreatGreatGrandChildQ07_module_GreatGreatGrandParentValid_GreatGrandParentValid_GrandParentValid_ParentValid_ChildValid_returnsObjectUrlAndFilterStringEmpty(self, setup, params):

        params['state'] = 'query'
        module = setup
        module.params.update(params)
        sut = ACIModule(module)
        tenant = 'Test-Tenant'
        out = 'Test-L3Out'
        lnodep = 'Test-NodeProfile'
        lifp = 'Test-LogicalInterfaceProfile'
        ifp = 'Test-InterfaceProfile'

        sut.construct_deep_url(
            parent_objects=[
                dict(
                    parent_class='uni',
                    aci_class='fvTenant',
                    aci_rn='tn-{0}'.format(tenant),
                    target_filter={'name': tenant},
                    module_object=tenant
                ),
                dict(
                    parent_class='fvTenant',
                    aci_class='l3extOut',
                    aci_rn='out-{0}'.format(out),
                    target_filter={'name': out},
                    module_object=out
                ),
                dict(
                    parent_class='l3extOut',
                    aci_class='l3extLNodeP',
                    aci_rn='lnodep-{0}'.format(lnodep),
                    target_filter={'name': lnodep},
                    module_object=lnodep
                ),
                dict(
                    parent_class='l3extLNodeP',
                    aci_class='l3extLIfP',
                    aci_rn='lifp-{0}'.format(lifp),
                    target_filter={'name': lifp},
                    module_object=lifp
                )
            ],
            target_object=dict(
                parent_class='l3extLIfP',
                aci_class='bfdIfP',
                aci_rn='bfdIfP',
                target_filter={'name': None},
                module_object=ifp
            )
        )

        assert 'https://local.host.local:443/api/mo/uni/tn-Test-Tenant/out-Test-L3Out/lnodep-Test-NodeProfile/lifp-Test-LogicalInterfaceProfile/bfdIfP.json' == sut.url
        assert '' == sut.filter_string

    def testGreatGreatGrandChildQ08_module_GreatGreatGrandParentNone_GreatGrandParentValid_GrandParentValid_ParentValid_ChildValid_returnsObjectUrlAndFilterStringQueryFilterAndSubtreeFull(self, setup, params):

        params['state'] = 'query'
        module = setup
        module.params.update(params)
        sut = ACIModule(module)
        tenant = None
        out = 'Test-L3Out'
        lnodep = 'Test-NodeProfile'
        lifp = 'Test-LogicalInterfaceProfile'
        ifp = 'Test-InterfaceProfile'

        sut.construct_deep_url(
            parent_objects=[
                dict(
                    parent_class='uni',
                    aci_class='fvTenant',
                    aci_rn='tn-{0}'.format(tenant),
                    target_filter={'name': tenant},
                    module_object=tenant
                ),
                dict(
                    parent_class='fvTenant',
                    aci_class='l3extOut',
                    aci_rn='out-{0}'.format(out),
                    target_filter={'name': out},
                    module_object=out
                ),
                dict(
                    parent_class='l3extOut',
                    aci_class='l3extLNodeP',
                    aci_rn='lnodep-{0}'.format(lnodep),
                    target_filter={'name': lnodep},
                    module_object=lnodep
                ),
                dict(
                    parent_class='l3extLNodeP',
                    aci_class='l3extLIfP',
                    aci_rn='lifp-{0}'.format(lifp),
                    target_filter={'name': lifp},
                    module_object=lifp
                )
            ],
            target_object=dict(
                parent_class='l3extLIfP',
                aci_class='bfdIfP',
                aci_rn='bfdIfP',
                target_filter={'name': None},
                module_object=ifp
            ),
            child_classes=['bfdRsIfPol']
        )

        assert 'https://local.host.local:443/api/class/l3extOut.json' == sut.url
        assert '?query-target-filter=eq%28l3extOut.name%2C+%22Test-L3Out%22%29&rsp-subtree=full&rsp-subtree-class=bfdIfP%2CbfdRsIfPol' == sut.filter_string

    def testGreatGreatGrandChildQ09_module_GreatGreatGrandParentNone_GreatGrandParentNone_GrandParentValid_ParentValid_ChildValid_returnsObjectUrlAndFilterStringreturnsObjectUrlAndFilterStringQueryFilterAndSubtreeFull(self, setup, params):

        params['state'] = 'query'
        module = setup
        module.params.update(params)
        sut = ACIModule(module)
        tenant = None
        out = None
        lnodep = 'Test-NodeProfile'
        lifp = 'Test-LogicalInterfaceProfile'
        ifp = 'Test-InterfaceProfile'

        sut.construct_deep_url(
            parent_objects=[
                dict(
                    parent_class='uni',
                    aci_class='fvTenant',
                    aci_rn='tn-{0}'.format(tenant),
                    target_filter={'name': tenant},
                    module_object=tenant
                ),
                dict(
                    parent_class='fvTenant',
                    aci_class='l3extOut',
                    aci_rn='out-{0}'.format(out),
                    target_filter={'name': out},
                    module_object=out
                ),
                dict(
                    parent_class='l3extOut',
                    aci_class='l3extLNodeP',
                    aci_rn='lnodep-{0}'.format(lnodep),
                    target_filter={'name': lnodep},
                    module_object=lnodep
                ),
                dict(
                    parent_class='l3extLNodeP',
                    aci_class='l3extLIfP',
                    aci_rn='lifp-{0}'.format(lifp),
                    target_filter={'name': lifp},
                    module_object=lifp
                )
            ],
            target_object=dict(
                parent_class='l3extLIfP',
                aci_class='bfdIfP',
                aci_rn='bfdIfP',
                target_filter={'name': None},
                module_object=ifp
            ),
            child_classes=['bfdRsIfPol']
        )

        assert 'https://local.host.local:443/api/class/l3extLNodeP.json' == sut.url
        assert '?query-target-filter=eq%28l3extLNodeP.name%2C+%22Test-NodeProfile%22%29&rsp-subtree=full&rsp-subtree-class=bfdIfP%2CbfdRsIfPol' == sut.filter_string

    def testGreatGreatGrandChildQ10_module_GreatGreatGrandParentNone_GreatGrandParentNone_GrandParentNone_ParentValid_ChildValid_returnsObjectUrlAndFilterStringreturnsObjectUrlAndFilterStringQueryFilterAndSubtreeFull(self, setup, params):

        params['state'] = 'query'
        module = setup
        module.params.update(params)
        sut = ACIModule(module)
        tenant = None
        out = None
        lnodep = None
        lifp = 'Test-LogicalInterfaceProfile'
        ifp = 'Test-InterfaceProfile'

        sut.construct_deep_url(
            parent_objects=[
                dict(
                    parent_class='uni',
                    aci_class='fvTenant',
                    aci_rn='tn-{0}'.format(tenant),
                    target_filter={'name': tenant},
                    module_object=tenant
                ),
                dict(
                    parent_class='fvTenant',
                    aci_class='l3extOut',
                    aci_rn='out-{0}'.format(out),
                    target_filter={'name': out},
                    module_object=out
                ),
                dict(
                    parent_class='l3extOut',
                    aci_class='l3extLNodeP',
                    aci_rn='lnodep-{0}'.format(lnodep),
                    target_filter={'name': lnodep},
                    module_object=lnodep
                ),
                dict(
                    parent_class='l3extLNodeP',
                    aci_class='l3extLIfP',
                    aci_rn='lifp-{0}'.format(lifp),
                    target_filter={'name': lifp},
                    module_object=lifp
                )
            ],
            target_object=dict(
                parent_class='l3extLIfP',
                aci_class='bfdIfP',
                aci_rn='bfdIfP',
                target_filter={'name': None},
                module_object=ifp
            ),
            child_classes=['bfdRsIfPol']
        )

        assert 'https://local.host.local:443/api/class/l3extLIfP.json' == sut.url
        assert '?query-target-filter=eq%28l3extLIfP.name%2C+%22Test-LogicalInterfaceProfile%22%29&rsp-subtree=full&rsp-subtree-class=bfdIfP%2CbfdRsIfPol' == sut.filter_string

    def testGreatGreatGrandChildQ11_module_GreatGreatGrandParentNone_GreatGrandParentNone_GrandParentNone_ParentNone_ChildValid_returnsObjectUrlAndFilterStringreturnsObjectUrlAndFilterStringQueryFilterAndSubtreeFull(self, setup, params):

        params['state'] = 'query'
        module = setup
        module.params.update(params)
        sut = ACIModule(module)
        tenant = None
        out = None
        lnodep = None
        lifp = None
        ifp = 'Test-InterfaceProfile'

        sut.construct_deep_url(
            parent_objects=[
                dict(
                    parent_class='uni',
                    aci_class='fvTenant',
                    aci_rn='tn-{0}'.format(tenant),
                    target_filter={'name': tenant},
                    module_object=tenant
                ),
                dict(
                    parent_class='fvTenant',
                    aci_class='l3extOut',
                    aci_rn='out-{0}'.format(out),
                    target_filter={'name': out},
                    module_object=out
                ),
                dict(
                    parent_class='l3extOut',
                    aci_class='l3extLNodeP',
                    aci_rn='lnodep-{0}'.format(lnodep),
                    target_filter={'name': lnodep},
                    module_object=lnodep
                ),
                dict(
                    parent_class='l3extLNodeP',
                    aci_class='l3extLIfP',
                    aci_rn='lifp-{0}'.format(lifp),
                    target_filter={'name': lifp},
                    module_object=lifp
                )
            ],
            target_object=dict(
                parent_class='l3extLIfP',
                aci_class='bfdIfP',
                aci_rn='bfdIfP',
                target_filter={'name': None},
                module_object=ifp
            ),
            child_classes=['bfdRsIfPol']
        )

        assert 'https://local.host.local:443/api/class/bfdIfP.json' == sut.url
        assert '?rsp-subtree=full&rsp-subtree-class=bfdRsIfPol' == sut.filter_string

    def testGreatGreatGrandChildQ12_module_GreatGreatGrandParentValid_GreatGrandParentNone_GrandParentNone_ParentNone_ChildValid_returnsObjectUrlAndFilterStringreturnsObjectUrlAndFilterStringSubtreeFullAndSubtreeClass(self, setup, params):

        params['state'] = 'query'
        module = setup
        module.params.update(params)
        sut = ACIModule(module)
        tenant = 'Test-Tenant'
        out = None
        lnodep = None
        lifp = None
        ifp = 'Test-InterfaceProfile'

        sut.construct_deep_url(
            parent_objects=[
                dict(
                    parent_class='uni',
                    aci_class='fvTenant',
                    aci_rn='tn-{0}'.format(tenant),
                    target_filter={'name': tenant},
                    module_object=tenant
                ),
                dict(
                    parent_class='fvTenant',
                    aci_class='l3extOut',
                    aci_rn='out-{0}'.format(out),
                    target_filter={'name': out},
                    module_object=out
                ),
                dict(
                    parent_class='l3extOut',
                    aci_class='l3extLNodeP',
                    aci_rn='lnodep-{0}'.format(lnodep),
                    target_filter={'name': lnodep},
                    module_object=lnodep
                ),
                dict(
                    parent_class='l3extLNodeP',
                    aci_class='l3extLIfP',
                    aci_rn='lifp-{0}'.format(lifp),
                    target_filter={'name': lifp},
                    module_object=lifp
                )
            ],
            target_object=dict(
                parent_class='l3extLIfP',
                aci_class='bfdIfP',
                aci_rn='bfdIfP',
                target_filter={'name': None},
                module_object=ifp
            ),
            child_classes=['bfdRsIfPol']
        )

        assert 'https://local.host.local:443/api/mo/uni/tn-Test-Tenant.json' == sut.url
        assert '?rsp-subtree=full&rsp-subtree-class=bfdIfP%2CbfdRsIfPol' == sut.filter_string

    def testGreatGreatGrandChildQ13_module_GreatGreatGrandParentValid_GreatGrandParentValid_GrandParentNone_ParentNone_ChildValid_returnsObjectUrlAndFilterStringreturnsObjectUrlAndFilterStringSubtreeFullAndSubtreeClass(self, setup, params):

        params['state'] = 'query'
        module = setup
        module.params.update(params)
        sut = ACIModule(module)
        tenant = 'Test-Tenant'
        out = 'Test-L3Out'
        lnodep = None
        lifp = None
        ifp = 'Test-InterfaceProfile'

        sut.construct_deep_url(
            parent_objects=[
                dict(
                    parent_class='uni',
                    aci_class='fvTenant',
                    aci_rn='tn-{0}'.format(tenant),
                    target_filter={'name': tenant},
                    module_object=tenant
                ),
                dict(
                    parent_class='fvTenant',
                    aci_class='l3extOut',
                    aci_rn='out-{0}'.format(out),
                    target_filter={'name': out},
                    module_object=out
                ),
                dict(
                    parent_class='l3extOut',
                    aci_class='l3extLNodeP',
                    aci_rn='lnodep-{0}'.format(lnodep),
                    target_filter={'name': lnodep},
                    module_object=lnodep
                ),
                dict(
                    parent_class='l3extLNodeP',
                    aci_class='l3extLIfP',
                    aci_rn='lifp-{0}'.format(lifp),
                    target_filter={'name': lifp},
                    module_object=lifp
                )
            ],
            target_object=dict(
                parent_class='l3extLIfP',
                aci_class='bfdIfP',
                aci_rn='bfdIfP',
                target_filter={'name': None},
                module_object=ifp
            ),
            child_classes=['bfdRsIfPol']
        )

        assert 'https://local.host.local:443/api/mo/uni/tn-Test-Tenant/out-Test-L3Out.json' == sut.url
        assert '?rsp-subtree=full&rsp-subtree-class=bfdIfP%2CbfdRsIfPol' == sut.filter_string

    def testGreatGreatGrandChildQ14_module_GreatGreatGrandParentValid_GreatGrandParentNone_GrandParentValid_ParentNone_ChildValid_returnsObjectUrlAndFilterStringreturnsObjectUrlAndFilterStringSubtreeFullAndSubtreeClass(self, setup, params):

        params['state'] = 'query'
        module = setup
        module.params.update(params)
        sut = ACIModule(module)
        tenant = 'Test-Tenant'
        out = None
        lnodep = 'Test-NodeProfile'
        lifp = None
        ifp = 'Test-InterfaceProfile'

        sut.construct_deep_url(
            parent_objects=[
                dict(
                    parent_class='uni',
                    aci_class='fvTenant',
                    aci_rn='tn-{0}'.format(tenant),
                    target_filter={'name': tenant},
                    module_object=tenant
                ),
                dict(
                    parent_class='fvTenant',
                    aci_class='l3extOut',
                    aci_rn='out-{0}'.format(out),
                    target_filter={'name': out},
                    module_object=out
                ),
                dict(
                    parent_class='l3extOut',
                    aci_class='l3extLNodeP',
                    aci_rn='lnodep-{0}'.format(lnodep),
                    target_filter={'name': lnodep},
                    module_object=lnodep
                ),
                dict(
                    parent_class='l3extLNodeP',
                    aci_class='l3extLIfP',
                    aci_rn='lifp-{0}'.format(lifp),
                    target_filter={'name': lifp},
                    module_object=lifp
                )
            ],
            target_object=dict(
                parent_class='l3extLIfP',
                aci_class='bfdIfP',
                aci_rn='bfdIfP',
                target_filter={'name': None},
                module_object=ifp
            ),
            child_classes=['bfdRsIfPol']
        )

        assert 'https://local.host.local:443/api/mo/uni/tn-Test-Tenant.json' == sut.url
        assert '?rsp-subtree=full&rsp-subtree-class=bfdIfP%2CbfdRsIfPol' == sut.filter_string

    def testGreatGreatGrandChildQ15_module_GreatGreatGrandParentValid_GreatGrandParentNone_GrandParentNone_ParentValid_ChildValid_returnsObjectUrlAndFilterStringreturnsObjectUrlAndFilterStringSubtreeFullAndSubtreeClass(self, setup, params):

        params['state'] = 'query'
        module = setup
        module.params.update(params)
        sut = ACIModule(module)
        tenant = 'Test-Tenant'
        out = None
        lnodep = None
        lifp = 'Test-LogicalInterfaceProfile'
        ifp = 'Test-InterfaceProfile'

        sut.construct_deep_url(
            parent_objects=[
                dict(
                    parent_class='uni',
                    aci_class='fvTenant',
                    aci_rn='tn-{0}'.format(tenant),
                    target_filter={'name': tenant},
                    module_object=tenant
                ),
                dict(
                    parent_class='fvTenant',
                    aci_class='l3extOut',
                    aci_rn='out-{0}'.format(out),
                    target_filter={'name': out},
                    module_object=out
                ),
                dict(
                    parent_class='l3extOut',
                    aci_class='l3extLNodeP',
                    aci_rn='lnodep-{0}'.format(lnodep),
                    target_filter={'name': lnodep},
                    module_object=lnodep
                ),
                dict(
                    parent_class='l3extLNodeP',
                    aci_class='l3extLIfP',
                    aci_rn='lifp-{0}'.format(lifp),
                    target_filter={'name': lifp},
                    module_object=lifp
                )
            ],
            target_object=dict(
                parent_class='l3extLIfP',
                aci_class='bfdIfP',
                aci_rn='bfdIfP',
                target_filter={'name': None},
                module_object=ifp
            ),
            child_classes=['bfdRsIfPol']
        )

        assert 'https://local.host.local:443/api/mo/uni/tn-Test-Tenant.json' == sut.url
        assert '?rsp-subtree=full&rsp-subtree-class=bfdIfP%2CbfdRsIfPol' == sut.filter_string

    def testGreatGreatGrandChildQ16_module_GreatGreatGrandParentValid_GreatGrandParentValid_GrandParentNone_ParentValid_ChildValid_returnsObjectUrlAndFilterStringreturnsObjectUrlAndFilterStringSubtreeFullAndSubtreeClass(self, setup, params):

        params['state'] = 'query'
        module = setup
        module.params.update(params)
        sut = ACIModule(module)
        tenant = 'Test-Tenant'
        out = 'Test-L3Out'
        lnodep = None
        lifp = 'Test-LogicalInterfaceProfile'
        ifp = 'Test-InterfaceProfile'

        sut.construct_deep_url(
            parent_objects=[
                dict(
                    parent_class='uni',
                    aci_class='fvTenant',
                    aci_rn='tn-{0}'.format(tenant),
                    target_filter={'name': tenant},
                    module_object=tenant
                ),
                dict(
                    parent_class='fvTenant',
                    aci_class='l3extOut',
                    aci_rn='out-{0}'.format(out),
                    target_filter={'name': out},
                    module_object=out
                ),
                dict(
                    parent_class='l3extOut',
                    aci_class='l3extLNodeP',
                    aci_rn='lnodep-{0}'.format(lnodep),
                    target_filter={'name': lnodep},
                    module_object=lnodep
                ),
                dict(
                    parent_class='l3extLNodeP',
                    aci_class='l3extLIfP',
                    aci_rn='lifp-{0}'.format(lifp),
                    target_filter={'name': lifp},
                    module_object=lifp
                )
            ],
            target_object=dict(
                parent_class='l3extLIfP',
                aci_class='bfdIfP',
                aci_rn='bfdIfP',
                target_filter={'name': None},
                module_object=ifp
            ),
            child_classes=['bfdRsIfPol']
        )

        assert 'https://local.host.local:443/api/mo/uni/tn-Test-Tenant/out-Test-L3Out.json' == sut.url
        assert '?rsp-subtree=full&rsp-subtree-class=bfdIfP%2CbfdRsIfPol' == sut.filter_string

    def testGreatGreatGrandChildQ17_module_GreatGreatGrandParentValid_GreatGrandParentNone_GrandParentValid_ParentValid_ChildValid_returnsObjectUrlAndFilterStringreturnsObjectUrlAndFilterStringSubtreeFullAndSubtreeClass(self, setup, params):

        params['state'] = 'query'
        module = setup
        module.params.update(params)
        sut = ACIModule(module)
        tenant = 'Test-Tenant'
        out = None
        lnodep = 'Test-NodeProfile'
        lifp = 'Test-LogicalInterfaceProfile'
        ifp = 'Test-InterfaceProfile'

        sut.construct_deep_url(
            parent_objects=[
                dict(
                    parent_class='uni',
                    aci_class='fvTenant',
                    aci_rn='tn-{0}'.format(tenant),
                    target_filter={'name': tenant},
                    module_object=tenant
                ),
                dict(
                    parent_class='fvTenant',
                    aci_class='l3extOut',
                    aci_rn='out-{0}'.format(out),
                    target_filter={'name': out},
                    module_object=out
                ),
                dict(
                    parent_class='l3extOut',
                    aci_class='l3extLNodeP',
                    aci_rn='lnodep-{0}'.format(lnodep),
                    target_filter={'name': lnodep},
                    module_object=lnodep
                ),
                dict(
                    parent_class='l3extLNodeP',
                    aci_class='l3extLIfP',
                    aci_rn='lifp-{0}'.format(lifp),
                    target_filter={'name': lifp},
                    module_object=lifp
                )
            ],
            target_object=dict(
                parent_class='l3extLIfP',
                aci_class='bfdIfP',
                aci_rn='bfdIfP',
                target_filter={'name': None},
                module_object=ifp
            ),
            child_classes=['bfdRsIfPol']
        )

        assert 'https://local.host.local:443/api/mo/uni/tn-Test-Tenant.json' == sut.url
        assert '?rsp-subtree=full&rsp-subtree-class=bfdIfP%2CbfdRsIfPol' == sut.filter_string

    def testGreatGreatGrandChildQ18_module_GreatGreatGrandParentNone_GreatGrandParentValid_GrandParentNone_ParentValid_ChildValid_returnsObjectUrlAndFilterStringreturnsObjectUrlAndFilterStringSubtreeFullAndSubtreeClass(self, setup, params):

        params['state'] = 'query'
        module = setup
        module.params.update(params)
        sut = ACIModule(module)
        tenant = None
        out = 'Test-L3Out'
        lnodep = None
        lifp = 'Test-LogicalInterfaceProfile'
        ifp = 'Test-InterfaceProfile'

        sut.construct_deep_url(
            parent_objects=[
                dict(
                    parent_class='uni',
                    aci_class='fvTenant',
                    aci_rn='tn-{0}'.format(tenant),
                    target_filter={'name': tenant},
                    module_object=tenant
                ),
                dict(
                    parent_class='fvTenant',
                    aci_class='l3extOut',
                    aci_rn='out-{0}'.format(out),
                    target_filter={'name': out},
                    module_object=out
                ),
                dict(
                    parent_class='l3extOut',
                    aci_class='l3extLNodeP',
                    aci_rn='lnodep-{0}'.format(lnodep),
                    target_filter={'name': lnodep},
                    module_object=lnodep
                ),
                dict(
                    parent_class='l3extLNodeP',
                    aci_class='l3extLIfP',
                    aci_rn='lifp-{0}'.format(lifp),
                    target_filter={'name': lifp},
                    module_object=lifp
                )
            ],
            target_object=dict(
                parent_class='l3extLIfP',
                aci_class='bfdIfP',
                aci_rn='bfdIfP',
                target_filter={'name': None},
                module_object=ifp
            ),
            child_classes=['bfdRsIfPol']
        )

        assert 'https://local.host.local:443/api/class/l3extOut.json' == sut.url
        assert '?query-target-filter=eq%28l3extOut.name%2C+%22Test-L3Out%22%29&rsp-subtree=full&rsp-subtree-class=bfdIfP%2CbfdRsIfPol' == sut.filter_string

    def testGreatGreatGrandChildQ19_module_GreatGreatGrandParentNone_GreatGrandParentValid_GrandParentNone_ParentNone_ChildValid_returnsObjectUrlAndFilterStringreturnsObjectUrlAndFilterStringSubtreeFullAndSubtreeClass(self, setup, params):

        params['state'] = 'query'
        module = setup
        module.params.update(params)
        sut = ACIModule(module)
        tenant = None
        out = 'Test-L3Out'
        lnodep = None
        lifp = None
        ifp = 'Test-InterfaceProfile'

        sut.construct_deep_url(
            parent_objects=[
                dict(
                    parent_class='uni',
                    aci_class='fvTenant',
                    aci_rn='tn-{0}'.format(tenant),
                    target_filter={'name': tenant},
                    module_object=tenant
                ),
                dict(
                    parent_class='fvTenant',
                    aci_class='l3extOut',
                    aci_rn='out-{0}'.format(out),
                    target_filter={'name': out},
                    module_object=out
                ),
                dict(
                    parent_class='l3extOut',
                    aci_class='l3extLNodeP',
                    aci_rn='lnodep-{0}'.format(lnodep),
                    target_filter={'name': lnodep},
                    module_object=lnodep
                ),
                dict(
                    parent_class='l3extLNodeP',
                    aci_class='l3extLIfP',
                    aci_rn='lifp-{0}'.format(lifp),
                    target_filter={'name': lifp},
                    module_object=lifp
                )
            ],
            target_object=dict(
                parent_class='l3extLIfP',
                aci_class='bfdIfP',
                aci_rn='bfdIfP',
                target_filter={'name': None},
                module_object=ifp
            ),
            child_classes=['bfdRsIfPol']
        )

        assert 'https://local.host.local:443/api/class/l3extOut.json' == sut.url
        assert '?query-target-filter=eq%28l3extOut.name%2C+%22Test-L3Out%22%29&rsp-subtree=full&rsp-subtree-class=bfdIfP%2CbfdRsIfPol' == sut.filter_string

    def testGreatGreatGrandChildQ20_module_GreatGreatGrandParentNone_GreatGrandParentValid_GrandParentNone_ParentNone_ChildNone_returnsObjectUrlAndFilterStringreturnsObjectUrlAndFilterStringSubtreeFullAndSubtreeClass(self, setup, params):

        params['state'] = 'query'
        module = setup
        module.params.update(params)
        sut = ACIModule(module)
        tenant = None
        out = 'Test-L3Out'
        lnodep = None
        lifp = None
        ifp = None

        sut.construct_deep_url(
            parent_objects=[
                dict(
                    parent_class='uni',
                    aci_class='fvTenant',
                    aci_rn='tn-{0}'.format(tenant),
                    target_filter={'name': tenant},
                    module_object=tenant
                ),
                dict(
                    parent_class='fvTenant',
                    aci_class='l3extOut',
                    aci_rn='out-{0}'.format(out),
                    target_filter={'name': out},
                    module_object=out
                ),
                dict(
                    parent_class='l3extOut',
                    aci_class='l3extLNodeP',
                    aci_rn='lnodep-{0}'.format(lnodep),
                    target_filter={'name': lnodep},
                    module_object=lnodep
                ),
                dict(
                    parent_class='l3extLNodeP',
                    aci_class='l3extLIfP',
                    aci_rn='lifp-{0}'.format(lifp),
                    target_filter={'name': lifp},
                    module_object=lifp
                )
            ],
            target_object=dict(
                parent_class='l3extLIfP',
                aci_class='bfdIfP',
                aci_rn='bfdIfP',
                target_filter={'name': None},
                module_object=ifp
            ),
            child_classes=['bfdRsIfPol']
        )

        assert 'https://local.host.local:443/api/class/l3extOut.json' == sut.url
        assert '?rsp-subtree=full&rsp-subtree-class=bfdRsIfPol' == sut.filter_string

    def testGreatGreatGrandChildQ21_module_GreatGreatGrandParentNone_GreatGrandParentValid_GrandParentValid_ParentNone_ChildNone_returnsObjectUrlAndFilterStringreturnsObjectUrlAndFilterStringSubtreeFullAndSubtreeClass(self, setup, params):

        params['state'] = 'query'
        module = setup
        module.params.update(params)
        sut = ACIModule(module)
        tenant = None
        out = 'Test-L3Out'
        lnodep = 'Test-NodeProfile'
        lifp = None
        ifp = None

        sut.construct_deep_url(
            parent_objects=[
                dict(
                    parent_class='uni',
                    aci_class='fvTenant',
                    aci_rn='tn-{0}'.format(tenant),
                    target_filter={'name': tenant},
                    module_object=tenant
                ),
                dict(
                    parent_class='fvTenant',
                    aci_class='l3extOut',
                    aci_rn='out-{0}'.format(out),
                    target_filter={'name': out},
                    module_object=out
                ),
                dict(
                    parent_class='l3extOut',
                    aci_class='l3extLNodeP',
                    aci_rn='lnodep-{0}'.format(lnodep),
                    target_filter={'name': lnodep},
                    module_object=lnodep
                ),
                dict(
                    parent_class='l3extLNodeP',
                    aci_class='l3extLIfP',
                    aci_rn='lifp-{0}'.format(lifp),
                    target_filter={'name': lifp},
                    module_object=lifp
                )
            ],
            target_object=dict(
                parent_class='l3extLIfP',
                aci_class='bfdIfP',
                aci_rn='bfdIfP',
                target_filter={'name': None},
                module_object=ifp
            ),
            child_classes=['bfdRsIfPol']
        )

        assert 'https://local.host.local:443/api/class/l3extOut.json' == sut.url
        assert '?rsp-subtree=full&rsp-subtree-class=bfdRsIfPol' == sut.filter_string

    def testGreatGreatGrandChildQ22_module_GreatGreatGrandParentNone_GreatGrandParentValid_GrandParentValid_ParentValid_ChildNone_returnsObjectUrlAndFilterStringreturnsObjectUrlAndFilterStringSubtreeFullAndSubtreeClass(self, setup, params):

        params['state'] = 'query'
        module = setup
        module.params.update(params)
        sut = ACIModule(module)
        tenant = None
        out = 'Test-L3Out'
        lnodep = 'Test-NodeProfile'
        lifp = 'Test-LogicalInterfaceProfile'
        ifp = None

        sut.construct_deep_url(
            parent_objects=[
                dict(
                    parent_class='uni',
                    aci_class='fvTenant',
                    aci_rn='tn-{0}'.format(tenant),
                    target_filter={'name': tenant},
                    module_object=tenant
                ),
                dict(
                    parent_class='fvTenant',
                    aci_class='l3extOut',
                    aci_rn='out-{0}'.format(out),
                    target_filter={'name': out},
                    module_object=out
                ),
                dict(
                    parent_class='l3extOut',
                    aci_class='l3extLNodeP',
                    aci_rn='lnodep-{0}'.format(lnodep),
                    target_filter={'name': lnodep},
                    module_object=lnodep
                ),
                dict(
                    parent_class='l3extLNodeP',
                    aci_class='l3extLIfP',
                    aci_rn='lifp-{0}'.format(lifp),
                    target_filter={'name': lifp},
                    module_object=lifp
                )
            ],
            target_object=dict(
                parent_class='l3extLIfP',
                aci_class='bfdIfP',
                aci_rn='bfdIfP',
                target_filter={'name': None},
                module_object=ifp
            ),
            child_classes=['bfdRsIfPol']
        )

        assert 'https://local.host.local:443/api/class/l3extOut.json' == sut.url
        assert '?rsp-subtree=full&rsp-subtree-class=bfdRsIfPol' == sut.filter_string

    def testGreatGreatGrandChildQ23_module_GreatGreatGrandParentNone_GreatGrandParentNone_GrandParentValid_ParentValid_ChildNone_returnsObjectUrlAndFilterStringreturnsObjectUrlAndFilterStringSubtreeFullAndSubtreeClass(self, setup, params):

        params['state'] = 'query'
        module = setup
        module.params.update(params)
        sut = ACIModule(module)
        tenant = None
        out = None
        lnodep = 'Test-NodeProfile'
        lifp = 'Test-LogicalInterfaceProfile'
        ifp = None

        sut.construct_deep_url(
            parent_objects=[
                dict(
                    parent_class='uni',
                    aci_class='fvTenant',
                    aci_rn='tn-{0}'.format(tenant),
                    target_filter={'name': tenant},
                    module_object=tenant
                ),
                dict(
                    parent_class='fvTenant',
                    aci_class='l3extOut',
                    aci_rn='out-{0}'.format(out),
                    target_filter={'name': out},
                    module_object=out
                ),
                dict(
                    parent_class='l3extOut',
                    aci_class='l3extLNodeP',
                    aci_rn='lnodep-{0}'.format(lnodep),
                    target_filter={'name': lnodep},
                    module_object=lnodep
                ),
                dict(
                    parent_class='l3extLNodeP',
                    aci_class='l3extLIfP',
                    aci_rn='lifp-{0}'.format(lifp),
                    target_filter={'name': lifp},
                    module_object=lifp
                )
            ],
            target_object=dict(
                parent_class='l3extLIfP',
                aci_class='bfdIfP',
                aci_rn='bfdIfP',
                target_filter={'name': None},
                module_object=ifp
            ),
            child_classes=['bfdRsIfPol']
        )

        assert 'https://local.host.local:443/api/class/l3extLNodeP.json' == sut.url
        assert '?rsp-subtree=full&rsp-subtree-class=bfdRsIfPol' == sut.filter_string

    def testGreatGreatGrandChildQ24_module_GreatGreatGrandParentNone_GreatGrandParentNone_GrandParentValid_ParentNone_ChildNone_returnsObjectUrlAndFilterStringreturnsObjectUrlAndFilterStringSubtreeFullAndSubtreeClass(self, setup, params):

        params['state'] = 'query'
        module = setup
        module.params.update(params)
        sut = ACIModule(module)
        tenant = None
        out = None
        lnodep = 'Test-NodeProfile'
        lifp = None
        ifp = None

        sut.construct_deep_url(
            parent_objects=[
                dict(
                    parent_class='uni',
                    aci_class='fvTenant',
                    aci_rn='tn-{0}'.format(tenant),
                    target_filter={'name': tenant},
                    module_object=tenant
                ),
                dict(
                    parent_class='fvTenant',
                    aci_class='l3extOut',
                    aci_rn='out-{0}'.format(out),
                    target_filter={'name': out},
                    module_object=out
                ),
                dict(
                    parent_class='l3extOut',
                    aci_class='l3extLNodeP',
                    aci_rn='lnodep-{0}'.format(lnodep),
                    target_filter={'name': lnodep},
                    module_object=lnodep
                ),
                dict(
                    parent_class='l3extLNodeP',
                    aci_class='l3extLIfP',
                    aci_rn='lifp-{0}'.format(lifp),
                    target_filter={'name': lifp},
                    module_object=lifp
                )
            ],
            target_object=dict(
                parent_class='l3extLIfP',
                aci_class='bfdIfP',
                aci_rn='bfdIfP',
                target_filter={'name': None},
                module_object=ifp
            ),
            child_classes=['bfdRsIfPol']
        )

        assert 'https://local.host.local:443/api/class/l3extLNodeP.json' == sut.url
        assert '?rsp-subtree=full&rsp-subtree-class=bfdRsIfPol' == sut.filter_string

    def testGreatGreatGrandChildQ25_module_GreatGreatGrandParentNone_GreatGrandParentNone_GrandParentNone_ParentValid_ChildNone_returnsObjectUrlAndFilterStringreturnsObjectUrlAndFilterStringSubtreeFullAndSubtreeClass(self, setup, params):

        params['state'] = 'query'
        module = setup
        module.params.update(params)
        sut = ACIModule(module)
        tenant = None
        out = None
        lnodep = None
        lifp = 'Test-LogicalInterfaceProfile'
        ifp = None

        sut.construct_deep_url(
            parent_objects=[
                dict(
                    parent_class='uni',
                    aci_class='fvTenant',
                    aci_rn='tn-{0}'.format(tenant),
                    target_filter={'name': tenant},
                    module_object=tenant
                ),
                dict(
                    parent_class='fvTenant',
                    aci_class='l3extOut',
                    aci_rn='out-{0}'.format(out),
                    target_filter={'name': out},
                    module_object=out
                ),
                dict(
                    parent_class='l3extOut',
                    aci_class='l3extLNodeP',
                    aci_rn='lnodep-{0}'.format(lnodep),
                    target_filter={'name': lnodep},
                    module_object=lnodep
                ),
                dict(
                    parent_class='l3extLNodeP',
                    aci_class='l3extLIfP',
                    aci_rn='lifp-{0}'.format(lifp),
                    target_filter={'name': lifp},
                    module_object=lifp
                )
            ],
            target_object=dict(
                parent_class='l3extLIfP',
                aci_class='bfdIfP',
                aci_rn='bfdIfP',
                target_filter={'name': None},
                module_object=ifp
            ),
            child_classes=['bfdRsIfPol']
        )

        assert 'https://local.host.local:443/api/class/l3extLIfP.json' == sut.url
        assert '?rsp-subtree=full&rsp-subtree-class=bfdRsIfPol' == sut.filter_string
