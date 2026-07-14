# -*- coding: utf-8 -*-
# (c) 2018 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

from ansible.module_utils.common.sys_info import get_all_subclasses


#
# Tests for get_all_subclasses
#

class TestGetAllSubclasses:
    class Base:
        pass

    class BranchI(Base):
        pass

    class BranchII(Base):
        pass

    class BranchIA(BranchI):
        pass

    class BranchIB(BranchI):
        pass

    class BranchIIA(BranchII):
        pass

    class BranchIIB(BranchII):
        pass

    class MultipleInheritanceBase:
        pass

    class MultipleInheritanceBranchI(MultipleInheritanceBase):
        pass

    class MultipleInheritanceBranchII(MultipleInheritanceBase):
        pass

    class MultipleInheritanceChild(MultipleInheritanceBranchI, MultipleInheritanceBranchII):
        pass

    def test_bottom_level(self):
        assert get_all_subclasses(self.BranchIIB) == set()

    def test_one_inheritance(self):
        assert set(get_all_subclasses(self.BranchII)) == set([self.BranchIIA, self.BranchIIB])

    def test_toplevel(self):
        assert set(get_all_subclasses(self.Base)) == set([self.BranchI, self.BranchII,
                                                          self.BranchIA, self.BranchIB,
                                                          self.BranchIIA, self.BranchIIB])

    def test_multiple_inheritance(self) -> None:
        assert get_all_subclasses(self.MultipleInheritanceBase) == {self.MultipleInheritanceBranchI,
                                                                    self.MultipleInheritanceBranchII,
                                                                    self.MultipleInheritanceChild}
