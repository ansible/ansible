from __future__ import annotations

import json
import os
import os.path
import pathlib


def main() -> None:
    collection_root = pathlib.Path(os.getcwd())
    print(f"Running windows-integration coverage test in '{collection_root}'")

    result_path = collection_root / "tests" / "output" / "coverage" / "coverage-powershell"
    adjacent_modules_path = collection_root / "tests" / "integration" / "targets" / "win_collection" / "library"
    adjacent_utils_path = collection_root / "tests" / "integration" / "targets" / "win_collection" / "module_utils"
    collection_modules_path = collection_root / "plugins" / "modules"
    collection_utils_path = collection_root / "plugins" / "module_utils"

    expected_hits = {
        str(adjacent_modules_path / 'test_win_collection_async.ps1'): {'5': 1, '6': 1},
        str(adjacent_modules_path / 'test_win_collection_become.ps1'): {'5': 1, '6': 1},
        str(adjacent_modules_path / 'test_win_collection_normal.ps1'): {'6': 1, '7': 1, '8': 1},
        str(adjacent_utils_path / 'Ansible.ModuleUtils.AdjacentPwshCoverage.psm1'): {'6': 1, '9': 1},
        str(collection_modules_path / 'win_collection.ps1'): {'6': 1, '7': 1, '8': 1},
        str(collection_utils_path / 'CollectionPwshCoverage.psm1'): {'6': 1, '9': 1},
    }
    found_hits = set()

    with open(result_path, mode="rb") as fd:
        data = json.load(fd)

    for path, result in data.items():
        print(f"Testing result for path '{path}' -> {result!r}")
        assert path in expected_hits, f"Found unexpected coverage result path '{path}'"

        expected = expected_hits[path]
        assert result == expected, f"Coverage result for {path} was {result!r} but was expecting {expected!r}"
        found_hits.add(path)

    missing_hits = set(expected_hits.keys()).difference(found_hits)
    assert not missing_hits, f"Expected coverage results for {', '.join(missing_hits)} but they were not present"


if __name__ == '__main__':
    main()
