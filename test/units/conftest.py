"""Monkey patch os._exit when running under coverage so we don't lose coverage data in forks, such as with `pytest --boxed`."""
import gc
import os

try:
    import coverage
except ImportError:
    coverage = None

try:
    test = coverage.Coverage
except AttributeError:
    coverage = None


def pytest_configure():
    if not coverage:
        return

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

    os_exit = os._exit

    def coverage_exit(*args, **kwargs):
        for instance in coverage_instances:
            instance.stop()
            instance.save()

        os_exit(*args, **kwargs)

    os._exit = coverage_exit

    if cov:
        cov.start()
