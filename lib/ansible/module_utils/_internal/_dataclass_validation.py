# Copyright (c) 2024 Ansible Project
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)

"""Code generation of __post_init__ methods for efficient dataclass field type checking at runtime."""

from __future__ import annotations

import atexit
import functools
import itertools
import shutil
import tempfile
import types
import typing as t

_write_generated_code_to_disk = False

# deprecated: description='types.UnionType is available in Python 3.10' python_version='3.9'
try:
    _union_type: type | None = types.UnionType  # type: ignore[attr-defined]
    _union_types: tuple = (t.Union, types.UnionType)  # type: ignore[attr-defined]
except AttributeError:
    _union_type = None  # type: ignore[assignment]
    _union_types = (t.Union,)  # type: ignore[assignment]


def inject_post_init_validation(cls: type, allow_subclasses=False) -> None:
    """Inject a __post_init__ field validation method on the given dataclass. An existing __post_init__ attribute must already exist."""
    # DTFIX-FUTURE: when cls must have a __post_init__, enforcing it as a no-op would be nice, but is tricky on slotted dataclasses due to double-creation
    post_validate_name = '_post_validate'
    method_name = '__post_init__'
    exec_globals: dict[str, t.Any] = {}
    known_types: dict[type, str] = {}
    lines: list[str] = []
    field_type_hints = t.get_type_hints(cls)
    indent = 1

    def append_line(line: str) -> None:
        """Append a line to the generated source at the current indentation level."""
        lines.append((' ' * indent * 4) + line)

    def register_type(target_type: type) -> str:
        """Register the target type and return the local name."""
        target_name = f'{target_type.__module__.replace(".", "_")}_{target_type.__name__}'

        known_types[target_type] = target_name
        exec_globals[target_name] = target_type

        return target_name

    def validate_value(target_name: str, target_ref: str, target_type: type) -> None:
        """Generate code to validate the specified value."""
        nonlocal indent

        origin_type = t.get_origin(target_type)

        if origin_type is t.ClassVar:
            return  # ignore annotations which are not fields, indicated by the t.ClassVar annotation

        allowed_types = _get_allowed_types(target_type)

        # check value

        if origin_type is t.Literal:
            # DTFIX-FUTURE: support optional literals

            values = t.get_args(target_type)

            append_line(f"""if {target_ref} not in {values}:""")
            append_line(f"""    raise ValueError(rf"{target_name} must be one of {values} instead of {{{target_ref}!r}}")""")

        allowed_refs = [register_type(allowed_type) for allowed_type in allowed_types]
        allowed_names = [repr(allowed_type) for allowed_type in allowed_types]

        if allow_subclasses:
            if len(allowed_refs) == 1:
                append_line(f"""if not isinstance({target_ref}, {allowed_refs[0]}):""")
            else:
                append_line(f"""if not isinstance({target_ref}, ({', '.join(allowed_refs)})):""")
        else:
            if len(allowed_refs) == 1:
                append_line(f"""if type({target_ref}) is not {allowed_refs[0]}:""")
            else:
                append_line(f"""if type({target_ref}) not in ({', '.join(allowed_refs)}):""")

        append_line(f"""    raise TypeError(f"{target_name} must be {' or '.join(allowed_names)} instead of {{type({target_ref})}}")""")

        # check elements (for containers)

        if target_ref.startswith('self.'):
            local_ref = target_ref[5:]
        else:
            local_ref = target_ref

        if tuple in allowed_types:
            tuple_type = _extract_type(target_type, tuple)

            idx_ref = f'{local_ref}_idx'
            item_ref = f'{local_ref}_item'
            item_name = f'{target_name}[{{{idx_ref}!r}}]'
            item_type, _ellipsis = t.get_args(tuple_type)

            if _ellipsis is not ...:
                raise ValueError(f"{cls} tuple fields must be a tuple of a single element type")

            append_line(f"""if isinstance({target_ref}, {known_types[tuple]}):""")
            append_line(f"""    for {idx_ref}, {item_ref} in enumerate({target_ref}):""")

            indent += 2
            validate_value(target_name=item_name, target_ref=item_ref, target_type=item_type)
            indent -= 2

        if list in allowed_types:
            list_type = _extract_type(target_type, list)

            idx_ref = f'{local_ref}_idx'
            item_ref = f'{local_ref}_item'
            item_name = f'{target_name}[{{{idx_ref}!r}}]'
            (item_type,) = t.get_args(list_type)

            append_line(f"""if isinstance({target_ref}, {known_types[list]}):""")
            append_line(f"""    for {idx_ref}, {item_ref} in enumerate({target_ref}):""")

            indent += 2
            validate_value(target_name=item_name, target_ref=item_ref, target_type=item_type)
            indent -= 2

        if dict in allowed_types:
            dict_type = _extract_type(target_type, dict)

            key_ref, value_ref = f'{local_ref}_key', f'{local_ref}_value'
            key_type, value_type = t.get_args(dict_type)
            key_name, value_name = f'{target_name!r} key {{{key_ref}!r}}', f'{target_name}[{{{key_ref}!r}}]'

            append_line(f"""if isinstance({target_ref}, {known_types[dict]}):""")
            append_line(f"""    for {key_ref}, {value_ref} in {target_ref}.items():""")

            indent += 2
            validate_value(target_name=key_name, target_ref=key_ref, target_type=key_type)
            validate_value(target_name=value_name, target_ref=value_ref, target_type=value_type)
            indent -= 2

    for field_name in cls.__annotations__:
        validate_value(target_name=f'{{type(self).__name__}}.{field_name}', target_ref=f'self.{field_name}', target_type=field_type_hints[field_name])

    if hasattr(cls, post_validate_name):
        append_line(f"self.{post_validate_name}()")

    if not lines:
        return  # nothing to validate (empty dataclass)

    if '__init__' in cls.__dict__ and not hasattr(cls, method_name):
        raise ValueError(f"{cls} must have a {method_name!r} method to override when invoked after the '__init__' method is created")

    if any(hasattr(parent, method_name) for parent in cls.__mro__[1:]):
        lines.insert(0, f'    super({register_type(cls)}, self).{method_name}()')

    lines.insert(0, f'def {method_name}(self):')

    source = '\n'.join(lines) + '\n'

    if _write_generated_code_to_disk:
        tmp = tempfile.NamedTemporaryFile(mode='w+t', suffix=f'-{cls.__module__}.{cls.__name__}.py', delete=False, dir=_get_temporary_directory())

        tmp.write(source)
        tmp.flush()

        filename = tmp.name
    else:
        filename = f'<string> generated for {cls}'

    code = compile(source, filename, 'exec')

    exec(code, exec_globals)
    setattr(cls, method_name, exec_globals[method_name])


@functools.lru_cache(maxsize=1)
def _get_temporary_directory() -> str:
    """Create a temporary directory and return its full path. The directory will be deleted when the process exits."""
    temp_dir = tempfile.mkdtemp()

    atexit.register(lambda: shutil.rmtree(temp_dir))

    return temp_dir


def _get_allowed_types(target_type: type) -> tuple[type, ...]:
    """Return a tuple of types usable in instance checks for the given target_type."""
    origin_type = t.get_origin(target_type)

    if origin_type in _union_types:
        allowed_types = tuple(set(itertools.chain.from_iterable(_get_allowed_types(arg) for arg in t.get_args(target_type))))
    elif origin_type is t.Literal:
        allowed_types = (str,)  # DTFIX-FUTURE: support non-str literal types
    elif origin_type:
        allowed_types = (origin_type,)
    else:
        allowed_types = (target_type,)

    return allowed_types


def _extract_type(target_type: type, of_type: type) -> type:
    """Return `of_type` from `target_type`, where `target_type` may be a union."""
    origin_type = t.get_origin(target_type)

    if origin_type is of_type:  # pylint: disable=unidiomatic-typecheck
        return target_type

    if origin_type is t.Union or (_union_type and isinstance(target_type, _union_type)):
        args = t.get_args(target_type)
        extracted_types = [arg for arg in args if type(arg) is of_type or t.get_origin(arg) is of_type]  # pylint: disable=unidiomatic-typecheck
        (extracted_type,) = extracted_types
        return extracted_type

    raise NotImplementedError(f'{target_type} is not supported')
