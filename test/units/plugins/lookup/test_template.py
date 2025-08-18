from __future__ import annotations

import pathlib

from ansible._internal._templating._utils import Omit
from ansible.parsing.dataloader import DataLoader
from ansible.template import Templar, trust_as_template


def test_no_finalize_marker_passthru(tmp_path: pathlib.Path) -> None:
    """Return an Undefined marker from a template lookup to ensure that the internal templating operation does not finalize its result."""
    template_path = tmp_path / 'template.txt'
    template_path.write_text("{{ bogusvar }}")

    templar = Templar(loader=DataLoader(), variables=dict(template_path=str(template_path)))

    assert templar.template(trust_as_template('{{ lookup("template", template_path) | default("pass") }}')) == "pass"


def test_no_finalize_omit_passthru(tmp_path: pathlib.Path) -> None:
    """Return an Omit scalar from a template lookup to ensure that the internal templating operation does not finalize its result."""
    template_path = tmp_path / 'template.txt'
    template_path.write_text("{{ omitted }}")

    data = dict(omitted=trust_as_template("{{ omit }}"), template_path=str(template_path))

    # The result from the lookup should be an Omit value, since the result of the template lookup's internal templating call should not be finalized.
    # If it were, finalize would trip the Omit and raise an error about a top-level template result resolving to an Omit scalar.
    res = Templar(loader=DataLoader(), variables=data).template(trust_as_template("{{ lookup('template', template_path) | type_debug }}"))

    assert res == type(Omit).__name__
