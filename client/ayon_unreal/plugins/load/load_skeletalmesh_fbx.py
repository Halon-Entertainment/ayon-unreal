# -*- coding: utf-8 -*-
"""Load Skeletal Meshes form FBX."""

from ayon_core.pipeline import AYON_CONTAINER_ID
from ayon_unreal.api import plugin
from ayon_unreal.api.pipeline import (
    create_container,
    imprint,
    format_asset_directory,
    get_dir_from_existing_asset
)
import unreal  # noqa


class SkeletalMeshFBXLoader(plugin.Loader):
    """Load Unreal SkeletalMesh from FBX."""

    product_types = {"rig", "skeletalMesh"}
    label = "Import FBX Skeletal Mesh"
    representations = {"fbx"}
    icon = "cube"
    color = "orange"

    loaded_asset_dir = "{folder[path]}/{product[name]}_{version[version]}"
    loaded_asset_name = "{folder[name]}_{product[name]}_{version[version]}_{representation[name]}"      # noqa
    show_dialog = False

    @classmethod
    def apply_settings(cls, project_settings):
        unreal_settings = project_settings["unreal"]["import_settings"]
        super(SkeletalMeshFBXLoader, cls).apply_settings(project_settings)
        cls.loaded_asset_dir = unreal_settings["loaded_asset_dir"]
        cls.loaded_asset_name = unreal_settings["loaded_asset_name"]
        cls.show_dialog = unreal_settings["show_dialog"]

    @classmethod
    def get_task(cls, filename, asset_dir, asset_name, replace):
        task = unreal.AssetImportTask()
        options = unreal.FbxImportUI()

        task.set_editor_property('filename', filename)
        task.set_editor_property('destination_path', asset_dir)
        task.set_editor_property('destination_name', asset_name)
        task.set_editor_property('replace_existing', replace)
        task.set_editor_property('automated', not cls.show_dialog)
        task.set_editor_property('save', True)

        options.set_editor_property(
            'automated_import_should_detect_type', False)
        options.set_editor_property('import_as_skeletal', True)
        options.set_editor_property('import_animations', False)
        options.set_editor_property('import_mesh', True)
        options.set_editor_property('import_materials', True)
        options.set_editor_property('import_textures', True)
        options.set_editor_property('skeleton', None)
        options.set_editor_property('create_physics_asset', False)

        options.set_editor_property(
            'mesh_type_to_import',
            unreal.FBXImportType.FBXIT_SKELETAL_MESH)

        options.skeletal_mesh_import_data.set_editor_property(
            'import_content_type',
            unreal.FBXImportContentType.FBXICT_ALL)

        options.skeletal_mesh_import_data.set_editor_property(
            'normal_import_method',
            unreal.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS)

        # Tell importer to search all project assets for duplicate materials
        options.texture_import_data.set_editor_property(
            'material_search_location',
            unreal.MaterialSearchLocation.ALL_ASSETS)

        task.options = options

        return task


    PHONG_PARENT = (
        "/Script/Engine.Material'"
        "/InterchangeAssets/Materials/"
        "FBXLegacyPhongSurfaceMaterial.FBXLegacyPhongSurfaceMaterial'"
    )

    @staticmethod
    def _is_phong_instance(material):
        """Check if a material is a Interchange phong placeholder."""
        if not material:
            return False
        if material.get_class().get_name() != "MaterialInstanceConstant":
            return False
        parent = material.get_editor_property("parent")
        if not parent:
            return False
        return "FBXLegacyPhongSurfaceMaterial" in parent.get_path_name()

    @staticmethod
    def _find_existing_material(name, exclude_path=None):
        """Search the asset registry for a Material or MaterialInstance.

        Skips assets under exclude_path (the import dir) so we don't
        match the phong instance the importer just created.
        """
        ar = unreal.AssetRegistryHelpers.get_asset_registry()
        for class_name in ("Material", "MaterialInstanceConstant"):
            assets = ar.get_assets_by_class(
                unreal.TopLevelAssetPath("/Script/Engine", class_name),
                True
            )
            for asset_data in assets:
                if asset_data.asset_name != name:
                    continue
                path = str(asset_data.package_name)
                # Skip materials created by this import
                if exclude_path and path.startswith(exclude_path):
                    continue
                # Skip Interchange phong materials
                if "/InterchangeAssets/" in path:
                    continue
                return asset_data.get_asset()
        return None

    @classmethod
    def _assign_existing_materials(cls, mesh_path, asset_dir):
        """Replace Interchange phong materials with existing project materials.

        For each slot on the mesh, if the current material is a phong
        placeholder, search for an existing material by slot name and
        assign it. Deletes any leftover phong instances from asset_dir.
        """
        mesh = unreal.EditorAssetLibrary.load_asset(mesh_path)
        if not mesh:
            return

        materials = mesh.get_editor_property("materials")
        if not materials:
            return

        phong_paths = []
        assigned = 0
        for i, slot in enumerate(materials):
            current_mat = slot.material_interface
            slot_name = str(slot.material_slot_name)
            if not slot_name:
                continue

            # Track phong instances for cleanup
            if cls._is_phong_instance(current_mat):
                phong_paths.append(current_mat.get_path_name())

                existing = cls._find_existing_material(
                    slot_name, exclude_path=asset_dir)
                if existing:
                    slot.material_interface = existing
                    assigned += 1
                    unreal.log(
                        f"AYON: Replaced phong with '{slot_name}' "
                        f"on slot {i}")

        if assigned:
            mesh.set_editor_property("materials", materials)
            unreal.EditorAssetLibrary.save_asset(mesh_path)

        # Clean up phong instances created by Interchange in asset_dir
        for phong_path in phong_paths:
            # Only delete if it's in our asset directory
            pkg = phong_path.split(".")[0]
            if pkg.startswith(asset_dir):
                unreal.EditorAssetLibrary.delete_asset(pkg)

    def import_and_containerize(
        self, filepath, asset_dir, asset_name, container_name
    ):
        task = None
        if not unreal.EditorAssetLibrary.does_directory_exist(asset_dir):
            unreal.EditorAssetLibrary.make_directory(asset_dir)
        if not unreal.EditorAssetLibrary.does_asset_exist(
            f"{asset_dir}/{asset_name}"):
                task = self.get_task(filepath, asset_dir, asset_name, False)

        unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])

        # Replace Interchange phong placeholders with existing materials
        self._assign_existing_materials(f"{asset_dir}/{asset_name}", asset_dir)

        if not unreal.EditorAssetLibrary.does_asset_exist(
            f"{asset_dir}/{container_name}"):
                # Create Asset Container
                create_container(container=container_name, path=asset_dir)

        return asset_dir

    def imprint(
        self,
        folder_path,
        asset_dir,
        container_name,
        asset_name,
        representation,
        product_type,
        project_name,
        layout
    ):
        data = {
            "schema": "ayon:container-2.0",
            "id": AYON_CONTAINER_ID,
            "folder_path": folder_path,
            "namespace": asset_dir,
            "container_name": container_name,
            "asset_name": asset_name,
            "loader": str(self.__class__.__name__),
            "representation": representation["id"],
            "parent": representation["versionId"],
            "product_type": product_type,
            # TODO these should be probably removed
            "asset": folder_path,
            "family": product_type,
            "project_name": project_name,
            "layout": layout
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
            data (dict): Those would be data to be imprinted.

        Returns:
            list(str): list of container content
        """
        # Create directory for asset and Ayon container
        folder_name = context["folder"]["name"]
        product_type = context["product"]["productType"]
        suffix = "_CON"
        path = self.filepath_from_context(context)
        asset_root, asset_name = format_asset_directory(
            context, self.loaded_asset_dir, self.loaded_asset_name
        )

        tools = unreal.AssetToolsHelpers().get_asset_tools()
        asset_dir, container_name = tools.create_unique_asset_name(
            asset_root, suffix="")

        container_name += suffix
        should_use_layout = options.get("layout", False)

        # Get existing asset dir if possible, otherwise import & containerize
        if should_use_layout and (
            existing_asset_dir := get_dir_from_existing_asset(
                 asset_dir, asset_name)
            ):
                asset_dir = existing_asset_dir
        else:
            asset_dir = self.import_and_containerize(
                path, asset_dir, asset_name, container_name
            )

        self.imprint(
            folder_name,
            asset_dir,
            container_name,
            asset_name,
            context["representation"],
            product_type,
            context["project"]["name"],
            should_use_layout
        )

        asset_content = unreal.EditorAssetLibrary.list_assets(
            asset_dir, recursive=True, include_folder=True
        )

        for a in asset_content:
            unreal.EditorAssetLibrary.save_asset(a)

        return asset_content

    def update(self, container, context):
        folder_path = context["folder"]["path"]
        product_type = context["product"]["productType"]
        repre_entity = context["representation"]

        # Create directory for asset and Ayon container
        suffix = "_CON"
        path = self.filepath_from_context(context)

        asset_root, asset_name = format_asset_directory(
            context, self.loaded_asset_dir, self.loaded_asset_name
        )
        tools = unreal.AssetToolsHelpers().get_asset_tools()
        asset_dir, container_name = tools.create_unique_asset_name(
            asset_root, suffix="")

        container_name += suffix
        should_use_layout = container.get("layout", False)

        # Get existing asset dir if possible, otherwise import & containerize
        if should_use_layout and (
            existing_asset_dir := get_dir_from_existing_asset(
                 asset_dir, asset_name)
            ):
                asset_dir = existing_asset_dir
        else:
            asset_dir = self.import_and_containerize(
                path, asset_dir, asset_name, container_name
            )

        self.imprint(
            folder_path,
            asset_dir,
            container_name,
            asset_name,
            repre_entity,
            product_type,
            context["project"]["name"],
            should_use_layout
        )

        asset_content = unreal.EditorAssetLibrary.list_assets(
            asset_dir, recursive=True, include_folder=False
        )

        for a in asset_content:
            unreal.EditorAssetLibrary.save_asset(a)

    def remove(self, container):
        path = container["namespace"]
        if unreal.EditorAssetLibrary.does_directory_exist(path):
            unreal.EditorAssetLibrary.delete_directory(path)
