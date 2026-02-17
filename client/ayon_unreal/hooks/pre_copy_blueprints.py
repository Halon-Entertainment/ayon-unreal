import pathlib
import shutil
from ayon_applications import LaunchTypes, PreLaunchHook
from ayon_unreal.addon import UNREAL_ADDON_ROOT
import semver
import filecmp


class CopyBlueprints(PreLaunchHook):
    app_groups = {"unreal"}
    launch_types = {LaunchTypes.local}
    order = 1

    def execute(self):
        # Halon: Check if unreal addon is enabled
        project_settings = self.data["project_settings"]
        unreal_settings = project_settings["unreal"]
        if not unreal_settings.get('enabled', True):
            return

        self.log.info("Running Copy Blueprints")
        version_str = self.launch_context.env.get("AYON_UNREAL_VERSION", "0.0")
        # Coerce to valid semver (e.g. "5.7" -> "5.7.0")
        version_parts = version_str.split(".")
        while len(version_parts) < 3:
            version_parts.append("0")
        unreal_version = semver.VersionInfo.parse(".".join(version_parts[:3]))
        if unreal_version >= semver.VersionInfo(5, 6, 0):
            self.log.info(f"Skipping Asset Copy for {str(unreal_version)}")
            return

        project_path = self.launch_context.env.get("AYON_UNREAL_PROJECT_PATH")
        if not project_path:
            project_path = self.launch_context.env.get("AYON_WORKDIR")
            if project_path:
                self.launch_context.env["AYON_UNREAL_PROJECT_PATH"] = project_path
                self.log.warning(
                    "AYON_UNREAL_PROJECT_PATH not set. "
                    "Using AYON_WORKDIR as fallback."
                )
            else:
                self.log.warning(
                    "AYON_UNREAL_PROJECT_PATH not set and AYON_WORKDIR missing. "
                    "Skipping blueprint copy."
                )
                return
        project_path = pathlib.Path(project_path)
        container_path = project_path.joinpath(
            "Content", "Ayon", "AyonContainerTypes"
        )

        self.log.debug(f"Container Path {container_path}")
        unreal_version_text = f"UE_{unreal_version.major}.{unreal_version.minor}"
        unreal_addon_root = pathlib.Path(UNREAL_ADDON_ROOT)
        unreal_blueprint_path = unreal_addon_root.joinpath(
            'blueprints',
            unreal_version_text
        )
        blueprint_files = unreal_blueprint_path.glob('*.uasset')

        container_path.mkdir(exist_ok=True, parents=True)
        for blueprint_file in blueprint_files:
            dest = container_path.joinpath(blueprint_file.name)
            if (
                not dest.exists()
                or not filecmp.cmp(blueprint_file, dest)
            ):
                shutil.copy(blueprint_file, dest)
