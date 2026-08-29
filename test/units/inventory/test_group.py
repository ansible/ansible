# Copyright 2018 Alan Rominger <arominge@redhat.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import pytest

from ansible.inventory.group import Group, to_safe_group_name
from ansible.inventory.host import Host
from ansible.errors import AnsibleError
from ansible import constants as C
from ansible.plugins.inventory import to_safe_group_name as wrapper_to_safe_group_name
from ansible.plugins.inventory import BaseInventoryPlugin
from units.test_utils.controller.display import emits_warnings


def test_depth_update():
    A = Group('A')
    B = Group('B')
    Z = Group('Z')
    A.add_child_group(B)
    A.add_child_group(Z)
    assert A.depth == 0
    assert Z.depth == 1
    assert B.depth == 1


def test_depth_update_dual_branches():
    alpha = Group('alpha')
    A = Group('A')
    alpha.add_child_group(A)
    B = Group('B')
    A.add_child_group(B)
    Z = Group('Z')
    alpha.add_child_group(Z)
    beta = Group('beta')
    B.add_child_group(beta)
    Z.add_child_group(beta)

    assert alpha.depth == 0  # apex
    assert beta.depth == 3  # alpha -> A -> B -> beta

    omega = Group('omega')
    omega.add_child_group(alpha)

    # verify that both paths are traversed to get the max depth value
    assert B.depth == 3  # omega -> alpha -> A -> B
    assert beta.depth == 4  # B -> beta


def test_depth_recursion():
    A = Group('A')
    B = Group('B')
    A.add_child_group(B)
    # hypothetical of adding B as child group to A
    A.parent_groups.append(B)
    B.child_groups.append(A)
    # can't update depths of groups, because of loop
    with pytest.raises(AnsibleError):
        B._check_children_depth()


def test_loop_detection():
    A = Group('A')
    B = Group('B')
    C = Group('C')
    A.add_child_group(B)
    B.add_child_group(C)
    with pytest.raises(AnsibleError):
        C.add_child_group(A)


def test_direct_host_ordering():
    """Hosts are returned in order they are added
    """
    group = Group('A')
    # host names not added in alphabetical order
    host_name_list = ['z', 'b', 'c', 'a', 'p', 'q']
    expected_hosts = []
    for host_name in host_name_list:
        h = Host(host_name)
        group.add_host(h)
        expected_hosts.append(h)
    assert group.get_hosts() == expected_hosts


def test_sub_group_host_ordering():
    """With multiple nested groups, asserts that hosts are returned
    in deterministic order
    """
    top_group = Group('A')
    expected_hosts = []
    for name in ['z', 'b', 'c', 'a', 'p', 'q']:
        child = Group('group_{0}'.format(name))
        top_group.add_child_group(child)
        host = Host('host_{0}'.format(name))
        child.add_host(host)
        expected_hosts.append(host)
    assert top_group.get_hosts() == expected_hosts


def test_populates_descendant_hosts():
    A = Group('A')
    B = Group('B')
    C = Group('C')
    h = Host('h')
    C.add_host(h)
    A.add_child_group(B)  # B is child of A
    B.add_child_group(C)  # C is descendant of A
    A.add_child_group(B)
    assert set(h.groups) == set([C, B, A])
    h2 = Host('h2')
    C.add_host(h2)
    assert set(h2.groups) == set([C, B, A])


def test_ancestor_example():
    # see docstring for Group._walk_relationship
    groups = {}
    for name in ['A', 'B', 'C', 'D', 'E', 'F']:
        groups[name] = Group(name)
    # first row
    groups['A'].add_child_group(groups['D'])
    groups['B'].add_child_group(groups['D'])
    groups['B'].add_child_group(groups['E'])
    groups['C'].add_child_group(groups['D'])
    # second row
    groups['D'].add_child_group(groups['E'])
    groups['D'].add_child_group(groups['F'])
    groups['E'].add_child_group(groups['F'])

    assert (
        set(groups['F'].get_ancestors()) ==
        set([
            groups['A'], groups['B'], groups['C'], groups['D'], groups['E']
        ])
    )


def test_ancestors_recursive_loop_safe():
    """
    The get_ancestors method may be referenced before circular parenting
    checks, so the method is expected to be stable even with loops
    """
    A = Group('A')
    B = Group('B')
    A.parent_groups.append(B)
    B.parent_groups.append(A)
    # finishes in finite time
    assert A.get_ancestors() == set([A, B])


@pytest.mark.parametrize("priority, expected", [
    pytest.param(5, 5, id="int"),
    pytest.param('10', 10, id="string"),
    pytest.param(-1, -1, id="negative number"),
])
def test_set_priority_valid_values(priority, expected):
    """Test that valid priority value is set"""
    group = Group('test_group')
    group.set_priority(priority)
    assert group.priority == expected


@pytest.mark.parametrize("priority, expected", [
    pytest.param('invalid', 1, id="invalid string"),
    pytest.param(None, 1, id="None"),
    pytest.param({'key': 'value'}, 1, id="dict"),
    pytest.param(['item'], 1, id="list")
])
def test_set_priority_invalid_values(priority, expected):
    """Test that invalid priority value is handled gracefully with warnings"""
    group = Group('test_group')
    group.set_priority(priority)
    assert group.priority == expected


@pytest.fixture
def force_transform_always(monkeypatch):
    """Ensure group name transformation is always enabled for testing."""
    monkeypatch.setattr(C, 'TRANSFORM_INVALID_GROUP_CHARS', 'always')


def test_to_safe_group_name_valid_unchanged():
    """Valid group names should pass through unchanged."""
    assert to_safe_group_name('valid_group') == 'valid_group'
    assert to_safe_group_name('group123') == 'group123'


def test_to_safe_group_name_hyphen_normalized():
    """Hyphens should be replaced with underscores."""
    assert to_safe_group_name('qa-windows', force=True) == 'qa_windows'
    assert to_safe_group_name('prod-linux-web', force=True) == 'prod_linux_web'


def test_to_safe_group_name_warning_emitted(force_transform_always):
    """Warning should be emitted when normalizing with silent=False."""
    with emits_warnings(warning_pattern=r'Invalid characters were found in group names'):
        result = to_safe_group_name('qa-windows', force=True, silent=False)

    assert result == 'qa_windows'


def test_to_safe_group_name_warning_suppressed_when_silent(force_transform_always):
    """Warning should be suppressed when silent=True."""
    # Empty pattern list with allow_unmatched_message=True verifies NO warnings
    with emits_warnings(warning_pattern=[], allow_unmatched_message=True):
        result = to_safe_group_name('qa-windows', force=True, silent=True)

    assert result == 'qa_windows'


def test_plugin_wrapper_emits_warnings(force_transform_always):
    """
    Plugin wrapper should emit warnings after fix (silent=True removed).

    NOTE: This test validates the FIXED behavior. It will FAIL on devel
    (where silent=True is present) and PASS after our change is applied.
    """
    with emits_warnings(warning_pattern=r'Invalid characters were found in group names'):
        result = wrapper_to_safe_group_name('qa-windows')

    assert result == 'qa_windows'


def test_plugin_wrapper_via_sanitize_group_name(force_transform_always):
    """
    Test wrapper through actual code path used by Constructable mixin.

    NOTE: This test validates the FIXED behavior. Tests the full integration:
    BaseInventoryPlugin._sanitize_group_name → wrapper → to_safe_group_name
    """
    with emits_warnings(warning_pattern=r'Invalid characters were found in group names'):
        plugin = BaseInventoryPlugin()
        result = plugin._sanitize_group_name('qa-windows')

    assert result == 'qa_windows'
