# -*- coding: utf-8 -*-
# Copyright 2015 Cristian van Ee <cristian at cvee.org>
# Copyright 2015 Igor Gnatenko <i.gnatenko.brain@gmail.com>
# Copyright 2018 Adam Miller <admiller@redhat.com>
# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# NOTE: This file intentionally supports a wider variety of python versions than does
# ansible.module_utils.basic, specifically on the lower bounds. The intent is for this
# to work against the system python where the dnf python bindings are supported.
#
# Requires-Python: ">=3.6"

import json
import os
import sys

try:
    import dnf
    import dnf.const
    import dnf.exceptions
    import dnf.module.module_base
    import dnf.package
    import dnf.subject
    import dnf.util

    HAS_DNF = True
except ImportError:
    HAS_DNF = False


class _DnfScriptError(Exception):
    """Exception raised for DNF script errors with structured error information."""

    def __init__(self, msg, failures=None, results=None, rc=1):
        """Initialize DNF script error."""
        self.msg = msg
        self.failures = failures or []
        self.results = results or []
        self.rc = rc
        super().__init__(msg)

    def to_dict(self):
        """Convert exception to dict format for JSON response."""
        return {'changed': False, 'msg': self.msg, 'failures': self.failures, 'results': self.results, 'rc': self.rc, 'failed': True}


def _package_to_envra(package):
    """Convert a dnf.package.Package object to ENVRA string (epoch always included)."""
    return f'{package.epoch}:{package.name}-{package.version}-{package.release}.{package.arch}'


class _DnfJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder that handles dnf-specific objects."""

    def default(self, o):
        if isinstance(o, dnf.package.Package):
            return self._package_to_dict(o)
        return super().default(o)

    @staticmethod
    def _package_to_dict(package):
        """Convert a dnf.package.Package object to a dictionary."""
        result = {
            'name': package.name,
            'arch': package.arch,
            'epoch': f'{package.epoch}',
            'release': package.release,
            'version': package.version,
            'repo': package.repoid,
        }

        result['envra'] = _package_to_envra(package)
        result['nevra'] = result['envra']

        if package.installtime == 0:
            result['yumstate'] = 'available'
        else:
            result['yumstate'] = 'installed'

        return result


def _exit_json(response):
    """Output JSON response and exit with appropriate code."""
    json.dump(response, sys.stdout, cls=_DnfJSONEncoder)
    sys.exit(1 if response.get('failed') else 0)  # pylint: disable=ansible-bad-function


def _configure_base(base, config_dict):
    """Configure the dnf Base object. Returns list of warnings."""
    warnings = []
    conf = base.conf

    conf_file = config_dict.get('conf_file')
    if conf_file:
        if not os.access(conf_file, os.R_OK):
            raise _DnfScriptError(f'cannot read configuration file: {conf_file}')
        conf.config_file_path = conf_file

    conf.read()
    conf.debuglevel = 0

    disable_gpg_check = config_dict.get('disable_gpg_check', False)
    conf.gpgcheck = not disable_gpg_check
    conf.localpkg_gpgcheck = not disable_gpg_check
    conf.assumeyes = True

    sslverify = config_dict.get('sslverify', True)
    conf.sslverify = sslverify

    installroot = config_dict.get('installroot', '/')
    if not os.path.isdir(installroot):
        raise _DnfScriptError(f'Installroot {installroot} must be a directory')

    conf.installroot = installroot
    conf.substitutions.update_from_etc(installroot)

    exclude = config_dict.get('exclude', [])
    if exclude:
        _excludes = list(conf.exclude)
        _excludes.extend(exclude)
        conf.exclude = _excludes

    disable_excludes = config_dict.get('disable_excludes')
    if disable_excludes:
        _disable_excludes = list(conf.disable_excludes)
        if disable_excludes not in _disable_excludes:
            _disable_excludes.append(disable_excludes)
            conf.disable_excludes = _disable_excludes

    releasever = config_dict.get('releasever')
    if releasever is not None:
        conf.substitutions['releasever'] = releasever

    if conf.substitutions.get('releasever') is None:
        warnings.append('Unable to detect release version (use "releasever" option to specify release version)')
        conf.substitutions['releasever'] = ''

    for opt in ('cachedir', 'logdir', 'persistdir'):
        conf.prepend_installroot(opt)

    skip_broken = config_dict.get('skip_broken', False)
    if skip_broken:
        conf.strict = 0

    nobest = config_dict.get('nobest')
    best = config_dict.get('best')
    if nobest is not None:
        conf.best = not nobest
    elif best is not None:
        conf.best = best

    download_only = config_dict.get('download_only', False)
    if download_only:
        conf.downloadonly = True
        download_dir = config_dict.get('download_dir')
        if download_dir:
            conf.destdir = download_dir

    cacheonly = config_dict.get('cacheonly', False)
    if cacheonly:
        conf.cacheonly = True

    autoremove = config_dict.get('autoremove', False)
    conf.clean_requirements_on_remove = autoremove

    install_weak_deps = config_dict.get('install_weak_deps', True)
    conf.install_weak_deps = install_weak_deps

    return warnings


def _configure_repos(base, disablerepo_list, enablerepo_list, disable_gpg_check):
    """Enable and disable repositories matching the provided patterns."""
    repos = base.repos

    for repo_pattern in disablerepo_list:
        if repo_pattern:
            for repo in repos.get_matching(repo_pattern):
                repo.disable()

    for repo_pattern in enablerepo_list:
        if repo_pattern:
            for repo in repos.get_matching(repo_pattern):
                repo.enable()

    if disable_gpg_check:
        for repo in base.repos.iter_enabled():
            repo.gpgcheck = False
            repo.repo_gpgcheck = False


def _init_plugins(base, disable_plugin_list, enable_plugin_list):
    """Initialize and configure plugins."""
    base.setup_loggers()
    base.init_plugins(set(disable_plugin_list), set(enable_plugin_list))
    base.pre_configure_plugins()


def _add_security_filters(base, bugfix, security):
    """Add security and bugfix filters for package upgrades."""
    add_security_filters_method = getattr(base, 'add_security_filters', None)
    if callable(add_security_filters_method):
        filters = {}
        if bugfix:
            filters.setdefault('types', []).append('bugfix')
        if security:
            filters.setdefault('types', []).append('security')
        if filters:
            add_security_filters_method('eq', **filters)
    else:
        # Fallback for older dnf versions
        filters = []
        if bugfix:
            key = {'advisory_type__eq': 'bugfix'}
            filters.append(base.sack.query().upgrades().filter(**key))
        if security:
            key = {'advisory_type__eq': 'security'}
            filters.append(base.sack.query().upgrades().filter(**key))
        if filters:
            base._update_security_filters = filters

    return True


def _is_package_installed(base, package_spec):
    """Check if a package is installed."""
    return bool(dnf.subject.Subject(package_spec).get_best_query(sack=base.sack).installed())


def _is_newer_version_installed(base, pkg_spec):
    """Check if a newer version of the package is already installed."""
    try:
        if isinstance(pkg_spec, dnf.package.Package):
            installed = sorted(base.sack.query().installed().filter(name=pkg_spec.name, arch=pkg_spec.arch))[-1]
            return installed.evr_gt(pkg_spec)
        else:
            solution = dnf.subject.Subject(pkg_spec).get_best_solution(base.sack)
            q = solution['query']
            nevra = solution['nevra']
            if not q or not nevra or nevra.has_just_name() or not nevra.version:
                return False

            # Filter by name and arch (if specified), but NOT by version
            # since we need to find installed packages to compare versions against
            filter_kwargs = {'name': nevra.name}
            if nevra.arch:
                filter_kwargs['arch'] = nevra.arch
            installed = base.sack.query().installed().filter(**filter_kwargs)
            if not installed:
                return False
            return installed[0].evr_gt(q[0])
    except IndexError:
        return False


def _get_modules(module_base, module_spec):
    """Get module information for a module specification."""
    module_spec = module_spec.strip()
    module_list, nsv = module_base._get_modules(module_spec)
    return {
        'module_list': module_list,
        'nsv': {'name': nsv.name if nsv else None, 'stream': nsv.stream if nsv else None, 'version': nsv.version if nsv and hasattr(nsv, 'version') else None},
    }


def _parse_spec_group_file(base, module_base, names, update_only, with_modules):
    """Parse the names list into package specs, group specs, module specs, and filenames."""
    pkg_specs, grp_specs, module_specs, filenames = [], [], [], []
    already_loaded_comps = False

    for name in names:
        if '://' in name:
            filenames.append(name)
        elif name.endswith('.rpm'):
            filenames.append(name)
        elif name.startswith('/'):
            installed = base.sack.query().filter(provides=name, file=name).installed().run()
            if installed:
                pkg_specs.append(installed[0].name)
            elif not update_only:
                pkg_specs.append(name)
        elif name.startswith('@') or ('/' in name):
            if not already_loaded_comps:
                base.read_comps()
                already_loaded_comps = True

            grp_env_mdl_candidate = name[1:].strip()

            if with_modules and module_base:
                mdl_info = _get_modules(module_base, grp_env_mdl_candidate)
                if mdl_info['module_list'] and mdl_info['module_list'][0]:
                    module_specs.append(grp_env_mdl_candidate)
                else:
                    grp_specs.append(grp_env_mdl_candidate)
            else:
                grp_specs.append(grp_env_mdl_candidate)
        else:
            pkg_specs.append(name)

    return pkg_specs, grp_specs, module_specs, filenames


def _update_only_helper(base, pkgs):
    """Handle update_only logic for packages. Returns list of not installed packages."""
    not_installed = []
    for pkg in pkgs:
        if isinstance(pkg, dnf.package.Package):
            pkg_nevra = _package_to_envra(pkg)
        else:
            pkg_nevra = pkg

        if _is_package_installed(base, pkg_nevra):
            try:
                if isinstance(pkg, dnf.package.Package):
                    base.package_upgrade(pkg)
                else:
                    base.upgrade(pkg)
            except Exception as e:
                raise _DnfScriptError(f'Error occurred attempting update_only operation: {e}')
        else:
            not_installed.append(pkg)

    return not_installed


def _install_remote_rpms_helper(base, filenames, update_only, allow_downgrade):
    """Handle installation of remote RPM files."""
    try:
        pkgs = base.add_remote_rpms(filenames)
        if update_only:
            _update_only_helper(base, pkgs)
        else:
            for pkg in pkgs:
                if not (_is_newer_version_installed(base, pkg) and not allow_downgrade):
                    base.package_install(pkg, strict=base.conf.strict)
    except _DnfScriptError:
        raise
    except Exception as e:
        raise _DnfScriptError(f'Error occurred attempting remote rpm operation: {e}')


def _is_module_installed(base, module_base, module_spec, with_modules):
    """Check if a module is installed."""
    if not with_modules:
        return False

    module_info = _get_modules(module_base, module_spec)
    enabled_streams = base._moduleContainer.getEnabledStream(module_info['nsv']['name'])

    if enabled_streams:
        if module_info['nsv']['stream']:
            if module_info['nsv']['stream'] in enabled_streams:
                return True
            else:
                return False
        else:
            return True

    return False


def _mark_package_install(base, pkg_spec, upgrade, allow_downgrade):
    """Mark a package for installation."""
    msg = ''
    strict = base.conf.strict

    try:
        if dnf.util.is_glob_pattern(pkg_spec):
            if upgrade:
                try:
                    base.upgrade(pkg_spec)
                except dnf.exceptions.PackagesNotInstalledError:
                    pass

            try:
                base.install(pkg_spec, strict=strict)
            except dnf.exceptions.MarkingError as e:
                msg = f'No package {pkg_spec} available.'
                if strict:
                    return {'failed': True, 'msg': msg, 'failure': f'{pkg_spec} {e}', 'rc': 1}
            except dnf.exceptions.DepsolveError as e:
                return {'failed': True, 'msg': f'Depsolve Error occurred for package {pkg_spec}.', 'failure': f'{pkg_spec} {e}', 'rc': 1}
            except dnf.exceptions.Error as e:
                return {'failed': True, 'msg': f'Unknown Error occurred for package {pkg_spec}.', 'failure': f'{pkg_spec} {e}', 'rc': 1}
        elif _is_newer_version_installed(base, pkg_spec):
            if allow_downgrade:
                try:
                    base.install(pkg_spec, strict=strict)
                except dnf.exceptions.MarkingError as e:
                    msg = f'No package {pkg_spec} available.'
                    if strict:
                        return {'failed': True, 'msg': msg, 'failure': f'{pkg_spec} {e}', 'rc': 1}
        elif _is_package_installed(base, pkg_spec):
            if upgrade:
                try:
                    base.upgrade(pkg_spec)
                except dnf.exceptions.PackagesNotInstalledError:
                    pass
        else:
            try:
                base.install(pkg_spec, strict=strict)
            except dnf.exceptions.MarkingError as e:
                msg = f'No package {pkg_spec} available.'
                if strict:
                    return {'failed': True, 'msg': msg, 'failure': f'{pkg_spec} {e}', 'rc': 1}
            except dnf.exceptions.DepsolveError as e:
                return {'failed': True, 'msg': f'Depsolve Error occurred for package {pkg_spec}.', 'failure': f'{pkg_spec} {e}', 'rc': 1}
            except dnf.exceptions.Error as e:
                return {'failed': True, 'msg': f'Unknown Error occurred for package {pkg_spec}.', 'failure': f'{pkg_spec} {e}', 'rc': 1}
    except Exception as e:
        return {'failed': True, 'msg': f'Unknown Error occurred for package {pkg_spec}.', 'failure': f'{pkg_spec} {e}', 'rc': 1}

    return {'failed': False, 'msg': msg, 'failure': '', 'rc': 0}


def _sanitize_install_error(spec, error):
    """Sanitize DNF error messages for install operations."""
    if 'no package matched' in str(error) or 'No match for argument:' in str(error):
        return f'No package {spec} available.'
    return error


def _ensure_impl(base, module_base, params):
    """Core implementation of ensure logic."""
    response = {'msg': '', 'changed': False, 'results': [], 'rc': 0}

    failures = []

    names = params.get('names', [])
    state = params.get('state')
    autoremove = params.get('autoremove', False)
    update_only = params.get('update_only', False)
    allow_downgrade = params.get('allow_downgrade', False)
    download_only = params.get('download_only', False)
    disable_gpg_check = params.get('disable_gpg_check', False)
    check_mode = params.get('check_mode', False)
    download_dir = params.get('download_dir')
    allowerasing = params.get('allowerasing', False)
    with_modules = dnf.base.WITH_MODULES and module_base is not None

    if not names and autoremove:
        names = []
        state = 'absent'

    if names == ['*'] and state == 'latest':
        try:
            base.upgrade_all()
        except dnf.exceptions.DepsolveError as e:
            raise _DnfScriptError(msg=f'Depsolve Error occurred attempting to upgrade all packages: {e}', rc=1)
    else:
        pkg_specs, group_specs, module_specs, filenames = _parse_spec_group_file(base, module_base, names, update_only, with_modules)

        pkg_specs = [p.strip() for p in pkg_specs]
        filenames = [f.strip() for f in filenames]
        groups = []
        environments = []

        for group_spec in (g.strip() for g in group_specs):
            group = base.comps.group_by_pattern(group_spec)
            if group:
                groups.append(group.id)
            else:
                environment = base.comps.environment_by_pattern(group_spec)
                if environment:
                    environments.append(environment.id)
                else:
                    raise _DnfScriptError(f'No group {group_spec} available.')

        if state in ['installed', 'present']:
            if filenames:
                _install_remote_rpms_helper(base, filenames, update_only, allow_downgrade)
                for filename in filenames:
                    response['results'].append(f'Installed {filename}')

            if module_specs and with_modules:
                for module in module_specs:
                    if not _is_module_installed(base, module_base, module, with_modules):
                        response['results'].append(f'Module {module} installed.')
                    try:
                        module_base.install([module])
                        module_base.enable([module])
                    except dnf.exceptions.MarkingErrors as e:
                        failures.append(f'{module} {e}')

            for group in groups:
                try:
                    count = base.group_install(group, dnf.const.GROUP_PACKAGE_TYPES)
                    if count == 0:
                        response['results'].append(f'Group {group} already installed.')
                    else:
                        response['results'].append(f'Group {group} installed.')
                except dnf.exceptions.DepsolveError:
                    raise _DnfScriptError(msg=f'Depsolve Error occurred attempting to install group: {group}', failures=failures, results=response['results'])
                except dnf.exceptions.Error as e:
                    failures.append(f'{group} {e}')

            for environment in environments:
                try:
                    base.environment_install(environment, dnf.const.GROUP_PACKAGE_TYPES)
                except dnf.exceptions.DepsolveError:
                    raise _DnfScriptError(
                        msg=f'Depsolve Error occurred attempting to install environment: {environment}', failures=failures, results=response['results']
                    )
                except dnf.exceptions.Error as e:
                    failures.append(f'{environment} {e}')

            if module_specs and not with_modules:
                raise _DnfScriptError(f'No group {module_specs[0]} available.')

            if update_only:
                not_installed = _update_only_helper(base, pkg_specs)
                for spec in not_installed:
                    response['results'].append(f'Packages providing {spec} not installed due to update_only specified')
            else:
                for pkg_spec in pkg_specs:
                    install_result = _mark_package_install(base, pkg_spec, False, allow_downgrade)
                    if install_result['failed']:
                        failures.append(_sanitize_install_error(pkg_spec, install_result['failure']))
                    else:
                        if install_result['msg']:
                            response['results'].append(install_result['msg'])

        elif state == 'latest':
            if filenames:
                _install_remote_rpms_helper(base, filenames, update_only, allow_downgrade)
                for filename in filenames:
                    response['results'].append(f'Installed {filename}')

            if module_specs and with_modules:
                for module in module_specs:
                    try:
                        if _is_module_installed(base, module_base, module, with_modules):
                            module_base.upgrade([module])
                            response['results'].append(f'Module {module} upgraded.')
                        else:
                            module_base.install([module])
                            module_base.enable([module])
                            response['results'].append("Module {0} installed.".format(module))
                    except dnf.exceptions.MarkingErrors as e:
                        failures.append(f'{module} {e}')

            for group in groups:
                try:
                    base.group_upgrade(group)
                    response['results'].append(f'Group {group} upgraded.')
                except dnf.exceptions.CompsError:
                    if not update_only:
                        try:
                            count = base.group_install(group, dnf.const.GROUP_PACKAGE_TYPES)
                            if count == 0:
                                response['results'].append(f'Group {group} already installed.')
                            else:
                                response['results'].append(f'Group {group} installed.')
                        except dnf.exceptions.Error as e2:
                            failures.append(f'{group} {e2}')
                except dnf.exceptions.Error as e:
                    failures.append(f'{group} {e}')

            for environment in environments:
                try:
                    base.environment_upgrade(environment)
                except dnf.exceptions.CompsError:
                    try:
                        base.environment_install(environment, dnf.const.GROUP_PACKAGE_TYPES)
                    except dnf.exceptions.DepsolveError as e2:
                        failures.append(f'{environment} {e2}')
                    except dnf.exceptions.Error as e2:
                        failures.append(f'{environment} {e2}')
                except dnf.exceptions.DepsolveError as e:
                    failures.append(f'{environment} {e}')
                except dnf.exceptions.Error as e:
                    failures.append(f'{environment} {e}')

            if update_only:
                not_installed = _update_only_helper(base, pkg_specs)
                for spec in not_installed:
                    response['results'].append(f'Packages providing {spec} not installed due to update_only specified')
            else:
                for pkg_spec in pkg_specs:
                    install_result = _mark_package_install(base, pkg_spec, True, allow_downgrade)
                    if install_result['failed']:
                        failures.append(_sanitize_install_error(pkg_spec, install_result['failure']))
                    else:
                        if install_result['msg']:
                            response['results'].append(install_result['msg'])

        else:
            if filenames:
                raise _DnfScriptError('Cannot remove paths -- please specify package name.')

            if module_specs and with_modules:
                for module in module_specs:
                    if _is_module_installed(base, module_base, module, with_modules):
                        response['results'].append(f'Module {module} removed.')
                    try:
                        module_base.remove([module])
                    except dnf.exceptions.MarkingErrors as e:
                        failures.append(f'{module} {e}')
                    try:
                        module_base.disable([module])
                    except dnf.exceptions.MarkingErrors as e:
                        failures.append(f'{module} {e}')
                    try:
                        module_base.reset([module])
                    except dnf.exceptions.MarkingErrors as e:
                        failures.append(f'{module} {e}')

            for group in groups:
                try:
                    base.group_remove(group)
                except dnf.exceptions.CompsError as e:
                    response['results'].append(f'{group} {e}')

            for environment in environments:
                try:
                    base.environment_remove(environment)
                except dnf.exceptions.CompsError as e:
                    response['results'].append(f'{environment} {e}')

            for pkg_spec in pkg_specs:
                try:
                    base.remove(pkg_spec)
                except dnf.exceptions.MarkingError as e:
                    response['results'].append(f'{e.value}: {pkg_spec}')

            allowerasing = True

            if autoremove:
                base.autoremove()

    try:
        has_changes = base.resolve(allow_erasing=allowerasing)
    except dnf.exceptions.DepsolveError as e:
        raise _DnfScriptError(msg=f'Depsolve Error occurred: {e}', failures=failures, results=response['results'])
    except dnf.exceptions.Error as e:
        raise _DnfScriptError(msg=f'Unknown Error occurred: {e}', failures=failures, results=response['results'])

    if not has_changes:
        if failures:
            raise _DnfScriptError(msg='Failed to install some of the specified packages', failures=failures, results=response['results'])
        response['msg'] = 'Nothing to do'
        return response
    else:
        response['changed'] = True

        install_action = 'Downloaded' if download_only else 'Installed'
        for package in base.transaction.install_set:
            response['results'].append(f'{install_action}: {package}')
        for package in base.transaction.remove_set:
            response['results'].append(f'Removed: {package}')

        if failures:
            raise _DnfScriptError(msg='Failed to install some of the specified packages', failures=failures, results=response['results'])

        if check_mode:
            response['msg'] = 'Check mode: No changes made, but would have if not in check mode'
            return response

        if download_only and download_dir and base.conf.destdir:
            dnf.util.ensure_dir(base.conf.destdir)
            base.repos.all().pkgdir = base.conf.destdir

        try:
            base.download_packages(base.transaction.install_set)
        except dnf.exceptions.DownloadError as e:
            raise _DnfScriptError(msg=f'Failed to download packages: {e}', failures=failures, results=response['results'])

        if not disable_gpg_check:
            for package in base.transaction.install_set:
                gpgres, gpgerr = base._sig_check_pkg(package)
                if gpgres != 0:  # Not validated successfully
                    if gpgres == 1:  # Need to install cert
                        try:
                            base._get_key_for_package(package)
                        except dnf.exceptions.Error as e:
                            raise _DnfScriptError(f'Failed to validate GPG signature for {package}: {e}')
                    else:  # Fatal error
                        raise _DnfScriptError(f'Failed to validate GPG signature for {package}: {gpgerr}')

        if download_only:
            return response
        else:
            tid = base.do_transaction()
            if tid is not None:
                transaction = base.history.old([tid])[0]
                if transaction.return_code:
                    failures.extend(transaction.output())

        if failures:
            raise _DnfScriptError(msg='Failed to install some of the specified packages', failures=failures, results=response['results'])

        return response


def _setup_base(config):
    """Internal helper to set up and configure a dnf.Base object."""
    base = dnf.Base()

    warnings = _configure_base(base, config)

    _init_plugins(base, config.get('disable_plugin', []), config.get('enable_plugin', []))

    base.read_all_repos()
    _configure_repos(base, config.get('disablerepo', []), config.get('enablerepo', []), config.get('disable_gpg_check', False))

    base.configure_plugins()

    try:
        if config.get('update_cache'):
            base.update_cache()

        base.fill_sack(load_system_repo='auto')
    except Exception:
        base.close()
        raise

    if config.get('bugfix') or config.get('security'):
        _add_security_filters(base, config.get('bugfix', False), config.get('security', False))

    module_base = None
    if dnf.base.WITH_MODULES:
        module_base = dnf.module.module_base.ModuleBase(base)

    return base, module_base, warnings


def list_items(config, command):
    """List packages based on command."""
    base = None
    try:
        base, module_base, warnings = _setup_base(config)

        if command == 'updates':
            command = 'upgrades'

        if command == 'installed':
            results = list(base.sack.query().installed())
        elif command == 'upgrades':
            results = list(base.sack.query().upgrades())
        elif command == 'available':
            results = list(base.sack.query().available())
        elif command in ['repos', 'repositories']:
            results = [{'repoid': repo.id, 'state': 'enabled'} for repo in base.repos.iter_enabled()]
        else:
            results = list(dnf.subject.Subject(command).get_best_query(base.sack))

        return {'results': results, 'warnings': warnings}
    except Exception as e:
        return {'results': [], 'warnings': [], 'failed': True, 'msg': f'{e}'}
    finally:
        if base:
            base.close()


def update_cache_only(config):
    """Update the cache only (no other operations)."""
    base = None
    try:
        base, module_base, warnings = _setup_base(config)
        return {'changed': False, 'warnings': warnings}
    except Exception as e:
        return {'changed': False, 'warnings': [], 'failed': True, 'msg': f'{e}'}
    finally:
        if base:
            base.close()


def ensure(config, params):
    """Main operation for installing, removing, or upgrading packages."""
    base = None
    try:
        base, module_base, warnings = _setup_base(config)

        result = _ensure_impl(base, module_base, params)

        result['warnings'] = warnings
        result['failures'] = []

        return result

    except _DnfScriptError as e:
        return e.to_dict()
    except Exception as e:
        return {'changed': False, 'results': [], 'warnings': [], 'failed': True, 'failures': [], 'rc': 1, 'msg': f'{e}'}
    finally:
        if base:
            base.close()


def main():
    """Main entry point for standalone script execution."""

    if not HAS_DNF:
        _exit_json({'failed': True, 'msg': 'python3-dnf not found'})

    try:
        request = json.load(sys.stdin)
    except Exception as e:
        _exit_json({'failed': True, 'msg': f'Failed to read JSON input: {e}'})

    command = request.get('command')
    if not command:
        _exit_json({'failed': True, 'msg': 'No command specified'})

    config = request.get('config', {})
    params = request.get('params', {})

    if command == 'list':
        list_command = params.get('list_command')
        if not list_command:
            _exit_json({'failed': True, 'msg': 'No list_command specified for list operation'})
        result = list_items(config, list_command)

    elif command == 'ensure':
        result = ensure(config, params)

    elif command == 'update-cache':
        result = update_cache_only(config)

    else:
        _exit_json({'failed': True, 'msg': f'Unknown command: {command}'})

    _exit_json(result)


if __name__ == '__main__':
    main()
