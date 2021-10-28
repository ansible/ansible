"""Unit tests for the hostname module."""
from __future__ import absolute_import, division, print_function

__metaclass__ = type

from units.compat.mock import patch, MagicMock, mock_open
from ansible.module_utils import basic
from ansible.module_utils.common._utils import get_all_subclasses
from ansible.modules import hostname
from units.modules.utils import ModuleTestCase, set_module_args
from ansible.module_utils.six import PY2


class TestHostname(ModuleTestCase):
    """Test class for the hostname module."""

    @patch("os.path.isfile")
    def test_stategy_get_never_writes_in_check_mode(self, isfile):
        """Don't write when in check mode."""
        isfile.return_value = True

        set_module_args({"name": "fooname", "_ansible_check_mode": True})
        subclasses = get_all_subclasses(hostname.BaseStrategy)
        module = MagicMock()
        for cls in subclasses:
            instance = cls(module)

            instance.module.run_command = MagicMock()
            instance.module.run_command.return_value = (0, "", "")

            mopen = mock_open()
            builtins = "builtins"
            if PY2:
                builtins = "__builtin__"
            with patch("%s.open" % builtins, mopen):
                instance.get_permanent_hostname()
                instance.get_current_hostname()
                self.assertFalse(
                    mopen.return_value.write.called,
                    msg="%s called write, should not have" % str(cls),
                )

    def test_all_named_strategies_exist(self):
        """Loop through the STRATS and see if anything is missing."""
        for _name, prefix in hostname.STRATS.items():
            classname = "%sStrategy" % prefix
            cls = getattr(hostname, classname, None)

            if cls is None:
                self.assertFalse(
                    cls is None, "%s is None, should be a subclass" % classname
                )
            else:
                self.assertTrue(issubclass(cls, hostname.BaseStrategy))
