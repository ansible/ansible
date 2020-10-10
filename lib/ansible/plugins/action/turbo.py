from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import importlib.machinery
import io
import json
import multiprocessing
import sys
import types
import time

from ansible.utils.display import Display
display = Display()

TURBO_MODULES = {}


def _turbo_target(q, module, module_path, module_args):
    """
    This is what we run in in the TurboProcess.
    """
    result = {
        "error": 0,
    }
    try:
        # Redirect stdout to a buffer...
        sys.stdout = io.TextIOWrapper(io.BytesIO())
        sys.stderr = io.TextIOWrapper(io.BytesIO())

        # Prepare stdin for the module to contain ANSIBLE_MODULE_ARGS
        bio = io.BytesIO()
        bio.write(json.dumps({"ANSIBLE_MODULE_ARGS": module_args}).encode("utf-8"))
        bio.seek(0)
        sys.stdin = io.TextIOWrapper(bio)
        sys.argv = [module_path]

        module.main()
    except SystemExit:
        # That's fine, sys.exit called explicity
        pass
    except RuntimeError:
        result["error"] = 2
    except Exception as e:
        result["error"] = 1
        try:
            result["exception"] = repr(e)
        except Exception:
            result["exception"] = str(e)

    try:
        sys.stdout.seek(0)
        result["stdout"] = sys.stdout.read()
    except Exception:
        result["stdout"] = "turbo: could not read stdout"

    try:
        sys.stderr.seek(0)
        result["stderr"] = sys.stderr.read()
    except Exception:
        result["stderr"] = "turbo: could not read stderr"

    # Send back the result
    q.put(result)


def prepare_turbo(module_path, module_args, final_environment, become_kwargs):
    """
    :returns: None or a Process object that can be started.
    """
    __unused = (final_environment, become_kwargs)  # XXX
    if not module_path.endswith(".py"):
        display.vvv("module_path %s not ending in .py" % module_path)
        return None

    package = module_path.rsplit(".", 1)[0]

    a, b, c = package.split("/")[-3:]
    if a != "ansible" or b != "modules":
        display.vvv("Non-ansible module: %s (?)" % module_path)

    # Load the requested module into ansible.turbo.odules
    name = ".".join(["ansible", "turbo", "modules", c])

    m = TURBO_MODULES.get(name)
    if m is None:
        display.vvv("Loading %s as %s" % (module_path, name))
        start_time = time.time()
        m = types.ModuleType(name)
        m.__path__ = module_path
        loader = importlib.machinery.SourceFileLoader(name, module_path)
        loader.exec_module(m)
        took = time.time() - start_time
        display.debug("[TURBO] Loaded %s (%s) took=%.4fs" % (name, module_path, took))
        TURBO_MODULES[name] = m

    q = multiprocessing.Queue()
    args = (q, m, module_path, module_args)
    proc = multiprocessing.Process(target=_turbo_target, args=args)
    return (q, proc)
