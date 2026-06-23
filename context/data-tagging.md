# Data tagging

## How not to break things

Avoid unnecessary mutation of values, such as calling `str.strip` or `to_text`, etc. as these will drop tags, losing things like origin and trust for templating.

When mutation of a value is necessary, carefully consider which tags, if any, need to be propagated to the resulting value.

## When tags must be removed

Some APIs don't understand tagged types and can't automatically treat them as their untagged equivalents.
This includes C-implemented Python APIs that perform exact type checks, serialization libraries that reject derived types,
and any interface where the consumer expects or requires plain types.
In these cases, use `transform_to_native_types()` from `ansible.utils.vars` to convert tagged values to native types before passing them to the API.
