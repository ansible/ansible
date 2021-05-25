#!/usr/bin/python
# Most of these names are only available via PluginLoader so pylint doesn't
# know they exist
# pylint: disable=no-name-in-module
__metaclass__ = type

results = {}

# Test import with no from
import ansible.module_utils.foo0
results['foo0'] = ansible.module_utils.foo0.data

# Test depthful import with no from
import ansible.module_utils.bar0.foo
results['bar0'] = ansible.module_utils.bar0.foo.data

# Test import of module_utils/foo1.py
from ansible.module_utils import foo1
results['foo1'] = foo1.data

# Test import of an identifier inside of module_utils/foo2.py
from ansible.module_utils.foo2 import data
results['foo2'] = data

# Test import of module_utils/bar1/__init__.py
from ansible.module_utils import bar1
results['bar1'] = bar1.data

# Test import of an identifier inside of module_utils/bar2/__init__.py
from ansible.module_utils.bar2 import data
results['bar2'] = data

# Test import of module_utils/baz1/one.py
from ansible.module_utils.baz1 import one
results['baz1'] = one.data

# Test import of an identifier inside of module_utils/baz2/one.py
from ansible.module_utils.baz2.one import data
results['baz2'] = data

# Test import of module_utils/spam1/ham/eggs/__init__.py
from ansible.module_utils.spam1.ham import eggs
results['spam1'] = eggs.data

# Test import of an identifier inside module_utils/spam2/ham/eggs/__init__.py
from ansible.module_utils.spam2.ham.eggs import data
results['spam2'] = data

# Test import of module_utils/spam3/ham/bacon.py
from ansible.module_utils.spam3.ham import bacon
results['spam3'] = bacon.data

# Test import of an identifier inside of module_utils/spam4/ham/bacon.py
from ansible.module_utils.spam4.ham.bacon import data
results['spam4'] = data

# Test import of module_utils.spam5.ham bacon and eggs (modules)
from ansible.module_utils.spam5.ham import bacon, eggs
results['spam5'] = (bacon.data, eggs.data)

# Test import of module_utils.spam6.ham bacon and eggs (identifiers)
from ansible.module_utils.spam6.ham import bacon, eggs
results['spam6'] = (bacon, eggs)

# Test import of module_utils.spam7.ham bacon and eggs (module and identifier)
from ansible.module_utils.spam7.ham import bacon, eggs
results['spam7'] = (bacon.data, eggs)

# Test import of module_utils/spam8/ham/bacon.py and module_utils/spam8/ham/eggs.py separately
from ansible.module_utils.spam8.ham import bacon
from ansible.module_utils.spam8.ham import eggs
results['spam8'] = (bacon.data, eggs)

# Test that import of module_utils/qux1/quux.py using as works
from ansible.module_utils.qux1 import quux as one
results['qux1'] = one.data

# Test that importing qux2/quux.py and qux2/quuz.py using as works
from ansible.module_utils.qux2 import quux as one, quuz as two
results['qux2'] = (one.data, two.data)

# Test depth
from ansible.module_utils.a.b.c.d.e.f.g.h import data

results['abcdefgh'] = data
from ansible.module_utils.basic import AnsibleModule
AnsibleModule(argument_spec=dict()).exit_json(**results)
