# Copyright (c) 2024 Ynput s.r.o.
import os
from pathlib import Path

# DEBUG: Write to file for troubleshooting
debug_file = Path.home() / "ayon_unreal_startup_debug.txt"
def debug_log(msg):
    print(f"[AYON STARTUP] {msg}")
    with open(debug_file, "a") as f:
        f.write(f"{msg}\n")

debug_log("=" * 50)
debug_log("init_unreal.py started")
debug_log(f"AYON_PLUGIN_ENABLED = {os.getenv('AYON_PLUGIN_ENABLED', 'NOT SET')}")

import unreal
try:
    import qtpy #noqa F401
    from qtpy import QtWidgets #noqa F401
    debug_log("qtpy imported successfully")
except ImportError as exc:
    # this is because `QtBingingsNotFoundError` exception is risen
    # directly from `import qtpy`
    debug_log(f"qtpy import failed: {exc}")
    if exc.__class__.__name__ != "QtBindingsNotFoundError":
        raise exc
    message = "PySide 2 is missing, please visit to https://ayon.ynput.io/docs/addon_unreal_admin for more installation info"
    title = "Notification"
    message_type = unreal.AppMsgType.OK
    default_value = unreal.AppReturnType.NO

    # Show the message dialog
    unreal.EditorDialog.show_message(title, message, message_type, default_value)

ayon_detected = True
try:
    # AYON support (both ayon-core and ayon-unreal addon locations)
    debug_log("Importing ayon_core.pipeline...")
    from ayon_core.pipeline import install_host

    try:
        debug_log("Importing UnrealHost from ayon_unreal.api...")
        from ayon_unreal.api import UnrealHost
        debug_log("UnrealHost imported from ayon_unreal.api")
    except ImportError as e:
        debug_log(f"Failed to import from ayon_unreal.api: {e}")
        debug_log("Trying ayon_core.hosts.unreal.api...")
        from ayon_core.hosts.unreal.api import UnrealHost

    debug_log("Creating UnrealHost instance...")
    ayon_host = UnrealHost()
    debug_log("UnrealHost created successfully")
except ImportError as exc:
    ayon_host = None
    ayon_detected = False
    debug_log(f"AYON detection failed: {exc}")
    import traceback
    debug_log(traceback.format_exc())
    unreal.log_error(f"Ayon: cannot load Ayon integration [ {exc} ]")
except Exception as exc:
    ayon_host = None
    ayon_detected = False
    debug_log(f"Unexpected error: {exc}")
    import traceback
    debug_log(traceback.format_exc())

if ayon_detected:
    debug_log("Installing host...")
    try:
        install_host(ayon_host)
        debug_log("Host installed successfully")
    except Exception as exc:
        debug_log(f"Failed to install host: {exc}")
        import traceback
        debug_log(traceback.format_exc())
else:
    debug_log("AYON not detected, skipping host installation")


