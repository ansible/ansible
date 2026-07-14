# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations


class ModuleDocFragment:
    DOCUMENTATION = r"""
options: {}
"""

    RETURN = r"""
bar:
  description:
    - Some foo bar.
    - P(a.b.asfd#dfsa) this is an error.
  returned: success
  type: int
  sample: 42
"""
