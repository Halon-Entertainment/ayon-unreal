from ayon_server.settings import BaseSettingsModel, SettingsField

from .imageio import UnrealImageIOModel


class ProjectSetup(BaseSettingsModel):
    dev_mode: bool = SettingsField(
        False,
        title="Dev mode"
    )
    allow_project_creation: bool = SettingsField(
        False,
        title="Allow Project Creation",
        description="Allows Ayon to create the unreal project."
    )


def _render_format_enum():
    return [
        {"value": "png", "label": "PNG"},
        {"value": "exr", "label": "EXR"},
        {"value": "jpg", "label": "JPG"},
        {"value": "bmp", "label": "BMP"}
    ]


class UnrealSettings(BaseSettingsModel):
    project_folder: str = SettingsField(
        "{project[name]}",
        title="Project Folder",
        description="Project Folder"
    )
    imageio: UnrealImageIOModel = SettingsField(
        default_factory=UnrealImageIOModel,
        title="Color Management (ImageIO)"
    )
    level_sequences_for_layouts: bool = SettingsField(
        False,
        title="Generate level sequences when loading layouts"
    )
    delete_unmatched_assets: bool = SettingsField(
        False,
        title="Delete assets that are not matched"
    )
    render_queue_path: str = SettingsField(
        "",
        title="Render Queue Path",
        description="Path to Render Queue UAsset for farm publishing"
    )
    render_config_path: str = SettingsField(
        "",
        title="Render Config Path",
        description="Path to Render Configuration UAsset for farm publishing"
    )
    preroll_frames: int = SettingsField(
        0,
        title="Pre-roll frames"
    )
    render_format: str = SettingsField(
        "png",
        title="Render format",
        enum_resolver=_render_format_enum
    )
    project_setup: ProjectSetup = SettingsField(
        default_factory=ProjectSetup,
        title="Project Setup",
    )


DEFAULT_VALUES = {
    "level_sequences_for_layouts": True,
    "delete_unmatched_assets": False,
    "render_queue_path": "/Game/Ayon/renderQueue",
    "render_config_path": "/Game/Ayon/DefaultMovieRenderQueueConfig.DefaultMovieRenderQueueConfig",
    "preroll_frames": 0,
    "render_format": "exr",
    "project_setup": {
        "dev_mode": False
    }
}
