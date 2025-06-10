from __future__ import annotations


def _respawn_main(
    json_params: bytes,
    profile: str,
    module_fqn: str,
    modlib_path: str,
) -> None:
    import sys

    sys.path.insert(0, modlib_path)

    from ansible.module_utils._internal._ansiballz import _loader

    _loader.run_module(
        json_params=json_params,
        profile=profile,
        module_fqn=module_fqn,
        modlib_path=modlib_path,
        extensions={},
        init_globals=dict(_respawned=True),
    )
