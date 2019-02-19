import pytest

from ansible.module_utils.kubevirt import KubeAPIVersion


@pytest.mark.parametrize("lval, operations, rval, result", [
    ('v1', ['<', '<='], 'v2', True),
    ('v1', ['>', '>=', '=='], 'v2', False),
    ('v1', ['>'], 'v1alpha1', True),
    ('v1', ['==', '<', '<='], 'v1alpha1', False),
    ('v1beta5', ['==', '<=', '>='], 'v1beta5', True),
    ('v1beta5', ['<', '>', '!='], 'v1beta5', False),

])
def test_kubeapiversion_comparisons(lval, operations, rval, result):
    for op in operations:
        test = '(KubeAPIVersion("{0}") {1} KubeAPIVersion("{2}")) == {3}'.format(lval, op, rval, result)
        assert eval(test)


@pytest.mark.parametrize("ver", ('nope', 'v1delta7', '1.5', 'v1beta', 'v'))
def test_unsupported_versions(ver):
    threw = False
    try:
        KubeAPIVersion(ver)
    except ValueError:
        threw = True
    assert threw
