from __future__ import annotations

import json
import os
import os.path


def main() -> None:
    collection_root = os.getcwd()
    print(f"Running windows-integration coverage test in '{collection_root}'")

    result_path = os.path.join(collection_root, "tests", "output", "coverage", "coverage-powershell")
    module_path = os.path.join(collection_root, "plugins", "modules", "win_collection.ps1")
    test_path = os.path.join(collection_root, "tests", "integration", "targets", "win_collection", "library", "test_win_collection.ps1")
    with open(result_path, mode="rb") as fd:
        data = json.load(fd)

    for path, result in data.items():
        print(f"Testing result for path '{path}' -> {result!r}")
        assert path in [module_path, test_path], f"Found unexpected coverage result path '{path}'"
        assert result == {'5': 1, '6': 1}, "Coverage result did not pick up a hit on lines 5 and 6"

    assert len(data) == 2, f"Expected coverage results for 2 files but got {len(data)}"


if __name__ == '__main__':
    main()
