from ansible.template import Templar, display
from units.mock.loader import DictDataLoader
from jinja2.filters import FILTERS
from os.path import isabs


def test_tests_as_filters_warning(mocker):
    fake_loader = DictDataLoader({
        "/path/to/my_file.txt": "foo\n",
    })
    templar = Templar(loader=fake_loader, variables={})
    filters = templar._get_filters(templar.environment.filters)

    mocker.patch.object(display, 'deprecated')

    # Call successful test, ensure the message is correct
    filters['successful']({})
    display.deprecated.assert_called_once_with(
        'Using tests as filters is deprecated. Instead of using `result|successful` use `result is successful`', version='2.9'
    )

    # Call success test, ensure the message is correct
    display.deprecated.reset_mock()
    filters['success']({})
    display.deprecated.assert_called_once_with(
        'Using tests as filters is deprecated. Instead of using `result|success` use `result is success`', version='2.9'
    )

    # Call bool filter, ensure no deprecation message was displayed
    display.deprecated.reset_mock()
    filters['bool'](True)
    assert display.deprecated.call_count == 0

    # Ensure custom test does not override builtin filter
    assert filters.get('abs') != isabs
