import json
import pytest

from ansible.module_utils import kubevirt as mymodule


def test_simple_merge_dicts():
    dict1 = {'labels': {'label1': 'value'}}
    dict2 = {'labels': {'label2': 'value'}}
    dict3 = json.dumps({'labels': {'label1': 'value', 'label2': 'value'}}, sort_keys=True)
    assert dict3 == json.dumps(dict(mymodule.KubeVirtRawModule.merge_dicts(dict1, dict2)), sort_keys=True)


def test_simple_multi_merge_dicts():
    dict1 = {'labels': {'label1': 'value', 'label3': 'value'}}
    dict2 = {'labels': {'label2': 'value'}}
    dict3 = json.dumps({'labels': {'label1': 'value', 'label2': 'value', 'label3': 'value'}}, sort_keys=True)
    assert dict3 == json.dumps(dict(mymodule.KubeVirtRawModule.merge_dicts(dict1, dict2)), sort_keys=True)


def test_double_nested_merge_dicts():
    dict1 = {'metadata': {'labels': {'label1': 'value', 'label3': 'value'}}}
    dict2 = {'metadata': {'labels': {'label2': 'value'}}}
    dict3 = json.dumps({'metadata': {'labels': {'label1': 'value', 'label2': 'value', 'label3': 'value'}}}, sort_keys=True)
    assert dict3 == json.dumps(dict(mymodule.KubeVirtRawModule.merge_dicts(dict1, dict2)), sort_keys=True)


@pytest.mark.parametrize("lval, operations, rval, result", [
    ('v1', ['<', '<='], 'v2', True),
    ('v1', ['>', '>=', '=='], 'v2', False),
    ('v1', ['>'], 'v1alpha1', True),
    ('v1', ['==', '<', '<='], 'v1alpha1', False),
    ('v1beta5', ['==', '<=', '>='], 'v1beta5', True),
    ('v1beta5', ['<', '>', '!='], 'v1beta5', False),

])
def test_kubeapiversion_comparisons(lval, operations, rval, result):
    KubeAPIVersion = mymodule.KubeAPIVersion
    for op in operations:
        test = '(KubeAPIVersion("{0}") {1} KubeAPIVersion("{2}")) == {3}'.format(lval, op, rval, result)
        assert eval(test)


@pytest.mark.parametrize("ver", ('nope', 'v1delta7', '1.5', 'v1beta', 'v'))
def test_kubeapiversion_unsupported_versions(ver):
    threw = False
    try:
        mymodule.KubeAPIVersion(ver)
    except ValueError:
        threw = True
    assert threw
