from __future__ import annotations

import collections.abc as c
import itertools
import typing as t

from ansible.errors import AnsibleValueOmittedError, AnsibleError

from ._engine import TemplateEngine


class ChainTemplar:
    """A basic variable layering mechanism that supports templating and obliteration of `omit` values."""

    def __init__(self, *sources: c.Mapping, templar: TemplateEngine) -> None:
        self.sources = sources
        self.templar = templar

    def template(self, key: t.Any, value: t.Any) -> t.Any:
        """
        Render the given value using the templar.
        Intended to be overridden by subclasses.
        """
        return self.templar.template(value)

    def get(self, key: t.Any) -> t.Any:
        """Get the value for the given key, templating the result before returning it."""
        for source in self.sources:
            if key not in source:
                continue

            value = source[key]

            try:
                return self.template(key, value)
            except AnsibleValueOmittedError:
                break  # omit == obliterate - matches historical behavior where dict layers were squashed before templating was applied
            except Exception as ex:
                raise AnsibleError(f'Error while resolving value for {key!r}.', obj=value) from ex

        raise KeyError(key)

    def keys(self) -> t.Iterable[t.Any]:
        """
        Returns a sorted iterable of all keys present in all source layers, without templating associated values.
        Values that resolve to `omit` are thus included.
        """
        return sorted(set(itertools.chain.from_iterable(self.sources)))

    def items(self) -> t.Iterable[t.Tuple[t.Any, t.Any]]:
        """
        Returns a sorted iterable of (key, templated value) tuples.
        Any tuple where the templated value resolves to `omit` will not be included in the result.
        """
        for key in self.keys():
            try:
                yield key, self.get(key)
            except KeyError:
                pass

    def as_dict(self) -> dict[t.Any, t.Any]:
        """Returns a dict representing all layers, squashed and templated, with `omit` values dropped."""
        return dict(self.items())
