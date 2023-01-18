#!/usr/bin/env bash

if [[ "${ANSIBLE_DEBUG}" == true ]]  # `ansible-test` invoked with `--debug`
then
    CLI_VERBOSE_FLAG=-v
    SET_DEBUG_MODE=-x
else
    ANSIBLE_DEBUG=false
    CLI_VERBOSE_FLAG=
    SET_DEBUG_MODE=+x
fi


set -eEuo pipefail

source virtualenv.sh

set "${SET_DEBUG_MODE}"


CLEANED_UP=false

DIST_NAME=ansible_core

LOWEST_SUPPORTED_BUILD_DEPS_FILE="${PWD}"/minimum-build-constraints.txt

SRC_ROOT_DIR="$(dirname "$(dirname "$(dirname "$(dirname "${OUTPUT_DIR}")")")")"
GENERATED_MANPAGES_SUBDIR=docs/man/man1/

function git-clean-manpages() {
    >&2 echo
    >&2 echo '=>' Cleaning up the gitignored manpages...
    # git \
    #   --git-dir="${SRC_ROOT_DIR}"/.git \
    #   --work-tree="${SRC_ROOT_DIR}" \
    #   clean -dfX -- "${GENERATED_MANPAGES_SUBDIR}"
    rm -rf ${CLI_VERBOSE_FLAG} "${GENERATED_MANPAGES_SUBDIR}"
    >&2 echo '=>' Removed the generated manpages...
    >&2 echo
}


TMP_DIR_SDIST_WITHOUT_MANPAGES=$(mktemp -d)
TMP_DIR_SDIST_WITH_MANPAGES=$(mktemp -d)
TMP_DIR_REBUILT_SDIST=$(mktemp -d)
TMP_DIR_REBUILT_WHEEL=$(mktemp -d)

function cleanup-tmp-dirs() {
    # NOTE: Avoid multiple executions on race conditions caused by different
    # NOTE: signals being trapped.
    [ ${CLEANED_UP} == 'true' ] && return
    CLEANED_UP=true

    >&2 echo
    >&2 echo '=>' Cleaning up the directories...
    rm -rf ${CLI_VERBOSE_FLAG} \
      "${TMP_DIR_SDIST_WITHOUT_MANPAGES}" \
      "${TMP_DIR_SDIST_WITH_MANPAGES}" \
      "${TMP_DIR_REBUILT_SDIST}" \
      "${TMP_DIR_REBUILT_WHEEL}"
    >&2 echo '=>' Wiped clean the following directories: \
      "${TMP_DIR_SDIST_WITHOUT_MANPAGES}" \
      "${TMP_DIR_SDIST_WITH_MANPAGES}" \
      "${TMP_DIR_REBUILT_SDIST}" \
      "${TMP_DIR_REBUILT_WHEEL}"

    git-clean-manpages
}

trap cleanup-tmp-dirs EXIT INT QUIT TERM


function print-title {
    local title=$*

    >&2 echo
    >&2 echo
    >&2 echo '===' "${title}" '==='
    >&2 echo
}


function unpack-sdist {
    local sdist_tarball=$1
    local target_directory=$2

    mkdir -p ${CLI_VERBOSE_FLAG} "${target_directory}"

    tar ${CLI_VERBOSE_FLAG}xzf "${sdist_tarball}" \
      --directory="${target_directory}" \
      --strip-components=1
}


function _look-up-man1-in-tarball {
    local tarball=$1
    local dist_name_base=$2

    2>/dev/null \
    tar ${CLI_VERBOSE_FLAG}tzf "${tarball}" \
      --strip-components=1 \
      "${expected_sdist_name_base}/docs/man/man1"

    local return_code=${?}

    local not=not
    if [ ${return_code} -eq 0 ]
    then
        not=
    fi

    >&2 echo
    >&2 echo '=>' man1 is ${not} present in "${tarball}"...

    return ${return_code}
}


function assert-man1-in-tarball {
    local tarball=$1
    local dist_name_base=$2

    >&2 echo
    >&2 echo '=>' Verifying that man1 pages are present in the sdist...

    _look-up-man1-in-tarball "${tarball}" "${dist_name_base}"
}


function assert-man1-not-in-tarball {
    local tarball=$1
    local dist_name_base=$2

    >&2 echo
    >&2 echo '=>' Verifying that man1 pages are absent from the sdist...

    ! _look-up-man1-in-tarball "${tarball}" "${dist_name_base}"
}


function assert-directories-equal {
    local dir1=$1
    local dir2=$2

    >&2 echo
    >&2 echo \
      '=>' Verifying that the contents of "${dir1}" \
      and "${dir2}" are the same...

    diff -ur "${dir1}" "${dir2}"
}


function normalize-unpacked-rebuilt-sdist {
    local sdist_dir=$1
    if [[ "${ANSIBLE_DEBUG}" == true ]]  # `ansible-test` invoked w/ `--debug`
    then
        >&2 echo
        >&2 echo \
          '=>' Patching the metadata in "${sdist_dir}" \
          to match ancient setuptools output...
    fi

    # setuptools v39 emit `Platform: UNKNOWN` while the recent don't
    sed -i.bak \
      's/\(Classifier: Development Status :: 5\)/Platform: UNKNOWN'"\n"'\1/g' \
      "${sdist_dir}"/PKG-INFO
    sed -i.bak \
      's/\(Classifier: Development Status :: 5\)/Platform: UNKNOWN'"\n"'\1/g' \
      "${sdist_dir}"/lib/${DIST_NAME}.egg-info/PKG-INFO
    rm ${CLI_VERBOSE_FLAG} -f \
      "${sdist_dir}"/PKG-INFO.bak \
      "${sdist_dir}"/lib/${DIST_NAME}.egg-info/PKG-INFO.bak

    # setuptools v39 write out two trailing empty lines while the recent don't
    echo >> "${sdist_dir}"/PKG-INFO
    echo >> "${sdist_dir}"/PKG-INFO
    echo >> "${sdist_dir}"/lib/${DIST_NAME}.egg-info/PKG-INFO
    echo >> "${sdist_dir}"/lib/${DIST_NAME}.egg-info/PKG-INFO

    # setuptools v39 write out one trailing empty line while the recent don't
    echo >> "${sdist_dir}"/lib/${DIST_NAME}.egg-info/entry_points.txt
}


export PIP_DISABLE_PIP_VERSION_CHECK=true
export PIP_NO_PYTHON_VERSION_WARNING=true
export PIP_NO_WARN_SCRIPT_LOCATION=true

print-title Install pypa/build
python -m pip install 'build ~= 0.10.0'

print-title Test building an sdist without manpages from the Git checkout
git-clean-manpages
python -m build --sdist \
  --outdir "${TMP_DIR_SDIST_WITHOUT_MANPAGES}" \
  "${SRC_ROOT_DIR}"
pkg_dist_version=$(
    grep '^Version: ' "${SRC_ROOT_DIR}"/lib/ansible_core.egg-info/PKG-INFO |
      awk -F': ' '{print $2}'
)
expected_sdist_name_base="ansible-core-${pkg_dist_version}"
expected_sdist_name="${expected_sdist_name_base}.tar.gz"
ls -1 "${TMP_DIR_SDIST_WITHOUT_MANPAGES}"/"${expected_sdist_name}"
assert-man1-not-in-tarball "${TMP_DIR_SDIST_WITHOUT_MANPAGES}"/"${expected_sdist_name}" "${expected_sdist_name_base}"
unpack-sdist \
  "${TMP_DIR_SDIST_WITHOUT_MANPAGES}"/"${expected_sdist_name}" \
  "${TMP_DIR_SDIST_WITHOUT_MANPAGES}"/src

expected_wheel_name=${DIST_NAME}-${pkg_dist_version}-py3-none-any.whl


print-title \
  Test building an sdist with manpages from the Git checkout and lowest \
  supported build deps
git-clean-manpages
PIP_CONSTRAINT="${LOWEST_SUPPORTED_BUILD_DEPS_FILE}" \
  python -m build --sdist --config-setting=--build-manpages \
    --outdir "${TMP_DIR_SDIST_WITH_MANPAGES}" \
    "${SRC_ROOT_DIR}"
ls -1 "${TMP_DIR_SDIST_WITH_MANPAGES}"/"${expected_sdist_name}"
assert-man1-in-tarball "${TMP_DIR_SDIST_WITH_MANPAGES}"/"${expected_sdist_name}" "${expected_sdist_name_base}"
unpack-sdist \
  "${TMP_DIR_SDIST_WITH_MANPAGES}"/"${expected_sdist_name}" \
  "${TMP_DIR_SDIST_WITH_MANPAGES}"/src

print-title \
  Test re-building an sdist with manpages from the \
  sdist contents that does not include the manpages
python -m build --sdist --config-setting=--build-manpages \
  --outdir "${TMP_DIR_REBUILT_SDIST}" \
  "${TMP_DIR_SDIST_WITHOUT_MANPAGES}"/src
>&2 echo
>&2 echo \
  '=>' Checking that the expected sdist got \
  created from the previous unpacked sdist...
ls -1 "${TMP_DIR_REBUILT_SDIST}"/"${expected_sdist_name}"
assert-man1-in-tarball \
  "${TMP_DIR_REBUILT_SDIST}"/"${expected_sdist_name}" \
  "${expected_sdist_name_base}"
unpack-sdist \
  "${TMP_DIR_REBUILT_SDIST}"/"${expected_sdist_name}" \
  "${TMP_DIR_REBUILT_SDIST}"/src
normalize-unpacked-rebuilt-sdist "${TMP_DIR_REBUILT_SDIST}"/src
assert-directories-equal \
  "${TMP_DIR_SDIST_WITH_MANPAGES}"/src \
  "${TMP_DIR_REBUILT_SDIST}"/src


print-title \
  Test building a wheel from the rebuilt sdist with manpages contents and \
  lowest supported build deps
PIP_CONSTRAINT="${LOWEST_SUPPORTED_BUILD_DEPS_FILE}" \
  python -m build --wheel \
    --outdir "${TMP_DIR_REBUILT_WHEEL}" \
    "${TMP_DIR_SDIST_WITH_MANPAGES}"/src
>&2 echo '=>' Checking that the expected wheel got created...
ls -1 "${TMP_DIR_REBUILT_WHEEL}"/"${expected_wheel_name}"

>&2 echo '=>' Resetting the current virtualenv...
source virtualenv.sh
set "${SET_DEBUG_MODE}"
print-title \
  Smoke-test PEP 660 editable install with the in-tree build backend wrapper

pip install --editable "${SRC_ROOT_DIR}"
pip show ansible-core
python -c 'from ansible import __version__; print(__version__)'
