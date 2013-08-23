#jinja2: variable_end_string: @@, variable_start_string: @@

{% raw %}
 if this succeeds you should see '{{ ansible_hostname }}' with the hostname on the line above
 if this fails you should see '@@ ansible_hostname @@' with the hostname on the line beneath
{% endraw %}

@@ ansible_hostname @@
{{ ansible_hostname }}

