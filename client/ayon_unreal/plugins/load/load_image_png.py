# -*- coding: utf-8 -*-
"""Load textures from PNG."""
import os

from ayon_core.pipeline import (
    get_representation_path,
    AYON_CONTAINER_ID
)
from ayon_unreal.api import plugin
from ayon_unreal.api.pipeline import (
    AYON_ASSET_DIR,
    create_container,
    imprint,
)

import unreal  # noqa


class TexturePNGLoader(plugin.Loader):
    """Load Unreal texture from PNG file."""

    product_types = {"image", "texture", "render"}
    label = "Import image texture 2d"
    representations = {"*"}
    extensions = {"png", "jpg", "tiff"}
    icon = "wallpaper"
    color = "orange"

    root = AYON_ASSET_DIR

    # Defined by settings
    use_interchange = False
    show_dialog = False
    pipeline_path = ""

    @classmethod  
    def apply_settings(cls, project_settings):  
        super(TexturePNGLoader, cls).apply_settings(project_settings)  
        
        # Apply import settings  
        import_settings = (  
            project_settings.get("unreal", {}).get("import_settings", {})  
        )  
        cls.use_interchange = import_settings.get("use_interchange", 
                                                  cls.use_interchange)  
        cls.show_dialog = import_settings.get("show_dialog", cls.show_dialog)
        cls.pipeline_path = import_settings.get("interchange", {}).get(  
            "pipeline_path_static_mesh", cls.pipeline_path  
        )  


    @classmethod
    def get_task(cls, filename, asset_dir, asset_name, replace):
        task = unreal.AssetImportTask()

        task.set_editor_property('filename', filename)
        task.set_editor_property('destination_path', asset_dir)
        task.set_editor_property('destination_name', asset_name)
        task.set_editor_property('replace_existing', replace)
        task.set_editor_property('automated', bool(not cls.show_dialog))
        task.set_editor_property('save', True)

        # set import options here

        return task

    @classmethod
    def import_and_containerize(  
        self, filepath, asset_dir, asset_name, container_name  
    ):  
        unreal.EditorAssetLibrary.make_directory(asset_dir)  

        if self.use_interchange:  
            print("Import using interchange method")  

            unreal.SystemLibrary.execute_console_command(
                None, "Interchange.FeatureFlags.Import.PNG 1")
            unreal.SystemLibrary.execute_console_command(
                None, "Interchange.FeatureFlags.Import.JPG 1")
            unreal.SystemLibrary.execute_console_command(
                None, "Interchange.FeatureFlags.Import.TIFF 1")

            import_assetparameters = unreal.ImportAssetParameters()
            editor_asset_subsystem = unreal.EditorAssetSubsystem()
            import_assetparameters.is_automated = bool(not self.show_dialog)
            import_assetparameters.is_automated = bool(not self.show_dialog)

            # The path to the Interchange asset
            tmp_pipeline_path = "/Game/tmp"
            pipeline = editor_asset_subsystem.duplicate_asset(
                self.pipeline_path, tmp_pipeline_path)

            # Interchange settings here
            pipeline.asset_name = asset_name

            import_assetparameters.override_pipelines.append(
                unreal.SoftObjectPath(f"{tmp_pipeline_path}.tmp"))

            source_data = unreal.InterchangeManager.create_source_data(
                filepath)
            interchange_manager = unreal.InterchangeManager.get_interchange_manager_scripted()  # noqa
            interchange_manager.import_asset(asset_dir, source_data,
                                             import_assetparameters)

            # remove temp file
            editor_asset_subsystem.delete_asset(tmp_pipeline_path)

        else:
            self.log.info("Import using deferred method")
            task = self.get_task(filepath, asset_dir, asset_name, False)
            unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks(
                [task])

        # Create Asset Container
        create_container(container=container_name, path=asset_dir)

    def imprint(
            self,
            folder_path,
            asset_dir,
            container_name,
            asset_name,
            repre_entity,
            product_type
    ):
        data = {
            "schema": "ayon:container-2.0",
            "id": AYON_CONTAINER_ID,
            "namespace": asset_dir,
            "folder_path": folder_path,
            "container_name": container_name,
            "asset_name": asset_name,
            "loader": str(self.__class__.__name__),
            "representation": repre_entity["id"],
            "parent": repre_entity["versionId"],
            "product_type": product_type,
            # TODO these shold be probably removed
            "asset": folder_path,
            "family": product_type,
        }
        imprint(f"{asset_dir}/{container_name}", data)

    def load(self, context, name, namespace, options):
        """Load and containerise representation into Content Browser.

        Args:
            context (dict): application context
            name (str): Product name
            namespace (str): in Unreal this is basically path to container.
                             This is not passed here, so namespace is set
                             by `containerise()` because only then we know
                             real path.
            options (dict): Those would be data to be imprinted.

        Returns:
            list(str): list of container content
        """
        # Create directory for asset and Ayon container
        folder_path = context["folder"]["path"]
        folder_name = context["folder"]["name"]
        suffix = "_CON"
        asset_name = f"{folder_name}_{name}" if folder_name else f"{name}"
        version = context["version"]["version"]
        # Check if version is hero version and use different name
        if version < 0:
            name_version = f"{name}_hero"
        else:
            name_version = f"{name}_v{version:03d}"

        tools = unreal.AssetToolsHelpers().get_asset_tools()
        asset_dir, container_name = tools.create_unique_asset_name(
            f"{self.root}/{folder_name}/{name_version}", suffix=""
        )

        container_name += suffix

        if not unreal.EditorAssetLibrary.does_directory_exist(asset_dir):
            path = self.filepath_from_context(context)

            self.import_and_containerize(
                path, asset_dir, asset_name, container_name)

        self.imprint(
            folder_path,
            asset_dir,
            container_name,
            asset_name,
            context["representation"],
            context["product"]["productType"]
        )

        asset_contents = unreal.EditorAssetLibrary.list_assets(
            asset_dir, recursive=True, include_folder=True
        )
        for unreal_asset in asset_contents:
            unreal.EditorAssetLibrary.save_asset(unreal_asset)

        return asset_contents

    def update(self, container, context):
        folder_path = context["folder"]["path"]
        folder_name = context["folder"]["name"]
        product_name = context["product"]["name"]
        product_type = context["product"]["productType"]
        version = context["version"]["version"]
        repre_entity = context["representation"]

        # Create directory for asset and Ayon container
        suffix = "_CON"
        asset_name = product_name
        if folder_name:
            asset_name = f"{folder_name}_{product_name}"
        # Check if version is hero version and use different name
        if version < 0:
            name_version = f"{product_name}_hero"
        else:
            name_version = f"{product_name}_v{version:03d}"
        tools = unreal.AssetToolsHelpers().get_asset_tools()
        asset_dir, container_name = tools.create_unique_asset_name(
            f"{self.root}/{folder_name}/{name_version}", suffix="")

        container_name += suffix

        if not unreal.EditorAssetLibrary.does_directory_exist(asset_dir):
            path = get_representation_path(repre_entity)

            self.import_and_containerize(
                path, asset_dir, asset_name, container_name)

        self.imprint(
            folder_path,
            asset_dir,
            container_name,
            asset_name,
            repre_entity,
            product_type,
        )

        asset_contents = unreal.EditorAssetLibrary.list_assets(
            asset_dir, recursive=True, include_folder=False
        )
        for unreal_asset in asset_contents:
            unreal.EditorAssetLibrary.save_asset(unreal_asset)

    def remove(self, container):
        path = container["namespace"]
        parent_path = os.path.dirname(path)

        unreal.EditorAssetLibrary.delete_directory(path)

        asset_contents = unreal.EditorAssetLibrary.list_assets(
            parent_path, recursive=False
        )

        if len(asset_contents) == 0:
            unreal.EditorAssetLibrary.delete_directory(parent_path)
