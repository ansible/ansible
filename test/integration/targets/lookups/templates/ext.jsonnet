{
  two: std.native("ansible_expr")("{{ 1 + 1 }}"),
  evar: std.extVar("evar"),
  bare: std.native("ansible_expr")("another_var"),
}
