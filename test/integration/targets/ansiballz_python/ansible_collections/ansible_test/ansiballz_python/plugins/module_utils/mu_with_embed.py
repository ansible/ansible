ANSIBLE_EMBED = (('ansible_collections.ansible_test.ansiballz_python.plugins.module_utils', 'embed_this.py'),)

some_value = 42  # ignore single assignments not involving ANSIBLE_EMBED
x = y = "z"  # ignore multiple assignments not involving ANSIBLE_EMBED
zzz = ANSIBLE_EMBED  # ignore ANSIBLE_EMBED on RHS

foo = []
foo[:] = [123]  # ignore slice assignments not involving ANSIBLE_EMBED

a, b = (42, 42)  # ignore tuple unpacking not involving ANSIBLE_EMBED
