
import os
from pathlib import Path

from ayon_unreal.api.backends.ayon_plugin import AyonPluginBackend
from ayon_unreal.api.backends.native_unreal import NativeUnrealBackend

# DEBUG: Write to file for troubleshooting
debug_file = Path.home() / "ayon_unreal_startup_debug.txt"
def debug_log(msg):
    print(f"[AYON BACKEND] {msg}")
    with open(debug_file, "a") as f:
        f.write(f"{msg}\n")

def get_backend_class():
    plugin_enabled = os.getenv('AYON_PLUGIN_ENABLED')
    debug_log(f"get_backend_class: AYON_PLUGIN_ENABLED = {plugin_enabled!r}")
    use_plugin = plugin_enabled == '1'
    if use_plugin:
        debug_log("Using AyonPluginBackend")
        return AyonPluginBackend
    debug_log("Using NativeUnrealBackend")
    return NativeUnrealBackend
