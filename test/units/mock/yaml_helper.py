from __future__ import annotations

import io
import yaml

from ansible.parsing.yaml.dumper import AnsibleDumper


class YamlTestUtils(object):
    """Mixin class to combine with a unittest.TestCase subclass."""
    def _loader(self, stream):
        """Vault related tests will want to override this.

        Vault cases should setup a AnsibleLoader that has the vault password."""

    def _dump_stream(self, obj, stream, dumper=None):
        """Dump to a py2-unicode or py3-string stream."""
        return yaml.dump(obj, stream, Dumper=dumper)

    def _dump_string(self, obj, dumper=None):
        """Dump to a py2-unicode or py3-string"""
        return yaml.dump(obj, Dumper=dumper)

    def _dump_load_cycle(self, obj):
        # Each pass though a dump or load revs the 'generation'
        # obj to yaml string
        string_from_object_dump = self._dump_string(obj, dumper=AnsibleDumper)

        # wrap a stream/file like StringIO around that yaml
        stream_from_object_dump = io.StringIO(string_from_object_dump)
        loader = self._loader(stream_from_object_dump)
        # load the yaml stream to create a new instance of the object (gen 2)
        obj_2 = loader.get_data()

        # dump the gen 2 objects directory to strings
        string_from_object_dump_2 = self._dump_string(obj_2,
                                                      dumper=AnsibleDumper)

        # The gen 1 and gen 2 yaml strings
        self.assertEqual(string_from_object_dump, string_from_object_dump_2)
        # the gen 1 (orig) and gen 2 py object
        self.assertEqual(obj, obj_2)

        # again! gen 3... load strings into py objects
        stream_3 = io.StringIO(string_from_object_dump_2)
        loader_3 = self._loader(stream_3)
        obj_3 = loader_3.get_data()

        string_from_object_dump_3 = self._dump_string(obj_3, dumper=AnsibleDumper)

        self.assertEqual(obj, obj_3)
        # should be transitive, but...
        self.assertEqual(obj_2, obj_3)
        self.assertEqual(string_from_object_dump, string_from_object_dump_3)
