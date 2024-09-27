import bpy

bl_info = {
    "name": "Material Pro Tools",
    "blender": (4, 2, 0),
    "category": "Object",
}


class MaterialSlot(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty(name="Material Name")

class GeoNodeSlot(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty(name="GeoNode Modifier Name")

class MeshMaterialSlot(bpy.types.PropertyGroup):
    mesh_name: bpy.props.StringProperty(name="Mesh Name")
    material_names: bpy.props.CollectionProperty(type=MaterialSlot, name="Material Names")
    geonodes: bpy.props.CollectionProperty(type=GeoNodeSlot, name="GeoNode Modifiers")

class MeshMaterialSlotsUIList(bpy.types.UIList):
    bl_idname = "MESH_MATERIAL_SLOTS_UL"
    
    def draw_item(self, context, layout, data, item, index, flt):
        layout.label(text=item.mesh_name)

class MeshMaterialProperties(bpy.types.PropertyGroup):
    slots: bpy.props.CollectionProperty(type=MeshMaterialSlot)

class OBJECT_PT_mesh_material_panel(bpy.types.Panel):
    bl_label = "Mesh-Material Assigner"
    bl_idname = "OBJECT_PT_mesh_material_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'AJO'
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        mesh_material_props = scene.mesh_material_props

        row = layout.row(align=True)
        row.operator("mesh_material.import_slots", text="Import File", icon='IMPORT')
        row.separator()
        row.operator("mesh_material.export_slots", text="Export File", icon='EXPORT')

        layout.row()  # Placeholder row

        row = layout.row()
        row.scale_x = 2.0
        row.scale_y = 1.5
        row.operator("mesh_material.apply_materials", text="Start Apply", icon='PLAY')

        row = layout.row(align=True)
        row.operator("mesh_material.add_slot", icon='ADD', text="Add Slot")
        row.separator()
        row.operator("mesh_material.remove_all_slots", icon='X', text="Remove All")

class OBJECT_PT_slots_panel(bpy.types.Panel):
    bl_label = "Slots"
    bl_idname = "OBJECT_PT_slots_panel"
    bl_parent_id = "OBJECT_PT_mesh_material_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'MTP'
    bl_options = {'DEFAULT_CLOSED'}
        
    def draw(self, context):
        layout = self.layout
        scene = context.scene
        mesh_material_props = scene.mesh_material_props

        if not mesh_material_props.slots:
            layout.label(text="Slot Not Available", icon='ERROR')
            return

        layout.template_list("MESH_MATERIAL_SLOTS_UL", "", mesh_material_props, "slots", mesh_material_props, "active_slot_index", rows=3)

        for index, slot in enumerate(mesh_material_props.slots):
            box = layout.box()
            row = box.row(align=True)
            row.prop(slot, "mesh_name", text="", icon='MESH_DATA')

            col = row.column(align=True)
            subrow = col.row(align=True)
            subcol = subrow.column(align=True)
            for material_slot in slot.material_names:
                subcol.prop(material_slot, "name", text="", icon='MATERIAL')

            subcol = subrow.column(align=True)
            for geonode_slot in slot.geonodes:
                subcol.prop(geonode_slot, "name", text="", icon='NODETREE')

            row.operator("mesh_material.remove_slot", text="", icon='X').index = index

class OBJECT_OT_add_slot(bpy.types.Operator):
    """Add Material Data from Selected Objects."""
    bl_idname = "mesh_material.add_slot"
    bl_label = "Add Slot"

    def execute(self, context):
        scene = context.scene
        mesh_material_props = scene.mesh_material_props
        selected_objs = context.selected_objects

        for obj in selected_objs:
            if obj and obj.type == 'MESH':
                new_slot = mesh_material_props.slots.add()
                new_slot.mesh_name = obj.name

                for mat in obj.data.materials:
                    material_slot = new_slot.material_names.add()
                    material_slot.name = mat.name if mat else ""

                if not new_slot.material_names:
                    new_slot.material_names.add()

                for modifier in obj.modifiers:
                    if modifier.type == 'NODES' and modifier.node_group:
                        geonode_slot = new_slot.geonodes.add()
                        geonode_slot.name = modifier.node_group.name

                if not new_slot.geonodes:
                    new_slot.geonodes.add()

                self.report({'INFO'}, f"Added {obj.name} with {len(new_slot.material_names)} materials and {len(new_slot.geonodes)} GeoNode modifiers")
            else:
                self.report({'WARNING'}, f"Object {obj.name} is not a valid mesh.")

        return {'FINISHED'}

class OBJECT_OT_remove_slot(bpy.types.Operator):
    """Remove All Material Slot"""
    bl_idname = "mesh_material.remove_slot"
    bl_label = "Remove Slot"

    index: bpy.props.IntProperty()

    def execute(self, context):
        scene = context.scene
        mesh_material_props = scene.mesh_material_props
        mesh_material_props.slots.remove(self.index)
        return {'FINISHED'}

class OBJECT_OT_remove_all_slots(bpy.types.Operator):
    """Remove Material Data from Selected Objects"""
    bl_idname = "mesh_material.remove_all_slots"
    bl_label = "Remove All Slots"

    def execute(self, context):
        scene = context.scene
        mesh_material_props = scene.mesh_material_props
        mesh_material_props.slots.clear()
        return {'FINISHED'}

class OBJECT_OT_apply_materials(bpy.types.Operator):
    """Start Apply Materials using Txt File Data"""
    bl_idname = "mesh_material.apply_materials"
    bl_label = "Start Apply"

    def execute(self, context):
        scene = context.scene
        mesh_material_props = scene.mesh_material_props
        
        for slot in mesh_material_props.slots:
            print(f"Processing slot for mesh: {slot.mesh_name}")
            mesh = bpy.data.objects.get(slot.mesh_name)
            if mesh and mesh.type == 'MESH':
                for i, mat_slot in enumerate(slot.material_names):
                    material = bpy.data.materials.get(mat_slot.name)
                    if material:
                        if i < len(mesh.data.materials):
                            mesh.data.materials[i] = material
                        else:
                            mesh.data.materials.append(material)
                        print(f"Applied {material.name} to {mesh.name} slot {i}")
                    else:
                        print(f"Material '{mat_slot.name}' not found.")
            else:
                print(f"Mesh '{slot.mesh_name}' not found or invalid.")

        return {'FINISHED'}

class OBJECT_OT_export_slots(bpy.types.Operator):
    """Export Materials Data as Txt file"""
    bl_idname = "mesh_material.export_slots"
    bl_label = "Export to Notepad"

    filepath: bpy.props.StringProperty(subtype="FILE_PATH")

    def execute(self, context):
        scene = context.scene
        mesh_material_props = scene.mesh_material_props

        if not self.filepath:
            self.report({'ERROR'}, "No file path specified")
            return {'CANCELLED'}

        try:
            with open(self.filepath, 'w') as file:
                for slot in mesh_material_props.slots:
                    materials = ",".join([mat.name for mat in slot.material_names])
                    geonodes = ",".join([gn.name for gn in slot.geonodes])
                    file.write(f"{slot.mesh_name}|{materials}|{geonodes}\n")

            self.report({'INFO'}, f"Exported to {self.filepath}")
        except Exception as e:
            self.report({'ERROR'}, f"Failed to export: {e}")

        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

class OBJECT_OT_import_slots(bpy.types.Operator):
    """Import Materials Data as Txt file"""
    bl_idname = "mesh_material.import_slots"
    bl_label = "Import from Notepad"

    filepath: bpy.props.StringProperty(subtype="FILE_PATH")

    def execute(self, context):
        scene = context.scene
        mesh_material_props = scene.mesh_material_props

        if not self.filepath:
            self.report({'ERROR'}, "No file path specified")
            return {'CANCELLED'}

        try:
            with open(self.filepath, 'r') as file:
                lines = file.readlines()

                for line in lines:
                    line = line.strip()
                    if not line:
                        continue

                    try:
                        parts = line.split('|')
                        if len(parts) < 3:
                            self.report({'ERROR'}, f"Invalid format in line: {line}")
                            continue

                        mesh_name = parts[0].strip()
                        materials_str = parts[1].strip()
                        geonodes_str = parts[2].strip()

                        materials = [mat.strip() for mat in materials_str.split(',') if mat.strip()]
                        geonodes = [gn.strip() for gn in geonodes_str.split(',') if gn.strip()]

                        slot = mesh_material_props.slots.add()
                        slot.mesh_name = mesh_name

                        if not materials:
                            materials = [""]
                        if not geonodes:
                            geonodes = [""]

                        for mat_name in materials:
                            material_slot = slot.material_names.add()
                            material_slot.name = mat_name

                        for gn_name in geonodes:
                            geonode_slot = slot.geonodes.add()
                            geonode_slot.name = gn_name

                    except ValueError as e:
                        self.report({'ERROR'}, f"Failed to parse line: {line}. Error: {e}")
                        continue

            self.report({'INFO'}, f"Imported from {self.filepath}")
        except Exception as e:
            self.report({'ERROR'}, f"Failed to import: {e}")

        return {'FINISHED'}
    
    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

def register():
    bpy.utils.register_class(MaterialSlot)
    bpy.utils.register_class(GeoNodeSlot)
    bpy.utils.register_class(MeshMaterialSlot)
    bpy.utils.register_class(MeshMaterialSlotsUIList)
    bpy.utils.register_class(OBJECT_PT_mesh_material_panel)
    bpy.utils.register_class(OBJECT_PT_slots_panel)
    bpy.utils.register_class(OBJECT_OT_add_slot)
    bpy.utils.register_class(OBJECT_OT_remove_slot)
    bpy.utils.register_class(OBJECT_OT_remove_all_slots)
    bpy.utils.register_class(OBJECT_OT_apply_materials)
    bpy.utils.register_class(OBJECT_OT_export_slots)
    bpy.utils.register_class(OBJECT_OT_import_slots)
    bpy.utils.register_class(MeshMaterialProperties)
    bpy.types.Scene.mesh_material_props = bpy.props.PointerProperty(type=MeshMaterialProperties)
    print("Addon Registered")

def unregister():
    bpy.utils.unregister_class(MaterialSlot)
    bpy.utils.unregister_class(GeoNodeSlot)
    bpy.utils.unregister_class(MeshMaterialSlot)
    bpy.utils.unregister_class(MeshMaterialSlotsUIList)
    bpy.utils.unregister_class(OBJECT_PT_mesh_material_panel)
    bpy.utils.unregister_class(OBJECT_PT_slots_panel)
    bpy.utils.unregister_class(OBJECT_OT_add_slot)
    bpy.utils.unregister_class(OBJECT_OT_remove_slot)
    bpy.utils.unregister_class(OBJECT_OT_remove_all_slots)
    bpy.utils.unregister_class(OBJECT_OT_apply_materials)
    bpy.utils.unregister_class(OBJECT_OT_export_slots)
    bpy.utils.unregister_class(OBJECT_OT_import_slots)
    bpy.utils.unregister_class(MeshMaterialProperties)
    del bpy.types.Scene.mesh_material_props
    print("Addon Unregistered")

if __name__ == "__main__":
    register()
