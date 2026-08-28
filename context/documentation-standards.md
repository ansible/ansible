# Documentation standards

## Module and plugin documentation

- Modules and plugins require `DOCUMENTATION`, `EXAMPLES`, and `RETURN` blocks as static YAML string variables.
- These blocks cannot be dynamically generated -- they are parsed via AST/token parsing.
- Alternative: "sidecar" documentation as `.yml` files with same stem name adjacent to plugin files.
- All modules should have a `main()` function and `if __name__ == '__main__':` block.
- Use `version_added` fields in documentation following existing version format patterns.
- Filter, test, and lookup plugins should declare positional arguments using the `positional` key in `DOCUMENTATION`.

## Markup in plugin documentation blocks

Plugin `DOCUMENTATION`, `EXAMPLES`, and `RETURN` blocks use Ansible-specific markup, not reStructuredText or Markdown.

### Semantic markup

- `O(name)` -- option name, optionally with a value: `O(state=present)`.
- `V(value)` -- option value mentioned alone: `V(present)`.
- `RV(name)` -- return value name, optionally with a value: `RV(changed=true)`.
- `E(name)` -- environment variable: `E(ANSIBLE_CONFIG)`.

Suboptions use dot-separated paths: `O(foo.bar)`.
Backslash escaping is supported inside these macros.

### Formatting

- `C()` -- monospace/code text. Example: `This works like the unix command C(grep).`.
- `B()` -- bold text.
- `I()` -- italic text.

`C()`, `B()`, and `I()` do not support escaping, so they cannot contain `)`.

Use `V()` instead of `C()` when the value may contain `)`.

### Linking

- `M(ansible.builtin.copy)` -- link to a module (FQCN required).
- `P(ansible.builtin.file#lookup)` -- link to a plugin (FQCN and type required).
- `L(title,https://example.com)` -- link with custom title.
- `U(https://example.com)` -- bare URL.
- `R(title,rst_anchor)` -- cross-reference to an RST anchor.

`O()` and `RV()` can also link to options/return values in other plugins using the syntax
`O(ansible.builtin.copy#module:src)`.

## Changelog requirements

- Changes require entries in `changelogs/fragments/` as YAML files.
- Create a new fragment file per PR (never reuse existing fragments to avoid merge conflicts).
- Fragment structure follows sections defined in `changelogs/config.yaml` under the `sections` key.
- Verify changelog fragments use a valid section from `changelogs/config.yaml`.
- Naming: `{issue_number}-{short-description}.yml` or `{component}-{description}.yml` if no issue.
- Format: `- {component} - {description} ({optional URL to GH issue})`.
- Content supports Sphinx markup (use double backticks for code references).
