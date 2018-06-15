#!/bin/bash -eu

python_versions=(
    2.6
    2.7
    3.5
    3.6
    3.7
)

requirements=()

for requirement in *.txt; do
    if [ "${requirement}" != "constraints.txt" ]; then
        requirements+=("${requirement}")
    fi
done

for python_version in "${python_versions[@]}"; do
    version_requirements=()

    for requirement in "${requirements[@]}"; do
        case "${python_version}" in
            "2.6")
                case "${requirement}" in
                    "integration.cloud.azure.txt") continue ;;
                esac
        esac

        version_requirements+=("${requirement}")
    done

    echo "==> Installing pip for python ${python_version} ..."

    set -x
    "python${python_version}" --version
    "python${python_version}" /tmp/get-pip.py -c constraints.txt
    "pip${python_version}" --version --disable-pip-version-check
    set +x

    echo "==> Installing requirements for python ${python_version} ..."

    for requirement in "${version_requirements[@]}"; do
        set -x
        "pip${python_version}" install --disable-pip-version-check -c constraints.txt -r "${requirement}"
        set +x
    done

    echo "==> Checking for requirements conflicts for ${python_version} ..."

    after=$("pip${python_version}" list --format=legacy)

    for requirement in "${version_requirements[@]}"; do
        before="${after}"

        set -x
        "pip${python_version}" install --disable-pip-version-check -c constraints.txt -r "${requirement}"
        set +x

        after=$("pip${python_version}" list --format=legacy)

        if [ "${before}" != "${after}" ]; then
            echo "==> Conflicts detected in requirements for python ${python_version}: ${requirement}"
            echo ">>> Before"
            echo "${before}"
            echo ">>> After"
            echo "${after}"
            exit 1
        fi
    done

    echo "==> Finished with requirements for python ${python_version}."
done
