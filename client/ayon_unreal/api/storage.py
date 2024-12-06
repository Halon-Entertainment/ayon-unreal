from ayon_core.pipeline import anatomy
from ayon_api import get_addons_project_settings

HALON_PATH_CONFIG = get_addons_project_settings(anatomy.Anatomy().project_name)['unreal']['halon_storage_path']