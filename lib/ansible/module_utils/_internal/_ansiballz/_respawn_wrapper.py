from __future__ import annotations


def _respawn_main(
    json_params: bytes,
    profile: str,
    module_fqn: str,
    modlib_path: str,
) -> None:
    import sys
    import runpy

    sys.path.insert(0, modlib_path)

    from ansible.module_utils import basic
    from ansible.module_utils._internal._ansiballz import _loader

    basic._ANSIBLE_ARGS = json_params
    basic._ANSIBLE_PROFILE = profile

    init_globals = dict(_respawned=True, _module_fqn=module_fqn, _modlib_path=modlib_path)

    try:
        runpy.run_module(mod_name=module_fqn, init_globals=init_globals, run_name='__main__', alter_sys=True)

        raise RuntimeError('New-style module did not handle its own exit.')
    except Exception as e:
        _loader._handle_exception(e, profile)
