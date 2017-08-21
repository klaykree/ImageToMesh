import bpy
import importlib
from bpy.props import StringProperty
from bpy.props import BoolProperty
from bpy.props import EnumProperty
from bpy.props import CollectionProperty
from bpy.props import FloatProperty
from bpy.props import *

import inspect, os, sys
def dir_of_this():
    raw_path = inspect.getfile(inspect.currentframe())
    l = len(bpy.data.filepath)
    if raw_path[:l] == bpy.data.filepath:
        buf_name = raw_path[l+1:]
        raw_path = bpy.data.texts[buf_name].filepath
    return os.path.dirname(raw_path)

p1 = dir_of_this()
if not p1 in sys.path:
    sys.path.append(p1)

import mesh_shape
importlib.reload(mesh_shape)
from mesh_shape import *

#import os
#os.system("cls")
#bpy.app.debug = True

bl_info = {
 "name": "Image to mesh",
 "author": "Kree",
 "version": (1, 0),
 "blender": (2, 7, 8),
 "location": "Add > Mesh > Image",
 "description": "Creates a mesh from an image",
 "warning": "",
 "wiki_url": "",
 "tracker_url": "",
 "category": "Import-Export",
 }

DepthButtonPressed = False
OutlineButtonPressed = False

class ImageToMesh(bpy.types.Operator):
 """Creates a mesh from an image"""
 bl_idname = "add.image_to_mesh"
 bl_label = "Image to mesh"
 bl_options = {'REGISTER', 'UNDO'}
 
 Image = StringProperty(subtype="FILE_PATH")
 filename_ext = ".png"
 filter_glob = StringProperty(default="*.png", options={'HIDDEN'})
 
 DepthGradient = bpy.props.EnumProperty(items=(('BlackToWhite', 'Black to white', 'Black foreground with white background'),
                                               ('WhiteToBlack', 'White to black', 'White foreground with black background'),
                                               ('Alpha', 'Alpha', 'Alpha channel depth')))
 
 Depth = bpy.props.FloatProperty(min=0.0, soft_min=0.0, default=5.0)
 
 def draw(self, context):
    self.layout.prop(self, 'Image')
    self.layout.operator("depth.button")
    self.layout.prop(self, 'Depth', text='Mesh depth')
    self.layout.operator("outline.button")
    self.layout.prop(self, "DepthGradient", text='')
 
 def execute(self, context):
    global DepthButtonPressed
    global OutlineButtonPressed
    
    if DepthButtonPressed:
        DepthButtonPressed = False
        Image = None
        if len(self.Image) != 0:
            Image = bpy.data.images.load(self.Image)
            
        if Image != None:
            #Defined = DefineMesh(self.__GetGradientEnum(), GenerateType.Depth, Image)
            MeshShape(self.__GetGradientEnum(), self.Depth, GenerateType.Depth, Image)
    
    if OutlineButtonPressed:
        OutlineButtonPressed = False
        Image = None
        if len(self.Image) != 0:
            Image = bpy.data.images.load(self.Image)
            
        if Image != None:
            #Defined = DefineMesh(self.__GetGradientEnum(), GenerateType.Outline, Image)
            MeshShape(self.__GetGradientEnum(), self.Depth, GenerateType.Outline, Image)
    
    return {'FINISHED'}

 def __GetGradientEnum(self):
     if self.DepthGradient == 'BlackToWhite':
         return Gradient.BlackToWhite
     if self.DepthGradient == 'WhiteToBlack':
         return Gradient.WhiteToBlack
     if self.DepthGradient == 'Alpha':
         return Gradient.Alpha

#ImageToMesh class end

class DepthButton(bpy.types.Operator):
    bl_idname = "depth.button"
    bl_label = "Create depth mesh"
    
    def execute(self, context):
        global DepthButtonPressed
        DepthButtonPressed = True
        return{'FINISHED'}

class OutlineButton(bpy.types.Operator):
    bl_idname = "outline.button"
    bl_label = "Create outline mesh"
    
    def execute(self, context):
        global OutlineButtonPressed
        OutlineButtonPressed = True
        return{'FINISHED'}

def menu_func_import(self, context):
    #self.layout.operator_context = 'INVOKE_DEFAULT'
    
    self.layout.operator(ImageToMesh.bl_idname,
      text="Image (to mesh)",
      icon='PLUGIN')

def register():
    bpy.utils.register_module(__name__)
    bpy.types.INFO_MT_mesh_add.append(menu_func_import)
 
def unregister():
    bpy.utils.unregister_module(__name__)
    bpy.types.INFO_MT_mesh_add.remove(menu_func_import)

if __name__ == "__main__":
 register()