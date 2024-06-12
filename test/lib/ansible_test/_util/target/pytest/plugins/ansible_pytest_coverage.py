"""Monkey patch os._exit when running under coverage so we don't lose coverage data in forks, such as with `pytest --boxed`. PYTEST_DONT_REWRITE"""
from __future__ import annotations


def pytest_configure():
    """Configure this pytest plugin."""
    try:
        if pytest_configure.executed:
            return
    except AttributeError:
        pytest_configure.executed = True

    try:
        import coverage
    except ImportError:
        coverage = None

    try:
        coverage.Coverage
    except AttributeError:
        coverage = None

    if not coverage:
        return

    import gc
    import os

    coverage_instances = []

    for obj in gc.get_objects():
        if isinstance(obj, coverage.Coverage):
            coverage_instances.append(obj)

    if not coverage_instances:
        coverage_config = os.environ.get('COVERAGE_CONF')

        if not coverage_config:
            return

        coverage_output = os.environ.get('COVERAGE_FILE')

        if not coverage_output:
            return

        cov = coverage.Coverage(config_file=coverage_config)
        coverage_instances.append(cov)
    else:
        cov = None

    # noinspection PyProtectedMember
    os_exit = os._exit  # pylint: disable=protected-access

    def coverage_exit(*args, **kwargs):
        for instance in coverage_instances:
            # skip coverage instances which have no collector, or the collector is not the active collector
            # this avoids issues with coverage 7.4.0+ when tests create subprocesses which inherit our overridden os._exit method
            # pylint: disable=protected-access
            if not instance._collector or not instance._collector._collectors or instance._collector != instance._collector._collectors[-1]:
                continue

            instance.stop()
            instance.save()

        os_exit(*args, **kwargs)

    os._exit = coverage_exit  # pylint: disable=protected-access

    if cov:
        cov.start()


pytest_configure()
