# coding: utf-8
"""
UnityHumanoidHelper

reference
    https://github.com/sugiany/blender_mmd_tools
"""
import bpy
import math
import json


class SelectObjects:
    def __init__(self, active_object, selected_objects=[]):
        if not isinstance(active_object, bpy.types.Object):
            raise ValueError
        try:
            bpy.ops.object.mode_set(mode='OBJECT')
        except Exception:
            pass

        for i in bpy.context.selected_objects:
            i.select = False

        self.__active_object = active_object
        self.__selected_objects = [active_object]+selected_objects

        self.__hides = []
        for i in self.__selected_objects:
            self.__hides.append(i.hide)
            i.hide = False
            i.select = True
        bpy.context.scene.objects.active = active_object

    def __enter__(self):
        return self.__active_object

    def __exit__(self, type, value, traceback):
        for i, j in zip(self.__selected_objects, self.__hides):
            i.hide = j
            
            
class EditMode:
    def __init__(self, obj):
        if not isinstance(obj, bpy.types.Object):
            raise ValueError
        self.__prevMode = obj.mode
        self.__obj = obj
        with SelectObjects(obj) as act_obj:
            if obj.mode != 'EDIT':
                bpy.ops.object.mode_set(mode='EDIT')

    def __enter__(self):
        return self.__obj.data

    def __exit__(self, type, value, traceback):
        bpy.ops.object.mode_set(mode=self.__prevMode)
        
        
class PasteUnityHumanoid(bpy.types.Operator):
    
    bl_idname = "unityhumanoid.paste_armature_unity_humanoid"
    bl_label = "Paste Unity Humanoid"
    bl_description = "paste Armature that has Unity Humanoid Bones"
    bl_options = {'REGISTER', 'UNDO'}
    
    @staticmethod
    def is_connected(a, b):
        if a.startswith('Left'):
            return b.startswith('Left')
        elif a.startswith('Right'):
            return b.startswith('Right')
        else:
            if b.startswith('Left'):
                return False
            elif b.startswith('Right'):
                return False
            else:
                return True                 

    @staticmethod    
    def build_tree(armature, root):
        min_height=[0]
        def build(parent, node):
            if 'pos' not in node:
                bone=parent
            else:
                bone = armature.edit_bones.new(name=node['name'])
                if parent:
                    bone.parent=parent
                    p=node['pos']
                    pos=[-p[0], -p[2], p[1]]
                    bone.head = [x + y for x, y in zip(parent.head, pos)]
                    
                    if bone.head[2]<min_height[0]:
                        min_height[0]=bone.head[2]
                        print(min_height)
                        
                    if PasteUnityHumanoid.is_connected(bone.name, parent.name):
                        parent.tail=bone.head
                        bone.use_connect=True
                else:
                    # hips
                    pass
                bone.tail=bone.head
                
            if 'children' in node:
                for child in node['children']:
                    build(bone, child)
            else:
                # leaf bone
                d = bone.head - bone.parent.head
                if bone.name.endswith('Toes'):
                    d[2]=0
                d.normalize()
                #print(help(d))
                bone.tail = [x + y for x, y in zip(bone.head, d * 0.05)]
                    
        build(None, root)
        
        print(min_height)                    
        bpy.context.scene.cursor_location = (0.0, 0.0, 0.0)
        bpy.context.space_data.pivot_point = 'CURSOR'
        bpy.ops.armature.select_all(action='SELECT')
        bpy.ops.transform.translate(value=(0.0, 0.0, -min_height[0]))
            

    def execute(self, context):
        parsed=json.loads(bpy.context.window_manager.clipboard)        
        
        arm = bpy.data.armatures.new(name='humanoid')
        armObj = bpy.data.objects.new(name='PastedHumanoid', object_data=arm)
        bpy.context.scene.objects.link(armObj)
        armObj.show_x_ray=True
        
        with EditMode(armObj) as arm:
            PasteUnityHumanoid.build_tree(arm, parsed)        
        
        return {'FINISHED'}            


class BoneDefine:
    def __init__(self, name, tail, children=[], head=None):
        self.name=name
        self.tail=tail
        self.head=head
        self.children=children

    @property
    def is_connected(self):
        return not self.head
            
        
class CreateUnityHumanoid(bpy.types.Operator):
    
    bl_idname = "unityhumanoid.add_armature_unity_humanoid"
    bl_label = "Add Unity Humanoid"
    bl_description = "add Armature that has Unity Humanoid Bones"
    bl_options = {'REGISTER', 'UNDO'}

    @staticmethod    
    def build_tree(armature, parent, data):
        bone = armature.edit_bones.new(name=data.name)
        if parent:
            bone.head = parent.tail
        else:
            bone.head = [0, 0, 0]
        if data.head:
            bone.head=[x+y for x, y in zip(bone.head, data.head)]
        
        bone.tail = [x+y for x, y in zip(bone.head, data.tail)]
        if parent:
            bone.parent=parent
            bone.use_connect=data.is_connected
        #print(bone)
        for child in data.children:
            CreateUnityHumanoid.build_tree(armature, bone, child)

    def execute(self, context):
        arm = bpy.data.armatures.new(name='humanoid')
        armObj = bpy.data.objects.new(name='ArmatureHumanoid', object_data=arm)
        bpy.context.scene.objects.link(armObj)
        armObj.show_x_ray=True
        #arm.show_names=True
        hip_height=2.1
        with EditMode(armObj) as arm:
            CreateUnityHumanoid.build_tree(arm, None,
                BoneDefine('Hips', [0, 0, 0.3], [
                    BoneDefine('Spine', [0, 0, 0.3], [
                        BoneDefine('Chest', [0, 0, 0.3], [
                            BoneDefine('Neck', [0, 0, 0.3], [
                                BoneDefine('Head', [0, 0, 0.5], [
                                    BoneDefine('Eye.L', [0.1, -0.3, 0]),
                                    BoneDefine('Jaw', [0, -0.3, -0.2])
                                ])
                            ]),
                            BoneDefine('Shoulder.L', [0.3, 0, 0], [
                                BoneDefine('UpperArm.L', [0.5, 0, 0], [
                                    BoneDefine('LowerArm.L', [0.5, 0, 0], [
                                        BoneDefine('Hand.L', [0.1, 0, 0], [
                                            BoneDefine('ThumbProximal.L', [0.03, -0.03, 0], [
                                                BoneDefine('ThumbIntermediate.L', [0.03, -0.03, 0], [
                                                    BoneDefine('ThumbDistal.L', [0.03, -0.03, 0])
                                                ])
                                            ]),
                                            BoneDefine('IndexProximal.L', [0.08, -0.03, 0], [
                                                BoneDefine('IndexIntermediate.L', [0.06, 0, 0], [
                                                    BoneDefine('IndexDistal.L', [0.06, 0, 0])
                                                ])
                                            ]),
                                            BoneDefine('MiddleProximal.L', [0.08, -0.01, 0], [
                                                BoneDefine('MiddleIntermediate.L', [0.06, 0, 0], [
                                                    BoneDefine('MiddleDistal.L', [0.06, 0, 0])
                                                ])
                                            ]),
                                            BoneDefine('RingProximal.L', [0.08, 0.01, 0], [
                                                BoneDefine('RingIntermediate.L', [0.06, 0, 0], [
                                                    BoneDefine('RingDistal.L', [0.06, 0, 0])
                                                ])
                                            ]),
                                            BoneDefine('LittleProximal.L', [0.07, 0.03, 0], [
                                                BoneDefine('LittleIntermediate.L', [0.05, 0, 0], [
                                                    BoneDefine('LittleDistal.L', [0.05, 0, 0])
                                                ])
                                            ]),
                                        ])
                                    ])
                                ])
                            ])
                        ])
                    ]),
                    BoneDefine('UpperLeg.L', [0, 0, -1], [
                        BoneDefine('LowerLeg.L', [0, 0, -1], [
                            BoneDefine('Foot.L', [0, -0.3, -0.2], [
                                BoneDefine('Toe.L', [0, -0.1, 0])
                            ])
                        ])
                    ], [0.3, 0, -0.2])
                ], [0, 0, hip_height])
            )
            
            bpy.ops.armature.select_all(action='SELECT')
            bpy.ops.armature.symmetrize()

            bpy.context.scene.cursor_location = (0.0, 0.0, 0.0)
            bpy.context.space_data.pivot_point = 'CURSOR'
            bpy.ops.armature.select_all(action='SELECT')
            bpy.ops.transform.resize(value=(0.5, 0.5, 0.5))
            
            
        return {'FINISHED'}


class AddXMirrorVertexGroup(bpy.types.Operator):

    bl_idname = "unityhumanoid.add_xmirror_vertexgroup"
    bl_label = "Add X-Mirror VertexGroup"
    bl_description = "add vertex group for mirroring Armature"
    bl_options = {'REGISTER', 'UNDO'}

    @staticmethod
    def createVertexGroupWithEachBone(mesh, armature):
        print(mesh, armature)
        for b in armature.bones.keys():
            name=b.lower()
            if name.endswith('.l') or name.endswith('_l') or name.endswith('.r') or name.endswith('_r'):            
                bpy.ops.object.vertex_group_add()
                bpy.context.active_object.vertex_groups.active.name=b
                
    def execute(self, context):
        o=context.object
        #print(dir(o))
        for m in o.modifiers:
            print(m)
            if m.name=="Armature":
                MirrorVertexGroup.createVertexGroupWithEachBone(o.data, m.object.data)
        return {'FINISHED'}
    
    
class FixRotation(bpy.types.Operator):
    
    bl_idname = "unityhumanoid.fixrotation"
    bl_label = "Fix Rotation"
    bl_description = "Fix rotation to Unity's left handed y-up coordinate"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        o=context.object
        bpy.ops.transform.rotate(value=-math.pi/2 , axis=(1, 0, 0))
        bpy.ops.object.transform_apply(rotation=True)
        bpy.ops.transform.rotate(value=math.pi/2 , axis=(1, 0, 0))
        
        for m in o.modifiers:
            if m.name=="Armature":
                with SelectObjects(m.object):
                    bpy.ops.transform.rotate(value=-math.pi/2 , axis=(1, 0, 0))
                    bpy.ops.object.transform_apply(rotation=True)
                    bpy.ops.transform.rotate(value=math.pi/2 , axis=(1, 0, 0))                                
                                
        return {'FINISHED'}
        
    
class UnityHumanoidPanel(bpy.types.Panel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Unity Humanoid"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'

    def draw(self, context):
        if context.mode!='OBJECT':
            return
        
        layout = self.layout
        obj = context.object
                    
        row = layout.row()
        row.operator(PasteUnityHumanoid.bl_idname)
        
        row = layout.row()
        row.operator(CreateUnityHumanoid.bl_idname)

        if bpy.context.selected_objects and context.active_object and context.active_object.type=='MESH':
            print(context.active_object)
                        
            row = layout.row()
            row.operator(AddXMirrorVertexGroup.bl_idname)
            
        if bpy.context.selected_objects and context.active_object:
            if context.active_object.type=='MESH' or context.active_object.type=='ARMATURE':
                print(context.active_object)
            
                row = layout.row()
                row.operator(FixRotation.bl_idname)                        


bl_info = {
    "name": "UnityHumanoidHelper",
    "author": "ousttrue",
    "version": (1, 0),
    "blender": (2, 77, 0),
    "location": "",
    "description": "Helper tools for Unity Humanoid Model",
    "warning": "",
    "support": "TESTING",
    "wiki_url": "",
    "tracker_url": "",
    "category": "Object"
}


def register():
    bpy.utils.register_module(__name__)


def unregister():
    bpy.utils.unregister_module(__name__)


if __name__ == "__main__":
    unregister()
    register()
