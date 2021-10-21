# Copyright (c) 2021 Red Hat
#
# This code is part of Ansible, but is an independent component.
# This particular file snippet, and this file snippet only, is BSD licensed.
# Modules you write using this snippet, which is embedded dynamically by Ansible
# still belong to the author of the module, and may assign their own license
# to the complete work.
#
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
#
#    * Redistributions of source code must retain the above copyright
#      notice, this list of conditions and the following disclaimer.
#    * Redistributions in binary form must reproduce the above copyright notice,
#      this list of conditions and the following disclaimer in the documentation
#      and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
# IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE
# USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
import argparse
import asyncio
import importlib

# py38 only, See: https://github.com/PyCQA/pylint/issues/2976
import inspect  # pylint: disable=syntax-error
import io
import json

# py38 only, See: https://github.com/PyCQA/pylint/issues/2976
import collections  # pylint: disable=syntax-error
import os
import signal
import sys
import traceback
import zipfile
from zipimport import zipimporter
import pickle

sys_path_lock = None
env_lock = None

import ansible.module_utils.basic

please_include_me = "bar"


def fork_process():
    """
    This function performs the double fork process to detach from the
    parent process and execute.
    """
    pid = os.fork()

    if pid == 0:
        fd = os.open(os.devnull, os.O_RDWR)

        # clone stdin/out/err
        for num in range(3):
            if fd != num:
                os.dup2(fd, num)

        if fd not in range(3):
            os.close(fd)

        pid = os.fork()
        if pid > 0:
            os._exit(0)

        # get new process session and detach
        sid = os.setsid()
        if sid == -1:
            raise Exception("Unable to detach session while daemonizing")

        # avoid possible problems with cwd being removed
        os.chdir("/")

        pid = os.fork()
        if pid > 0:
            sys.exit(0)  # pylint: disable=ansible-bad-function
    else:
        sys.exit(0)  # pylint: disable=ansible-bad-function
    return pid


class EmbeddedModule:
    def __init__(self, ansiblez_path, params):
        self.ansiblez_path = ansiblez_path
        self.collection_name, self.module_name = self.find_module_name()
        self.params = params
        self.module_class = None
        self.debug_mode = False
        self.module_path = (
            "ansible_collections.{collection_name}." "plugins.modules.{module_name}"
        ).format(collection_name=self.collection_name, module_name=self.module_name)

    def find_module_name(self):
        with zipfile.ZipFile(self.ansiblez_path) as zip:
            for path in zip.namelist():
                if not path.startswith("ansible_collections"):
                    continue
                if not path.endswith(".py"):
                    continue
                if path.endswith("__init__.py"):
                    continue
                splitted = path.split("/")
                if len(splitted) != 6:
                    continue
                if splitted[-3:-1] != ["plugins", "modules"]:
                    continue
                collection = ".".join(splitted[1:3])
                name = splitted[-1][:-3]
                return collection, name
        raise Exception("Cannot find module name")

    async def load(self):
        async with sys_path_lock:
            # Add the Ansiblez_path in sys.path
            sys.path.insert(0, self.ansiblez_path)

            # resettle the loaded modules that were associated
            # with a different Ansiblez.
            for path, module in tuple(sys.modules.items()):
                if path and module and path.startswith("ansible_collections"):
                    try:
                        prefix = sys.modules[path].__loader__.prefix
                    except AttributeError:
                        # Not from a zipimporter loader, skipping
                        continue
                    py_path = self.ansiblez_path + os.sep + prefix
                    my_loader = zipimporter(py_path)
                    sys.meta_path.append(my_loader)
                    if hasattr(sys.modules[path], "__path__"):
                        sys.modules[path].__path__ = py_path

            # Finally, load the plugin class.
            self.module_class = importlib.import_module(self.module_path)

    async def unload(self):
        async with sys_path_lock:
            sys.path = [i for i in sys.path if i != self.ansiblez_path]
            sys.meta_path = [
                i
                for i in sys.meta_path
                if not (isinstance(i, zipimporter) and i.archive == self.ansiblez_path)
            ]

    def create_profiler(self):
        if self.debug_mode:
            import cProfile

            pr = cProfile.Profile()
            pr.enable()
            return pr

    def print_profiling_info(self, pr):
        if self.debug_mode:
            import pstats

            sortby = pstats.SortKey.CUMULATIVE
            ps = pstats.Stats(pr).sort_stats(sortby)
            ps.print_stats(20)

    def print_backtrace(self, backtrace):
        if self.debug_mode:
            print(backtrace)  # pylint: disable=ansible-bad-function

    async def run(self):
        class FakeStdin:
            buffer = None

        from .exceptions import (
            EmbeddedModuleFailure,
            EmbeddedModuleUnexpectedFailure,
            EmbeddedModuleSuccess,
        )

        # monkeypatching to pass the argument to the module, this is not
        # really safe, and in the future, this will prevent us to run several
        # modules in parallel. We can maybe use a scoped monkeypatch instead
        _fake_stdin = FakeStdin()
        _fake_stdin.buffer = io.BytesIO(self.params.encode())
        sys.stdin = _fake_stdin
        # Trick to be sure ansible.module_utils.basic._load_params() won't
        # try to build the module parameters from the daemon arguments
        sys.argv = sys.argv[:1]
        ansible.module_utils.basic._ANSIBLE_ARGS = None
        pr = self.create_profiler()
        if not hasattr(self.module_class, "main"):
            raise EmbeddedModuleFailure("No main() found!")
        try:
            if inspect.iscoroutinefunction(self.module_class.main):
                await self.module_class.main()
            elif pr:
                pr.runcall(self.module_class.main)
            else:
                self.module_class.main()
        except EmbeddedModuleSuccess as e:
            self.print_profiling_info(pr)
            return e.kwargs
        except EmbeddedModuleFailure as e:
            backtrace = traceback.format_exc()
            self.print_backtrace(backtrace)
            raise
        except Exception as e:
            backtrace = traceback.format_exc()
            self.print_backtrace(backtrace)
            raise EmbeddedModuleUnexpectedFailure(str(backtrace))
        else:
            raise EmbeddedModuleUnexpectedFailure(
                "Likely a bug: exit_json() or fail_json() should be called during the module excution"
            )


async def run_as_lookup_plugin(data):
    errors = None
    try:
        import ansible.plugins.loader as plugin_loader
        from ansible.parsing.dataloader import DataLoader
        from ansible.template import Templar
        from ansible.module_utils._text import to_native

        (
            lookup_name,
            terms,
            variables,
            kwargs,
        ) = data

        # load lookup plugin
        templar = Templar(loader=DataLoader(), variables=None)
        ansible_collections = "ansible_collections."
        if lookup_name.startswith(ansible_collections):
            lookup_name = lookup_name.replace(ansible_collections, "", 1)
        ansible_plugins_lookup = ".plugins.lookup."
        if ansible_plugins_lookup in lookup_name:
            lookup_name = lookup_name.replace(ansible_plugins_lookup, ".", 1)

        instance = plugin_loader.lookup_loader.get(
            name=lookup_name, loader=templar._loader, templar=templar
        )

        if not hasattr(instance, "_run"):
            return [None, "No _run() found"]
        if inspect.iscoroutinefunction(instance._run):
            result = await instance._run(terms, variables=variables, **kwargs)
        else:
            result = instance._run(terms, variables=variables, **kwargs)
    except Exception as e:
        errors = to_native(e)
    return [result, errors]


async def run_as_module(content, debug_mode):
    from ansible.module_utils.turbo.exceptions import (
        EmbeddedModuleFailure,
    )

    try:
        (
            ansiblez_path,
            params,
            env,
        ) = json.loads(content)
        if debug_mode:
            print(  # pylint: disable=ansible-bad-function
                f"-----\nrunning {ansiblez_path} with params: ¨{params}¨"
            )

        embedded_module = EmbeddedModule(ansiblez_path, params)
        if debug_mode:
            embedded_module.debug_mode = True

        await embedded_module.load()
        try:
            async with env_lock:
                os.environ.clear()
                os.environ.update(env)
                result = await embedded_module.run()
        except SystemExit:
            backtrace = traceback.format_exc()
            result = {"msg": str(backtrace), "failed": True}
        except EmbeddedModuleFailure as e:
            result = {"msg": str(e), "failed": True}
            if e.kwargs:
                result.update(e.kwargs)
        except Exception as e:
            result = {
                "msg": traceback.format_stack() + [str(e)],
                "failed": True,
            }
        await embedded_module.unload()
    except Exception as e:
        result = {"msg": traceback.format_stack() + [str(e)], "failed": True}
    return result


class AnsibleVMwareTurboMode:
    def __init__(self):
        self.sessions = collections.defaultdict(dict)
        self.socket_path = None
        self.ttl = None
        self.debug_mode = None

    async def ghost_killer(self):
        await asyncio.sleep(self.ttl)
        self.stop()

    async def handle(self, reader, writer):
        self._watcher.cancel()

        raw_data = await reader.read()
        if not raw_data:
            return

        (plugin_type, content) = pickle.loads(raw_data)

        def _terminate(result):
            writer.write(json.dumps(result).encode())
            writer.close()
            self._watcher = self.loop.create_task(self.ghost_killer())

        if plugin_type == "module":
            result = await run_as_module(content, debug_mode=self.debug_mode)
        elif plugin_type == "lookup":
            result = await run_as_lookup_plugin(content)
        _terminate(result)

    def handle_exception(self, loop, context):
        e = context.get("exception")
        traceback.print_exception(type(e), e, e.__traceback__)
        self.stop()

    def start(self):
        self.loop = asyncio.get_event_loop()
        self.loop.add_signal_handler(signal.SIGTERM, self.stop)
        self.loop.set_exception_handler(self.handle_exception)
        self._watcher = self.loop.create_task(self.ghost_killer())

        import sys

        if sys.hexversion >= 0x30A00B1:
            # py3.10 drops the loop argument of create_task.
            self.loop.create_task(
                asyncio.start_unix_server(self.handle, path=self.socket_path)
            )
        else:
            self.loop.create_task(
                asyncio.start_unix_server(
                    self.handle, path=self.socket_path, loop=self.loop
                )
            )
        self.loop.run_forever()

    def stop(self):
        os.unlink(self.socket_path)
        self.loop.stop()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Start a background daemon.")
    parser.add_argument("--socket-path")
    parser.add_argument("--ttl", default=15, type=int)
    parser.add_argument("--fork", action="store_true")

    args = parser.parse_args()
    if args.fork:
        fork_process()
    sys_path_lock = asyncio.Lock()
    env_lock = asyncio.Lock()

    server = AnsibleVMwareTurboMode()
    server.socket_path = args.socket_path
    server.ttl = args.ttl
    server.debug_mode = not args.fork
    server.start()
