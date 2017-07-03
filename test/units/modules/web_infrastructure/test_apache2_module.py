import pytest

from ansible.modules.web_infrastructure.apache2_module import create_apache_identifier

REPLACEMENTS = [
    ('php7.1', 'php7_module'),
    ('php5.6', 'php5_module'),
    ('shib2', 'mod_shib'),
    ('evasive', 'evasive20_module'),
    ('thismoduledoesnotexist', 'thismoduledoesnotexist_module'),  # the default
]


@pytest.mark.parametrize("replacement", REPLACEMENTS, ids=lambda x: x[0])
def test_apache_identifier(replacement):
    "test the correct replacement of an a2enmod name with an apache2ctl name"
    assert create_apache_identifier(replacement[0]) == replacement[1]
