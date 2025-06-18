#########################################################################################
# Filename:   LinearAlgebra.py
# Author:     Rafel Amer (rafel.amer AT upc.edu)
# Copyright:  Rafel Amer 2020-2025
#
#             This file contains code from the files add_mesh_3d_function_surface.
#             and object_utils.py distributed with Blender as add_ons
# 
# Disclaimer: This code is presented "as is" and it has been written to learn
#             to use the python scripting language and the Blender sofware
#             use them in the studies of Linear Algebra and Geometry
#
# License:    This software is free software; you can redistribute it and/or
#             modify it under the terms of either:
#
#             1 the GNU Lesser General Public License as published by the Free
#               Software Foundation; either version 3 of the License, or (at your
#               option) any later version.
#
#             or
#
#             2 the GNU General Public License as published by the Free
#               Foundation; either version 2 of the License, or (at your option)
#               any later version.
#
#	          See https://www.gnu.org/licenses/
#
#########################################################################################
import math
import bpy
import bmesh
import random
import numpy as np
try:
	from sympy import *
except:
	print("Python sympy not available")
	pass
from mathutils import Vector, Matrix, Euler, Quaternion


def add_object_align_init(context, operator):
    properties = operator.properties if operator is not None else None

    space_data = context.space_data
    if space_data and space_data.type != 'VIEW_3D':
        space_data = None

    # location
    if operator and properties.is_property_set("location"):
        location = Matrix.Translation(Vector(properties.location))
    else:
        location = Matrix.Translation(context.scene.cursor.location)

        if operator:
            properties.location = location.to_translation()

    # rotation
    add_align_preference = context.preferences.edit.object_align
    if operator:
        if not properties.is_property_set("rotation"):
            # So one of "align" and "rotation" will be set
            properties.align = add_align_preference

        if properties.align == 'WORLD':
            rotation = properties.rotation.to_matrix().to_4x4()
        elif properties.align == 'VIEW':
            rotation = space_data.region_3d.view_matrix.to_3x3().inverted()
            rotation.resize_4x4()
            properties.rotation = rotation.to_euler()
        elif properties.align == 'CURSOR':
            rotation = context.scene.cursor.matrix
            rotation.col[3][0:3] = 0.0, 0.0, 0.0
            properties.rotation = rotation.to_euler()
        else:
            rotation = properties.rotation.to_matrix().to_4x4()
    else:
        if (add_align_preference == 'VIEW') and space_data:
            rotation = space_data.region_3d.view_matrix.to_3x3().inverted()
            rotation.resize_4x4()
        elif add_align_preference == 'CURSOR':
            rotation = context.scene.cursor.rotation_euler.to_matrix().to_4x4()
        else:
            rotation = Matrix()

    return location @ rotation

#
#
#
def object_data_add(context, obdata, operator=None, name=None):
    layer = context.view_layer
    layer_collection = context.layer_collection or layer.active_layer_collection
    scene_collection = layer_collection.collection
	
    for ob in layer.objects:
        if ob is not None:
            ob.select_set(False)

    if name is None:
        name = "Object" if obdata is None else obdata.name

    obj_act = layer.objects.active
    obj_new = bpy.data.objects.new(name, obdata)
    scene_collection.objects.link(obj_new)
    obj_new.select_set(True)
    obj_new.matrix_world = add_object_align_init(context, operator)

    space_data = context.space_data
    if space_data and space_data.type != 'VIEW_3D':
        space_data = None

    if space_data:
        if space_data.local_view:
            obj_new.local_view_set(space_data, True)

    if obj_act and obj_act.mode == 'EDIT' and obj_act.type == obj_new.type:
        bpy.ops.mesh.select_all(action='DESELECT')
        obj_act.select_set(True)
        bpy.ops.object.mode_set(mode='OBJECT')

        obj_act.select_set(True)
        layer.update()  # apply location
        # layer.objects.active = obj_new

        # Match up UV layers, this is needed so adding an object with UVs
        # doesn't create new layers when there happens to be a naming mismatch.
        uv_new = obdata.uv_layers.active
        if uv_new is not None:
            uv_act = obj_act.data.uv_layers.active
            if uv_act is not None:
                uv_new.name = uv_act.name

        bpy.ops.object.join()  # join into the active.
        if obdata:
            bpy.data.meshes.remove(obdata)

        bpy.ops.object.mode_set(mode='EDIT')
    else:
        layer.objects.active = obj_new
        if context.preferences.edit.use_enter_edit_mode:
            if obdata and obdata.library is None:
                obtype = obj_new.type
                mode = None
                if obtype in {'ARMATURE', 'CURVE', 'CURVES', 'FONT', 'LATTICE', 'MESH', 'META', 'SURFACE'}:
                    mode = 'EDIT'
                elif obtype == 'GPENCIL':
                    mode = 'EDIT_GPENCIL'

                if mode is not None:
                    bpy.ops.object.mode_set(mode=mode)
    return obj_new
#
#
#
def create_mesh_object(context,verts,edges,faces,name):
	mesh = bpy.data.meshes.new(name)
	mesh.from_pydata(verts, edges, faces)
	mesh.update()
	return object_data_add(context, mesh, operator=None)
#
#
#
def createFaces(vertIdx1,vertIdx2,closed=False,flipped=False):
	faces = []
	if not vertIdx1 or not vertIdx2:
		return None
	if len(vertIdx1) < 2 and len(vertIdx2) < 2:
		return None

	fan = False
	if (len(vertIdx1) != len(vertIdx2)):
		if (len(vertIdx1) == 1 and len(vertIdx2) > 1):
			fan = True
		else:
			return None

	total = len(vertIdx2)
	if closed:
		if flipped:
			face = [vertIdx1[0],vertIdx2[0],vertIdx2[total - 1]]
			if not fan:
				face.append(vertIdx1[total - 1])
			faces.append(face)
		else:
			face = [vertIdx2[0], vertIdx1[0]]
			if not fan:
				face.append(vertIdx1[total - 1])
			face.append(vertIdx2[total - 1])
			faces.append(face)
	for num in range(total - 1):
		if flipped:
			if fan:
				face = [vertIdx2[num], vertIdx1[0], vertIdx2[num + 1]]
			else:
				face = [vertIdx2[num], vertIdx1[num],vertIdx1[num + 1], vertIdx2[num + 1]]
			faces.append(face)
		else:
			if fan:
				face = [vertIdx1[0], vertIdx2[num], vertIdx2[num + 1]]
			else:
				face = [vertIdx1[num], vertIdx2[num],vertIdx2[num + 1], vertIdx1[num + 1]]
			faces.append(face)
	return faces
#
#
#
def draw_parametric_surface(eq,range_u_min,range_u_max,range_u_step,range_v_min,range_v_max,range_v_step,name,wrap_u=False,wrap_v=False,close_v=False):
	verts = []
	faces = []
	if not callable(range_u_min) and not callable(range_u_max):
		uStep = (range_u_max - range_u_min) / range_u_step
	vStep = (range_v_max - range_v_min) / range_v_step
	uRange = range_u_step + 1
	vRange = range_v_step + 1

	if wrap_u:
		uRange = uRange - 1
	if wrap_v:
		vRange = vRange - 1

	for vN in range(vRange):
		v = range_v_min + (vN * vStep)
		if callable(range_u_min):
			u_min = range_u_min(v)
		else:
			u_min = range_u_min
		if callable(range_u_max):
			u_max = range_u_max(v)
		else:
			u_max = range_u_max
		uStep = (u_max - u_min) / range_u_step
		for uN in range(uRange):
			u = u_min + (uN * uStep)
			verts.append(eq(u,v))

	for vN in range(range_v_step):
		vNext = vN + 1
		if vNext >= vRange:
			vNext = 0
		for uN in range(range_u_step):
			uNext = uN + 1
			if uNext >= uRange:
				uNext = 0
			faces.append([(vNext * uRange) + uNext,(vNext * uRange) + uN,(vN * uRange) + uN,(vN * uRange) + uNext])

	if close_v and wrap_u and (not wrap_v):
		for uN in range(1, range_u_step - 1):
			faces.append([range_u_step - 1,range_u_step - 1 - uN,range_u_step - 2 - uN])
			faces.append([range_v_step * uRange,range_v_step * uRange + uN,range_v_step * uRange + uN + 1])
	create_mesh_object(bpy.context,verts, [], faces, name)
#
#
#
class Color():
	"""
    Class that defines a color in RGB format
    """
	def __init__(self,r,g,b,name):
		self.r = r
		self.g = g
		self.b = b
		self.name = name
#
#
#
class Colors():
	"""
	Class that defines a list of colors by name
	"""
	colorsbyname = {
		'Black' : Color(0,0,0,'Black'),
		'GrayObscure' : Color(0.2,0.2,0.2,'GrayObscure'),
		'GrayDark' : Color(0.4,0.4,0.4,'GrayDark'),
		'GrayLight' : Color(0.6,0.6,0.6,'GrayLight'),
		'GrayPale' : Color(0.8,0.8,0.8,'GrayPale'),
		'White' : Color(1,1,1,'White'),
		'Red' : Color(1,0,0,'Red'),
		'RedDarkHard' : Color(0.8,0,0,'RedDarkHard'),
		'RedLightHard' : Color(1,0.2,0.2,'RedLightHard'),
		'RedDarkFaded' : Color(0.6,0,0,'RedDarkFaded'),
		'RedMediumFaded' : Color(0.8,0.2,0.2,'RedMediumFaded'),
		'RedLightFaded' : Color(1,0.4,0.4,'RedLightFaded'),
		'RedObscureDull' : Color(0.4,0,0,'RedObscureDull'),
		'RedDarkDull' : Color(0.6,0.2,0.2,'RedDarkDull'),
		'RedLightDull' : Color(0.8,0.4,0.4,'RedLightDull'),
		'RedPaleDull' : Color(1,0.6,0.6,'RedPaleDull'),
		'RedObscureWeak' : Color(0.2,0,0,'RedObscureWeak'),
		'RedDarkWeak' : Color(0.4,0.2,0.2,'RedDarkWeak'),
		'RedMediumWeak' : Color(0.6,0.4,0.4,'RedMediumWeak'),
		'RedLightWeak' : Color(0.8,0.6,0.6,'RedLightWeak'),
		'RedPaleWeak' : Color(1,0.8,0.8,'RedPaleWeak'),
		'Orange' : Color(1,0.37,0.12,'Orange'),
		'OrangeRedDark' : Color(0.6,0.2,0,'OrangeRedDark'),
		'OrangeRedMedium' : Color(0.8,0.4,0.2,'OrangeRedMedium'),
		'OrangeRedLight' : Color(1,0.6,0.4,'OrangeRedLight'),
		'OrangeOrangeRed' : Color(1,0.4,0,'OrangeOrangeRed'),
		'RedOrangeDark' : Color(0.8,0.2,0,'RedOrangeDark'),
		'RedOrangeLight' : Color(1,0.4,0.2,'RedOrangeLight'),
		'RedRedOrange' : Color(1,0.2,0,'RedRedOrange'),
		'OrangeDarkHard' : Color(0.8,0.4,0,'OrangeDarkHard'),
		'OrangeLightHard' : Color(1,0.6,0.2,'OrangeLightHard'),
		'OrangeObscureDull' : Color(0.4,0.2,0,'OrangeObscureDull'),
		'OrangeDarkDull' : Color(0.6,0.4,0.2,'OrangeDarkDull'),
		'OrangeLightDull' : Color(0.8,0.6,0.4,'OrangeLightDull'),
		'OrangePaleDull' : Color(1,0.8,0.6,'OrangePaleDull'),
		'OrangeYellowDark' : Color(0.6,0.4,0,'OrangeYellowDark'),
		'OrangeYellowMedium' : Color(0.8,0.6,0.2,'OrangeYellowMedium'),
		'OrangeYellowLight' : Color(1,0.8,0.4,'OrangeYellowLight'),
		'OrangeOrangeYellow' : Color(1,0.6,0,'OrangeOrangeYellow'),
		'YellowOrangeDark' : Color(0.8,0.6,0,'YellowOrangeDark'),
		'YellowOrangeLight' : Color(1,0.8,0.2,'YellowOrangeLight'),
		'YellowYellowOrange' : Color(1,0.8,0,'YellowYellowOrange'),
		'Yellow' : Color(1,1,0,'Yellow'),
		'YellowDarkHard' : Color(0.8,0.8,0,'YellowDarkHard'),
		'YellowLightHard' : Color(1,1,0.2,'YellowLightHard'),
		'YellowDarkFaded' : Color(0.6,0.6,0,'YellowDarkFaded'),
		'YellowMediumFaded' : Color(0.8,0.8,0.2,'YellowMediumFaded'),
		'YellowLightFaded' : Color(1,1,0.4,'YellowLightFaded'),
		'YellowObscureDull' : Color(0.4,0.4,0,'YellowObscureDull'),
		'YellowDarkDull' : Color(0.6,0.6,0.2,'YellowDarkDull'),
		'YellowLightDull' : Color(0.8,0.8,0.4,'YellowLightDull'),
		'YellowPaleDull' : Color(1,1,0.6,'YellowPaleDull'),
		'YellowObscureWeak' : Color(0.2,0.2,0,'YellowObscureWeak'),
		'YellowDarkWeak' : Color(0.4,0.4,0.2,'YellowDarkWeak'),
		'YellowMediumWeak' : Color(0.6,0.6,0.4,'YellowMediumWeak'),
		'YellowLightWeak' : Color(0.8,0.8,0.6,'YellowLightWeak'),
		'YellowPaleWeak' : Color(1,1,0.8,'YellowPaleWeak'),
		'SpringYellowDark' : Color(0.4,0.6,0,'SpringYellowDark'),
		'SpringYellowMedium' : Color(0.6,0.8,0.2,'SpringYellowMedium'),
		'SpringYellowLight' : Color(0.8,1,0.4,'SpringYellowLight'),
		'SpringSpringYellow' : Color(0.6,1,0,'SpringSpringYellow'),
		'YellowSpringDark' : Color(0.6,0.8,0,'YellowSpringDark'),
		'YellowSpringLight' : Color(0.8,1,0.2,'YellowSpringLight'),
		'YellowYellowSpring' : Color(0.8,1,0,'YellowYellowSpring'),
		'SpringDarkHard' : Color(0.4,0.8,0,'SpringDarkHard'),
		'SpringLightHard' : Color(0.6,1,0.2,'SpringLightHard'),
		'SpringObscureDull' : Color(0.2,0.4,0,'SpringObscureDull'),
		'SpringDarkDull' : Color(0.4,0.6,0.2,'SpringDarkDull'),
		'SpringLightDull' : Color(0.6,0.8,0.4,'SpringLightDull'),
		'SpringPaleDull' : Color(0.8,1,0.6,'SpringPaleDull'),
		'SpringGreenDark' : Color(0.2,0.6,0,'SpringGreenDark'),
		'SpringGreenMedium' : Color(0.4,0.8,0.2,'SpringGreenMedium'),
		'SpringGreenLight' : Color(0.6,1,0.4,'SpringGreenLight'),
		'SpringSpringGreen' : Color(0.4,1,0,'SpringSpringGreen'),
		'GreenSpringDark' : Color(0.2,0.8,0,'GreenSpringDark'),
		'GreenSpringLight' : Color(0.4,1,0.2,'GreenSpringLight'),
		'GreenGreenSpring' : Color(0.2,1,0,'GreenGreenSpring'),
		'Green' : Color(0,1,0,'Green'),
		'GreenDarkHard' : Color(0,0.8,0,'GreenDarkHard'),
		'GreenLightHard' : Color(0.2,1,0.2,'GreenLightHard'),
		'GreenDarkFaded' : Color(0,0.6,0,'GreenDarkFaded'),
		'GreenMediumFaded' : Color(0.2,0.8,0.2,'GreenMediumFaded'),
		'GreenLightFaded' : Color(0.4,1,0.4,'GreenLightFaded'),
		'GreenObscureDull' : Color(0,0.4,0,'GreenObscureDull'),
		'GreenDarkDull' : Color(0.2,0.6,0.2,'GreenDarkDull'),
		'GreenLightDull' : Color(0.4,0.8,0.4,'GreenLightDull'),
		'GreenPaleDull' : Color(0.6,1,0.6,'GreenPaleDull'),
		'GreenObscureWeak' : Color(0,0.2,0,'GreenObscureWeak'),
		'GreenDarkWeak' : Color(0.2,0.4,0.2,'GreenDarkWeak'),
		'GreenMediumWeak' : Color(0.4,0.6,0.4,'GreenMediumWeak'),
		'GreenLightWeak' : Color(0.6,0.8,0.6,'GreenLightWeak'),
		'GreenPaleWeak' : Color(0.8,1,0.8,'GreenPaleWeak'),
		'TealGreenDark' : Color(0,0.6,0.2,'TealGreenDark'),
		'TealGreenMedium' : Color(0.2,0.8,0.4,'TealGreenMedium'),
		'TealGreenLight' : Color(0.4,1,0.6,'TealGreenLight'),
		'TealTealGreen' : Color(0,1,0.4,'TealTealGreen'),
		'GreenTealDark' : Color(0,0.8,0.2,'GreenTealDark'),
		'GreenTealLight' : Color(0.2,1,0.4,'GreenTealLight'),
		'GreenGreenTeal' : Color(0,1,0.2,'GreenGreenTeal'),
		'TealDarkHard' : Color(0,0.8,0.4,'TealDarkHard'),
		'TealLightHard' : Color(0.2,1,0.6,'TealLightHard'),
		'TealObscureDull' : Color(0,0.4,0.2,'TealObscureDull'),
		'TealDarkDull' : Color(0.2,0.6,0.4,'TealDarkDull'),
		'TealLightDull' : Color(0.4,0.8,0.6,'TealLightDull'),
		'TealPaleDull' : Color(0.6,1,0.8,'TealPaleDull'),
		'TealCyanDark' : Color(0,0.6,0.4,'TealCyanDark'),
		'TealCyanMedium' : Color(0.2,0.8,0.6,'TealCyanMedium'),
		'TealCyanLight' : Color(0.4,1,0.8,'TealCyanLight'),
		'TealTealCyan' : Color(0,1,0.6,'TealTealCyan'),
		'CyanTealDark' : Color(0,0.8,0.6,'CyanTealDark'),
		'CyanTealLight' : Color(0.2,1,0.8,'CyanTealLight'),
		'CyanCyanTeal' : Color(0,1,0.8,'CyanCyanTeal'),
		'Cyan' : Color(0,1,1,'Cyan'),
		'CyanDarkHard' : Color(0,0.8,0.8,'CyanDarkHard'),
		'CyanLightHard' : Color(0.2,1,1,'CyanLightHard'),
		'CyanDarkFaded' : Color(0,0.6,0.6,'CyanDarkFaded'),
		'CyanMediumFaded' : Color(0.2,0.8,0.8,'CyanMediumFaded'),
		'CyanLightFaded' : Color(0.4,1,1,'CyanLightFaded'),
		'CyanObscureDull' : Color(0,0.4,0.4,'CyanObscureDull'),
		'CyanDarkDull' : Color(0.2,0.6,0.6,'CyanDarkDull'),
		'CyanLightDull' : Color(0.4,0.8,0.8,'CyanLightDull'),
		'CyanPaleDull' : Color(0.6,1,1,'CyanPaleDull'),
		'CyanObscureWeak' : Color(0,0.2,0.2,'CyanObscureWeak'),
		'CyanDarkWeak' : Color(0.2,0.4,0.4,'CyanDarkWeak'),
		'CyanMediumWeak' : Color(0.4,0.6,0.6,'CyanMediumWeak'),
		'CyanLightWeak' : Color(0.6,0.8,0.8,'CyanLightWeak'),
		'CyanPaleWeak' : Color(0.8,1,1,'CyanPaleWeak'),
		'AzureCyanDark' : Color(0,0.4,0.6,'AzureCyanDark'),
		'AzureCyanMedium' : Color(0.2,0.6,0.8,'AzureCyanMedium'),
		'AzureCyanLight' : Color(0.4,0.8,1,'AzureCyanLight'),
		'AzureAzureCyan' : Color(0,0.6,1,'AzureAzureCyan'),
		'CyanAzureDark' : Color(0,0.6,0.8,'CyanAzureDark'),
		'CyanAzureLight' : Color(0.2,0.8,1,'CyanAzureLight'),
		'CyanCyanAzure' : Color(0,0.8,1,'CyanCyanAzure'),
		'AzureDarkHard' : Color(0,0.4,0.8,'AzureDarkHard'),
		'AzureLightHard' : Color(0.2,0.6,1,'AzureLightHard'),
		'AzureObscureDull' : Color(0,0.2,0.4,'AzureObscureDull'),
		'AzureDarkDull' : Color(0.2,0.4,0.6,'AzureDarkDull'),
		'AzureLightDull' : Color(0.4,0.6,0.8,'AzureLightDull'),
		'AzurePaleDull' : Color(0.6,0.8,1,'AzurePaleDull'),
		'AzureBlueDark' : Color(0,0.2,0.6,'AzureBlueDark'),
		'AzureBlueMedium' : Color(0.2,0.4,0.8,'AzureBlueMedium'),
		'AzureBlueLight' : Color(0.4,0.6,1,'AzureBlueLight'),
		'AzureAzureBlue' : Color(0,0.4,1,'AzureAzureBlue'),
		'BlueAzureDark' : Color(0,0.2,0.8,'BlueAzureDark'),
		'BlueAzureLight' : Color(0.2,0.4,1,'BlueAzureLight'),
		'BlueBlueAzure' : Color(0,0.2,1,'BlueBlueAzure'),
		'Blue' : Color(0,0,1,'Blue'),
		'BlueDarkHard' : Color(0,0,0.8,'BlueDarkHard'),
		'BlueLightHard' : Color(0.2,0.2,1,'BlueLightHard'),
		'BlueDarkFaded' : Color(0,0,0.6,'BlueDarkFaded'),
		'BlueMediumFaded' : Color(0.2,0.2,0.8,'BlueMediumFaded'),
		'BlueLightFaded' : Color(0.4,0.4,1,'BlueLightFaded'),
		'BlueObscureDull' : Color(0,0,0.4,'BlueObscureDull'),
		'BlueDarkDull' : Color(0.2,0.2,0.6,'BlueDarkDull'),
		'BlueLightDull' : Color(0.4,0.4,0.8,'BlueLightDull'),
		'BluePaleDull' : Color(0.6,0.6,1,'BluePaleDull'),
		'BlueObscureWeak' : Color(0,0,0.2,'BlueObscureWeak'),
		'BlueDarkWeak' : Color(0.2,0.2,0.4,'BlueDarkWeak'),
		'BlueMediumWeak' : Color(0.4,0.4,0.6,'BlueMediumWeak'),
		'BlueLightWeak' : Color(0.6,0.6,0.8,'BlueLightWeak'),
		'BluePaleWeak' : Color(0.8,0.8,1,'BluePaleWeak'),
		'VioletBlueDark' : Color(0.2,0,0.6,'VioletBlueDark'),
		'VioletBlueMedium' : Color(0.4,0.2,0.8,'VioletBlueMedium'),
		'VioletBlueLight' : Color(0.6,0.4,1,'VioletBlueLight'),
		'VioletVioletBlue' : Color(0.4,0,1,'VioletVioletBlue'),
		'BlueVioletDark' : Color(0.2,0,0.8,'BlueVioletDark'),
		'BlueVioletLight' : Color(0.4,0.2,1,'BlueVioletLight'),
		'BlueBlueViolet' : Color(0.2,0,1,'BlueBlueViolet'),
		'VioletDarkHard' : Color(0.4,0,0.8,'VioletDarkHard'),
		'VioletLightHard' : Color(0.6,0.2,1,'VioletLightHard'),
		'VioletObscureDull' : Color(0.2,0,0.4,'VioletObscureDull'),
		'VioletDarkDull' : Color(0.4,0.2,0.6,'VioletDarkDull'),
		'VioletLightDull' : Color(0.6,0.4,0.8,'VioletLightDull'),
		'VioletPaleDull' : Color(0.8,0.6,1,'VioletPaleDull'),
		'VioletMagentaDark' : Color(0.4,0,0.6,'VioletMagentaDark'),
		'VioletMagentaMedium' : Color(0.6,0.2,0.8,'VioletMagentaMedium'),
		'VioletMagentaLight' : Color(0.8,0.4,1,'VioletMagentaLight'),
		'VioletVioletMagenta' : Color(0.6,0,1,'VioletVioletMagenta'),
		'MagentaVioletDark' : Color(0.6,0,0.8,'MagentaVioletDark'),
		'MagentaVioletLight' : Color(0.8,0.2,1,'MagentaVioletLight'),
		'MagentaMagentaViolet' : Color(0.8,0,1,'MagentaMagentaViolet'),
		'Magenta' : Color(1,0,1,'Magenta'),
		'MagentaDarkHard' : Color(0.8,0,0.8,'MagentaDarkHard'),
		'MagentaLightHard' : Color(1,0.2,1,'MagentaLightHard'),
		'MagentaDarkFaded' : Color(0.6,0,0.6,'MagentaDarkFaded'),
		'MagentaMediumFaded' : Color(0.8,0.2,0.8,'MagentaMediumFaded'),
		'MagentaLightFaded' : Color(1,0.4,1,'MagentaLightFaded'),
		'MagentaObscureDull' : Color(0.4,0,0.4,'MagentaObscureDull'),
		'MagentaDarkDull' : Color(0.6,0.2,0.6,'MagentaDarkDull'),
		'MagentaLightDull' : Color(0.8,0.4,0.8,'MagentaLightDull'),
		'MagentaPaleDull' : Color(1,0.6,1,'MagentaPaleDull'),
		'MagentaObscureWeak' : Color(0.2,0,0.2,'MagentaObscureWeak'),
		'MagentaDarkWeak' : Color(0.4,0.2,0.4,'MagentaDarkWeak'),
		'MagentaMediumWeak' : Color(0.6,0.4,0.6,'MagentaMediumWeak'),
		'MagentaLightWeak' : Color(0.8,0.6,0.8,'MagentaLightWeak'),
		'MagentaPaleWeak' : Color(1,0.8,1,'MagentaPaleWeak'),
		'PinkMagentaDark' : Color(0.6,0,0.4,'PinkMagentaDark'),
		'PinkMagentaMedium' : Color(0.8,0.2,0.6,'PinkMagentaMedium'),
		'PinkMagentaLight' : Color(1,0.4,0.8,'PinkMagentaLight'),
		'PinkPinkMagenta' : Color(1,0,0.6,'PinkPinkMagenta'),
		'MagentaPinkDark' : Color(0.8,0,0.6,'MagentaPinkDark'),
		'MagentaPinkLight' : Color(1,0.2,0.8,'MagentaPinkLight'),
		'MagentaMagentaPink' : Color(1,0,0.8,'MagentaMagentaPink'),
		'PinkDarkHard' : Color(0.8,0,0.4,'PinkDarkHard'),
		'PinkLightHard' : Color(1,0.2,0.6,'PinkLightHard'),
		'PinkObscureDull' : Color(0.4,0,0.2,'PinkObscureDull'),
		'PinkDarkDull' : Color(0.6,0.2,0.4,'PinkDarkDull'),
		'PinkLightDull' : Color(0.8,0.4,0.6,'PinkLightDull'),
		'PinkPaleDull' : Color(1,0.6,0.8,'PinkPaleDull'),
		'PinkRedDark' : Color(0.6,0,0.2,'PinkRedDark'),
		'PinkRedMedium' : Color(0.8,0.2,0.4,'PinkRedMedium'),
		'PinkRedLight' : Color(1,0.4,0.6,'PinkRedLight'),
		'PinkPinkRed' : Color(1,0,0.4,'PinkPinkRed'),
		'RedPinkDark' : Color(0.8,0,0.2,'RedPinkDark'),
		'RedPinkLight' : Color(1,0.2,0.4,'RedPinkLight'),
		'RedRedPink' : Color(1,0,0.2,'RedRedPink')
	}
	#
	#
	#
	@classmethod
	def color(self,name):
		"""
		Function that returns a color from his name
		Parameters:
		   name: name of the color
		"""
		try:
			color = self.colorsbyname[name]
		except:
			return self.colorsbyname["Black"]
		return color
	#
	#
	#
	@classmethod
	def colors(self,names):
		"""
		Return a list of colors fron their names
		Parameters:
		   names: list of names
		"""
		return [self.colorsbyname[x] for x in names]
#
#
#
class Rotation():
	"""
    Class used for work with rotations. The stored value in the class is a quaternion
	"""
	def __init__(self,angle=None,vector=None,axis=None,quaternion=None,radians=False):
		"""
		Initializes the value for a rotation
		Parameters:
		   angle: angle of rotation

		   vector: axis of rotation

		   quaternion: The quaternion itself

		   radians: must be True if the angle is entered in radians and False if the
		            is entered in degrees.
		"""
		if vector is not None and axis is not None:
			return
		if axis is not None:
			if axis in ('X','x'):
				vector = Vector([1,0,0])
			elif axis in ('Y','y'):
				vector = Vector([0,1,0])
			elif axis in ('Z','z'):
				vector = Vector([0,0,1])
			else:
				return

		if angle is not None:
			if not radians:
				angle = math.radians(angle)
			if not isinstance(vector,Vector):
				vector = Vector(vector)
			self.quaternion = Quaternion(vector,angle)
		elif quaternion is not None:
			self.quaternion = quaternion
		else:
			self.quaternion = (1,0,0,0)
	#
	#
	#
	@classmethod
	def from_euler_angles(self,psi,theta,phi,axis='ZXZ',radians=False):
		"""
		Initializes a rotation from its Euler angles in the order ZXZ
		Parameters:
		   phi, theta, psi: Euler angles

		   axis: it must be 'XYZ', 'XZY', 'YXZ', 'YZX', 'ZXY', 'ZYX', 'XYX', 'XZX', 'YXY', 'YZY', 'ZXZ' or 'ZYZ'

		   radians: if radians, psi, theta and must be in radians
		"""
		if not radians:
			phi = math.radians(phi)
			theta = math.radians(theta)
			psi = math.radians(psi)

		if axis is None:
			return None
		if not isinstance(axis,str):
			return None
		axis = axis.upper()
		if axis not in ('XYZ','XZY','YXZ','YZX','ZXY','ZYX','XYX','XZX','YXY','YZY','ZXZ','ZYZ'):
			return None

		r1 = Matrix.Rotation(psi,3,axis[0])
		r2 = Matrix.Rotation(theta,3,axis[1])
		r3 = Matrix.Rotation(phi,3,axis[2])
		m = r3 @ r2 @ r1
		q = m.to_quaternion()
		return self(quaternion=q)
	#
	#
	#
	def apply(self,v):
		"""
        Applies the rotation to an object v
		Parameters:
		   v: any object that can be transformed by a rotation
		"""
		return self.quaternion @ v
	#
	#
	#
	def to_axis_angle(self,radians=False):
		"""
		Returns the axis and angle of the rotation
		Parameters:
		   radians: if True, the angle returned is in radians, if not, is
		            returned in degrees
		"""
		v, alpha = self.quaternion.to_axis_angle()
		if radians:
			return v, alpha
		return v, 180*alpha/math.pi
	#
	#
	#
	def to_euler_angles(self,axis='ZXZ',randomize=False,radians=False):
		"""
		Returns the Euler angles according to axis 'axis'
		Parameters:
		   axis: it must be 'XYZ', 'XZY', 'YXZ', 'YZX', 'ZXY', 'ZYX', 'XYX', 'XZX', 'YXY', 'YZY', 'ZXZ' or 'ZYZ'

		   radians: if True, the angle returned is in radians, if not, is
		            returned in degrees
		"""
		def ACOS(x):
			if x > 1.0:
				x = 1.0
			if x < -1.0:
				x = -1.0
			return math.acos(x)

		def ASIN(x):
			if x > 1.0:
				x = 1.0
			if x < -1.0:
				x = -1.0
			return math.asin(x)

		axis = axis.upper()
		if axis not in ('XYZ','XZY','YXZ','YZX','ZXY','ZYX','XYX','XZX','YXY','YZY','ZXZ','ZYZ'):
			return None
		rndm = 0
		A = self.quaternion.to_matrix()
		if axis == 'ZXZ':
			theta = ACOS(A[2][2])
			if abs(A[2][2]) != 1:
				psi = math.atan2(A[2][0],A[2][1])
				phi = math.atan2(A[0][2],-A[1][2])
			else:
				rndm = A[2][2]
				phi = 0
				psi = math.atan2(A[1][0],A[0][0])
		if axis == 'XZX':
			theta = ACOS(A[0][0])
			if abs(A[0][0]) != 1:
				psi = math.atan2(A[0][2],-A[0][1])
				phi = math.atan2(A[2][0],A[1][0])
			else:
				rndm = A[0][0]
				phi = 0
				psi = math.atan2(-A[1][2],A[2][2])
		if axis == 'ZYZ':
			theta = ACOS(A[2][2])
			if abs(A[2][2]) != 1:
				psi = math.atan2(A[2][1],-A[2][0])
				phi = math.atan2(A[1][2],A[0][2])
			else:
				rndm = A[2][2]
				phi = 0
				psi = math.atan2(-A[0][1],A[1][1])
		if axis == 'YZY':
			theta = ACOS(A[1][1])
			if abs(A[1][1]) != 1:
				psi = math.atan2(A[1][2],A[1][0])
				phi = math.atan2(A[2][1],-A[0][1])
			else:
				rndm = A[1][1]
				phi = 0
				psi = math.atan2(A[0][2],A[2][2])
		if axis == 'XYX':
			theta = ACOS(A[0][0])
			if abs(A[0][0]) != 1:
				psi = math.atan2(A[0][1],A[0][2])
				phi = math.atan2(A[1][0],-A[2][0])
			else:
				rndm = A[0][0]
				phi = 0
				psi = math.atan2(A[2][1],A[1][1])
		if axis == 'YXY':
			theta = ACOS(A[1][1])
			if abs(A[1][1]) != 1:
				psi = math.atan2(A[1][0],-A[1][2])
				phi = math.atan2(A[0][1],A[2][1])
			else:
				rndm = A[1][1]
				phi = 0
				psi = math.atan2(-A[2][0],A[0][0])
		if axis == 'XYZ':
			theta = ASIN(-A[2][0])
			if abs(A[2][0]) != 1:
				psi = math.atan2(A[2][1],A[2][2])
				phi = math.atan2(A[1][0],A[0][0])
			else:
				rndm = A[2][0]
				phi = 0
				psi = math.atan2(-A[0][1],A[1][1])
		if axis == 'XZY':
			theta = ASIN(A[1][0])
			if abs(A[1][0]) != 1:
				psi = math.atan2(-A[1][2],A[1][1])
				phi = math.atan2(-A[2][0],A[0][0])
			else:
				rndm = A[1][0]
				phi = 0
				psi = math.atan2(A[0][2],A[2][2])
		if axis == 'YXZ':
			theta = ASIN(A[2][1])
			if abs(A[2][1]) != 1:
				psi = math.atan2(-A[2][0],A[2][2])
				phi = math.atan2(-A[0][1],A[1][1])
			else:
				rndm = A[2][1]
				phi = 0
				psi = math.atan2(A[1][0],A[0][0])
		if axis == 'YZX':
			theta = ASIN(-A[0][1])
			if abs(A[0][1]) != 1:
				psi = math.atan2(A[0][2],A[0][0])
				phi = math.atan2(A[2][1],A[1][1])
			else:
				rndm = A[0][1]
				phi = 0
				psi = math.atan2(-A[1][2],A[2][2])
		if axis == 'ZXY':
			theta = ASIN(-A[1][2])
			if abs(A[1][2]) != 1:
				psi = math.atan2(A[1][0],A[1][1])
				phi = math.atan2(A[0][2],A[2][2])
			else:
				rndm = A[1][2]
				phi = 0
				psi = math.atan2(-A[0][2],A[0][0])
		if axis == 'ZYX':
			theta = ASIN(A[0][2])
			if abs(A[0][2]) != 1:
				psi = math.atan2(-A[0][1],A[0][0])
				phi = math.atan2(-A[1][2],A[2][2])
			else:
				rndm = A[0][2]
				phi = 0
				psi = math.atan2(A[2][1],A[1][1])

		if psi < 0:
			psi += 2*math.pi
		if theta < 0:
			theta += 2*math.pi
		if phi < 0:
			phi += 2*math.pi

		if rndm != 0 and randomize:
			phi = random.uniform(0.0,psi)
			psi = rndm * (psi - phi)
			if psi < 0:
				psi += 2*math.pi

		if not radians:
			psi, theta, phi = 180.0/math.pi * psi, 180.0/math.pi * theta, 180.0/math.pi * phi
			T = 359.9
		else:
			T = 359.9 * math.pi / 180.0
		if psi > T:
			psi = 0.0
		if theta > T:
			theta = 0.0
		if phi > T:
			phi = 0.0
		return psi, theta, phi
#
#
#
class EuclideanReference():
	"""
	Class used to work with Eucliean References
	"""
	def __init__(self,o=Vector([0,0,0]),u1=Vector([1,0,0]),u2=Vector([0,1,0])):
		"""
		Initializes the elements of the reference from the origin and two independent vectors
		Parameters:
		   o: origin of 
		   u1, u2: vectors
		"""
		if isinstance(o,Vector):
			self.origin = o
		else:
			self.origin = Vector(o)
		if isinstance(u1,Vector):
			v1 = u1
		else:
			v1 = Vector(v1)
		if isinstance(u2,Vector):
			v2 = u2
		else:
			v2 = Vector(u2)
		v2 = v2 - v2.project(v1)
		v1.normalize()
		v2.normalize()
		v3 = v1.cross(v2)
		self.matrix = Matrix([v1,v2,v3]).transposed()
	#
	#
	#
	def coordinates(self,u=Vector([0,0,0])):
		"""
		Returns the coordinates of a point (expressed in the canonical reference) in the actual reference 
		Parameters:
		   u: coordinates of a point in the canonical reference 
		"""	
		if not isinstance(u,Vector):
			u = Vector(u)
		return self.matrix.transposed() @ (u - self.origin)
	#
	#
	#
	def base(self):
		"""
		Returns the columns of the matrix
		"""
		mat = self.matrix.transposed()
		return [mat.row[0],mat.row[1],mat.row[2]]
#
#
#
class LinearAlgebra():
	"""
	Class used to define all the functions in this module to work with graphics in Blender
	"""
	def __init__(self):
		"""
        Initializes the values for scene, objects, meshes, collection, etc.
		"""
		self.scene = bpy.context.scene
		self.objects = bpy.data.objects
		self.meshes = bpy.data.meshes
		self.collection = bpy.context.collection
		self.ops = bpy.ops
		self.colors= Colors.colors(["Red","GreenDarkHard","Blue"])
		self.rotation = None
		self.origin = [0,0,0]
		self.base = [[1,0,0],[0,1,0],[0,0,1]]
		self.defaultcolor = None
		self.frame = 0
	#
	#
	#
	def base_cilinder(self):
		"""
		Draws a base cilinder with radius 1 and depth 1
		"""
		bpy.ops.mesh.primitive_cylinder_add(radius=1,depth=1,enter_editmode=False,location=(0, 0, 0))
		bpy.ops.transform.translate(value=(0, 0, 0.5), orient_type='GLOBAL',orient_matrix_type='GLOBAL',
			constraint_axis=(False, False, True), mirror=True, use_proportional_edit=False,
			proportional_edit_falloff='SMOOTH',proportional_size=1, use_proportional_connected=False, use_proportional_projected=False)
		bpy.ops.object.origin_set(type='ORIGIN_CURSOR', center='MEDIAN')
		bpy.ops.object.shade_smooth()
		bpy.context.object.name = 'Arrow_stem'
	#
	#
	#
	def base_cone(self):
		"""
		Draws a base cone with radius1=1.5, radius2=0, depth=2
		"""
		bpy.ops.mesh.primitive_cone_add(radius1=1.5, radius2=0, depth=2, enter_editmode=False, location=(0, 0, 0))
		bpy.ops.transform.translate(value=(0, 0, 1), orient_type='GLOBAL',orient_matrix_type='GLOBAL',
			constraint_axis=(False, False, True), mirror=True, use_proportional_edit=False,
			proportional_edit_falloff='SMOOTH', proportional_size=1, use_proportional_connected=False, use_proportional_projected=False)
		bpy.ops.object.origin_set(type='ORIGIN_CURSOR', center='MEDIAN')
		bpy.ops.object.shade_smooth()
		bpy.context.object.name = 'Arrow_cone'
	#
	#
	#
	def base_disk(self):
		"""
		Draws a base cone with radius1=1.5, radius2=0, depth=2
		"""
		bpy.ops.mesh.primitive_circle_add(vertices=32,fill_type='NGON',enter_editmode=False,align='WORLD',location=(0.0, 0.0, 0.0))
		bpy.ops.object.origin_set(type='ORIGIN_CURSOR', center='MEDIAN')
		bpy.ops.object.shade_smooth()
		bpy.context.object.name = 'Base_disk'
	#
	#
	#
	def delete_base_cilinder(self):
		"""
		Removes the base cilinder
		"""
		bpy.ops.object.select_all(action='DESELECT')
		bpy.data.objects['Arrow_stem'].select_set(True)
		bpy.ops.object.delete()
	#
	#
	#
	def delete_base_cone(self):
		"""
		Removes the base cone
		"""
		bpy.ops.object.select_all(action='DESELECT')
		bpy.data.objects['Arrow_cone'].select_set(True)
		bpy.ops.object.delete()
	#
	#
	#
	def delete_base_disk(self):
		"""
		Removes the base disk
		"""
		bpy.ops.object.select_all(action='DESELECT')
		bpy.data.objects['Base_disk'].select_set(True)
		bpy.ops.object.delete()
	#
	#
	#
	def set_colors(self,names=None):
		"""
		Set self.colors to the list of colors with names 'names'
		Parameters:
		   names: list of name colors
		"""
		if names is None:
			self.colors = Colors.colors(["Red","GreenDarkHard","Blue"])
		else:
			self.colors = Colors.colors(names)
	#
	#
	#
	def reset_colors(self):
		"""
		Set self.colors to default colors
		"""
		self.colors = Colors.colors(["Red","GreenDarkHard","Blue"])
	#
	#
	#
	def set_default_color(self,name):
		"""
		Set self.defaultcolor to the color with name 'name'
		Parameters:
		   name: name of a color
		"""
		self.defaultcolor = name
	#
	#
	#
	def reset_frames(self):
		"""
		Set self.frame to 0
		Parameters:
		   name: name of a color
		"""
		self.frame = 0
	#
	#
	#
	def reset(self):
		"""
		Resets origin, base, rotation, frames and colors
		"""
		self.reset_origin()
		self.reset_base()
		self.reset_rotation()
		self.reset_frames()
		self.reset_colors()
	#
	#
	#
	def set_rotation(self,angle=None,vector=None,quaternion=None):
		"""
		Sets self.rotation to the rotation defined by an angle and an axis or
		by a quaternion.
		Parameters:
		   angle: angle of rotation in degrees

		   vector: axis of rotation

		   quaternion: quaternion that defines a rotation

		The angle and vector takes precedence over the quaternion
		"""
		if angle is not None:
			self.rotation = Rotation(angle,vector)
		elif quaternion is not None:
			self.rotation = Rotation(quaternion=quaternion)
		else:
			self.rotation = Rotation(0,[1,0,0])
	#
	#
	#
	def reset_rotation(self):
		"""
		Sets the rotation to identity, i.e., rotation of 0 degrees around the
		vector (1,0,0)
		"""
		self.set_rotation()
	#
	#
	#
	def set_origin(self,vector=[0,0,0]):
		"""
		Sets the origin of the reference coordinates used to display objects.
		Parameters:
		   vector: origin's position
		"""
		if isinstance(vector,Vector):
			v1 = vector.copy()
		else:
			v1 = Vector(vector)
		self.origin = v1
	#
	#
	#
	def reset_origin(self):
		"""
		Sets the origin to the point (0,0,0)
		"""
		self.origin = Vector([0,0,0])
	#
	#
	#
	def reset_base(self):
		"""
		Sets self.base to the canonical basis
		"""
		self.base = [[1,0,0],[0,1,0],[0,0,1]]
	#
	#
	#
	def set_base(self,base=[[1,0,0],[0,1,0],[0,0,1]],orthonormal=False):
		"""
		Sets the self.base, i.e., the basis of the reference coordinates used to display
		objects
		Parameters:
		   base: list of three vectors

		   orthonormal: if True, the Gram-Schmidt method is applied and the vectors
		   are normalized.
		"""
		if orthonormal:
			u1 = base[0]
			u2 = base[1]
			if isinstance(u1,Vector):
				v1 = u1
			else:
				v1 = Vector(u1)
			if isinstance(u2,Vector):
				v2 = u2
			else:
				v2 = Vector(u2)
			v2 = v2 - v2.project(v1)
			v1.normalize()
			v2.normalize()
			v3 = v1.cross(v2)
			self.base=[v1,v2,v3]
		else:
			self.base = base
	#
	#
	#
	def base_is_canonica(self):
		"""
		Returns True if self.base is the canonical basis
		"""
		return Matrix(self.base).is_identity
	#
	#
	#
	def add_material(self,obj,material_name,r,g,b,opacity=1.0):
		"""
		Adds a material and color to an object
		Parameters:
		   obj: object

		   material_name: material's name

		   r, g, b: RGB color values

		   opacity: the opacity
		"""
		material = bpy.data.materials.get(material_name)
		if material is None:
			material = bpy.data.materials.new(material_name)
		material.use_nodes = True
		principled_bsdf = material.node_tree.nodes['Principled BSDF']
		if principled_bsdf is not None:
			principled_bsdf.inputs['Base Color'].default_value = (r, g, b, opacity)
			principled_bsdf.inputs['IOR'].default_value = 0.0
			principled_bsdf.inputs['Metallic'].default_value = 1.0
			principled_bsdf.inputs['Roughness'].default_value = 0.55
			if bpy.app.version[0] < 4:
				principled_bsdf.inputs['Specular'].default_value = 1.0
			else:
				principled_bsdf.inputs['Specular IOR Level'].default_value = 1.0
			if bpy.app.version[0] < 4:
				principled_bsdf.inputs['Emission'].default_value = (r, g, b, opacity)
			else:
				principled_bsdf.inputs['Emission Color'].default_value = (r, g, b, opacity)
			principled_bsdf.inputs['Emission Strength'].default_value = 0.0
			if opacity < 1.0:
				material.blend_method = 'BLEND'
				principled_bsdf.inputs['Alpha'].default_value = opacity
			else:
				material.blend_method = 'OPAQUE'
				principled_bsdf.inputs['Alpha'].default_value = 1.0
		obj.active_material = material
	#
	#
	#
	def add_ligth(self,location=[0,0,100],energy=3,direction=[0,0,-1]):
		"""
		Adds a ligth to the scene
		Parameters:
		   location: location point of the light

		   energy: energy of the ligth

		   direction: direction of the light
		"""
		l = bpy.data.lights.new(name="Light", type='SUN')
		l.energy = energy
		l.specular_factor = 4
		obj = self.objects.new(name="Light", object_data=l)
		obj.rotation_mode = 'QUATERNION'
		obj.location = location
		n = Vector(direction)
		mat = Matrix(self.base)
		mat.transpose()
		n = mat @ n
		z = Vector([0,0,-1])
		quaternion = z.rotation_difference(n)
		obj.rotation_quaternion.rotate(quaternion)
		self.collection.objects.link(obj)
	#
	#
	#
	def add_ligths(self,energy=1):
		"""
		Adds diferent lights to the scene
		Parameters:
		   energy: energy of the lights
		"""
		self.add_ligth()
		self.add_ligth(location=[100,0,0],direction=[-1,0,0],energy=energy)
		self.add_ligth(location=[0,100,0],direction=[0,-1,0],energy=energy)
		self.add_ligth(location=[-100,0,0],direction=[1,0,0],energy=energy)
		self.add_ligth(location=[0,-100,0],direction=[0,1,0],energy=energy)
	#
	#
	#
	def components_in_base(self,vector=None,base=None):
		"""
		Returns the components of the vector 'vector' in the basis determined by
		self.rotation and the basis self.base
		Parameters:
		   vector: components of the vector in the canonical basis

		   base: A base of V3. If None, we use self.base
		"""
		if vector is None:
			return Vector([0,0,0])
		if isinstance(vector,Vector):
			u = vector
		else:
			u = Vector(vector)
		if self.rotation is not None:
			mat = self.rotation.quaternion.to_matrix()
			mat.invert()
			u = mat @ u
		mat = Matrix(self.base)
		if base is not None:
			mat = Matrix(base)
		mat.transpose()
		mat.invert()
		u = mat @ u
		return u
	#
	#
	#
	def coordinates_en_referencia(self,point=None):
		"""
		Returns the coordinates of the point 'point' in the reference determined by
		self.origin, self.rotation and the basis self.base
		Parameters:
		   point: coordinates of the point in the canonical reference
		"""
		if point is None:
			return Vector([0,0,0])
		if isinstance(point,Vector):
			u = point
		else:
			u = Vector(point)
		if self.rotation is not None:
			mat = self.rotation.quaternion.to_matrix()
			mat.invert()
			u = mat @ u
		mat = Matrix(self.base)
		mat.transpose()
		mat.invert()
		u = mat @ (u - Vector(self.origin))
		return u
	#
	#
	#
	def coordinates_en_canonica(self,point=None):
		"""
		Returns the coordinates of the point 'point' in the reference determined by
		self.origin, self.rotation and the basis self.base
		Parameters:
		   point: coordinates of the point in the reference {self.origin;self.base}
		"""
		if point is None:
			return Vector([0,0,0])
		if isinstance(point,Vector):
			u = point
		else:
			u = Vector(point)
		if self.rotation is not None:
			mat = self.rotation.quaternion.to_matrix()
			u = mat @ u
		mat = Matrix(self.base)
		mat.transpose()
		u = Vector(self.origin) + mat @ u
		return u
	#
	#
	#
	def set_cursor(self,origin=[0,0,0],direction=[1,0,0],axis='x'):
		"""
		Sets the cursor position and direction
		Parameters:
		  origin: position of the cursor

		  direction: vector that indicates the direction of the axis 'axis'

		  axis: 'x', 'y' or 'z'
		"""
		axis = axis.lower()
		if axis not in ['x','y','z']:
			return
		eixos = {'x' : Vector([1,0,0]),
				 'y' : Vector([0,1,0]),
				 'z' : Vector([0,0,1])
		}
		if isinstance(direction,Vector):
			d = direction
		else:
			d = Vector(direction)
		x = eixos[axis]
		quaternion = x.rotation_difference(d)
		self.scene.cursor.location = origin
		self.scene.cursor.rotation_mode = 'QUATERNION'
		self.scene.cursor.rotation_quaternion = quaternion
	#
	#
	#
	def set_cursor_rotation(self,origin=[0,0,0],rotation=Matrix.Identity(3)):
		"""
		Sets the rotation of the cursor
		Parameters:
		   origin: position of the cursor

		   rotation: matrix of a rotation
		"""
		m = rotation.copy()
		det = m.determinant()
		if abs(- det - 1.0) < 0.1:
			m[2] = - m[2]
		quaternion = m.to_quaternion()
		self.scene.cursor.location = origin
		self.scene.cursor.rotation_mode = 'QUATERNION'
		self.scene.cursor.rotation_quaternion = quaternion.conjugated()
	#
	#
	#
	def draw_base_axis(self,scale=0.05,head_height=0.15,axis=0,name="Axis",positive=True,zaxis=True):
		"""
		Draws a reference axis given by self.origin, self.rotation and the basis self.base
		Parameters:
		   scale: scale of the cylinder

		   head_height: height of the head of the vector from self.base

		   axis: length of the coordinate axis. If the length is 0, only the basis vectors are drawn

		   name: name of the result object

		   positive: if True, draw the positive part of the axis

		   zaxis: if True, draw the z axis
		"""
		self.base_cilinder()
		self.base_cone()
		o = Vector([0,0,0])
		op = Vector(self.origin)
		color = 0

		if axis != 0 and axis < 8:
			scale /= 3

		base = self.base
		if not zaxis:
			base = self.base[0:2]
		
		for vec in base:
			#
			# Draw the stem
			#
			v = Vector(vec)
			t = bpy.data.objects.get("Arrow_stem")
			obj = t.copy()
			obj.name = "Axis%d" % (color + 1)
			obj.data = obj.data.copy()
			obj.location = o
			obj.scale = (scale,scale,(v - o).length - 2 * head_height)
			obj.rotation_mode = 'QUATERNION'
			obj.rotation_quaternion = (v - o).to_track_quat('Z','Y')
			if self.colors is not None and len(self.colors) > color:
				c = self.colors[color]
				self.add_material(obj,c.name,c.r,c.g,c.b)
			if self.rotation is not None:
				obj.rotation_quaternion.rotate(self.rotation.quaternion)
			obj.location = op
			self.scene.collection.objects.link(obj)
			#
			# Draw the arrow
			#
			t = bpy.data.objects.get("Arrow_cone")
			obj2 = t.copy()
			obj2.name = "Arrow"
			obj2.data = obj2.data.copy()
			obj2.location =  v - 2 * head_height * v / v.length
			obj2.scale = (scale + 0.05,scale + 0.05,head_height)
			obj2.rotation_mode = 'QUATERNION'
			obj2.rotation_quaternion = (v - o).to_track_quat('Z','Y')
			if self.colors is not None and len(self.colors) > color:
				c = self.colors[color]
				self.add_material(obj2,c.name,c.r,c.g,c.b)
			if self.rotation is not None:
				obj2.rotation_quaternion.rotate(self.rotation.quaternion)
				obj2.location.rotate(self.rotation.quaternion)
			obj2.location = op + obj2.location
			self.scene.collection.objects.link(obj2)
			#
			# Draw the line
			#
			obj3 = None
			if axis != 0:
				v = axis * Vector(vec)
				t = bpy.data.objects.get("Arrow_stem")
				obj3 = t.copy()
				obj3.name = "Line"
				obj3.data = obj3.data.copy()
				obj3.location = op - v
				obj3.scale = (scale / 2,scale / 2,(2 * v).length)
				obj3.rotation_mode = 'QUATERNION'
				obj3.rotation_quaternion = v.to_track_quat('Z','Y')
				if self.colors is not None and len(self.colors) > color:
					c = self.colors[color]
					self.add_material(obj3,c.name,c.r,c.g,c.b)
				if self.rotation is not None:
					obj3.rotation_quaternion.rotate(self.rotation.quaternion)
				if positive:
					obj3.location = op
				else:
					if self.rotation is not None:
						v.rotate(self.rotation.quaternion)
					obj3.location = op - v
				self.scene.collection.objects.link(obj3)
			#
			# Joint the three objects
			#
			bpy.ops.object.select_all(action='DESELECT')
			bpy.context.view_layer.objects.active = obj
			obj.select_set(True)
			obj2.select_set(True)
			if obj3 is not None:
				obj3.select_set(True)
			bpy.ops.object.join()
			color += 1
		#
		# Join all the axis
		#
		t1 = bpy.data.objects.get("Axis1")
		t1.name = name
		bpy.ops.object.select_all(action='DESELECT')
		bpy.context.view_layer.objects.active = t1
		t1.select_set(True)
		t2 = bpy.data.objects.get("Axis2")
		t2.select_set(True)
		if zaxis:
			t3 = bpy.data.objects.get("Axis3")
			t3.select_set(True)
		bpy.ops.object.join()
		self.delete_base_cilinder()
		self.delete_base_cone()
		bpy.ops.object.shade_smooth()
		bpy.context.view_layer.objects.active = None
		return t1
	#
	#
	#
	def draw_vector(self,origin=Vector([0,0,0]),vector=None,canonica=False,color="Black",scale=0.05,arrow=True,head_height=None,axis=0,name="Vector",positive=True):
		"""
		Draw the vector with components 'vector' trough 'origin'
		Parameters:

		   origin: point of the line
		
		   vector: components of the vector

		   canonica: if True, the components are in the canonical basis, else they are in the basis self.base. Finally,
		      self.rotation is applied

		   color: color of the vector

		   scale: scale of the cylinder

		   arrow: if True draws the vector itself

		   head_height: height of the head of the vector

		   head_scale: scale of the head of the vector

		   axis: if not zero, draw also the line generated by the vector

		   positive: if axis is not zero and positive is True, draw only the positive part of the line
		      generated by the vector
		"""
		if vector is None:
			return None
		if isinstance(vector,Vector):
			vec = vector
		else:
			vec = Vector(vector)
		if isinstance(origin,Vector):
			orig = origin
		else:
			orig = Vector(origin)
		if vec.length == 0:
			return None
		self.base_cilinder()
		self.base_cone()
		o = Vector([0,0,0])
		op = Vector(self.origin + orig)
		if color is not None:
			color = Colors.color(color)
		v = vec
		if not canonica:
			mat = Matrix(self.base)
			mat.transpose()
			v = mat @ vec

		if head_height is None:
			head_height = 0.15*(v - o).length
		if head_height > 0.15:
			head_height = 0.15

		if arrow:
			t = bpy.data.objects.get("Arrow_stem")
			obj = t.copy()
			obj.name = name
			obj.data = obj.data.copy()
			obj.location = o
			obj.scale = (scale,scale,(v - o).length - 2 * head_height)
			obj.rotation_mode = 'QUATERNION'
			obj.rotation_quaternion = (v - o).to_track_quat('Z','Y')
			if color is not None:
				self.add_material(obj,color.name,color.r,color.g,color.b)
			if self.rotation is not None:
				obj.rotation_quaternion.rotate(self.rotation.quaternion)
			obj.location = op
			self.scene.collection.objects.link(obj)

			t = bpy.data.objects.get("Arrow_cone")
			obj2 = t.copy()
			obj2.data = obj2.data.copy()
			obj2.name = "Arrow"
			obj2.location =  v - 2 * head_height * v / v.length
			obj2.scale = (2*scale,2*scale,head_height)
			obj2.rotation_mode = 'QUATERNION'
			obj2.rotation_quaternion = (v - o).to_track_quat('Z','Y')
			if color is not None:
				self.add_material(obj2,color.name,color.r,color.g,color.b)
			if self.rotation is not None:
				obj2.rotation_quaternion.rotate(self.rotation.quaternion)
				obj2.location.rotate(self.rotation.quaternion)
			obj2.location = op + obj2.location
			self.scene.collection.objects.link(obj2)

		obj3 = None
		if axis != 0:
			v = axis * v / v.length
			t = bpy.data.objects.get("Arrow_stem")
			obj3 = t.copy()
			if not arrow:
				obj3.name = "Line"
			else:
				obj3.name = "Generated"
			obj3.data = obj3.data.copy()
			obj3.scale = (scale / 2,scale / 2,(2 * v).length)
			obj3.rotation_mode = 'QUATERNION'
			obj3.rotation_quaternion = v.to_track_quat('Z','Y')
			if color is not None:
				self.add_material(obj3,color.name,color.r,color.g,color.b)
			if self.rotation is not None:
				obj3.rotation_quaternion.rotate(self.rotation.quaternion)
			if positive:
				obj3.location = op
			else:
				obj3.location = op - v
			self.scene.collection.objects.link(obj3)

		bpy.ops.object.select_all(action='DESELECT')
		if arrow:
			bpy.context.view_layer.objects.active = obj
		elif axis != 0:
			bpy.context.view_layer.objects.active = obj3
		if arrow:
			obj.select_set(True)
			obj2.select_set(True)
		if obj3 is not None:
			obj3.select_set(True)
		if arrow:
			bpy.ops.object.join()
		bpy.ops.object.shade_smooth()
		bpy.ops.object.select_all(action='DESELECT')
		self.delete_base_cilinder()
		self.delete_base_cone()
		bpy.context.view_layer.objects.active = None
		if arrow:
			return obj
		if axis != 0:
			return obj3
		self.set_origin()
		return None
	#
	#
	#
	def product_components(self,u,v):
		"""
		Computes the vectorial product u x v
		Parameters:
		   u, v: two Vectors
		"""
		if not isinstance(u,Vector):
			u = Vector(u)
		if not isinstance(v,Vector):
			v = Vector(v)
		return Vector([u.x * v.x,u.y * v.y,u.z * v.z])
	#
	#
	#
	def draw_line(self,start=[1,1,1],end=[10,10,10],scale=0.05,name="Line",color="Black",segment=False):
		"""
		Draws a line from the point start to the point end. The reference given by self.origin,
		self.rotation and the basis self.base is used
		Parameters:
		   start: starting point of the line

		   end: ending point of the line

		   scale: scale of the cylinder

		   name: name of the object

		   color: color of the vector

		   segment: if True, draw points start and end
		"""
		if start is None or end is None:
			return
		self.base_cilinder()
		o = Vector([0,0,0])
		op = Vector(self.origin)
		if isinstance(start,Vector):
			u = start
		else:
			u = Vector(start)
		if isinstance(end,Vector):
			v = end
		else:
			v = Vector(end)
		mat = Matrix(self.base)
		mat.transpose()
		u = mat @ u
		v = mat @ v
		l = (v - u).length
		t = bpy.data.objects.get("Arrow_stem")
		obj = t.copy()
		obj.name = name
		obj.location = u
		obj.scale = (scale / 2,scale / 2,l)
		obj.rotation_mode = 'QUATERNION'
		obj.rotation_quaternion = (v - u).to_track_quat('Z','Y')
		if color is not None:
			c = Colors.color(color)
			self.add_material(obj,c.name,c.r,c.g,c.b)
		if self.rotation is not None:
			obj.rotation_quaternion.rotate(self.rotation.quaternion)
			obj.location.rotate(self.rotation.quaternion)
		obj.location = obj.location + op
		self.scene.collection.objects.link(obj)
		bpy.ops.object.shade_flat()
		self.delete_base_cilinder()
		bpy.ops.object.select_all(action='DESELECT')
		bpy.context.view_layer.objects.active = None
		if segment:
			s1 = self.draw_point(radius=2*scale,location=end,name="End point",color=color,opacity=1.0)
			s2 = self.draw_point(radius=2*scale,location=start,name="Start point",color=color,opacity=1.0)
			self.join([obj,s1,s2])
		return obj
	#
	#
	#
	def draw_components(self,vector=None,color="Cyan",name="Components",scale=0.0075):
		"""
		Draws the components of the the vector 'vector' in the reference given by self.origin,
		self.rotation and the basis self.base
		Parameters:
		   vector: the vector

		   color: color of the lines of components

		   name: name of the object

		   scale: scale of the lines
		"""
		if vector is None:
			return
		if isinstance(vector,Vector):
			v = vector
		else:
			v = Vector(vector)
		mat = Matrix(self.base)
		mat.transpose()
		list = [[0,0,0],[1,0,0],[1,1,0],[0,1,0],[0,0,1],[1,0,1],[1,1,1],[0,1,1]]
		lines = [[0,1],[1,2],[2,3],[0,3],[0,4],[1,5],[2,6],[3,7],[4,5],[5,6],[6,7],[4,7]]
		vecs = [self.product_components(v,Vector(x)) for x in list]
		count = 0
		for first, last in lines:
			if count == 0:
				this = name
			else:
				this = f"Line{count}"
			count += 1
			self.draw_line(start=vecs[first],end=vecs[last],scale=scale,name=this,color=color)
		t = bpy.data.objects.get(name)
		list = [t]
		for count in range(1,12):
			obj = bpy.data.objects.get(f"Line{count}")
			if obj is not None:
				list.append(obj)
		t = self.join(list)
		bpy.context.view_layer.objects.active = None
		return t
	#
	#
	#
	def draw_vectors(self,vectors=[],canonica=False,color="Black",scale=0.05,head_height=0.2,name="Vectors",axis=0):
		"""
		Draws a list of vectors.
		Parameters:
		   vectors: list of vectors

		   canonica: if True, the the vectors are expressed in the canonical basis.

		   color: color of the vectors

		   scale: scale of the cylinder

		   head_height: height of the head of the vector

		   axis: if not zero, draw also the line generated by every vector
		"""
		if len(vectors) == 0:
			return
		count = 0
		for v in vectors:
			if count == 0:
				this = name
			else:
				this = f"Vector{count}"
			count += 1
			t = self.draw_vector(vector=v,canonica=canonica,color=color,scale=scale,head_height=head_height,axis=axis,name=this)
		t = bpy.data.objects.get(name)
		list = [t]
		for count in range(1,len(vectors)+1):
			obj = bpy.data.objects.get(f"Vector{count}")
			if obj is not None:
				list.append(obj)
		t = self.join(list)
		return t
	#
	#
	#
	def draw_plane(self,normal=None,base=None,sizex=10,sizey=10,color="AzureBlueDark",name='Plane',opacity=1.0,thickness=0.01):
		"""
		Draws a plane with normal vector or base vectors. It passes through the point self.origin.
		Only normal or base can be not None
		Parameters:
		   normal: normal vector to the plane

		   base: list of two independent vectors

		   sizex: x-size of the plane

		   sizey: y-size of the plane

		   color: color of the plane

		   name: name of the plane

		   opacity: opacity of the plane

		   thickness: thickness of the plane
		"""
		if sizex == 0.0:
			return
		bpy.ops.mesh.primitive_plane_add(size=sizex,enter_editmode=True,location=(0, 0, 0))
		bpy.context.object.name = name
		bpy.ops.object.mode_set(mode='OBJECT')
		obj = bpy.data.objects.get(name)
		if sizey is not None and sizey != 0.0:
			t = sizey / sizex
			obj.scale = [1,t,1]
		o = Vector([0,0,0])
		op = Vector(self.origin)
		obj.location = o
		modifier = obj.modifiers.new(name="SubSurf", type='SUBSURF')
		modifier.levels = 4
		modifier.subdivision_type = 'SIMPLE'
		if thickness > 0.0:
			modifier = obj.modifiers.new(name="Solidify", type='SOLIDIFY')
			modifier.thickness = thickness
			modifier.offset = 1.0
		c = Colors.color(color)
		obj.rotation_mode = 'QUATERNION'
		if self.rotation is not None:
			obj.rotation_quaternion.rotate(self.rotation.quaternion)
			obj.location.rotate(self.rotation.quaternion)
		self.add_material(obj,c.name,c.r,c.g,c.b,opacity)
		if normal is not None and base is not None:
			return
		if base is not None:
			if len(base) != 2:
				return
			if isinstance(base[0],Vector):
			 	v1 = base[0]
			else:
				v1 = Vector(base[0])
			if isinstance(base[1],Vector):
			 	v2 = base[1]
			else:
				v2 = Vector(base[1])

			if self.base is None:
				normal = v1.cross(v2)
			else:
				u1 = v1[0]*self.base[0] + v1[1]*self.base[1] + v1[2]*self.base[2]
				u2 = v2[0]*self.base[0] + v2[1]*self.base[1] + v2[2]*self.base[2]
				normal = u1.cross(u2)
		if normal is not None and normal != Vector([0,0,0]):
			z = Vector([0,0,1])
			quaternion = z.rotation_difference(normal)
			obj.rotation_quaternion.rotate(quaternion)
			bpy.ops.object.select_all(action='DESELECT')
		obj.location = op
		bpy.ops.object.shade_smooth()
		bpy.context.view_layer.objects.active = None
		return obj
	#
	#
	#
	def simple_curve(self,f=None,tmin=0.0,tmax=1.0,steps=25,name="Simple curve",symmetry=None,draw=False):
		"""
		Return a curve defined by the parametrization f
		Parameters:
		   f: Parametrization of the curve

		   tmin: minimum value of the parameter

		   tmax: maximum value of the parameter

		   steps: number of steps

		   name: name of the curve

		   symmetry: None or a value in the list ('XY','XZ','YZ','X','Y','Z','O'). Symmetry of the curve

		   draw: if True, the curve is drawn
		"""
		if f is None:
			return None

		delta = (tmax - tmin)/steps
		t = tmin
		bm = bmesh.new()
		verts = []
		verts2 = []

		for k in range(steps + 1):
			p = f(t)
			q = None
			verts.append(bm.verts.new(p))
			if symmetry == 'XY':
				q = (p[0],p[1],-p[2])
			elif symmetry == 'XZ':
				q = (p[0],-p[1],p[2])
			elif symmetry == 'YZ':
				q = (-p[0],p[1],p[2])
			elif symmetry == 'X':
				q = (p[0],-p[1],-p[2])
			elif symmetry == 'Y':
				q = (-p[0],p[1],-p[2])
			elif symmetry == 'Z':
				q = (-p[0],-p[1],p[2])
			elif symmetry == 'O':
				q = (-p[0],-p[1],-p[2])

			if q is not None:
				verts2.append(bm.verts.new(q))
			t += delta
			if t > tmax:
				t = tmax

		for i in range(len(verts) - 1):
			bm.edges.new([verts[i], verts[i+1]])
			if len(verts2) > 0:
				bm.edges.new([verts2[i], verts2[i+1]])

		me = bpy.data.meshes.new('placeholder_mesh')
		obj = bpy.data.objects.new(name,me)
		bm.to_mesh(me)
		bm.free()

		if draw:
			self.scene.collection.objects.link(obj)
		bpy.context.view_layer.objects.active = None
		return obj
	#
	#
	#
	def draw_elliptic_paraboloid(self,a=0.5,xmin=0.0,xmax=3.0,steps=50,scale=[1,1,1],color="AzureBlueDark",name="EllipticParaboloid",opacity=1.0,thickness=0.05):
		"""
		Draws an elliptic paraboloid from the parabola z=a*t^2
		Parameters:
		   a: coefficient of the parabola

		   xmin: minimum value of x

		   xmax: maximum value of x

		   steps: numbers of steps to draw the parabola

		   scale: scaling factors in the X, Y and Z directions

		   color: color of the surface

		   name: name of the surface

		   opacity: opacity of the surface

		   thickness: thickness of the surface
		"""
		obj = self.simple_curve(f=lambda t:(t,0,a*t**2),tmin=xmin,tmax=xmax,steps=steps,name=name)
		modifier = obj.modifiers.new(name="Screw", type='SCREW')
		modifier.angle = 2 * math.pi
		modifier.steps = 128
		modifier = obj.modifiers.new(name="SubSurf", type='SUBSURF')
		modifier.levels = 4
		modifier.subdivision_type = 'SIMPLE'
		if thickness > 0.0:
			modifier = obj.modifiers.new(name="Solidify", type='SOLIDIFY')
			modifier.thickness = thickness
			modifier.offset = 1.0
		c = Colors.color(color)
		if self.defaultcolor is not None:
			c = Colors.color(self.defaultcolor)
		o = Vector([0,0,0])
		op = Vector(self.origin)
		obj.location = o
		obj.scale = scale
		obj.rotation_mode = 'QUATERNION'
		if self.rotation is not None:
			obj.rotation_quaternion.rotate(self.rotation.quaternion)
			obj.location.rotate(self.rotation.quaternion)
		self.add_material(obj,c.name,c.r,c.g,c.b,opacity)
		obj.location = op
		bpy.ops.object.shade_smooth()
		self.scene.collection.objects.link(obj)
		bpy.ops.object.shade_smooth()
		bpy.context.view_layer.objects.active = None
		return obj
	#
	#
	#
	def draw_one_sheet_hyperboloid(self,a=2.0,b=2.0,xmin=math.sqrt(2),xmax=5.0,steps=256,scale=[1,1,1],color="AzureBlueDark",name="HyperboloidOneSheet",opacity=1.0,thickness=0.05):
		r"""
		Draws a one sheet hyperboloid from the hyperbole z = \pm a*sqrt(x^2-b) in the XZ plane
		Parameters:
		   a, b: coefficients of the hyperbole

		   xmin: minimum value of x

		   xmax: maximum value of x

		   steps: numbers of steps to draw the parabola

		   scale: scaling factors in the X, Y and Z directions

		   color: color of the surface

		   name: name of the surface

		   opacity: opacity of the surface

		   thickness: thickness of the surface
		"""
		if xmin < math.sqrt(b):
			xmin = math.sqrt(b)
		delta = (xmax - xmin) / steps
		x = xmax
		bm = bmesh.new()
		verts = []

		for k in range(steps + 1):
			if x < math.sqrt(b):
				z = 0.0
			else:
				z = - a * math.sqrt(x**2 - b)
			verts.append(bm.verts.new((x,0,z)))
			x -= delta
		x = math.sqrt(b)
		for k in range(steps):
			x += delta
			if x**2 < b:
				z = 0.0
			else:
				z = a * math.sqrt(x**2 - b)
			verts.append(bm.verts.new((x,0,z)))

		for i in range(len(verts) - 1):
			bm.edges.new([verts[i], verts[i+1]])

		me = self.meshes.new('placeholder_mesh')
		obj = self.objects.new(name,me)
		bm.to_mesh(me)
		bm.free()
		modifier = obj.modifiers.new(name="Screw", type='SCREW')
		modifier.angle = 2 * math.pi
		modifier.steps = 128
		modifier = obj.modifiers.new(name="SubSurf", type='SUBSURF')
		modifier.levels = 4
		modifier.subdivision_type = 'SIMPLE'
		if thickness > 0.0:
			modifier = obj.modifiers.new(name="Solidify", type='SOLIDIFY')
			modifier.thickness = thickness
			modifier.offset = 1.0
		c = Colors.color(color)
		if self.defaultcolor is not None:
			c = Colors.color(self.defaultcolor)
		o = Vector([0,0,0])
		op = Vector(self.origin)
		obj.location = o
		obj.scale = scale
		obj.rotation_mode = 'QUATERNION'
		if self.rotation is not None:
			obj.rotation_quaternion.rotate(self.rotation.quaternion)
			obj.location.rotate(self.rotation.quaternion)
		self.add_material(obj,c.name,c.r,c.g,c.b,opacity)
		obj.location = op
		bpy.ops.object.shade_smooth()
		self.scene.collection.objects.link(obj)
		bpy.context.view_layer.objects.active = None
		return obj
	#
	#
	#
	def draw_two_sheets_hyperboloid(self,a=2.0,b=1.0,xmin=0.0,xmax=5.0,steps=50,scale=[1,1,1],color="AzureBlueDark",name="HyperboloidTwoSheets",opacity=1.0,thickness=0.05):
		r"""
		Draws a two sheet hyperboloid from the hyperbole z = \pm a * math.sqrt(x**2+b) in the XZ plane
		Parameters:
		   a, b: coefficients of the hyperbole

		   xmin: minimum value of x

		   xmax: maximum value of x

		   steps: numbers of steps to draw the parabola

		   scale: scaling factors in the X, Y and Z directions

		   color: color of the surface

		   name: name of the surface

		   opacity: opacity of the surface

		   thickness: thickness of the surface
		"""
		delta = (xmax - xmin) / steps
		x = xmax
		bm = bmesh.new()
		verts = []
		count = 2 * steps + 2
		sign = 1
		for k in range(count):
			if k == steps + 1:
				sign = -1
			z = sign * a * math.sqrt(x**2+b)
			verts.append(bm.verts.new((x,0,z)))
			if k == steps and xmin > 0:
				x = xmin
			else:
				x = x - sign * delta
			if k == 0 or k == steps + 1:
				continue
			bm.edges.new([verts[k-1], verts[k]])

		me = self.meshes.new('placeholder_mesh')
		obj = self.objects.new(name,me)
		bm.to_mesh(me)
		bm.free()

		modifier = obj.modifiers.new(name="Screw", type='SCREW')
		modifier.angle = 2 * math.pi
		modifier.steps = 128
		modifier = obj.modifiers.new(name="SubSurf", type='SUBSURF')
		modifier.levels = 4
		modifier.subdivision_type = 'SIMPLE'
		if thickness > 0.0:
			modifier = obj.modifiers.new(name="Solidify", type='SOLIDIFY')
			modifier.thickness = thickness
			modifier.offset = 1.0
		c = Colors.color(color)
		if self.defaultcolor is not None:
			c = Colors.color(self.defaultcolor)
		o = Vector([0,0,0])
		op = Vector(self.origin)
		obj.location = o
		obj.scale = scale
		obj.rotation_mode = 'QUATERNION'
		if self.rotation is not None:
			obj.rotation_quaternion.rotate(self.rotation.quaternion)
			obj.location.rotate(self.rotation.quaternion)
		self.add_material(obj,c.name,c.r,c.g,c.b,opacity)
		obj.location = op
		bpy.ops.object.shade_smooth()
		self.scene.collection.objects.link(obj)
		bpy.context.view_layer.objects.active = None
		return obj
	#
	#
	#
	def draw_cone(self,a=1.0,xmin=0.0,xmax=5.0,steps=50,scale=[1,1,1],half=False,color="AzureBlueDark",name="Cone",opacity=1.0,thickness=0.05):
		"""
		Draws a cone from the line z = a*x in the XZ plane
		Parameters:
		   a: slope of the line

		   xmin: minimum value of x

		   xmax: maximum value of x

		   steps: numbers of steps to draw the parabola

		   scale: scaling factors in the X, Y and Z directions

		   half: if True, draws half cone

		   color: color of the surface

		   name: name of the surface

		   opacity: opacity of the surface

		   thickness: thickness of the surface
		"""
		delta = (xmax - xmin) / steps
		x = xmax
		bm = bmesh.new()
		verts = []
		count = 2 * steps + 2
		if xmin == 0.0:
			count = 2 * steps + 1
		if half:
			count = steps + 1
		for k in range(count):
			z = a * x
			verts.append(bm.verts.new((x,0,z)))
			if k == steps and xmin > 0:
				x = - xmin
			else:
				x -= delta
			if k == 0 or (k == steps + 1 and xmin > 0.0):
				continue
			bm.edges.new([verts[k-1], verts[k]])

		me = self.meshes.new('placeholder_mesh')
		obj = self.objects.new(name,me)
		bm.to_mesh(me)
		bm.free()

		modifier = obj.modifiers.new(name="Screw", type='SCREW')
		modifier.angle = 2 * math.pi
		modifier.steps = 128
		modifier = obj.modifiers.new(name="SubSurf", type='SUBSURF')
		modifier.levels = 4
		modifier.subdivision_type = 'SIMPLE'
		if thickness > 0.0:
			modifier = obj.modifiers.new(name="Solidify", type='SOLIDIFY')
			modifier.thickness = thickness
			modifier.offset = 1.0
		c = Colors.color(color)
		if self.defaultcolor is not None:
			c = Colors.color(self.defaultcolor)
		o = Vector([0,0,0])
		op = Vector(self.origin)
		obj.location = o
		obj.scale = scale
		obj.rotation_mode = 'QUATERNION'
		if self.rotation is not None:
			obj.rotation_quaternion.rotate(self.rotation.quaternion)
			obj.location.rotate(self.rotation.quaternion)
		self.add_material(obj,c.name,c.r,c.g,c.b,opacity)
		obj.location = op
		bpy.ops.object.shade_smooth()
		self.scene.collection.objects.link(obj)
		bpy.context.view_layer.objects.active = None
		return obj
	#
	#
	#
	def draw_parabolic_cylinder(self,p=0.25,xmin=0.0,xmax=6.0,length=20,steps=50,scale=[1,1,1],color="AzureBlueDark",name="ParabolicCylinder",opacity=1.0,thickness=0.05):
		"""
		Draws a parabolic cylinder from the parabola z=p*x^2 in the XZ plane
		Parameters:
		   p: coefficient of the parabola

		   xmin: minimum value of x

		   xmax: maximum value of x

		   length: length in the Y direction

		   steps: numbers of steps to draw the parabola

		   scale: scaling factors in the X, Y and Z directions

		   color: color of the surface

		   name: name of the surface

		   opacity: opacity of the surface

		   thickness: thickness of the surface
		"""
		delta = (xmax - xmin) / steps
		x = xmax
		bm = bmesh.new()
		verts = []
		count = 2 * steps + 2
		if xmin == 0.0:
			count = 2 * steps + 1
		for k in range(count):
			z = p * x**2
			verts.append(bm.verts.new((x,0,z)))
			if k == steps and xmin > 0:
				x = - xmin
			else:
				x -= delta
			if k == 0 or (k == steps + 1 and xmin > 0.0):
				continue
			bm.edges.new([verts[k-1], verts[k]])

		me = self.meshes.new('ParabolicCylinderMesh')
		obj = self.objects.new(name, me)
		bm.to_mesh(me)
		bm.free()

		bpy.context.scene.collection.objects.link(obj)
		bpy.context.view_layer.objects.active = obj
		bpy.ops.object.mode_set(mode='EDIT')
		bpy.ops.mesh.select_mode(type="EDGE")
		bpy.ops.mesh.select_all(action='SELECT')
		bpy.ops.mesh.extrude_region_move(TRANSFORM_OT_translate={"value":(0, length, 0),"constraint_axis":(False, True, False),"use_accurate":True})
		bpy.ops.mesh.select_all(action='DESELECT')
		bpy.ops.object.mode_set(mode='OBJECT')
		obj.select_set(True)
		bpy.ops.transform.translate(value=(0, -length/2, 0),constraint_axis=(False, True, False))
		bpy.ops.object.origin_set(type='ORIGIN_CURSOR', center='MEDIAN')
		obj.select_set(False)

		modifier = obj.modifiers.new(name="SubSurf", type='SUBSURF')
		modifier.levels = 4
		modifier.subdivision_type = 'SIMPLE'
		if thickness > 0.0:
			modifier = obj.modifiers.new(name="Solidify", type='SOLIDIFY')
			modifier.thickness = thickness
			modifier.offset = 1.0
		c = Colors.color(color)
		if self.defaultcolor is not None:
			c = Colors.color(self.defaultcolor)
		o = Vector([0,0,0])
		op = Vector(self.origin)
		obj.location = o
		obj.scale = scale
		obj.rotation_mode = 'QUATERNION'
		if self.rotation is not None:
			obj.rotation_quaternion.rotate(self.rotation.quaternion)
			obj.location.rotate(self.rotation.quaternion)
		self.add_material(obj,c.name,c.r,c.g,c.b,opacity)
		obj.location = op
		bpy.ops.object.shade_smooth()
		bpy.context.view_layer.objects.active = None
		return obj
	#
	#
	#
	def draw_hyperbolic_cylinder(self,a=1.0,b=4.0,xmin=2.0,xmax=6.0,length=20,steps=50,scale=[1,1,1],color="AzureBlueDark",name="HyperbolicCylinder",opacity=1.0,thickness=0.05):
		"""
		Draws an hyperbolic cylinder from the hyperbole y = a * sqrt(x**2 - b) in the XY plane
		Parameters:
		   a, b: coefficients of the hyperbole

		   xmin: minimum value of x

		   xmax: maximum value of x

		   length: length in the Z direction

		   steps: numbers of steps to draw the parabola

		   scale: scaling factors in the X, Y and Z directions

		   color: color of the surface

		   name: name of the surface

		   opacity: opacity of the surface

		   thickness: thickness of the surface
		"""
		if xmin < math.sqrt(b):
			xmin = math.sqrt(b)
		delta = (xmax-xmin)/steps
		bm = bmesh.new()
		verts = []
		count = 2 * steps + 2
		if xmin == 0.0:
			count = 2 * steps + 1
		for q, d in [[1,0],[-1,count]]:
			x = xmax
			sign = 1
			for k in range(count):
				if k == steps + 1:
					sign = -1
				if x < math.sqrt(b):
					x = math.sqrt(b)
				y = sign * a * math.sqrt(x**2 - b)
				verts.append(bm.verts.new((q * x,y,0)))
				if k == steps and xmin > math.sqrt(b):
					x = xmin
				else:
					x = x - sign * delta
				if k == 0 or (k == steps + 1 and xmin > 0.0):
					continue
				bm.edges.new([verts[d + k-1], verts[d + k]])

		me = self.meshes.new('HyperboliclinderMesh')
		obj = self.objects.new(name, me)
		bm.to_mesh(me)
		bm.free()

		self.scene.collection.objects.link(obj)
		bpy.context.view_layer.objects.active = obj
		bpy.ops.object.mode_set(mode='EDIT')
		bpy.ops.mesh.select_mode(type="EDGE")
		bpy.ops.mesh.select_all(action='SELECT')
		bpy.ops.mesh.extrude_region_move(TRANSFORM_OT_translate={"value":(0,0,length),"constraint_axis":(False,False,True),"use_accurate":True})
		bpy.ops.mesh.select_all(action='DESELECT')
		bpy.ops.object.mode_set(mode='OBJECT')
		obj.select_set(True)
		bpy.ops.transform.translate(value=(0,0,-length/2),constraint_axis=(False,False,True))
		bpy.ops.object.origin_set(type='ORIGIN_CURSOR', center='MEDIAN')
		obj.select_set(False)

		if thickness > 0.0:
			modifier = obj.modifiers.new(name="Solidify", type='SOLIDIFY')
			modifier.thickness = thickness
			modifier.offset = 1.0
		modifier = obj.modifiers.new(name="SubSurf", type='SUBSURF')
		modifier.levels = 4
		modifier.subdivision_type = 'SIMPLE'
		c = Colors.color(color)
		if self.defaultcolor is not None:
			c = Colors.color(self.defaultcolor)
		o = Vector([0,0,0])
		op = Vector(self.origin)
		obj.location = o
		obj.scale = scale
		obj.rotation_mode = 'QUATERNION'
		if self.rotation is not None:
			obj.rotation_quaternion.rotate(self.rotation.quaternion)
			obj.location.rotate(self.rotation.quaternion)
		self.add_material(obj,c.name,c.r,c.g,c.b,opacity)
		obj.location = op
		bpy.ops.object.shade_smooth()
		bpy.context.view_layer.objects.active = None
		return obj
	#
	#
	#
	def draw_elliptic_cylinder(self,a=8.0,b=5.0,amin=0.0,amax=2*math.pi,length=20,steps=200,scale=[1,1,1],color="AzureBlueDark",name="EllipticCylinder",opacity=1.0,thickness=0.05):
		"""
		Draws an eliptic cylinder from the ellipse
		  x = a*cos(t)
		  y = b*sin(t)
		in the XY plane
		Parameters:
		   a, b: coefficients of the ellipsw

		   amin: minimum value of the angle t

		   amax: maximum value of the angle t

		   length: length in the Z direction

		   steps: numbers of steps to draw the parabola

		   scale: scaling factors in the X, Y and Z directions

		   color: color of the surface

		   name: name of the surface

		   opacity: opacity of the surface

		   thickness: thickness of the surface
		"""
		if amin < 0.0:
			amin = 0.0
		if amax > 2 * math.pi:
			amax = 2 * math.pi
		delta = (amax-amin)/steps
		bm = bmesh.new()
		verts = []
		t = amin
		for k in range(steps + 1):
			x = a * math.cos(t)
			y = b * math.sin(t)
			verts.append(bm.verts.new((x,y,0)))
			t += delta
			if k == 0:
				continue
			bm.edges.new([verts[k-1], verts[k]])

		me = self.meshes.new('EllipticCylinderMesh')
		obj = self.objects.new(name, me)
		bm.to_mesh(me)
		bm.free()
		self.scene.collection.objects.link(obj)

		bpy.context.view_layer.objects.active = obj
		bpy.ops.object.mode_set(mode='EDIT')
		bpy.ops.mesh.select_mode(type="EDGE")
		bpy.ops.mesh.select_all(action='SELECT')
		bpy.ops.mesh.extrude_region_move(TRANSFORM_OT_translate={"value":(0,0,length),"constraint_axis":(False,False,True),"use_accurate":True})
		bpy.ops.mesh.select_all(action='DESELECT')
		bpy.ops.object.mode_set(mode='OBJECT')
		obj.select_set(True)
		bpy.ops.transform.translate(value=(0,0,-length/2),constraint_axis=(False,False,True))
		bpy.ops.object.origin_set(type='ORIGIN_CURSOR', center='MEDIAN')
		obj.select_set(False)

		if thickness > 0.0:
			modifier = obj.modifiers.new(name="Solidify", type='SOLIDIFY')
			modifier.thickness = thickness
			modifier.offset = 1.0
		modifier = obj.modifiers.new(name="SubSurf", type='SUBSURF')
		modifier.levels = 4
		modifier.subdivision_type = 'SIMPLE'
		c = Colors.color(color)
		if self.defaultcolor is not None:
			c = Colors.color(self.defaultcolor)
		o = Vector([0,0,0])
		op = Vector(self.origin)
		obj.location = o
		obj.scale = scale
		obj.rotation_mode = 'QUATERNION'
		if self.rotation is not None:
			obj.rotation_quaternion.rotate(self.rotation.quaternion)
			obj.location.rotate(self.rotation.quaternion)
		self.add_material(obj,c.name,c.r,c.g,c.b,opacity)
		obj.location = op
		bpy.ops.object.shade_smooth()
		bpy.context.view_layer.objects.active = None
		return obj
	#
	#
	#
	def draw_hyperbolic_paraboloid(self,a=0.2,b=0.4,xmax=10.0,ymax=10.0,steps=64,scale=[1,1,1],color="AzureBlueDark",name="HyperbolicParaboloid",opacity=1.0,thickness=0.05):
		"""
		Draws an hyperbolic paraboloid with equation z = a*x^2 - b*y^2
		Parameters:
		   a, b: coefficients of the parabolic hyperboloid

		   xmax: maximum  value of x

		   ymax: maxim value y

		   steps: numbers of steps to draw the parabola

		   scale: scaling factors in the X, Y and Z directions

		   color: color of the surface

		   name: name of the surface

		   opacity: opacity of the surface

		   thickness: thickness of the surface
		"""
		equ = lambda x,y: (x,y,a*x**2-b*y**2)
		obj = self.draw_surface(eq=equ,umin=-xmax,umax=xmax,usteps=steps,vmin=-ymax,vmax=ymax,vsteps=steps,thickness=thickness,opacity=opacity,pmax=0,name="Hyperbolic paraboloid",color="AzureBlueDark",axis=False,o=Vector([0,0,0]),u1=Vector([1,0,0]),u2=Vector([0,1,0]),wrap_u=False,wrap_v=False,close_v=False)
		obj.scale = scale
		return obj
	#
	#
	#
	def draw_ellipsoid(self,radius=5.0,scale=[1.2,1.8,0.8],color="AzureBlueDark",name="Ellipsoid",opacity=1.0,thickness=0.05):
		"""
		Draws en ellipsoid
		Parameters:
		   radius: radius of the sphere

		   scale: scaling factors in the X, Y and Z directions

		   color: color of the surface

		   name: name of the surface

		   opacity: opacity of the surface

		   thickness: thickness of the surface
		"""
		bpy.ops.mesh.primitive_uv_sphere_add(segments=128, ring_count=128, radius=radius, enter_editmode=False, location=(0, 0, 0))
		bpy.context.object.name = name
		obj = bpy.data.objects.get(name)

		modifier = obj.modifiers.new(name="SubSurf", type='SUBSURF')
		modifier.levels = 4
		modifier.subdivision_type = 'SIMPLE'
		if thickness > 0.0:
			modifier = obj.modifiers.new(name="Solidify", type='SOLIDIFY')
			modifier.thickness = thickness
			modifier.offset = 1.0
		c = Colors.color(color)
		if self.defaultcolor is not None:
			c = Colors.color(self.defaultcolor)
		o = Vector([0,0,0])
		op = Vector(self.origin)
		obj.location = o
		obj.scale = scale
		obj.rotation_mode = 'QUATERNION'
		if self.rotation is not None:
			obj.rotation_quaternion.rotate(self.rotation.quaternion)
			obj.location.rotate(self.rotation.quaternion)
		self.add_material(obj,c.name,c.r,c.g,c.b,opacity)
		obj.location = op
		bpy.ops.object.shade_smooth()
		obj.select_set(False)
		bpy.ops.object.shade_smooth()
		bpy.context.view_layer.objects.active = None
		return obj
	#
	#
	#
	def draw_plane_surface(self,origin=None,normal=None,base=None,sizex=10,sizey=10,vectors=False,scalelines=0.05,scalevector=0.03,
						color="AzureBlueDark",linecolor="BlueDarkDull",vectorcolor="Black",name="Plane",opacity=1.0,thickness=0.0):
		"""
		Draws a plane with normal vector or base vectors. It passes through the point origin.
		Only normal or base can be not None
		Parameters:
		   origin: a point in the plane

		   normal: normal vector to the plane

		   base: list of two independent vectors

		   sizex: x-size of the plane

		   sizey: y-size of the plane

		   vectors: if True, draw the generators of the plane

		   scalelines: scale of the lines limiting the plane

		   scalevector: scale of the generators

		   color: color of the plane

		   linecolor: color of the lines limiting the plane

		   vectorcolor: color of the generators

		   name: name of the plane

		   opacity: opacity of the plane

		   thickness: thickness of the plane
		"""
		if normal is not None and base is not None:
			return
		if normal is None and base is None:
			return
		mat = Matrix(self.base)
		mat.transpose()
		if normal is not None:
			if not isinstance(normal,Vector):
			 	normal= Vector(normal)
			normal = mat @ normal
		if base is not None:
			if len(base) != 2:
				return
			if isinstance(base[0],Vector):
			 	v1 = base[0]
			else:
				v1 = Vector(base[0])
			if isinstance(base[1],Vector):
			 	v2 = base[1]
			else:
				v2 = Vector(base[1])
			v1 = mat @ v1
			v2 = mat @ v2
			normal = v1.cross(v2)

		if normal == Vector([0,0,0]):
			return

		steps = 4
		delta = sizex / steps
		x = - sizex / 2
		bm = bmesh.new()
		verts = []
		for k in range(steps + 1):
			verts.append(bm.verts.new((x,0,0)))
			x += delta
			if k == 0:
				continue
			bm.edges.new([verts[k-1], verts[k]])

		me = self.meshes.new('PlaneSurfaceMesh')
		obj = self.objects.new('PlaneSurface', me)
		bm.to_mesh(me)
		bm.free()

		bpy.context.scene.collection.objects.link(obj)
		bpy.context.view_layer.objects.active = obj
		bpy.ops.object.mode_set(mode='EDIT')
		bpy.ops.mesh.select_mode(type="EDGE")
		bpy.ops.mesh.select_all(action='SELECT')
		bpy.ops.mesh.extrude_region_move(TRANSFORM_OT_translate={"value":(0, sizey, 0),"constraint_axis":(False, True, False),"use_accurate":True})
		bpy.ops.mesh.select_all(action='DESELECT')
		bpy.ops.object.mode_set(mode='OBJECT')
		obj.select_set(True)
		bpy.ops.transform.translate(value=(0, -sizey/2, 0),constraint_axis=(False, True, False))
		bpy.ops.object.origin_set(type='ORIGIN_CURSOR', center='MEDIAN')
		obj.select_set(False)

		modifier = obj.modifiers.new(name="SubSurf", type='SUBSURF')
		modifier.levels = 4
		modifier.subdivision_type = 'SIMPLE'
		if thickness > 0.0:
			modifier = obj.modifiers.new(name="Solidify", type='SOLIDIFY')
			modifier.thickness = thickness
			modifier.offset = 1.0
		c = Colors.color(color)
		o = Vector([0,0,0])
		op = Vector(self.origin)
		if origin is not None:
			if isinstance(origin,Vector):
				op = op + origin
			else:
				op = op + Vector(origin)
		obj.location = o
		obj.rotation_mode = 'QUATERNION'
		if self.rotation is not None:
			obj.rotation_quaternion.rotate(self.rotation.quaternion)
			obj.location.rotate(self.rotation.quaternion)
		self.add_material(obj,c.name,c.r,c.g,c.b,opacity)

		lines = None
		vecs = None
		s = 0.0
		nodes = [[1,1,0],[-1,1,0],[-1,-1,0],[1,-1,0]]
		nodes = [self.product_components(Vector([sizex / 2,sizey / 2,0]),Vector(x)) for x in nodes]
		edges = [[0,1],[1,2],[2,3],[3,0]]

		if scalelines > 0.0:
			aux = self.origin
			self.origin = Vector([0,0,0])
			objects = []
			aux2 = self.base
			self.reset_base()
			for edge in edges:
				l = self.draw_line(start=nodes[edge[0]],end=nodes[edge[1]],scale=scalelines,name="Lines",color=linecolor)
				objects.append(l)
			lines = self.join(objects)
			self.set_origin(aux)
			self.set_base(aux2)

		if lines is not None:
			obj = self.join([obj,lines])

		if vectors:
			vecs = self.draw_vectors(nodes,True,color=vectorcolor,scale=scalevector,head_height=0.1,name="Vectors",axis=0)

		if vecs is not None:
			obj = self.join([obj,vecs])
		obj.name = name

		if isinstance(normal,Vector):
			n = normal
		else:
			n = Vector(normal)
		z = Vector([0,0,1])
		quaternion = z.rotation_difference(n)
		tmp = obj.rotation_quaternion
		quaternion = tmp @ quaternion
		obj.rotation_quaternion = quaternion
		bpy.ops.object.select_all(action='DESELECT')
		obj.location = op
		bpy.ops.object.shade_smooth()
		bpy.context.view_layer.objects.active = None
		return obj
	#
	#
	#
	def draw_point(self,radius=0.1,location=(0,0,0),name="Point",color="Black",opacity=1.0):
		"""
		Draws a point (in the reference self.origin, self.base)
		Parameters:
		   radius: radius of the point

		   location: location of the point

		   name: name of the point

		   color: color of the point

		   opacity: opacity of the point
		"""
		bpy.ops.mesh.primitive_uv_sphere_add(segments=8, ring_count=8, radius=radius, enter_editmode=False, location=location)
		bpy.context.object.name = name
		obj = bpy.data.objects.get(name)

		if not isinstance(location,Vector):
			location = Vector(location)
		mat = Matrix(self.base)
		mat.transpose()
		location = mat @ location

		modifier = obj.modifiers.new(name="SubSurf", type='SUBSURF')
		modifier.levels = 4
		modifier.subdivision_type = 'SIMPLE'
		modifier = obj.modifiers.new(name="Solidify", type='SOLIDIFY')
		modifier.thickness = 0.1
		modifier.offset = 0.0
		c = Colors.color(color)
		op = Vector(self.origin)
		obj.location = op + location
		self.add_material(obj,c.name,c.r,c.g,c.b,opacity)
		bpy.ops.object.shade_smooth()
		obj.select_set(False)
		bpy.context.view_layer.objects.active = None
		return obj
	#
	#
	#
	def draw_cube(self,origin=None,scale=[1,1,1],scalelines=0.05,vectors=False,color="Blue",linecolor="Red",vectorcolor="Black",name='Parallelepiped',opacity=1.0,thickness=0.0):
		"""
		Draws a rectangular parallelepiped
		Parameters:
		   origin: center of the parallelepiped

		   scale: scale of the sides of the parallelepiped

		   scalelines: scale of the edges of the parallelepiped

		   vectors: if True, draws vectors from the origin to the vertices

		   color: color of the parallelepiped

		   linecolor: color of the edges

		   vectorcolor: color of the vectors

		   name: name of the parallelepiped

		   opacity: opacity of the parallelepiped

		   thickness: thickness of the parallelepiped
		"""
		bpy.ops.mesh.primitive_cube_add(size=2,enter_editmode=False,align='WORLD',location=(0, 0, 0))
		bpy.context.object.name = name
		obj = bpy.data.objects.get(name)
		o = Vector([0,0,0])
		op = Vector(self.origin)
		if origin is not None:
			if isinstance(origin,Vector):
				op = op + origin
			else:
				op = op + Vector(origin)
		obj.location = o
		if thickness > 0.0:
			modifier = obj.modifiers.new(name="Solidify", type='SOLIDIFY')
			modifier.thickness = thickness
			modifier.offset = 0.0

		lines = None
		vecs = None
		s = 0.0
		nodes = [[1+s,1+s,1+s],[-1-s,1+s,1+s],[-1-s,-1-s,1+s],[1+s,-1-s,1+s],
				[1+s,1+s,-1-s],[-1-s,1+s,-1-s],[-1-s,-1-s,-1-s],[1+s,-1-s,-1-s]]
		nodes = [self.product_components(Vector(scale),Vector(x)) for x in nodes]
		edges =[[0,1],[1,2],[2,3],[3,0],[0,4],[1,5],[2,6],[3,7],[4,5],[5,6],[6,7],[7,4]]
		if scalelines > 0.0:
			objects = []
			for edge in edges:
				l = self.draw_line(start=op+nodes[edge[0]],end=op+nodes[edge[1]],scale=scalelines,name="Lines",color=linecolor)
				objects.append(l)
			lines = self.join(objects)

		if vectors:
			vecs = self.draw_vectors(nodes,color=vectorcolor,scale=0.05,head_height=0.2,name="Vectors",axis=0)

		c = Colors.color(color)
		self.add_material(obj,c.name,c.r,c.g,c.b,opacity)
		obj.scale = scale

		obj.rotation_mode = 'QUATERNION'
		if self.rotation is not None:
			obj.rotation_quaternion.rotate(self.rotation.quaternion)
			obj.location.rotate(self.rotation.quaternion)
		obj.location = op
		bpy.ops.object.shade_smooth()
		bpy.context.view_layer.objects.active = None
		if lines is not None:
			obj = self.join([obj,lines])

		if vecs is not None:
			obj = self.join([obj,vecs])
		return obj
	#
	#
	#
	def ortoedre(self,centre=Vector([0,0,0]),costats=[6,10,8],scalelines=0.05,vectors=False,color="Blue",linecolor="Red",vectorcolor="Black",name='Ortoedre',opacity=1.0,thickness=0.0):
		if not isinstance(centre,Vector):
			centre = Vector(centre)
		self.draw_cube(origin=centre,scale=costats,scalelines=scalelines,vectors=vectors,color=color,linecolor=linecolor,vectorcolor=vectorcolor,name=name,opacity=opacity,thickness=thickness)
	#
	#
	#
	def draw_parallelepiped(self,origin=[0,0,0],u1=[1,0,0],u2=[0,1,0],u3=[0,0,1],scalelines=0.025,color="AzureBlueDark",linecolor="OrangeObscureDull",name='Parallelepiped',opacity=1.0,thickness=0.0):
		"""
		Draws a parallelepiped
		Parameters:
		   origin: base vertex of the parallelepiped

		   u1, u2, u3: vectors that gives the edges

		   scalelines: scale of the edges of the parallelepiped

		   color: color of the parallelepiped

		   linecolor: color of the edges

		   name: name of the parallelepiped

		   opacity: opacity of the parallelepiped

		   thickness: thickness of the parallelepiped
		"""
		op = Vector(self.origin)
		if isinstance(origin,Vector):
			op = op + origin
		else:
			op = op + Vector(origin)
		if not isinstance(u1,Vector):
			u1 = Vector(u1)
		if not isinstance(u2,Vector):
			u2 = Vector(u2)
		if not isinstance(u3,Vector):
			u3 = Vector(u3)

		mat = Matrix(self.base)
		mat.transpose()
		u1 = mat @ u1
		u2 = mat @ u2
		u3 = mat @ u3

		bpy.ops.mesh.primitive_cube_add(size=2,enter_editmode=False,align='WORLD',location=(0, 0, 0))
		bpy.context.object.name = name
		obj = bpy.data.objects.get(name)

		verts = obj.data.vertices
		verts[0].co = op
		verts[1].co = op + u3
		verts[2].co = op + u2
		verts[3].co = op + u2 + u3
		verts[4].co = op + u1
		verts[5].co = op + u1 + u3
		verts[6].co = op + u1 + u2
		verts[7].co = op + u1 + u2 + u3

		if thickness > 0.0:
			modifier = obj.modifiers.new(name="Solidify", type='SOLIDIFY')
			modifier.thickness = thickness
			modifier.offset = 0.0

		lines = None
		s = 0.0
		edges =[[0,1],[0,2],[0,4],[1,3],[1,5],[2,3],[2,6],[3,7],[4,5],[4,6],[5,7],[6,7]]
		if scalelines > 0.0:
			objects = []
			for edge in edges:
				l = self.draw_line(start=verts[edge[0]].co,end=verts[edge[1]].co,scale=scalelines,name="Lines",color=linecolor)
				objects.append(l)
			lines = self.join(objects)

		c = Colors.color(color)
		self.add_material(obj,c.name,c.r,c.g,c.b,opacity)

		if lines is not None:
			obj = self.join([obj,lines])

		obj.rotation_mode = 'QUATERNION'
		if self.rotation is not None:
			obj.rotation_quaternion.rotate(self.rotation.quaternion)
			obj.location.rotate(self.rotation.quaternion)
		bpy.ops.object.shade_smooth()
		bpy.context.view_layer.objects.active = None

		return obj
	#
	#
	#
	def draw_tetrahedron(self,origin=[0,0,0],u1=[2,0,0],u2=[2*math.cos(math.pi/3),2*math.sin(math.pi/3),0],u3=[(2+2*math.cos(math.pi/3))/3,2*math.sin(math.pi/3)/3,2],scalelines=0.025,color="AzureBlueDark",linecolor="OrangeObscureDull",name='Tetrahedron',opacity=1.0,thickness=0.0):
		"""
		Draws a tetrahedron
		Parameters:
		   origin: base vertex of the tetrahedron

		   u1, u2, u3: vectors that gives the edges

		   scalelines: scale of the edges of the tetrahedron

		   color: color of the tetrahedron

		   linecolor: color of the edges

		   name: name of the tetrahedron

		   opacity: opacity of the tetrahedron

		   thickness: thickness of the tetrahedron
		"""
		op = Vector(self.origin)
		if isinstance(origin,Vector):
			op = op + origin
		else:
			op = op + Vector(origin)
		if not isinstance(u1,Vector):
			u1 = Vector(u1)
		if not isinstance(u2,Vector):
			u2 = Vector(u2)
		if not isinstance(u3,Vector):
			u3 = Vector(u3)

		mat = Matrix(self.base)
		mat.transpose()
		u1 = mat @ u1
		u2 = mat @ u2
		u3 = mat @ u3

		bpy.ops.mesh.primitive_solid_add()
		bpy.context.object.name = name
		obj = bpy.data.objects.get(name)

		verts = obj.data.vertices
		verts[0].co = op + u3
		verts[1].co = op
		verts[2].co = op + u1
		verts[3].co = op + u2

		if thickness > 0.0:
			modifier = obj.modifiers.new(name="Solidify", type='SOLIDIFY')
			modifier.thickness = thickness
			modifier.offset = 0.0

		lines = None
		s = 0.0
		edges =[[0,1],[0,2],[0,3],[1,2],[1,3],[2,3]]
		if scalelines > 0.0:
			objects = []
			for edge in edges:
				l = self.draw_line(start=verts[edge[0]].co,end=verts[edge[1]].co,scale=scalelines,name="Lines",color=linecolor)
				objects.append(l)
			lines = self.join(objects)

		c = Colors.color(color)
		self.add_material(obj,c.name,c.r,c.g,c.b,opacity)

		if lines is not None:
			obj = self.join([obj,lines])

		obj.rotation_mode = 'QUATERNION'
		if self.rotation is not None:
			obj.rotation_quaternion.rotate(self.rotation.quaternion)
			obj.location.rotate(self.rotation.quaternion)
		bpy.ops.object.shade_smooth()
		bpy.context.view_layer.objects.active = None

		return obj
	#
	#
	#
	def draw_pyramid(self,origin=[0,0,0],u1=[1,0,0],u2=[0,1,0],u3=[0.5,0.5,1],scalelines=0.025,color="AzureBlueDark",linecolor="OrangeObscureDull",name='Pyramid',opacity=1.0,thickness=0.0):
		"""
		Draws a pyramid
		Parameters:
		   origin: base vertex of the pyramid

		   u1, u2, u3: vectors that gives the edges

		   scalelines: scale of the edges of the pyramid

		   color: color of the pyramid

		   linecolor: color of the edges

		   name: name of the pyramid

		   opacity: opacity of the pyramid

		   thickness: thickness of the pyramid
		"""
		op = Vector(self.origin)
		if isinstance(origin,Vector):
			op = op + origin
		else:
			op = op + Vector(origin)
		if not isinstance(u1,Vector):
			u1 = Vector(u1)
		if not isinstance(u2,Vector):
			u2 = Vector(u2)
		if not isinstance(u3,Vector):
			u3 = Vector(u3)

		mat = Matrix(self.base)
		mat.transpose()
		u1 = mat @ u1
		u2 = mat @ u2
		u3 = mat @ u3

		bpy.ops.mesh.primitive_cone_add(radius1=1, radius2=0, depth=2, enter_editmode=False, align='WORLD',vertices=4)
		bpy.context.object.name = name
		obj = bpy.data.objects.get(name)

		verts = obj.data.vertices
		verts[0].co = op
		verts[1].co = op + u1
		verts[2].co = op + u1 + u2
		verts[3].co = op + u2
		verts[4].co = op + u3

		if thickness > 0.0:
			modifier = obj.modifiers.new(name="Solidify", type='SOLIDIFY')
			modifier.thickness = thickness
			modifier.offset = 0.0

		lines = None
		s = 0.0
		edges =[[0,1],[0,3],[0,4],[1,2],[1,4],[2,3],[2,4],[3,4]]
		if scalelines > 0.0:
			objects = []
			for edge in edges:
				l = self.draw_line(start=verts[edge[0]].co,end=verts[edge[1]].co,scale=scalelines,name="Lines",color=linecolor)
				objects.append(l)
			lines = self.join(objects)

		c = Colors.color(color)
		self.add_material(obj,c.name,c.r,c.g,c.b,opacity)

		if lines is not None:
			obj = self.join([obj,lines])

		obj.rotation_mode = 'QUATERNION'
		if self.rotation is not None:
			obj.rotation_quaternion.rotate(self.rotation.quaternion)
			obj.location.rotate(self.rotation.quaternion)
		bpy.ops.object.shade_smooth()
		bpy.context.view_layer.objects.active = None

		return obj
	#
	#
	#
	def draw_parallelogram(self,origin=[0,0,0],u1=[1,0,0],u2=[0,1,0],scalelines=0.025,color="AzureBlueDark",linecolor="OrangeObscureDull",name='Parallelogram',opacity=1.0,thickness=0.0):
		"""
		Draws a parallelogram
		Parameters:
		   origin: base vertex of the parallelogram

		   u1, u2: vectors that gives the edges

		   scalelines: scale of the edges of the parallelogram

		   color: color of the parallelogram

		   linecolor: color of the edges

		   name: name of the parallelogram

		   opacity: opacity of the parallelogram

		   thickness: thickness of the parallelogram
		"""
		op = Vector(self.origin)
		if isinstance(origin,Vector):
			op = op + origin
		else:
			op = op + Vector(origin)
		if not isinstance(u1,Vector):
			u1 = Vector(u1)
		if not isinstance(u2,Vector):
			u2 = Vector(u2)

		mat = Matrix(self.base)
		mat.transpose()
		u1 = mat @ u1
		u2 = mat @ u2

		bpy.ops.mesh.primitive_plane_add(size=2,enter_editmode=False,align='WORLD',location=(0, 0, 0))
		bpy.context.object.name = name
		obj = bpy.data.objects.get(name)

		verts = obj.data.vertices
		verts[0].co = op
		verts[1].co = op + u1
		verts[2].co = op + u2
		verts[3].co = op + u1 + u2

		if thickness > 0.0:
			modifier = obj.modifiers.new(name="Solidify", type='SOLIDIFY')
			modifier.thickness = thickness
			modifier.offset = 0.0

		lines = None
		s = 0.0
		edges =[[0,1],[0,2],[1,3],[2,3]]
		if scalelines > 0.0:
			objects = []
			for edge in edges:
				l = self.draw_line(start=verts[edge[0]].co,end=verts[edge[1]].co,scale=scalelines,name="Lines",color=linecolor)
				objects.append(l)
			lines = self.join(objects)

		c = Colors.color(color)
		self.add_material(obj,c.name,c.r,c.g,c.b,opacity)

		if lines is not None:
			obj = self.join([obj,lines])

		obj.rotation_mode = 'QUATERNION'
		if self.rotation is not None:
			obj.rotation_quaternion.rotate(self.rotation.quaternion)
			obj.location.rotate(self.rotation.quaternion)
		bpy.ops.object.shade_smooth()
		bpy.context.view_layer.objects.active = None

		return obj
	#
	# Draw a polygon
	#
	def draw_polygon(self,origin=[0,0,0],u1=[1,0,0],u2=[0,1,0],points=[[0,0],[1,0],[0,1]],scalelines=0.075,color="AzureBlueMedium",linecolor="AzureBlueDark",name='Polygon',opacity=1.0,thickness=0.0,vectors=None,scalevectors=0.01):
		"""
		Draws a polygon
		Parameters:
		   origin: base vertex of the polygon

		   u1, u2: base vectors for the polygon

		   points: list of coordinates of points. The coordinates are taken in the reference {origin; u1, u2}

		   scalelines: scale of the edges of the polygon

		   color: color of the polygon

		   linecolor: color of the edges

		   name: name of the polygon

		   opacity: opacity of the polygon

		   thickness: thickness of the polygon
		"""
		if len(points) < 3:
			return
		op = Vector(self.origin)
		if isinstance(origin,Vector):
			op = op + origin
		else:
			op = op + Vector(origin)
		if not isinstance(u1,Vector):
			u1 = Vector(u1)
		if not isinstance(u2,Vector):
			u2 = Vector(u2)
		for i in range(len(points)):
			if not isinstance(points[i],Vector):
				points[i] = Vector(points[i])

		mat = Matrix(self.base)
		mat.transpose()
		u1 = mat @ u1
		u2 = mat @ u2

		bpy.ops.curve.simple(Simple_Type='Polygon',Simple_sides=len(points),align='WORLD',location=(0, 0, 0))
		bpy.context.object.name = name
		obj = bpy.data.objects.get(name)
		bpy.ops.object.mode_set(mode='OBJECT')

		baricentre = Vector([0,0,0])
		verts = obj.data.splines[0].bezier_points
		for i in range(len(verts)):
			verts[i].co = op + points[i][0] * u1 + points[i][1] * u2
			baricentre += verts[i].co
		baricentre /= len(verts)

		for i in range(len(verts)):
			verts[i].co -= baricentre
		obj.location = baricentre

		obj.select_set(True)
		bpy.ops.object.convert(target='MESH')

		if thickness > 0.0:
			modifier = obj.modifiers.new(name="Solidify", type='SOLIDIFY')
			modifier.thickness = thickness
			modifier.offset = 0.0

		ps = [op + points[i][0] * u1 + points[i][1] * u2 for i in range(len(points))]
		lines = None
		if scalelines > 0.0:
			objects = []
			for i in range(len(points)):
				l = self.draw_line(start=ps[i],end=ps[(i + 1) % len(points)],scale=scalelines,name="Lines",color=linecolor)
				objects.append(l)
			lines = self.join(objects)

		if vectors is not None:
			old = self.origin
			self.set_origin(op)
			ps = [points[i][0] * u1 + points[i][1] * u2 for i in range(len(points))]
			vecs = self.draw_vectors(ps,color=vectors,scale=scalevectors)
			self.set_origin(old)

		c = Colors.color(color)
		self.add_material(obj,c.name,c.r,c.g,c.b,opacity)

		if lines is not None:
			obj = self.join([obj,lines])
		if vectors is not None:
			obj = self.join([obj,vecs])

		obj.rotation_mode = 'QUATERNION'
		if self.rotation is not None:
			obj.rotation_quaternion.rotate(self.rotation.quaternion)
			obj.location.rotate(self.rotation.quaternion)
		bpy.ops.object.shade_smooth()
		bpy.context.view_layer.objects.active = None

		return obj
	#
	# Draw a regular polygon
	#
	def draw_regular_polygon(self,origin=[0,0,0],u1=[1,0,0],u2=[0,1,0],vertexs=5,radius=1,scalelines=0.075,color="AzureBlueDark",linecolor="OrangeObscureDull",name='RegularPolygon',opacity=1.0,thickness=0.0,vectors=None):
		"""
		Draws a regular polygon
		Parameters:
		   origin: base vertex of the polygon

		   u1, u2: base vectors for the polygon

		   vertexs: number of vertices of the polygon

		   radius: radius of the polygon

		   scalelines: scale of the edges of the polygon

		   color: color of the polygon

		   linecolor: color of the edges

		   name: name of the polygon

		   opacity: opacity of the polygon

		   thickness: thickness of the polygon
		"""
		angle = 2*math.pi/vertexs
		points = [[radius*math.cos(i*angle),radius*math.sin(i*angle)] for i in range(vertexs)]
		return self.draw_polygon(origin=origin,u1=u1,u2=u2,points=points,scalelines=scalelines,color=color,linecolor=linecolor,name=name,opacity=opacity,thickness=thickness,vectors=vectors,scalevectors=radius/400)
	#
	# Draw a triangle
	#
	def draw_triangle(self,origin=[0,0,0],u1=[1,0,0],u2=[0,1,0],points=[[0,0],[1,0],[0,1]],scalelines=0.075,color="AzureBlueMedium",linecolor="OrangeObscureDull",name="Triangle",opacity=1.0,thickness=0.0):
		"""
		Draws a triangle. It's a polygon with three vertices
		Parameters:
		   origin: base vertex of the triangle

		   u1, u2: base vectors for the triangle

		   points: list of coordinates of points. The coordinates are taken in the reference {origin; u1, u2}

		   scalelines: scale of the edges of the triangle

		   color: color of the triangle

		   linecolor: color of the edges

		   name: name of the triangle

		   opacity: opacity of the triangle

		   thickness: thickness of the triangle
		"""
		if len(points) != 3:
			return
		self.draw_polygon(origin=origin,u1=u1,u2=u2,points=points,scalelines=scalelines,color=color,linecolor=linecolor,name=name,opacity=opacity,thickness=thickness)
	#
	# Draw a triangle from vertices
	#
	def triangle(self,vertices=[[0,0,0],[1,0,0],[0,1,0]],scalelines=0.075,color="AzureBlueMedium",linecolor="Blue",name="Triangle",baricentre=False,factors=(2,2,-2),ortocentre=False,opacity=1.0,thickness=0.0):
		"""
		Draws a triangle from the vertices
		Parameters:
		   vertices: vertices of the triangle

		   scalelines: scale of the edges of the triangle

		   color: color of the triangle

		   linecolor: color of the edges

		   name: name of the triangle

		   opacity: opacity of the triangle

		   thickness: thickness of the triangle
		"""
		if len(vertices) != 3:
			return None
		if len(factors) != 3:
			return None
		v = [Vector(x) for x in vertices]
		if ortocentre:
			u1 = v[1]-v[0]
			u2 = v[2]-v[0]
			u3 = v[2] - v[1] 
			p0 = v[1] - u1.project(u3) 
			self.draw_line(start=v[0],end=v[0]+factors[0]*(p0-v[0]),scale=0.05,name="Altura 1",color="White")
			p1 = v[2] - u3.project(u2) 
			self.draw_line(start=v[1],end=v[1]+factors[1]*(p1-v[1]),scale=0.05,name="Altura 2",color="White")
			p2 = v[0] + u2.project(u1) 
			self.draw_line(start=v[2],end=v[2]+factors[2]*(p2-v[2]),scale=0.05,name="Altura 3",color="White")
			
		if baricentre:
			m01 = (v[0]+v[1])/2
			m02 = (v[0]+v[2])/2
			m12 = (v[1]+v[2])/2
			m = (v[0]+v[1]+v[2])/3
			self.draw_line(start=v[0],end=m12,scale=0.05,name="Mitjana 1",color="White")
			self.draw_line(start=v[1],end=m02,scale=0.05,name="Mitjana 2",color="White")
			self.draw_line(start=v[2],end=m01,scale=0.05,name="Mitjana 2",color="White")
		self.draw_triangle(origin=v[0],u1=v[1]-v[0],u2=v[2]-v[0],scalelines=scalelines,color=color,linecolor=linecolor,name=name,opacity=opacity,thickness=thickness)
	#
	# Draw a rectangle 
	# 
	def rectangle(self,origin=[0,0,0],u1=[1,0,0],u2=[0,1,0],scalelines=0.1,color="AzureBlueMedium",linecolor="AzureBlueDark",name="Rectangle",sizex=10,sizey=10,opacity=1.0,thickness=0.0):
		"""
		Draws a rectangle
		Parameters:
		   origin: base vertex of the rectangle

		   u1, u2: base vectors for the rectangle

		   scalelines: scale of the edges of the rectangle

		   color: color of the rectangle

		   linecolor: color of the edges

		   name: name of the rectangle

		   sizex, sizey: sizes of the rectangle

		   opacity: opacity of the rectangle

		   thickness: thickness of the rectangle
		"""
		if not isinstance(u1,Vector):
			u1 = Vector(u1)
		if not isinstance(u2,Vector):
			u2 = Vector(u2)	
		u1.normalize()
		u2.normalize()
		points = [(0,0),(sizex,0),(sizex,sizey),(0,sizey)]	
		self.draw_polygon(origin=origin,u1=u1,u2=u2,points=points,scalelines=scalelines,color=color,linecolor=linecolor,name=name,opacity=opacity,thickness=thickness)
	#
	# Draw a list of points
	#
	def draw_points(self,points=[],name='Points',color="Blue",opacity=1):
		"""
		Draws a list of points
		Parameters:
		   points: list of points

		   name: name of the list of points

		   color: color of the points

		   opacity: opacity of the points
		"""
		bm = bmesh.new()
		verts = []
		for p in points:
			verts.append(bm.verts.new(p))

		me = self.meshes.new('PointsMesh')
		obj = self.objects.new(name, me)
		bm.to_mesh(me)
		bm.free()
		self.scene.collection.objects.link(obj)
		return obj
	#
	# Draw a mesh
	#
	def draw_mesh(self,mesh=None,name='Mesh',color="Blue",opacity=1):
		"""
		Draws a mesh. This function is used by other functions
		Parameters:
		   mesh: the mesh to be drawn

		   name: name of the mesh

		   color: color of the mesh

		   opacity: opacity of the mesh
		"""
		bm = bmesh.new()
		verts = []
		for p in mesh.points:
			verts.append(bm.verts.new(p))
		edges = [[0,1],[1,2],[2,3],[3,0]]
		for s in mesh.simplices:
			for e in edges:
				v = Vector(mesh.points[s[e[0]]]) - Vector(mesh.points[s[e[1]]])
				edge = [verts[s[e[0]]],verts[s[e[1]]]]
				try:
					bm.edges.new(edge)
				except:
					pass
		me = self.meshes.new('PointsMesh')
		obj = self.objects.new(name, me)
		bm.to_mesh(me)
		bm.free()
		self.scene.collection.objects.link(obj)
		return obj
	#
	# Join a list a objects
	#
	def join(self,llista):
		"""
		Joins a list of objects
		Parameters:
		   llista: list of objects
		"""
		if len(llista) == 0:
			return
		if len(llista) == 1:
			return llista[0]
		bpy.ops.object.select_all(action='DESELECT')
		bpy.context.view_layer.objects.active = llista[0]
		for obj in llista:
			obj.select_set(True)
		bpy.ops.object.join()
		bpy.ops.object.select_all(action='DESELECT')
		return llista[0]
	#
	# Vectors to quaternion
	#
	def vectors_to_quaternion(self,u1=Vector([1,0,0]),u2=Vector([0,1,0])):
		"""
		Returns the quaternion correspondint to the base {v1,v2,v3}
		u1, u2: the principal basis {v1, v2, v3} is constructed from this vectors in the following way
		       v1 = u1
			   v2 = u2 - u2.project(v1)
			   v1.normalize()
			   v2.normalize()
			   v3 = v1.cross(v2)
		"""
		if isinstance(u1,Vector):
			v1 = u1
		else:
			v1 = Vector(u1)
		if isinstance(u2,Vector):
			v2 = u2
		else:
			v2 = Vector(u2)
		v2 = v2 - v2.project(v1)
		v1.normalize()
		v2.normalize()
		v3 = v1.cross(v2)
		mat = Matrix([v1,v2,v3])
		mat.transpose()
		return mat.to_quaternion()
	#
	# Draw an ellpsoid
	#
	def ellipsoid(self,o=[0,0,0],u1=[1,0,0],u2=[0,1,0],a2=1,b2=1,c2=1,principal=True,canonica=True,color="AzureBlueDark",name="Ellipsoid",cmax=15,pmax=15,thickness=0.02,opacity=1.0,preserve=True):
		"""
		Draws an ellipsoid
		Parameters:
		   o: center of the ellipsoid

		   u1, u2: the principal basis {v1, v2, v3} is constructed from this vectors in the following way
		       v1 = u1
			   v2 = u2 - u2.project(v1)
			   v1.normalize()
			   v2.normalize()
			   v3 = v1.cross(v2)

		   a2, b2, c2: squares of semi-axes of the ellipsoid. The equation is x'^2/a^2 + y'^2/b^2 + z'^2/c^2 = 1

		   principal: if True, the principal axis are drawn

		   canonica: if True, the canonical axis are drawn

		   color: color of the surface

		   name: name of the ellipsoid

		   cmax: the canonical axis are drawn between -cmax and cmax

		   pmax: the principal axis are drawn between -pmax and pmax

		   thickness: thickness of the ellipsoid

		   opacity: opaccity of the ellipsoid

		   preserve: Keep self.origin and self.base as the principal reference
		"""
		axis1 = None
		axis2 = None
		q = self.vectors_to_quaternion(u1,u2)
		u = Quaternion([1,0,0,0])
		orig = [0,0,0]
		if q != u or o != orig:
			if canonica:
				if principal:
					self.colors = Colors.colors(["White","White","White"])
				else:
					self.colors = Colors.colors(["Red","Green","Blue"])
				self.draw_base_axis(axis = cmax,positive=False,name="Referència canònica")
				self.colors = Colors.colors(["Red","Green","Blue"])
		elif canonica and not principal:
			axis1 = self.draw_base_axis(axis = cmax,positive=False,name="Referència canònica")
		self.set_origin(o)
		self.set_rotation(quaternion=q)
		if principal:
			axis2 = self.draw_base_axis(axis = pmax,positive=False,name="Referència principal")
		a = math.sqrt(a2)
		b = math.sqrt(b2)
		c = math.sqrt(c2)
		el = self.draw_ellipsoid(radius=1,scale=[a,b,c],color=color,name=name,thickness=thickness,opacity=opacity)
		if not preserve:
			self.set_origin()
			self.set_base()
			self.set_rotation()
		return axis1, axis2, el
	#
	#
	#
	def sphere(self,o=[0,0,0],r2=1,principal=True,canonica=True,color="AzureBlueDark",name="Sphere",cmax=15,pmax=15,thickness=0.02,opacity=1.0,preserve=True):
		"""
		Draws a sphere of center 'o' and radius squared equal to 'r2'
		Parameters:
		   o: center of the sphere

		   r2: radius of the sphere squared

		   principal: if True, the principal axis are drawn

		   canonica: if True, the canonical axis are drawn

		   color: color of the surface

		   name: name of the sphere

		   cmax: the canonical axis are drawn between -cmax and cmax

		   pmax: the principal axis are drawn between -cmax and cmax

		   thickness: thickness of the sphere

		   opacity: opacity of the sphere

		   preserve: Keep self.origin and self.base as the principal reference
		"""
		u1 = Vector([1,0,0])
		u2 = Vector([0,1,0])
		return self.ellipsoid(o=o,u1=u1,u2=u2,a2=r2,b2=r2,c2=r2,principal=principal,canonica=canonica,color=color,name=name,cmax=cmax,pmax=pmax,thickness=thickness,opacity=opacity,preserve=preserve)
	#
	#
	#
	def one_sheet_hyperboloid(self,o=[0,0,0],u1=[1,0,0],u2=[0,1,0],a2=1,b2=1,c2=1,principal=True,canonica=True,color="AzureBlueDark",name="OneSheetHyperboloid",xmax=None,cmax=15,pmax=15,thickness=0.02,opacity=1.0,preserve=True):
		"""
		Draws an one sheet hyperboloid
		Parameters:
		   o: center of the hyperboloid

		   u1, u2: the principal basis {v1, v2, v3} is constructed from this vectors

		   a2, b2, c2: squares of semi-axes of the hyperboloid. The equation is x'^2/a^2 + y'^2/b^2 - z'^2/c^2 = 1

		   principal: if True, the principal axis are drawn

		   canonica: if True, the canonical axis are drawn

		   color: color of the surface

		   name: name of the hyperboloid

		   xmax: maximum value of the x coordinate

		   cmax: the canonical axis are drawn between -cmax and cmax

		   pmax: the principal axis are drawn between -cmax and cmax

		   thickness: thickness of the hyperboloid

		   opacity: opacity of the hyperboloid

		   preserve: Keep self.origin and self.base as the principal reference
		"""
		axis1 = None
		axis2 = None
		q = self.vectors_to_quaternion(u1,u2)
		u = Quaternion([1,0,0,0])
		orig = [0,0,0]
		if q != u or o != orig:
			if canonica:
				if principal:
					self.colors = Colors.colors(["White","White","White"])
				else:
					self.colors = Colors.colors(["Red","Green","Blue"])
				axis1 = self.draw_base_axis(axis = cmax,positive=False,name="Referència canònica")
				self.colors = Colors.colors(["Red","Green","Blue"])
		elif canonica and not principal:
			axis1 = self.draw_base_axis(axis = cmax,positive=False,name="Referència canònica")
		self.set_origin(o)
		self.set_rotation(quaternion=q)
		if principal:
			axis2 = self.draw_base_axis(axis = pmax,positive=False,name="Referència principal")
		a = math.sqrt(a2)
		b = math.sqrt(b2)
		c = math.sqrt(c2)
		if xmax is None:
			xmax=10.0/a + 2
		xmax /= a
		hy = self.draw_one_sheet_hyperboloid(a=1.0,b=1.0,xmin=1.0,xmax=xmax,scale=[a,b,c],color=color,name=name,thickness=thickness,opacity=opacity)
		if not preserve:
			self.set_origin()
			self.set_base()
			self.set_rotation()
		return axis1, axis2, hy
	#
	#
	#
	def two_sheets_hyperboloid(self,o=[0,0,0],u1=[1,0,0],u2=[0,1,0],a2=1,b2=1,c2=1,principal=True,canonica=True,color="AzureBlueDark",name="TwoSheetParaboloid",xmax=None,cmax=15,pmax=15,thickness=0.02,opacity=1.0,preserve=True):
		"""
		Draws a two sheets hyperboloid
		Parameters:
		   o: center of the hyperboloid

		   u1, u2: the principal basis {v1, v2, v3} is constructed from this vectors

		   a2, b2, c2: squares of semi-axes of the hyperboloid. The equation is x'^2/a^2 + y'^2/b^2 - z'^2/c^2 = -1

		   principal: if True, the principal axis are drawn

		   canonica: if True, the canonical axis are drawn

		   color: color of the surface

		   name: name of the hyperboloid

		   xmax: maximum value of the x coordinate

		   cmax: the canonical axis are drawn between -cmax and cmax

		   pmax: the principal axis are drawn between -cmax and cmax

		   thickness: thickness of the hyperboloid

		   opacity: opacity of the hyperboloid

		   preserve: Keep self.origin and self.base as the principal reference
		"""
		axis1 = None
		axis2 = None
		q = self.vectors_to_quaternion(u1,u2)
		u = Quaternion([1,0,0,0])
		orig = [0,0,0]
		if q != u or o != orig:
			if canonica:
				if principal:
					self.colors = Colors.colors(["White","White","White"])
				else:
					self.colors = Colors.colors(["Red","Green","Blue"])
				axis1 = self.draw_base_axis(axis = cmax,positive=False,name="Referència canònica")
				self.colors = Colors.colors(["Red","Green","Blue"])
		elif canonica and not principal:
			axis1 = self.draw_base_axis(axis = cmax,positive=False,name="Referència canònica")
		self.set_origin(o)
		self.set_rotation(quaternion=q)
		if principal:
			axis2 = self.draw_base_axis(axis = pmax,positive=False,name="Referència principal")
		a = math.sqrt(a2)
		b = math.sqrt(b2)
		c = math.sqrt(c2)
		if xmax is None:
			xmax = 5.0/a + 2
		xmax /= a
		hy = self.draw_two_sheets_hyperboloid(a=1.0,b=1.0,xmin=0.0,xmax=xmax,color=color,scale=[a,b,c],name=name,thickness=thickness,opacity=opacity)
		if not preserve:
			self.set_origin()
			self.set_base()
			self.set_rotation()
		return axis1, axis2, hy
	#
	#
	#
	def cone(self,o=[0,0,0],u1=[1,0,0],u2=[0,1,0],a2=1,b2=1,c2=1,half=False,principal=True,canonica=True,color="AzureBlueDark",name="Cone",xmax=None,cmax=15,pmax=15,thickness=0.02,opacity=1.0,preserve=True):
		"""
		Draws a cone
		Parameters:
		   o: center of the cone

		   u1, u2: the principal basis {v1, v2, v3} is constructed from this vectors

		   a2, b2, c2: squares of semi-axes of the cone. The equation is x'^2/a^2 + y'^2/b^2 - z'^2/c^2 = 0

		   half: if True draws half cone

		   principal: if True, the principal axis are drawn

		   canonica: if True, the canonical axis are drawn

		   color: color of the surface

		   name: name of the cone

		   xmax: maximum value of the x coordinate

		   cmax: the canonical axis are drawn between -cmax and cmax

		   pmax: the principal axis are drawn between -pmax and pmax

		   thickness: thickness of the cone

		   opacity: opacity of the cone

		   preserve: Keep self.origin and self.base as the principal reference
		"""
		axis1 = None
		axis2 = None
		q = self.vectors_to_quaternion(u1,u2)
		u = Quaternion([1,0,0,0])
		orig = [0,0,0]
		if q != u or o != orig:
			if canonica:
				if principal:
					self.colors = Colors.colors(["White","White","White"])
				else:
					self.colors = Colors.colors(["Red","Green","Blue"])
				axis1 = self.draw_base_axis(axis = cmax,positive=False,name="Referència canònica")
				self.colors = Colors.colors(["Red","Green","Blue"])
		elif canonica and not principal:
			axis1 = self.draw_base_axis(axis = cmax,positive=False,name="Referència canònica")
		self.set_origin(o)
		self.set_rotation(quaternion=q)
		if principal:
			self.draw_base_axis(axis = pmax,positive=False,name="Referència principal")
		a = math.sqrt(a2)
		b = math.sqrt(b2)
		c = math.sqrt(c2)
		if xmax is None:
			xmax = 10.0/a + 2
		xmax /= a
		co = self.draw_cone(a=1.0,xmin=0.0,xmax=xmax,steps=50,half=half,color=color,scale=[a,b,c],name=name,thickness=thickness,opacity=opacity)
		if not preserve:
			self.set_origin()
			self.set_base()
			self.set_rotation()
		return axis1, axis2, co
	#
	#
	#
	def hyperbolic_cylinder(self,o=[0,0,0],u1=[1,0,0],u2=[0,1,0],a2=1,b2=1,principal=True,canonica=True,color="AzureBlueDark",name="Hyperbolic Cylinder",xmax=None,zmax=15,cmax=15,pmax=15,thickness=0.02,opacity=1.0,preserve=True):
		"""
		Draws an hyperbolic cylinder
		Parameters:
		   o: center of the hyperbolic cylinder

		   u1, u2: the principal basis {v1, v2, v3} is constructed from this vectors

		   a2, b2: squares of semi-axes of the hyperbolic cylinder. The equation is x'^2/a^2 - y'^2/b^2 = 1

		   principal: if True, the principal axis are drawn

		   canonica: if True, the canonical axis are drawn

		   color: color of the surface

		   name: name of the hyperbolic cylinder

		   xmax: maximum value of the x coordinate

		   zmax: the hyperbolic cylinder is drawn between -zmax and zmax

		   cmax: the canonical axis are drawn between -cmax and cmax

		   pmax: the principal axis are drawn between -cmax and cmax

		   thickness: thickness of the hyperbolic cylinder

		   opacity: opacity of the hyperbolic cylinder

		   preserve: Keep self.origin and self.base as the principal reference
		"""
		if cmax < zmax + 2:
			cmax = zmax + 2
		axis1 = None
		axis2 = None
		q = self.vectors_to_quaternion(u1,u2)
		u = Quaternion([1,0,0,0])
		orig = [0,0,0]
		if q != u or o != orig:
			if canonica:
				if principal:
					self.colors = Colors.colors(["White","White","White"])
				else:
					self.colors = Colors.colors(["Red","Green","Blue"])
				axis1 = self.draw_base_axis(axis = cmax,positive=False,name="Referència canònica")
				self.colors = Colors.colors(["Red","Green","Blue"])
		elif canonica and not principal:
			axis1 = self.draw_base_axis(axis = cmax,positive=False,name="Referència canònica")
		self.set_origin(o)
		self.set_rotation(quaternion=q)
		if principal:
			axis2 = self.draw_base_axis(axis = pmax,positive=False,name="Referència principal")
		a = math.sqrt(a2)
		b = math.sqrt(b2)
		if xmax is None:
			xmax = 5.0/a + 2
		xmax /= a
		hy = self.draw_hyperbolic_cylinder(a=1.0,b=1.0,xmin=1.0,xmax=xmax,length=2*zmax,steps=128,color=color,name=name,scale=[a,b,1],thickness=thickness,opacity=opacity)
		if not preserve:
			self.set_origin()
			self.set_base()
			self.set_rotation()
		return axis1, axis2, hy
	#
	#
	#
	def elliptic_cylinder(self,o=[0,0,0],u1=[1,0,0],u2=[0,1,0],a2=1,b2=1,principal=True,canonica=True,color="AzureBlueDark",name="EllipticCylinder",zmax=20,cmax=20,pmax=15,thickness=0.02,opacity=1.0,preserve=True):
		"""
		Draws an elliptic cylinder
		Parameters:
		   o: center of the elliptic cylinder

		   u1, u2: the principal basis {v1, v2, v3} is constructed from this vectors

		   a2, b2: squares of semi-axes of the elliptic cylinder. The equation is x'^2/a^2 + y'^2/b^2 = 1

		   principal: if True, the principal axis are drawn

		   canonica: if True, the canonical axis are drawn

		   color: color of the surface

		   name: name of the elliptic cylinder

		   zmax: the elliptic cylinder is drawn between -zmax and zmax

		   cmax: the canonical axis are drawn between -cmax and cmax

		   pmax: the principal axis are drawn between -cmax and cmax

		   thickness: thickness of the elliptic cylinder

		   opacity: opacity of the elliptic cylinder

		   preserve: Keep self.origin and self.base as the principal reference
		"""
		axis1 = None
		axis2 = None
		if cmax < zmax + 2:
			cmax = zmax + 2
		q = self.vectors_to_quaternion(u1,u2)
		u = Quaternion([1,0,0,0])
		orig = [0,0,0]
		if q != u or o != orig:
			if canonica:
				if principal:
					self.colors = Colors.colors(["White","White","White"])
				else:
					self.colors = Colors.colors(["Red","Green","Blue"])
				axis1 = self.draw_base_axis(axis = cmax,positive=False,name="Referència canònica")
				self.colors = Colors.colors(["Red","Green","Blue"])
		elif canonica and not principal:
			axis1 = self.draw_base_axis(axis = cmax,positive=False,name="Referència canònica")
		self.set_origin(o)
		self.set_rotation(quaternion=q)
		if principal:
			axis2 = self.draw_base_axis(axis = pmax,positive=False,name="Referència principal")
		a = math.sqrt(a2)
		b = math.sqrt(b2)
		el = self.draw_elliptic_cylinder(a=1.0,b=1.0,length=2*zmax,color=color,name=name,scale=[a,b,1],thickness=thickness,opacity=opacity)
		if not preserve:
			self.set_origin()
			self.set_base()
			self.set_rotation()
		return axis1, axis2, el
	#
	#
	#
	def elliptic_paraboloid(self,o=[0,0,0],u1=[1,0,0],u2=[0,1,0],a2=1,b2=1,principal=True,canonica=True,color="AzureBlueDark",name="EllipticParaboloid",xmax=None,cmax=15,pmax=15,thickness=0.02,opacity=1.0,preserve=True):
		"""
		Draws an elliptic paraboloid
		Parameters:
		   o: vertex of the elliptic paraboloid

		   u1, u2: the principal basis {v1, v2, v3} is constructed from this vectors

		   a2, b2: squares of semi-axes of the elliptic paraboloid. The equation is z = x'^2/a^2 + y'^2/b^2

		   principal: if True, the principal axis are drawn

		   canonica: if True, the canonical axis are drawn

		   color: color of the surface

		   name: name of the elliptic paraboloid

		   xmax: maximum value of the coordinate x

		   cmax: the canonical axis are drawn between -cmax and cmax

		   pmax: the principal axis are drawn between -cmax and cmax

		   thickness: thickness of the elliptic paraboloid

		   opacity: opacity of the elliptic paraboloid

		   preserve: Keep self.origin and self.base as the principal reference
		"""
		axis1 = None
		axis2 = None
		q = self.vectors_to_quaternion(u1,u2)
		u = Quaternion([1,0,0,0])
		orig = [0,0,0]
		if q != u or o != orig:
			if canonica:
				if principal:
					self.colors = Colors.colors(["White","White","White"])
				else:
					self.colors = Colors.colors(["Red","Green","Blue"])
				axis1 = self.draw_base_axis(axis = cmax,positive=False,name="Referència canònica")
				self.colors = Colors.colors(["Red","Green","Blue"])
		elif canonica and not principal:
			axis1 = self.draw_base_axis(axis = cmax,positive=False,name="Referència canònica")
		self.set_origin(o)
		self.set_rotation(quaternion=q)
		if principal:
			axis2 = self.draw_base_axis(axis = pmax,positive=False,name="Referència principal")
		a = math.sqrt(a2)
		b = math.sqrt(b2)
		if xmax is None:
			xmax = 10.0/a
		xmax /= a
		el = self.draw_elliptic_paraboloid(a=1.0,xmin=0.0,xmax=xmax,steps=50,scale=[a,b,1],color=color,name=name,opacity=opacity,thickness=thickness)
		if not preserve:
			self.set_origin()
			self.set_base()
			self.set_rotation()
		return axis1, axis2, el
	#
	#
	#
	def hyperbolic_paraboloid(self,o=[0,0,0],u1=[1,0,0],u2=[0,1,0],a2=1,b2=1,principal=True,canonica=True,color="AzureBlueDark",name="HyperbolicParaboloid",xmax=None,ymax=None,cmax=15,pmax=15,thickness=0.02,opacity=1.0,preserve=True):
		"""
		Draws an hyperbolic paraboloid
		Parameters:
		   o: vertex of the hyperbolic paraboloid

		   u1, u2: the principal basis {v1, v2, v3} is constructed from this vectors

		   a2, b2: squares of semi-axes of the hyperbolic paraboloid. The equation is z = x'^2/a^2 - y'^2/b^2

		   principal: if True, the principal axis are drawn

		   canonica: if True, the canonical axis are drawn

		   color: color of the surface

		   name: name of the elliptic paraboloid

		   xmax: maximum value of the coordinate x

		   ymax: maximum value of the coordinate y

		   cmax: the canonical axis are drawn between -cmax and cmax

		   pmax: the principal axis are drawn between -cmax and cmax

		   thickness: thickness of the hyperbolic paraboloid

		   opacity: opacity of the hyperbolic paraboloid

		   preserve: Keep self.origin and self.base as the principal reference
		"""
		axis1 = None
		axis2 = None
		a = math.sqrt(a2)
		b = math.sqrt(b2)
		if xmax is None:
			xmax = 10.0/a + 2
		if ymax is None:
			ymax = 10.0/b + 1
		xmax /= a
		ymax /= b
		hy = self.draw_hyperbolic_paraboloid(a=1.0,b=1.0,xmax=xmax,ymax=ymax,color=color,name=name,scale=[a,b,1],thickness=thickness,opacity=opacity)

		q = self.vectors_to_quaternion(u1,u2)
		u = Quaternion([1,0,0,0])
		orig = [0,0,0]
		if q != u or o != orig:
			if canonica:
				if principal:
					self.colors = Colors.colors(["White","White","White"])
				else:
					self.colors = Colors.colors(["Red","Green","Blue"])
				axis1 = self.draw_base_axis(axis = cmax,positive=False,name="Referència canònica")
				self.colors = Colors.colors(["Red","Green","Blue"])
		elif canonica and not principal:
			axis1 = self.draw_base_axis(axis = cmax,positive=False,name="Referència canònica")
		self.set_origin(o)
		self.set_rotation(quaternion=q)
		if principal:
			self.draw_base_axis(axis = pmax,positive=False,name="Referència principal")
		hy.rotation_mode = 'QUATERNION'
		if self.rotation is not None:
			hy.rotation_quaternion.rotate(self.rotation.quaternion)
			hy.location.rotate(self.rotation.quaternion)
		hy.location = o
		if not preserve:
			self.set_origin()
			self.set_base()
			self.set_rotation()
		return axis1, axis2, hy
	#
	#
	#
	def parabolic_cylinder(self,o=[0,0,0],u1=[1,0,0],u2=[0,1,0],p=1,principal=True,canonica=True,color="AzureBlueDark",name="ParabolicCylinder",xmax=12,ymax=30,cmax=20,pmax=20,thickness=0.02,opacity=1.0,preserve=True):
		"""
		Draws an hyperbolic paraboloid
		Parameters:
		   o: vertex of the hyperbolic paraboloid

		   u1, u2: the principal basis {v1, v2, v3} is constructed from this vectors

		   p: Parameter of the cylinder z' = x'^2/(2*p)

		   principal: if True, the principal axis are drawn

		   canonica: if True, the canonical axis are drawn

		   color: color of the surface

		   name: name of the elliptic paraboloid

		   xmax: maximum value of the coordinate x

		   ymax: maximum value of the coordinate y

		   cmax: the canonical axis are drawn between -cmax and cmax

		   pmax: the principal axis are drawn between -cmax and cmax

		   thickness: thickness of the hyperbolic paraboloid

		   opacity: opacity of the hyperbolic paraboloid

		   preserve: Keep self.origin and self.base as the principal reference
		"""
		axis1 = None
		axis2 = None
		q = self.vectors_to_quaternion(u1,u2)
		u = Quaternion([1,0,0,0])
		orig = [0,0,0]
		if q != u or o != orig:
			if canonica:
				if principal:
					self.colors = Colors.colors(["White","White","White"])
				else:
					self.colors = Colors.colors(["Red","Green","Blue"])
				axis1 = self.draw_base_axis(axis = cmax,positive=False,name="Referència canònica")
				self.colors = Colors.colors(["Red","Green","Blue"])
		elif canonica and not principal:
			axis1 = self.draw_base_axis(axis = cmax,positive=False,name="Referència canònica")
		self.set_origin(o)
		self.set_rotation(quaternion=q)
		if principal:
			axis2 = self.draw_base_axis(axis = pmax,positive=False,name="Referència principal")
		coef = 1.0
		if p < 0:
			coef = -1
		xmax /= math.sqrt(2*coef*p)
		pa = self.draw_parabolic_cylinder(p=coef,xmin=0.0,xmax=xmax,length=ymax,color=color,name=name,scale=[math.sqrt(2*coef*p),1,1],thickness=thickness,opacity=opacity)
		if not preserve:
			self.set_origin()
			self.set_base()
			self.set_rotation()
		return axis1, axis2, pa
	#
	#
	#
	def draw_simple_curve(self,fun=None,tmin=0.0,tmax=1.0,steps=25,thickness=0.02,color="White",name="Curve"):
		"""
		Draws a parametric curve
		Parameters:
		   fun: the parametric function

		   tmin: minimum value of the parameter

		   tmax: maximum value of the parameter

		   steps: number of steps

		   thickness: thickness of the curve

		   color: color of the curve

		   name: name of the curve
		"""
		if fun is None:
			return None
		delta = (tmax - tmin) / steps
		t = tmin

		curve = bpy.data.curves.new('myCurve', type='CURVE')
		curve.dimensions = '3D'
		curve.resolution_u = 2

		line = curve.splines.new('POLY')
		line.points.add(steps)

		for i in range(steps+1):
			p = fun(t)
			p.append(1)
			line.points[i].co = p
			t += delta

		obj = bpy.data.objects.new(name, curve)
		curve.bevel_depth = thickness

		modifier = obj.modifiers.new(name="SubSurf", type='SUBSURF')
		modifier.levels = 4
		modifier.subdivision_type = 'SIMPLE'
		c = Colors.color(color)
		self.add_material(obj,c.name,c.r,c.g,c.b,1.0)
		self.scene.collection.objects.link(obj)
		return obj
	#
	#
	#
	def draw_curve(self,fun=None,tmin=0.0,tmax=1.0,steps=25,thickness=0.01,name="Curve",color="White",axis=False,zaxis=True,o=Vector([0,0,0]),u1=Vector([1,0,0]),u2=Vector([0,1,0])):
		"""
		Draws a curve in a reference R' determined by the origin o and basis {v1, v2, v3} constructed from u1 and u2
		Parameters:
		   fun: the parametric function

		   tmin: minimum value of the parameter

		   tmax: maximum value of the parameter

		   steps: number of steps

		   thickness: thickness of the curve

		   name: name of the curve

		   color: color of the curve

		   axis: if True draws the axis of the reference R'

		   zaxis: if True draws the z' axis

		   o: origin of the reference R'

		   u1, u2: vectors to construct the basis {v1, v2, v3}
		"""
		if fun is None:
			return None
		qt = self.vectors_to_quaternion(u1,u2)
		delta = (tmax - tmin) / steps
		t = tmin
		bm = bmesh.new()
		verts = []

		pmax = 0
		for k in range(steps + 1):
			p = fun(t)
			m = max(map(abs,p))
			if m > pmax:
				pmax = m
			verts.append(bm.verts.new(p))
			t += delta
			if t > tmax:
				t = tmax

		for i in range(len(verts) - 1):
			bm.edges.new([verts[i], verts[i+1]])

		me = self.meshes.new('placeholder_mesh')
		obj = self.objects.new(name,me)
		bm.to_mesh(me)
		bm.free()

		modifier = obj.modifiers.new(type='SKIN',name = 'skin')
		for v in obj.data.skin_vertices[0].data:
			v.radius = (thickness,thickness)

		modifier = obj.modifiers.new(name="SubSurf", type='SUBSURF')
		modifier.levels = 4
		modifier.subdivision_type = 'SIMPLE'
		if thickness > 0.0:
			modifier = obj.modifiers.new(name="Solidify", type='SOLIDIFY')
			modifier.thickness = thickness
			modifier.offset = 1.0
		c = Colors.color(color)
		self.add_material(obj,c.name,c.r,c.g,c.b,1.0)
		self.set_origin(o)
		self.set_rotation(quaternion=qt)
		if self.rotation is not None:
			obj.rotation_mode = 'QUATERNION'
			obj.rotation_quaternion.rotate(self.rotation.quaternion)
			obj.location.rotate(self.rotation.quaternion)
		if axis:
			self.draw_base_axis(axis = pmax+3,positive=False,name="Referència escollida",zaxis=zaxis)
		self.scene.collection.objects.link(obj)
		bpy.ops.object.shade_smooth()
		obj.location = o
		bpy.context.view_layer.objects.active = None
		return obj
	#
	#
	#
	def draw_disk(self,center=Vector([0,0,0]),radius=5,u1=Vector([1,0,0]),u2=Vector([0,1,0]),thickness=0.01,name="Disc",color="AzureBlueDark"):
		"""
		Draws a disc in a reference R' determined by self.origin and self.base
		Parameters:
		   radius: radius of the disc

		   thickness: thickness of the surface

		   name: name of the curve

		   color: color of the curve
		"""
		self.base_disk()
		t = bpy.data.objects.get("Base_disk")
		obj = t.copy()
		obj.name = name
		self.delete_base_disk()
		if radius != 1.0:
			obj.scale = (radius,radius,1)
		modifier = obj.modifiers.new(name="SubSurf", type='SUBSURF')
		modifier.levels = 4
		modifier.subdivision_type = 'SIMPLE'
		if thickness > 0.0:
			modifier = obj.modifiers.new(name="Solidify", type='SOLIDIFY')
			modifier.thickness = thickness
			modifier.offset = 1.0
		c = Colors.color(color)
		self.add_material(obj,c.name,c.r,c.g,c.b,1.0)
		qt = self.vectors_to_quaternion(u1,u2)
		self.set_rotation(quaternion=qt)
		if self.rotation is not None:
			obj.rotation_mode = 'QUATERNION'
			obj.rotation_quaternion.rotate(self.rotation.quaternion)
			### obj.location.rotate(self.rotation.quaternion)
		obj.location = center
		self.scene.collection.objects.link(obj)
		bpy.ops.object.shade_smooth()
		bpy.context.view_layer.objects.active = None
		obj.select_set(False)
		return obj
	#
	#
	#
	def curve(self,fun=None,tmin=0.0,tmax=1.0,steps=25,thickness=0.01,name="Curve",color="White",axis=False,zaxis=True,o=Vector([0,0,0]),u1=Vector([1,0,0]),u2=Vector([0,1,0]),symmetry=None,change=False):
		"""
		Draws a curve in a reference R' determined by the origin o and basis {v1, v2, v3} constructed from u1 and u2 and
		the symmetric curve or curves from the parameter 'symmetry'
		Parameters:
		   fun: the parametric function

		   tmin: minimum value of the parameter

		   tmax: maximum value of the parameter

		   steps: number of steps

		   thickness: thickness of the curve

		   name: name of the curve

		   color: color of the curve

		   axis: if True draws the axis of the reference R'

		   zaxis: if True draws the z' axis

		   o: origin of the reference R'

		   u1, u2: vectors to construct the basis {v1, v2, v3}

		   symmetry: list of values in ('XY','XZ','YZ','X','Y','Z','O'). For every value S, draw the symmetric curve respect to S

		   change: if True, set the reference self.origin, self.base to {o; v1, v2, v3}
		"""
		if fun is None:
			return None
		obj = self.draw_curve(fun,tmin=tmin,tmax=tmax,steps=steps,thickness=thickness,name=name,color=color,axis=axis,zaxis=zaxis,o=o,u1=u1,u2=u2)

		if symmetry is None:
			if change:
				self.set_origin(o)
				self.set_base([u1,u2],orthonormal=True)
			return obj
		objs = [obj]
		if isinstance(symmetry,str):
			symmetry = [symmetry]
		elif not isinstance(symmetry,list) and not isinstance(symmetry,tuple):
			if change:
				self.set_origin(o)
				self.set_base([u1,u2],orthonormal=True)
			return obj
		for s in symmetry:
			namem = name + s
			if s == 'XY':
				def f(t):
					p = fun(t)
					return (p[0],p[1],-p[2])
				obj2 = self.draw_curve(f,tmin=tmin,tmax=tmax,steps=steps,thickness=thickness,name=namem,color=color,axis=axis,zaxis=zaxis,o=o,u1=u1,u2=u2)
				objs.append(obj2)
			if s == 'XZ':
				def f(t):
					p = fun(t)
					return (p[0],-p[1],p[2])
				obj2 = self.draw_curve(f,tmin=tmin,tmax=tmax,steps=steps,thickness=thickness,name=namem,color=color,axis=axis,zaxis=zaxis,o=o,u1=u1,u2=u2)
				objs.append(obj2)
			if s == 'YZ':
				def f(t):
					p = fun(t)
					return (-p[0],p[1],p[2])
				obj2 = self.draw_curve(f,tmin=tmin,tmax=tmax,steps=steps,thickness=thickness,name=namem,color=color,axis=axis,zaxis=zaxis,o=o,u1=u1,u2=u2)
				objs.append(obj2)
			if s == 'X':
				def f(t):
					p = fun(t)
					return (p[0],-p[1],-p[2])
				obj2 = self.draw_curve(f,tmin=tmin,tmax=tmax,steps=steps,thickness=thickness,name=namem,color=color,axis=axis,zaxis=zaxis,o=o,u1=u1,u2=u2)
				objs.append(obj2)
			if s == 'Y':
				def f(t):
					p = fun(t)
					return (-p[0],p[1],-p[2])
				obj2 = self.draw_curve(f,tmin=tmin,tmax=tmax,steps=steps,thickness=thickness,name=namem,color=color,axis=axis,zaxis=zaxis,o=o,u1=u1,u2=u2)
				objs.append(obj2)
			if s == 'Z':
				def f(t):
					p = fun(t)
					return (-p[0],-p[1],p[2])
				obj2 = self.draw_curve(f,tmin=tmin,tmax=tmax,steps=steps,thickness=thickness,name=namem,color=color,axis=axis,zaxis=zaxis,o=o,u1=u1,u2=u2)
				objs.append(obj2)
			if s == 'O':
				def f(t):
					p = fun(t)
					return (-p[0],-p[1],-p[2])
				obj2 = self.draw_curve(f,tmin=tmin,tmax=tmax,steps=steps,thickness=thickness,name=namem,color=color,axis=axis,zaxis=zaxis,o=o,u1=u1,u2=u2)
				objs.append(obj2)
		if change:
			self.set_origin(o)
			self.set_base([u1,u2],orthonormal=True)
		return self.join(objs)
	#
	#
	#
	def draw_circle(self,center=[0,0,0],u1=Vector([1,0,0]),u2=Vector([0,1,0]),axis=False,zaxis=False,radius=1,steps=128,thickness=0.01,name="Circle",color="White",fillcolor=None,change=False):
		"""
		Draws a circle of center 'center' and radius 'radius' in the plane determined by vectors u1 and u2
		Parameters:
		   center: center of the circle

		   u1, u2: vectors to construct the basis {v1, v2, v3}

		   axis: if True draws the axis of the reference R'

		   zaxis: if True draws the z' axis

		   radius: radius of the circle

		   steps: number of steps

		   thickness: thickness of the curve

		   name: name of the curve

		   color: color of the curve

		   change: if True, set the reference self.orifin, self.base to {o; v1, v2, v3}
		"""
		d = None
		if fillcolor is not None:
			d = self.draw_disk(center=center,radius=radius,u1=u1,u2=u2,thickness=0.5*thickness,name="Disc",color=fillcolor)
		c = self.draw_curve(lambda t: (radius*math.cos(t),radius*math.sin(t),0),tmin=0.0,tmax=2*math.pi,axis=axis,zaxis=zaxis,steps=steps,thickness=thickness,name=name,color=color,o=center,u1=u1,u2=u2)
		if change:
			self.set_origin(center)
			self.set_base([u1,u2],orthonormal=True)
		return c, d
	#
	#
	#
	def draw_ellipse(self,center=[0,0,0],u1=Vector([1,0,0]),u2=Vector([0,1,0]),a=1,b=1,axis=False,zaxis=False,steps=25,thickness=0.01,name="Ellipse",color="White",change=False):
		"""
		Draws an ellipse of center 'center' and semi-axes a and b in the plane determined by vectors u1 and u2
		Parameters:
		   center: center of the ellipse

		   u1, u2: vectors to construct the basis {v1, v2, v3}

		   a, b: semi-axes of the ellipse

		   axis: if True draws the axis of the reference R'

		   zaxis: if True draws the z' axis

		   steps: number of steps

		   thickness: thickness of the curve

		   name: name of the curve

		   color: color of the curve

		   change: if True, set the reference self.orifin, self.base to {o; v1, v2, v3}
		"""
		if change:
			self.set_origin(center)
			self.set_base([u1,u2],orthonormal=True)
		return self.draw_curve(lambda t: (a*math.cos(t),b*math.sin(t),0),tmin=0.0,tmax=2*math.pi,axis=axis,zaxis=zaxis,steps=steps,thickness=thickness,name=name,color=color,o=center,u1=u1,u2=u2)
	#
	#
	#
	def draw_parabola(self,vertex=[0,0,0],u1=Vector([1,0,0]),u2=Vector([0,1,0]),a=1,xmax=3.0,axis=False,zaxis=False,steps=25,thickness=0.01,name="Parabola",color="White",change=False):
		"""
		Draws a parabola of vertex 'vertex' of equation y'=ax'^2 in the reference {vertex; v1, v2, v3} determined by vectors u1 and u2
		Parameters:
		   vertex: vertex of the parabola

		   u1, u2: vectors to construct the basis {v1, v2, v3}

		   a: coefficient of the parabola

		   xmax: maximum value of x'

		   axis: if True draws the axis of the reference R'

		   zaxis: if True draws the z' axis

		   steps: number of steps

		   thickness: thickness of the curve

		   name: name of the curve

		   color: color of the curve

		   change: if True, set the reference self.orifin, self.base to {o; v1, v2, v3}
		"""
		if change:
			self.set_origin(vertex)
			self.set_base([u1,u2],orthonormal=True)
		return self.draw_curve(lambda t: (t,a*t**2,0),tmin=-xmax,tmax=xmax,axis=axis,zaxis=zaxis,steps=steps,thickness=thickness,name=name,color=color,o=vertex,u1=u1,u2=u2)
	#
	#
	#
	def draw_hyperbole(self,center=[0,0,0],u1=Vector([1,0,0]),u2=Vector([0,1,0]),a=1,b=1,ymax=3.0,axis=False,zaxis=False,steps=25,thickness=0.01,name="Hyperbole",color="White",change=False):
		"""
		Draws an hyperbole of center 'center' and semi-axes a and b in the plane determined by vectors u1 and u2
		Parameters:
		   center: center of the hyperbole

		   u1, u2: vectors to construct the basis {v1, v2, v3}

		   a, b: semi-axes of the hyperbole

		   ymax: maximum value of the y'

		   axis: if True draws the axis of the reference R'

		   zaxis: if True draws the z' axis

		   steps: number of steps

		   thickness: thickness of the curve

		   name: name of the curve

		   color: color of the curve

		   change: if True, set the reference self.origin, self.base to {o; v1, v2, v3}
		"""
		c1 = self.draw_curve(lambda t: (a*math.sqrt(1+t**2/b**2),t,0),tmin=-ymax,tmax=ymax,axis=axis,zaxis=zaxis,steps=steps,thickness=thickness,name=name,color=color,o=center,u1=u1,u2=u2)
		c2 = self.draw_curve(lambda t: (-a*math.sqrt(1+t**2/b**2),t,0),tmin=-ymax,tmax=ymax,axis=False,zaxis=False,steps=steps,thickness=thickness,name=name,color=color,o=center,u1=u1,u2=u2)
		self.join([c1,c2])
		if change:
			self.set_origin(center)
			self.set_base([u1,u2],orthonormal=True)
		return c1
	#
	#
	#
	def draw_surface(self,eq=None,umin=-1,umax=1,usteps=64,vmin=-1,vmax=1,vsteps=64,thickness=0.02,opacity=1.0,pmax=10,name="Surface",color="AzureBlueDark",axis=False,o=Vector([0,0,0]),u1=Vector([1,0,0]),u2=Vector([0,1,0]),wrap_u=False,wrap_v=False,close_v=False):
		"""
		Draws a parametric surface in the reference R'
		Parameters:
		   eq: parametric equacion f(u,v)

		   umin: minimum value of u

		   umax: maximum value of u

		   usteps: steps in the u direction

		   vmin: minimum value of v

		   vmax: maximum value of v

		   vsteps: steps in the v direction

		   thickness: thickness of the surface

		   opacity: opacity of the surface

		   color: color of the surface

		   pmax: the principal axis are drawn between -cmax and cmax

		   name: name of the surface

		   color: color of the surface

		   axis: if True draw the axis of the reference {o, v1, v2, v3}

		   o: origin of the reference R'

		   u1, u2: vectors to construct the basis {v1, v2, v3}

		   scale: scale coefficients

		   wrap_u: wrap the u coordinate

		   wrap_v: wrap the u coordinate

		   close_v: close the v coordinate
		"""
		if eq is None:
			return

		q = self.vectors_to_quaternion(u1,u2)
		draw_parametric_surface(eq=eq,range_u_min=umin,range_u_max=umax,range_u_step=usteps,range_v_min=vmin,range_v_max=vmax,range_v_step=vsteps,name=name,wrap_u=wrap_u,wrap_v=wrap_v,close_v=close_v)

		bpy.context.object.name = name
		obj = bpy.data.objects.get(name)
		obj.show_wire = False

		modifier = obj.modifiers.new(name="SubSurf", type='SUBSURF')
		modifier.levels = 4
		modifier.subdivision_type = 'SIMPLE'
		if thickness > 0.0:
			modifier = obj.modifiers.new(name="Solidify", type='SOLIDIFY')
			modifier.thickness = thickness
			modifier.offset = 1.0
		c = Colors.color(color)
		self.add_material(obj,c.name,c.r,c.g,c.b,opacity)
		self.set_origin(o)
		self.set_rotation(quaternion=q)
		if self.rotation is not None:
			obj.rotation_mode = 'QUATERNION'
			obj.rotation_quaternion.rotate(self.rotation.quaternion)
			obj.location.rotate(self.rotation.quaternion)
		if axis:
			self.draw_base_axis(axis = pmax,positive=False,name="Referència escollida")

		bpy.ops.object.shade_smooth()
		obj.location = o
		obj.select_set(False)
		bpy.context.view_layer.objects.active = None
		return obj
	#
	#
	#
	def draw_function(self,f=None,xmin=-3,xmax=3,xsteps=64,ymin=-3,ymax=3,ysteps=64,thickness=0.02,opacity=1.0,pmax=10,name="Function",color="AzureBlueDark",axis=False,o=Vector([0,0,0]),u1=Vector([1,0,0]),u2=Vector([0,1,0])):
		"""
		Draws a function of two variables f(x,y) i the reference R' = {o, v1, v2, v3}
		Parameters:
		   f: the function of two variables f(x,y)

		   xmin: minimum value of x

		   xmax: maximum value of x

		   xsteps: steps in the x direction

		   ymin: minimum value of y

		   ymax: maximum value of y

		   ysteps: steps in the x direction

		   thickness: thickness of the surface

		   opacity: opacity of the surface

		   pmax: the axis are drawn between -pmax and pmax

		   name: name of the surface

		   color: color of the surface

		   axis: if True the axis of the reference R' are drawn

		   o: origin of the reference R'

		   u1, u2: vectors to construct the basis {v1, v2, v3}
		"""
		if f is None:
			return None
		return self.draw_surface(eq=lambda x,y:(x,y,f(x,y)),umin=xmin,umax=xmax,usteps=xsteps,vmin=ymin,vmax=ymax,vsteps=ysteps,thickness=thickness,opacity=opacity,pmax=pmax,name=name,color=color,axis=axis,o=o,u1=u1,u2=u2,wrap_u=False,wrap_v=False,close_v=False)
	#
	#
	#
	def draw_vector_field(self,f=None,xmin=-3,xmax=3,xsteps=8,ymin=-3,ymax=3,ysteps=8,zmin=-3,zmax=3,zsteps=8,name="Vector Field",color="Red",scale=0.02,head_height=0.05):
		"""
		Draws a vector field
		Parameters:
		   f: the vector field

		   xmin: minimum value of x

		   xmax: maximum value of x

		   xsteps: steps in the x direction

		   ymin: minimum value of y

		   ymax: maximum value of y

		   ysteps: steps in the y direction

		   zmin: minimum value of z

		   zmax: maximum value of z

		   zsteps: steps in the z direction

		   name: name of the vector field

		   color: color of the vector field

		   scale: scale of the vectors

		   head_height: head height of the vectors
		"""
		if f is None:
			return None
		xstep = (xmax - xmin)/xsteps
		ystep = (ymax - ymin)/ysteps
		zstep = (zmax - zmin)/zsteps
		if xstep == 0 or ystep == 0 or zstep == 0:
			return None
		vectors = []
		count = 1
		x = xmin
		while x <= xmax:
			y = ymin
			while y <= ymax:
				z = zmin
				while z <= zmax:
					o = Vector([x,y,z])
					v = f(x,y,z)
					if not isinstance(v,Vector):
						v = Vector(v)
					self.set_origin(o)
					vec = self.draw_vector(v,color=color,name=f"Vector{count}",scale=scale,head_height=head_height)
					if vec is not None:
						vectors.append(vec)
					z += zstep
					count += 1
				y += ystep
			x += xstep
		v = self.join(vectors)
		bpy.context.object.name = name
		return v
	#
	#
	#
	def revolution_surface(self,fun=None,tmin=0.0,tmax=1.0,o=Vector([0,0,0]),u1=Vector([1,0,0]),u2=Vector([0,1,0]),pmax=0,steps=256,thickness=0.025,axis='Z',name="Revolution surface",color="AzureBlueDark"):
		"""
		Draws a revolution surface from a curve in the reference R'
		Parameters:
		   fun: parametric equacion of the curve

		   steps: number of steps

		   axis: axis of revolution. It must be 'X', 'Y' or 'Z'

		   o: origin of the reference R'

		   u1, u2: vectors to construct the basis {v1, v2, v3}

		   pmax: the principal axis are drawn between -pmax and pmax

		   color: color of the surface
		"""
		if fun is None:
			return None
		q = self.vectors_to_quaternion(u1,u2)
		obj = self.simple_curve(fun,tmin=tmin,tmax=tmax,steps=steps,name=name)
		m = obj.modifiers.new(name="SubSurf", type='SUBSURF')
		m.levels = 4
		m.subdivision_type = 'SIMPLE'
		m = obj.modifiers.new(name="Solidify", type='SOLIDIFY')
		m.thickness = thickness
		m.offset = 1.0
		m = obj.modifiers.new(name="Screw", type='SCREW')
		m.angle = 2*math.pi
		m.steps = steps
		m.axis =  axis
		c = Colors.color(color)
		self.add_material(obj,c.name,c.r,c.g,c.b,1.0)
		bpy.context.scene.collection.objects.link(obj)
		self.set_origin(o)
		self.set_rotation(quaternion=q)
		if self.rotation is not None:
			obj.rotation_mode = 'QUATERNION'
			obj.rotation_quaternion.rotate(self.rotation.quaternion)
			obj.location.rotate(self.rotation.quaternion)
		if pmax > 0.0:
			self.draw_base_axis(axis = pmax,positive=False,name="Referència R'")
		bpy.ops.object.shade_smooth()
		obj.location = o
		obj.select_set(False)
		bpy.context.view_layer.objects.active = None
	#
	#
	#
	def animate_revolution_surface(self,fun=None,tmin=0.0,tmax=1.0,steps=256,curvethicknes=0.025,thickness=0.025,frames=3,angle=3,radians=False,axis='Z',origin=Vector([0,0,0]),symmetry=None,name="Revolution surface",color="AzureBlueDark",point=None):
		"""
		Draws and animates a revolution surface from a curve
		Parameters:
		   fun: parametric equacion of the curve

		   steps: number of steps to graw the curve

		   curvethicknes: thickness of the curve

		   frames: number of frames at each step of revolution

		   angle: step angle of the revolution

		   radians: if True, angle must be in radians

		   axis: axis of revolution. It must be 'X', 'Y' or 'Z'

		   origin: point of the axis of revolution

		   symmetry: symmetry used to draw the curve

		   name: name of the surface

		   color: color of the surface

		   point: if not None draw three points and a cercle. Must be a float between tmax and tmin
		"""
		if radians:
			angle *= 180/math.pi
		stepsr = int(360/angle) + 1
		angle = 360/stepsr
		if fun is None:
			return None
		
		def myfun(t):
			return Vector(fun(t)) - origin

		if not isinstance(origin,Vector):
			origin = Vector(origin)

		if axis == 'X':
			r = Rotation(angle,Vector([1,0,0]))
			d1 = Vector([0,1,0])
			d2 = Vector([0,0,1])
		elif axis == 'Y':
			r = Rotation(angle,Vector([0,1,0]))
			d1 = Vector([0,0,1])
			d2 = Vector([1,0,0])
		elif axis == 'Z':
			r = Rotation(angle,Vector([0,0,1]))
			d1 = Vector([1,0,0])
			d2 = Vector([0,1,0])
		else:
			return None

		if point is not None:
			try:
				tp = 1.0 * point
			except:
				pass
			if not isinstance(tp,float):
				return None
			if tp < tmin or tp > tmax:
				tp = random.uniform(tmin,tmax)
			zp = Vector(myfun(tp))
			e = d1.cross(d2)
			z0 = zp.project(e)

		p2 = self.curve(myfun,tmin=tmin,tmax=tmax,steps=steps,thickness=curvethicknes,color="Red",symmetry=symmetry,name="Rotating curve")
		p1 = self.curve(myfun,tmin=tmin,tmax=tmax,steps=steps,thickness=1.05*curvethicknes,color="Blue",symmetry=symmetry,name="Curve")
		obj = self.simple_curve(myfun,tmin=tmin,tmax=tmax,steps=steps,name=name,symmetry=symmetry)

		if point is not None:
			m1 = self.draw_point(radius=0.1,location=zp,name="Punt p0",color="Red")
			m2 = self.draw_point(radius=0.2,location=zp,name="Punt p1",color="Black")
			m3 = self.draw_point(radius=0.1,location=z0,name="Punt p2",color="Blue")
			l1 = self.draw_line(start=z0,end=zp,scale=0.04,name="Línia 1",color="Black")
			l2 = self.draw_line(start=z0,end=zp,scale=0.03,name="Línia 2",color="Red")
			l1 = self.join([l1,m2])
			self.draw_circle(center=z0,u1=d1,u2=d2,radius=(zp-z0).length,steps=128,thickness=0.005,name="Circle",color="Cyan")
	
		m = obj.modifiers.new(name="SubSurf", type='SUBSURF')
		m.levels = 4
		m.subdivision_type = 'SIMPLE'
		m = obj.modifiers.new(name="Solidify", type='SOLIDIFY')
		m.thickness = thickness
		m.offset = 1.0
		m = obj.modifiers.new(name="Screw", type='SCREW')
		m.angle = 0.0
		m.steps = steps
		m.axis =  axis
		c = Colors.color(color)
		self.add_material(obj,c.name,c.r,c.g,c.b,1.0)
		bpy.context.scene.collection.objects.link(obj)

		bpy.context.scene.frame_set(self.frame)
		obj.keyframe_insert(data_path="rotation_quaternion",index=-1)
		obj.keyframe_insert(data_path='modifiers["Screw"].angle',index=-1)
		p2.keyframe_insert(data_path="rotation_quaternion",index=-1)
		if point is not None:
			l1.keyframe_insert(data_path="rotation_quaternion",index=-1)
			# m2.keyframe_insert(data_path="location",index=-1)
		fn = frames + self.frame
		w = Vector([-1,0,3])
		for i in range(0,stepsr):
			bpy.context.scene.frame_set(fn)
			p2.rotation_quaternion.rotate(r.quaternion)
			p2.keyframe_insert(data_path="rotation_quaternion",index=-1)
			obj.modifiers["Screw"].angle = 2 * (i+1) * math.pi / stepsr
			obj.modifiers["Screw"].steps = i+1
			obj.keyframe_insert(data_path='modifiers["Screw"].angle',index=-1)
			if point is not None:
				l1.rotation_quaternion.rotate(r.quaternion)
				l1.keyframe_insert(data_path="rotation_quaternion",index=-1)
				#m2.location.rotate(r.quaternion)
				# m2.location = m2.location + w
				#m2.keyframe_insert(data_path="location",index=-1)
			fn += frames
		self.frame = fn - frames
		bpy.context.scene.frame_end = self.frame
		bpy.context.view_layer.update()
		self.reset()
		bpy.context.scene.frame_set(0)
		bpy.ops.object.select_all(action='SELECT')
		bpy.ops.transform.translate(value=origin)
		bpy.ops.object.select_all(action='DESELECT')
	#
	# Helical motion or rotation of objects
	#
	def rotate_objects(self,objs=[],axis='Z',angle=None,frames=1,origin=Vector([0,0,0]),translation=0,rounds=1,length=25,draw=False):
		"""
		Rotates an object around the axis
		Parameters:
		   objs: the list of objects

		   axis: it must be 'X', 'Y', 'Z' or a Vector

		"""
		if objs is None or (not isinstance(objs,list) and not isinstance(objs,tuple)):
			return None
		if not isinstance(origin,Vector):
			origin = Vector(origin)
		if isinstance(axis,str):
			axis = axis.strip().upper()
		if axis == 'X':
			u = Vector([1,0,0])
		elif axis == 'Y':
			u = Vector([0,1,0])
		elif axis == 'Z':
			u = Vector([0,0,1])
		elif isinstance(axis,Vector):
			u = axis
		else:
			u = Vector(axis)

		if angle is None:
			angle = 360
		else:
			rounds = 1

		if draw:
			self.set_origin(origin)
			self.draw_vector(u,axis=length,positive=False,color="White")
			self.set_origin()

		r = Rotation(1/int(frames),u)
		axis, alfa = r.to_axis_angle()
		axis.normalize()
		r = Rotation(1/int(frames),u)
		t =  translation / (alfa * int(frames) * 360) * axis
		bpy.context.scene.frame_set(self.frame)
		for obj in objs:
			obj.keyframe_insert(data_path="rotation_quaternion",index=-1)
			obj.keyframe_insert(data_path="location",index=-1)
		fn = self.frame + 1
		for i in range(int(frames) * int(rounds) * angle):
			for obj in objs:
				bpy.context.scene.frame_set(fn)
				obj.rotation_quaternion.rotate(r.quaternion)
				obj.keyframe_insert(data_path="rotation_quaternion",index=-1)
				w = obj.location - origin
				w.rotate(r.quaternion)
				obj.location = origin + w + t
				obj.keyframe_insert(data_path="location",index=-1)
			fn += 1
		self.frame = fn - frames
		bpy.context.scene.frame_end = self.frame
		bpy.context.scene.frame_set(0)
		bpy.context.view_layer.update()
	#
	# Rotation of a vector
	#
	def rotate_vector(self,vector=None,axis='Z',length=25):
		"""
		Rotates a vector around the axis
		Parameters:
		   vector: the vector

		   axis: it must be 'X', 'Y', 'Z' or a vector
		"""
		draw = False
		if vector is None:
			return None
		if axis == 'X':
			u = Vector([1,0,0])
		elif axis == 'Y':
			u = Vector([0,1,0])
		elif axis == 'Z':
			u = Vector([0,0,1])
		elif isinstance(axis,Vector):
			u = axis
		else:
			u = Vector(axis)

		self.draw_vector(vector,color="Black")
		obj = self.draw_vector(vector,color="Red")
		w1 = u.orthogonal().normalized()
		vec1 = vector.project(u)
		w3 = vec1.normalized()
		w2 = w3.cross(w1)
		a = vec1.length
		b = (vector-vec1).length
		p2 = b**2/a**2
		self.rotate_object(obj,u,length=length)
		self.cone(u1=w1,u2=w2,a2=p2,b2=p2,c2=1,half=True, principal=False,canonica=False,xmax=b,color="GrayLight",opacity=0.1,thickness=0.01)
	#
	# Rotation of a point
	#
	def rotate_point(self,punt=None,origen=Vector([0,0,0]),axis='Z',length=25,vectors=True):
		"""
		Rotates a point around an affine line
		Parameters:
		   point: the point

		   origen: a point of the affine line

		   axis: it must be 'X', 'Y', 'Z' or a vector

		   length: length of the
		"""
		draw = False
		if punt is None:
			return None
		if axis == 'X':
			u = Vector([1,0,0])
		elif axis == 'Y':
			u = Vector([0,1,0])
		elif axis == 'Z':
			u = Vector([0,0,1])
		elif isinstance(axis,Vector):
			u = axis
		else:
			u = Vector(axis)

		if not isinstance(origen,Vector):
			origen = Vector(origen)

		self.draw_point(radius=0.3,location=punt,name="Blue",color="Blue")
		obj = self.draw_point(radius=0.3,location=punt,name="Red",color="Red")
		if vectors:
			self.set_origin(origen)
			self.draw_vector(punt-origen,name="VBlack",color="Black")
			obj2 = self.draw_vector(punt-origen,name="VRed",color="Red")
		w1 = u.orthogonal().normalized()
		vec1 = (punt-origen).project(u)
		center = origen + vec1
		radius = (center-punt).length
		w3 = vec1.normalized()
		w2 = w3.cross(w1)
		a = vec1.length
		b = (punt-origen-vec1).length
		p2 = b**2/a**2
		if vectors:
			self.rotate_objects([obj,obj2],u,angle=360,origin=origen,length=length,draw=True)
		else:
			self.rotate_object(obj,u,origin=origen,length=length)
		self.draw_circle(center=center,u1=w1,u2=w2,radius=radius,name="Circumferència",steps=128,color="Yellow")
		self.cone(o=origen,u1=w1,u2=w2,a2=p2,b2=p2,c2=1,half=True, principal=False,canonica=False,xmax=b,color="GrayLight",opacity=0.25,thickness=0.01)
		self.reset()
	#
	#
	#
	def rotate_object_by_axis_angle(self,obj=None,axis=Vector([1,0,0]),angle=90,amax=15,frames=1,scaleaxis=0.075,local=False):
		"""
		Rotates an object around an angle 'angle' around the axis
		Parameters:
		   obj: the object

		   axis: any non nul Vector

		   angle: the angle of rotation in degrees

		   frames: increment of the frame set

		   scaleaxis: scale value for draw_base_axis

		   local: if True the center of rotation is the location of the object
		"""
		if obj is None:
			return None
		if isinstance(axis,Vector):
			u = axis
		else:
			u = Vector(axis)
		if u.length == 0.0 or angle <= 1:
			return

		self.draw_base_axis(axis = amax,scale=scaleaxis,positive=False,name="Base canònica")
		self.draw_vector(u,scale=0.1,axis=amax,positive=False,color="White",name="Eix rotació")

		num = int(angle)
		alfa = angle / num
		r = Rotation(alfa,u)
		bpy.context.scene.frame_set(self.frame)
		obj.keyframe_insert(data_path="rotation_quaternion",index=-1)
		if not local:
			obj.keyframe_insert(data_path="location",index=-1)
		fn = frames + self.frame

		for i in range(num):
			bpy.context.scene.frame_set(fn)
			obj.rotation_quaternion.rotate(r.quaternion)
			obj.keyframe_insert(data_path="rotation_quaternion",index=-1)
			if not local:
				w = obj.location
				w.rotate(r.quaternion)
				obj.location = w
				obj.keyframe_insert(data_path="location",index=-1)
			fn += frames
		self.frame = fn - frames
		bpy.context.scene.frame_end = self.frame
		bpy.context.scene.frame_set(0)
		bpy.context.view_layer.update()
	#
	# Rotation by Euler's angles
	#
	def rotate_euler(self,obj=None,psi=0.0,theta=0.0,phi=0.0,frames=3,axis='ZXZ',amax=15,scaleaxis=0.075,reverse=False,local=False,radians=False,canonica=True,positive=False):
		"""
		Rotates an object by the Euler angles psi, theta and phi
		Parameters:
		   object: the object

		   psi, theta, phi: the Euler angles expressed in degrees

		   axis: it must be 'XYZ', 'XZY', 'YXZ', 'YZX', 'ZXY', 'ZYX', 'XYX', 'XZX', 'YXY', 'YZY', 'ZXZ' or 'ZYZ'

		   amax: axis valur for draw_base_axis

		   scaleaxis: scale value for draw_base_axis

		   local: if True the center of rotation is the location of the object

		   radians: if True, psi, theta and phi must be in radians

		   positive: if False and psi, theta or phi are greather than 180 degrees, they rae converted
		             to negative angles
		"""
		def vector_from_axis(axis):
			if axis == 'X':
				return Vector([1,0,0])
			if axis == 'Y':
				return Vector([0,1,0])
			if axis == 'Z':
				return Vector([0,0,1])
			return None

		if obj is None or axis is None:
			return None

		if not isinstance(axis,str):
			return None

		axis = axis.upper()
		if axis not in ('XYZ','XZY','YXZ','YZX','ZXY','ZYX','XYX','XZX','YXY','YZY','ZXZ','ZYZ'):
			return None

		u1 = vector_from_axis(axis[0])
		u2 = vector_from_axis(axis[1])
		u3 = vector_from_axis(axis[2])

		if radians:
			psi *= 180/math.pi
			theta *= 180/math.pi
			phi *= 180/math.pi
		if positive:
			if psi < 0.0:
				psi += 360
			if theta < 0.0:
				theta += 360
			if phi < 0.0:
				phi += 360
		else:
			if psi > 180.0:
				psi -= 360
			if theta > 180.0:
				theta -= 360
			if phi > 180.0:
				phi -= 360

		if reverse:
			self.set_colors(["OrangeRedDark","Yellow","Magenta"])
			axis = self.draw_base_axis(axis=amax,scale=scaleaxis,positive=False,name="Eixos transformats")
			obj = self.join([obj,axis])
			u1, u2, u3 = u3, u2, u1
			psi, theta, phi = phi, theta, psi
			s = Rotation(psi,u1)
			u2 = s.apply(u2)
			u3 = s.apply(u3)
			s = Rotation(theta,u2)
			u3 = s.apply(u3)
		elif canonica:
			self.draw_base_axis(axis=amax,scale=scaleaxis,positive=False,name="Base canònica")

		bpy.context.scene.frame_set(self.frame)
		obj.keyframe_insert(data_path="rotation_quaternion",index=-1)
		if not local:
			obj.keyframe_insert(data_path="location",index=-1)
		fn = frames + self.frame
		if psi > 0:
			num = int(psi)
		elif psi < 0:
			num = int(-psi)
		alfa = psi / num
		r = Rotation(alfa,u1)
		for i in range(num):
			bpy.context.scene.frame_set(fn)
			obj.rotation_quaternion.rotate(r.quaternion)
			obj.keyframe_insert(data_path="rotation_quaternion",index=-1)
			if not local:
				w = obj.location
				w.rotate(r.quaternion)
				obj.location = w
				obj.keyframe_insert(data_path="location",index=-1)
			fn += frames

		if theta > 0:
			num = int(theta)
		elif theta < 0:
			num = int(-theta)
		alfa = theta / num
		r = Rotation(alfa,u2)
		for i in range(num):
			bpy.context.scene.frame_set(fn)
			obj.rotation_quaternion.rotate(r.quaternion)
			obj.keyframe_insert(data_path="rotation_quaternion",index=-1)
			if not local:
				w = obj.location
				w.rotate(r.quaternion)
				obj.location = w
				obj.keyframe_insert(data_path="location",index=-1)
			fn += frames

		if phi > 0:
			num = int(phi)
		elif phi < 0:
			num = int(-phi)
		alfa = phi / num
		r = Rotation(alfa,u3)
		for i in range(num):
			bpy.context.scene.frame_set(fn)
			obj.rotation_quaternion.rotate(r.quaternion)
			obj.keyframe_insert(data_path="rotation_quaternion",index=-1)
			if not local:
				w = obj.location
				w.rotate(r.quaternion)
				obj.location = w
				obj.keyframe_insert(data_path="location",index=-1)
			fn += frames

		self.frame = fn - frames
		bpy.context.scene.frame_end = self.frame
		bpy.context.scene.frame_set(0)
		bpy.context.view_layer.update()
	#
	# Rotate objects or helical motion
	#
	def rotate_object(self,obj=None,axis='Z',frames=1,origin=Vector([0,0,0]),localaxis=None,localangle=None,translation=0.0,rounds=1,length=25,draw=True):
		"""
		Rotates an object around the axis
		Parameters:
		   obj: the object

		   axis: it must be 'X', 'Y', 'Z' or a Vector

		   frames: increment of the frame set

		   traslation: tranlation by round

		   local: if True the center of rotation is the location of the object
		"""
		if obj is None:
			return None
		if not isinstance(origin,Vector):
			origin = Vector(origin)
		if isinstance(axis,str):
			axis = axis.strip().upper()
		if axis == 'X':
			u = Vector([1,0,0])
		elif axis == 'Y':
			u = Vector([0,1,0])
		elif axis == 'Z':
			u = Vector([0,0,1])
		elif isinstance(axis,Vector):
			u = axis
		else:
			u = Vector(axis)

		line = None
		if localaxis is not None and localangle is not None:
			old = self.origin
			self.set_origin(obj.location)
			l = obj.dimensions.length / 2
			line = self.draw_vector(localaxis,axis=l,scale=0.1,arrow=False,positive=False,color="Orange",name="Eix rotació local")
			line.select_set(True)
			bpy.ops.object.origin_set(type='ORIGIN_CENTER_OF_MASS', center='MEDIAN')
			line.select_set(False)
			self.set_origin(old)
			lr = Rotation(localangle,localaxis)
		if draw:
			self.set_origin(origin)
			self.draw_vector(u,axis=length,positive=False,color="White")
			self.set_origin()
		r = Rotation(1/int(frames),u)
		axis, angle = r.to_axis_angle()
		axis.normalize()
		t =  translation / (angle * int(frames) * 360) * axis
		bpy.context.scene.frame_set(self.frame)
		obj.keyframe_insert(data_path="rotation_quaternion",index=-1)
		obj.keyframe_insert(data_path="location",index=-1)
		fn = self.frame + 1
		for i in range(int(frames) * int(rounds) * 360):
			bpy.context.scene.frame_set(fn)
			if line is None:
				obj.rotation_quaternion.rotate(r.quaternion)
			else:
				obj.rotation_quaternion.rotate(lr.quaternion)
			obj.keyframe_insert(data_path="rotation_quaternion",index=-1)
			w = obj.location - origin
			w.rotate(r.quaternion)
			obj.location = origin + w + t
			if line is not None:
				line.location = origin + w + t
				line.keyframe_insert(data_path="location",index=-1)
			obj.keyframe_insert(data_path="location",index=-1)
			fn += 1
		self.frame = fn - frames
		bpy.context.scene.frame_end = self.frame
		bpy.context.scene.frame_set(0)
		bpy.context.view_layer.update()
	#
	#
	#
	def draw_frenet_curve(self,fun=None,var=None,tmin=0.0,tmax=1.0,radius=0.1,steps=25,thickness=0.01,name="Curve",color="White",point=True,tangent=False,acceleration=False,normal=False,osculator=False,frenet=False,units=False,sizex=8,sizey=8,axis=10):
		"""
		Draws a curve and diferents elements related to the curve
		Parameters:
		   fun: the parametric function

		   var = parameter variable of the function fun

		   tmin: minimum value of the parameter

		   tmax: maximum value of the parameter

		   radius: radius of the point

		   steps: number of steps

		   frames: increment of the frame set

		   thickness: thickness of the curve

		   name: name of the curve

		   color: color of the curve

		   point: if True draw a point along the curve

		   tangent: if True draw the tangent vector along the curve

		   acceleration: if True draw the acceleration vector along the curve

		   normal: if True draw the normal vector along the curve

		   osculator: if True draw the osculating plane along the curve

		   frenet: if True draw the Frenet trihedron along the curve

		   units: if True normalize the tangent and normal vectors

		   sizex, sizey: sizes of the osculating plane

		   axis: length of the coordinate axis
		"""
		if fun is None:
			return None

		self.draw_base_axis(axis=axis,positive=False)

		def _fun_(x):
			return [u.subs(var,x) for u in fun]

		def frenet_quaternion(tangent,normal):
			v1 = tangent.normalized()
			v2 = normal.normalized()
			v3 = v1.cross(v2)
			return Matrix([v1,v2,v3]).transposed().to_quaternion()

		frames = 1
		curve = self.draw_curve(_fun_,tmin=tmin,tmax=tmax,steps=steps,thickness=thickness,color=color,axis=False)
		if not point and not tangent and not osculator and not frenet:
			return curve

		T = [diff(u,var) for u in fun]
		#
		# Here is sqrt from sympy
		#
		Tnorm = math.sqrt(sum([u**2 for u in T]))
		A = [diff(u,var) for u in T]
		p0 = Vector([u.subs(var,tmin) for u in fun])
		v0 = Vector([N(u.subs(var,tmin)) for u in T])
		a0 = Vector([N(u.subs(var,tmin)) for u in A])
		n0 = a0 - a0.project(v0)
		q0 = frenet_quaternion(v0,n0)
		f0 = [Vector([1,0,0]),Vector([0,1,0]),Vector([0,0,1])]

		if units:
			v0.normalize()
			n0.normalize()
		bpy.context.scene.frame_set(self.frame)

		if point:
			p = self.draw_point(radius=radius,location=p0,name="Punt",color="Black")
			p.keyframe_insert(data_path="location",index=-1)
		self.set_origin(p0)
		if tangent:
			l = v0.length
			if not units:
				vp = 5*v0.normalized()
			else:
				vp = v0
			if not units:
				v = self.draw_vector(vp,color="Red",scale=0.035,head_height=0.3)
				v.scale.z *= l / 5.0
			else:
				v = self.draw_vector(vp,color="Red",scale=0.035,head_height=0.2)
			v.keyframe_insert(data_path="location",index=-1)
			v.keyframe_insert(data_path="scale",index=-1)
			v.keyframe_insert(data_path="rotation_quaternion",index=-1)
		if acceleration:
			l = a0.length
			ap = 5*a0.normalized()
			a = self.draw_vector(ap,color="Green",scale=0.035,head_height=0.2)
			a.scale.z *= l / 5.0
			a.keyframe_insert(data_path="location",index=-1)
			a.keyframe_insert(data_path="scale",index=-1)
			a.keyframe_insert(data_path="rotation_quaternion",index=-1)
		if normal:
			l = n0.length
			if not units:
				np = 5*n0.normalized()
			else:
				np = n0
			if not units:
				n = self.draw_vector(np,color="Red",scale=0.035,head_height=0.2)
				n.scale.z *= l / 5.0
			else:
				n = self.draw_vector(np,color="Red",scale=0.035,head_height=0.1)
			n.keyframe_insert(data_path="location",index=-1)
			n.keyframe_insert(data_path="scale",index=-1)
			n.keyframe_insert(data_path="rotation_quaternion",index=-1)
		if osculator:
			o = self.draw_plane_surface(base=[[1,0,0],[0,1,0]],color="GreenPaleDull",linecolor="GreenDarkDull",sizex=sizex,sizey=sizey,opacity=0.25)
			o.rotation_quaternion = q0
			o.keyframe_insert(data_path="location",index=-1)
			o.keyframe_insert(data_path="rotation_quaternion",index=-1)
		if frenet:
			f = self.draw_vectors(f0,color="Red",scale=0.035,head_height=0.1)
			f.rotation_quaternion = q0
			f.keyframe_insert(data_path="location",index=-1)
			f.keyframe_insert(data_path="rotation_quaternion",index=-1)
		self.set_origin()

		fn = frames + self.frame
		for i in range(steps):
			bpy.context.scene.frame_set(fn)
			x = tmin + (tmax - tmin)*i/steps
			pos = Vector([u.subs(var,x) for u in fun])
			v1 = Vector([N(u.subs(var,x)) for u in T])
			a1 = Vector([N(u.subs(var,x)) for u in A])
			n1 = a1 - a1.project(v1)
			q1 = frenet_quaternion(v1,n1)
			if point:
				p.location = pos
				p.keyframe_insert(data_path="location",index=-1)
			if tangent:
				if not units:
					r = v1.length / v0.length
					v.scale.z *= r
				v.location = pos
				v.keyframe_insert(data_path="location",index=-1)
				v.keyframe_insert(data_path="scale",index=-1)
				q = v0.rotation_difference(v1)
				v.rotation_quaternion.rotate(q)
				v.keyframe_insert(data_path="rotation_quaternion",index=-1)
			if acceleration:
				r = a1.length / a0.length
				a.scale.z *= r
				a.location = pos
				a.keyframe_insert(data_path="location",index=-1)
				a.keyframe_insert(data_path="scale",index=-1)
				q = a0.rotation_difference(a1)
				a.rotation_quaternion.rotate(q)
				a.keyframe_insert(data_path="rotation_quaternion",index=-1)
			if normal:
				if not units:
					r = n1.length / n0.length
					n.scale.z *= r
				n.location = pos
				n.keyframe_insert(data_path="location",index=-1)
				n.keyframe_insert(data_path="scale",index=-1)
				q = n0.rotation_difference(n1)
				n.rotation_quaternion.rotate(q)
				n.keyframe_insert(data_path="rotation_quaternion",index=-1)
			if osculator:
				o.location = pos
				o.rotation_quaternion = q1
				o.keyframe_insert(data_path="location",index=-1)
				o.keyframe_insert(data_path="rotation_quaternion",index=-1)
			if frenet:
				f.location = pos
				f.rotation_quaternion = q1
				f.keyframe_insert(data_path="location",index=-1)
				f.keyframe_insert(data_path="rotation_quaternion",index=-1)
			v0 = v1.copy()
			a0 = a1.copy()
			n0 = n1.copy()
			fn += frames
		self.frame = fn - frames
		bpy.context.scene.frame_end = self.frame
		bpy.context.scene.frame_set(0)
		bpy.context.view_layer.update()
	#
	# Examples of use
	#
	def clear(self):
		"""
		Clears and removes all the elements
		"""
		self.reset()
		for obj in bpy.data.objects:
			bpy.data.objects.remove(obj)
	#
	# Base canònica
	#
	def base_canonica(self,origin=Vector([0,0,0]),length=15,scale=0.04,zaxis=True,name="Base canònica"):
		"""
		Draws the canonical base
		Parameters:
		   origin: point where to represent the base

		   length: length of the axis

		   scale: scale of the cylinder

		   zaxis: if False the z axis is not drawn

		   name: name of the object
		"""
		if not isinstance(origin,Vector):
			origin = Vector(origin)
		self.set_origin(origin)
		self.draw_base_axis(axis=length,positive=False,scale=scale,zaxis=zaxis,name=name)
	#
	#
	def base_canonica_white(self,origin=Vector([0,0,0]),length=20,scale=0.04,zaxis=True,name="Base canònica"):
		"""
		Draws the canonical base in white
		Parameters:
		   origin: point where to represent the base

		   length: length of the axis

		   scale: scale of the cylinder

		   zaxis: if False the z axis is not drawn

		   name: name of the object
		"""
		if not isinstance(origin,Vector):
			origin = Vector(origin)
		self.colors = Colors.colors(["White","White","White"])
		self.draw_base_axis(axis=length,positive=False,scale=scale,zaxis=zaxis,name=name)
		self.colors = Colors.colors(["Red","Green","Blue"])
	#
	# Vector i base canònica
	#
	def vector_base_canonica(self,vector=Vector([-4,7,6]),length=12,name="Vector",components=True):
		"""
		Draws a vector expressed in the canonical base
		Parameters:
		   vector: the vector to draw

		   length: length of the axis

		   name: name of the vector

		   components: if True draws lines representing the components
		"""
		self.base_canonica(length=length)
		if not isinstance(vector,Vector):
			vector = Vector(vector)
		self.draw_vector(vector,name=name)
		if components:
			self.draw_components(vector,name="Components en base canònica")
	#
	# Base no canònica
	#
	def base_no_canonica(self,origin=Vector([0,0,0]),u1=Vector([1,-1,0]),u2=1/2*Vector([1,-1,-1]),u3=Vector([-1,0,1]),length=12,scale=0.04,preserve=False,name="Base B'"):
		"""
		Draws the base {u1,u2,u3} with origin in the point origin and sets the default
		origin and default base to them
		Parameters:
			origin: origin of the vector and the base

			u1, u2, u3: vectors of the base

			length: length of the axis

			scale: scale of the base

			name: name of the base

			preserve: 
		"""
		if not isinstance(origin,Vector):
			origin = Vector(origin)
		if not isinstance(u1,Vector):
			u1 = Vector(u1)
		if not isinstance(u2,Vector):
			u2 = Vector(u2)
		if not isinstance(u3,Vector):
			u3 = Vector(u3)
		self.set_origin(origin)
		self.set_base([u1,u2,u3])
		self.draw_base_axis(axis=length,positive=False,scale=scale,name=name)
		if not preserve:
			self.set_origin()
			self.set_base()
			self.set_rotation()
	#
	# Base a partir d'un eix
	#
	def base_adaptada(self,origin=Vector([0,0,0]),axis=Vector([1,1,1]),length=15,scale=0.04,name="Base adaptada"):
		"""
		Draws an ortonormal base from vector axis with origin in the point origin and sets the default
		origin and default base to them
		Parameters:
			origin: origin of the vector and the base

			axis: first vector of the base

			length: length of the axis

			scale: scale of the base

			name: name of the base
		"""
		if not isinstance(origin,Vector):
			origin = Vector(origin)
		if not isinstance(axis,Vector):
			axis = Vector(axis)
		self.set_origin(origin)
		u1 = axis.normalized()
		u2 = u1.orthogonal().normalized()
		u3 = u1.cross(u2)
		self.set_base([u1,u2,u3])
		self.draw_base_axis(axis=length,positive=False,scale=scale,name=name)
		self.reset()
	#
	# Vector en base no canònica
	#
	def vector_base_no_canonica(self,vector=Vector([5,6,-5]),origin=Vector([0,0,0]),u1=1/3*Vector([-1,-2,2]),u2=1/3*Vector([2,1,2]),u3=1/3*Vector([-2,2,1]),length=12,scale=0.04,name="Base B'",canonica=True,preserve=False):
		"""
		Draws a vector expressed in the base {u1,u2,u3} with origin in the point origin and sets the default
		origin and default base to them
		Parameters:
			vector: vector to draw

			origin: origin of the vector and the base

			u1, u2, u3: vectors of the base

			length: length of the axis

			scale: scale of the base

			name: name of the base
		"""
		self.base_no_canonica(origin=origin,u1=u1,u2=u2,u3=u3,length=length,scale=scale,preserve=preserve,name=name)
		if not isinstance(vector,Vector):
			vector = Vector(vector)
		if canonica:
			vector = self.coordinates_en_referencia(vector)
		self.draw_vector(vector,scale=0.06,head_height=0.25)
		self.draw_components(vector,scale=0.015,name="Components en base B'")
		if not preserve:
			self.set_origin()
			self.set_base()
			self.set_rotation()
	#
	# Canvi de base
	#
	def canvi_base(self,vector=Vector([8,-6,7]),u1=1/3*Vector([-1,-2,2]),u2=1/3*Vector([2,1,2]),u3=1/3*Vector([-2,2,1]),length=12):
		"""
		Draw the components of a vectors in the canonical base and in the base {u1,u2,u3}. Sets the default
		origin and default base to them
		Parameters:
			vector: vector to draw

			u1, u2, u3: vectors of the base

			length: length of the axis
		"""
		self.vector_base_canonica(vector=vector,length=length)
		self.set_colors(["Magenta","Yellow","Cyan"])
		self.base_no_canonica(u1=u1,u2=u2,u3=u3,length=length)
		v = self.components_in_base(vector)
		self.draw_components(v,color="White",name="Components en la base B'")
	#
	# Pla vectorial
	#
	def pla_vectorial(self,v1=Vector([3,2,1]),v2=Vector([1,-2,0.5]),canonica=False,length=15,color="Cyan",sizex=25,sizey=20,opacity=0.8):
		"""
		Draws the plane generated by two vectors
		Parameters:
			v1, v2: generators of the plane

			canonica: if True, draws the x, y and z axis

			length: length of the axis x, y and z

			color: color of the plane

			sizex, sizey: size of the plane

			opacicity: opacity of the plane
		"""
		if canonica:
			if length > 15:
				self.base_canonica(length=length,scale=0.01)
			else:
				self.base_canonica(length=length)
		self.draw_vectors([v1,v2],color="Blue")
		self.draw_plane_surface(base=[v1,v2],color=color,sizex=sizex,sizey=sizey,opacity=opacity)
	#
	# Pla afí
	#
	def pla_afi(self,punt=Vector([0,0,0]),normal=None,v1=Vector([3,2,1]),v2=Vector([1,-2,0.5]),canonica=False,name="Pla afí",length=15,color="Cyan",sizex=25,sizey=20,opacity=0.9,elements=True):
		"""
		Draws the affine plane generated by two vectors passing through a point
		Parameters:
			punt: point of the plane

			normal: normal vector of the plane

			v1, v2: generators of the plane

			canonica: if True, draws the x, y and z axis

			name: name of the affine plane

			length: length of the axis x, y and z

			color: color of the plane

			sizex, sizey: size of the plane

			opacicity: opacity of the plane
		"""
		if canonica:
			if length > 15:
				self.base_canonica(length=length,scale=0.08)
			else:
				self.base_canonica(length=length)
		if normal is not None:
			if not isinstance(normal,Vector):
				normal = Vector(normal)
			self.draw_plane_surface(origin=punt,normal=normal,color=color,sizex=sizex,sizey=sizey,name=name,opacity=opacity)
		else:
			self.draw_plane_surface(origin=punt,base=[v1,v2],color=color,sizex=sizex,sizey=sizey,name=name,opacity=opacity)
		if elements:
			self.set_origin(punt)
			self.draw_point(color="Blue")
			if normal is not None:
				self.draw_vector(normal,color="Blue")
			else:
				self.draw_vectors(vectors=[v1,v2],canonica=canonica,color="Blue")
			self.set_origin()
	#
	# Posició relativa de tres plans
	#
	def posicio_relativa_tres_plans(self,punts=None,normals=None,colors=None,canonica=True,length=25,sizex=45,sizey=40,opacity=1.0,elements=False):
		"""
		Draws threee planes
		Parametres:
			punts: three points, one for each plane

			normals: three normal vectors, one for each plane

			colors: three colors, one for each plane

			canonica: if True, draws the x, y and z axis

			length: length of the axis x, y and z

			sizex, sizey: size of the planes

			opacicity: opacity of the planes

			elements: if True, draws the point and the normal vector for each plane
		"""
		punts = [p if isinstance(p,Vector) else Vector(p) for p in punts]
		normals = [n if isinstance(n,Vector) else Vector(n) for n in normals]
		n = ("Primer pla","Segon pla","Tercer pla")
		if canonica:
			b = (True,False,False)
		else:
			b = (False,False,False)
		for i in range(3):
			self.pla_afi(punt=punts[i],normal=normals[i],canonica=b[i],name=n[i],length=length,color=colors[i],sizex=sizex,sizey=sizey,opacity=opacity,elements=elements)
	#
	# Recta afí
	#
	def recta_afi(self,punt=Vector([3,4,-2]),v=Vector([1,2,1]),color="Black",size=15,name="Recta afí",canonica=True,length=12,scale=0.03,elements=True):
		"""
		Draws the affine line generated by a vector passing through a point
		Parameters:
			punt: point of the plane

			v: generators of the line

			canonica: if True, draws the x, y and z axis

			name: name of the affine plane

			length: length of the axis x, y and z

			color: color of the plane

			size: lenght of the line

			scale: scale of the line
		"""
		if canonica:
			if length > 15:
				self.base_canonica(length=length,scale=0.08)
			else:
				self.base_canonica(length=length)
		if not isinstance(v,Vector):
			v = Vector(v)
		if not isinstance(punt,Vector):
			punt = Vector(punt)
		l = v.length
		p0 = punt + size/l * v
		p1 = punt - size/l * v
		self.draw_line(start=p0,end=p1,scale=0.04,color=color)
		if elements:
			self.set_origin(punt)
			self.draw_point(color=color,radius=2 * scale)
			self.draw_vector(v,color=color)
			self.set_origin()
	#
	# Distància entre dues rectes que s'encreuen
	#
	def distancia_rectes_encreuen(self,p0=Vector([3,4,-2]),v0=Vector([1,2,3]),c0="Black",n0="Primera recta",p1=Vector([-3,4,1]),v1=Vector([1,-2,-1]),c1="Blue",n1="Segona recta",canonica=True,length=12,size=15,scale=0.03):
		"""
		Draws the distance between two affine lines
		Parameters:
			p0: point of the first line

			v0: generator of the first line

			c0: color of the first line

			n0: name of the first line

			p1: point of the second line

			v1: generator of the second line

			c1: color of the second line

			n1: name of the second line

			canonica: if True, draws the x, y and z axis

			length: length of the axis x, y and z

			size: lenght of the lines
		"""
		self.recta_afi(punt=p0,v=v0,color=c0,name=n0,canonica=canonica,length=length,size=size,scale=scale)
		self.recta_afi(punt=p1,v=v1,color=c1,name=n1,canonica=False,length=length,size=size,scale=scale)
		u = p0 - p1
		w = v0.cross(v1)
		t0, t1, t2 = self.components_in_base(u,[v0,v1,w])
		self.draw_line(start=p0-t0*v0,end=p1+t1*v1,scale=0.04,color="White",name="Distància",segment=True)
		self.pla_afi(punt=p0,v1=v0,v2=v1,name="Pla que conté a 1a recta i és paral·lel a la segon",sizex=2*size,sizey=2*size,opacity=0.9,elements=False)
	#
	# Projecció ortogonal i simètric sobre un pla vectorial
	#
	def projeccio_ortogonal_simetric_pla_vectorial(self,vector=Vector([7,-1,12]),v1=Vector([3,-1,1]),v2=Vector([1,0.5,0.5]),sizex=None,sizey=None,canonica=True):
		"""
		Draws the otoghonal projection and the symmetric of a vector with respecte a plane
		Parameters:
			vector: the initial vector

			v1, v2: generators of the plane

			sizex, sizey: size of the plane

			canonica: if True, draws the x, y and z axis
		"""
		if not isinstance(vector,Vector):
			vector = Vector(vector)
		if not isinstance(v1,Vector):
			v1 = Vector(v1)
		if not isinstance(v2,Vector):
			v2 = Vector(v2)
		self.draw_vector(vector)
		w = v1.cross(v2)
		vp = vector - vector.project(w)
		self.draw_vector(vp,color="Red")
		if sizex is None:
			sizex = 4*vp.length
		if sizey is None:
			sizey = 4*vp.length	
		self.pla_vectorial(v1,v2,sizex=sizex,sizey=sizey,canonica=canonica,color="AzureLightHard")
		self.set_origin(vp)
		self.draw_vector(vector.project(w),scale=0.025,color="White")
		self.set_origin()
		self.set_base([v1,v2,w])
		vb = self.components_in_base(vector)
		self.set_base()
		p1 = vb.x * v1
		p2 = vb.y * v2
		self.draw_line(start=[0,0,0],end=p1,scale=0.04,color="Blue")
		self.draw_line(start=[0,0,0],end=p2,scale=0.04,color="Blue")
		self.draw_line(start=vp,end=p1,scale=0.04,color="Blue")
		self.draw_line(start=vp,end=p2,scale=0.04,color="Blue")
		self.draw_vector(2 * vp - vector,color="Green")
		self.draw_line(start=2 * vp - vector,end=vp,scale=0.04,color="White")
	#
	# Projecció ortogonal i simètric d'un punt sobre un pla afí
	#
	def projeccio_ortogonal_simetric_pla_afi(self,punt=Vector([6,-5,8]),p0=Vector([3,-2,-3]),v1=Vector([3,-1,1]),v2=Vector([1,0.5,0.5]),radi=0.15,sizex=35,sizey=30,line=1.8,canonica=True):
		"""
		Draws the orthogonal projection and the symmetric of a point with respect an affine plane
		Parameters:
			punt: the initial point

			p0: point of the affine plane

			v1, v2: generators of the plane

			radi: radius of the points

			sizex, sizey: sizes of the affine plane

			factor: how to draw the perpendicular line

			canonica: if True, draws the x, y and z axis
		"""
		if not isinstance(punt,Vector):
			punt = Vector(punt)
		if not isinstance(p0,Vector):
			p0 = Vector(p0)
		if not isinstance(v1,Vector):
			v1 = Vector(v1)
		if not isinstance(v2,Vector):
			v2 = Vector(v2)
		self.draw_point(location=punt,color="Black",radius=radi,name="Punt")
		w = v1.cross(v2)
		self.pla_afi(punt=p0,v1=v1,v2=v2,sizex=sizex,sizey=sizey,color="AzureBlueMedium",canonica=canonica,elements=False)
		u = punt - p0
		up = punt - u.project(w)
		self.draw_point(location=up,color="Red",radius=radi,name="Projecció ortogonal")
		us = punt - 2*u.project(w)
		self.draw_point(location=us,color="Green",radius=radi,name="Simètric")
		u = punt - up
		self.draw_line(start=up-line*u,end=up+line*u,scale=0.04,color="White",name="Recta perpendicular al pla")
	#
	# Projecció ortogonal i simètric d'un punt sobre una recta afí
	#
	def projeccio_ortogonal_simetric_recta_afi(self,punt=Vector([6,-5,8]),p0=Vector([3,-2,-3]),v1=Vector([3,-1,1]),scale=0.1,radi=0.15,sizex=10,sizey=10,canonica=True):
		"""
		Draws the orthogonal projection and the symmetric of a point with respect an affine line
		Parameters:
			punt: the initial point

			p0: point of the affine line

			v1: generator of the line

			radi: radius of the points

			sizex, sizey: sizes of the affine plane

			canonica: if True, draws the x, y and z axis
		"""
		if not isinstance(punt,Vector):
			punt = Vector(punt)
		if not isinstance(p0,Vector):
			p0 = Vector(p0)
		if not isinstance(v1,Vector):
			v1 = Vector(v1)
		if canonica:
			self.base_canonica(length=0.75*sizex,name="Referència canònica")
		self.draw_point(location=p0,color="Blue",radius=radi,name="Punt de la recta")
		self.set_origin(p0)
		self.draw_vector(vector=v1,canonica=canonica,scale=scale,head_height=0.15,axis=20,name="Recta afí",color="Blue",positive=False)
		self.set_origin()
		self.draw_point(location=punt,color="Black",radius=radi,name="Punt inicial")
		u = punt - p0
		p1 = p0 + u.project(v1)
		self.draw_point(location=p1,color="Red",radius=radi,name="Projecció ortogonal")
		self.draw_plane_surface(origin=p1,normal=v1,name="Pla perpendicular a la recta",sizex=sizex,sizey=sizey,color="AzureBlueMedium")
		self.draw_point(location=2*p1-punt,color="Green",radius=radi,name="Simètric")
		self.draw_line(start=punt,end=2*p1-punt,scale=0.04,color="White")
	#
	# Projecció ortogonal i simètric sobre una recta vectorial
	#
	def projeccio_ortogonal_simetric_recta_vectorial(self,vector=Vector([7,-1,12]),v1=Vector([3,-1,1]),canonica=True,length=15):
		"""
		Draws the otoghonal projection and the symmetric of a vector with respecte a line
		Parameters:
			vector: the initial vector

			v1: generator of the line

			canonica: if True, draws the x, y and z axis

			length: length for x, y and z axis and v1 axis
		"""
		if not isinstance(vector,Vector):
			vector = Vector(vector)
		if not isinstance(v1,Vector):
			v1 = Vector(v1)
		if canonica:
			self.base_canonica(length=length)
		self.draw_vector(v1,axis=length,positive=False,color="Blue",scale=0.066)
		self.draw_vector(vector)
		vp = vector.project(v1)
		self.draw_vector(vp,color="Red")
		self.set_origin(vp)
		self.draw_vector(vector - vp,scale=0.025,color="White")
		self.set_origin()
		self.draw_vector(2 * vp - vector,color="Green")
		self.draw_line(start=2 * vp - vector,end=vp,scale=0.04,color="White")
	#
	# Referència canònica
	#
	def referencia_canonica(self,origin=Vector([0,0,0]),length=15,scale=0.04,zaxis=True,name="Referència canònica"):
		"""
		Draws the canonical reference
		Parameters:
		   origin: point where to represent the base

		   length: length of the axis

		   scale: scale of the cylinder

		   zaxis: if False the z axis is not drawn

		   name: name of the object
		"""
		if not isinstance(origin,Vector):
			origin = Vector(origin)
		self.set_origin(origin)
		self.draw_base_axis(axis=length,positive=False,scale=scale,zaxis=zaxis,name=name)
	#
	# Punt en referència canònica
	#
	def punt_referencia_canonica(self,punt=Vector([-4,7,6]),radius=0.1,length=12,name="Punt p",coordenades=True,vector=True):
		"""
		Draws a point expressed in the canonical reference
		Parameters:
		   punt: the point to draw

		   length: length of the axis

		   name: name of the point

		   coordenades: if True draws lines representing the coordinates

		   vector: if True, it draws the position vector
		"""
		self.base_canonica(length=length)
		if not isinstance(punt,Vector):
			punt = Vector(punt)
		self.draw_point(location=punt,color="Black",radius=radius,name=name)
		if coordenades:
			self.draw_components(punt,name="Coordenades en referència canònica")
		if vector:
			self.draw_vector(punt)
	#
	# Referència no canònica
	#
	def referencia_no_canonica(self,origin=Vector([0,0,0]),u1=Vector([1,-1,0]),u2=1/2*Vector([-1,2,1]),u3=Vector([-1,0,1]),length=12,scale=0.04,preserve=True,name="Referència R'"):
		"""
		Draws the reference {o;u1,u2,u3} with origin in the point origin and sets the default
		origin and default base to them
		Parameters:
			origin: origin of the reference

			u1, u2, u3: vectors of the base

			length: length of the axis

			scale: scale of the axis

			name: name of the reference
		"""
		if not isinstance(origin,Vector):
			origin = Vector(origin)
		if not isinstance(u1,Vector):
			u1 = Vector(u1)
		if not isinstance(u2,Vector):
			u2 = Vector(u2)
		if not isinstance(u3,Vector):
			u3 = Vector(u3)
		self.set_origin(origin)
		self.set_base([u1,u2,u3])
		self.draw_base_axis(axis=length,positive=False,scale=scale,name=name)
		if not preserve:
			self.set_origin()
			self.set_base()
			self.set_rotation()
	#
	# Punt en referencia no canònica
	#
	def punt_referencia_no_canonica(self,punt=Vector([5,6,-5]),origin=Vector([-2,3,3]),u1=1/3*Vector([-1,-2,2]),u2=1/3*Vector([2,1,2]),u3=1/3*Vector([-2,2,1]),length=12,scale=0.04,radius=0.1,name="Punt p",vector=True):
		"""
		Draws a point expressed in the reference {o,u1,u2,u3} with origin in the point origin and sets the default
		origin and default base to them
		Parameters:
			punt: point to draw

			origin: origin of the reference

			u1, u2, u3: vectors of the base

			length: length of the axis

			scale: scale of the axis

			name: name of the reference

			vector: if True, it draws the position vector
		"""
		self.referencia_no_canonica(origin=origin,u1=u1,u2=u2,u3=u3,length=length,scale=scale,name="Referència R'")
		if not isinstance(punt,Vector):
			punt = Vector(punt)
		self.draw_point(location=punt,color="Black",radius=radius,name=name)
		self.draw_components(punt,scale=0.015,name="Coordenades en referència R'")
		if vector:
			self.draw_vector(punt)
	#
	# Canvi de coordenades
	#
	def canvi_coordenades(self,punt=Vector([8,-6,7]),origin=Vector([-2,3,3]),u1=1/3*Vector([-1,-2,2]),u2=1/3*Vector([2,1,2]),u3=1/3*Vector([-2,2,1]),canonica=False,length=12,radius=0.1):
		"""
		Draw the coordinates of a point in the canonical reference and in the reference {o;u1,u2,u3}. Sets the default
		origin and default base to them
		Parameters:
			punt: point to draw

			origin: origin of the reference

			u1, u2, u3: vectors of the base

			canonica: if True, the coordinates of punt are in the canonical reference

			length: length of the axis
		"""
		if canonica:
			self.punt_referencia_canonica(punt=punt,length=length,radius=radius)
		else:
			self.set_colors(["Magenta","Yellow","Cyan"])
			self.punt_referencia_no_canonica(punt=punt,origin=origin,u1=u1,u2=u2,u3=u3,length=length,radius=radius)
			p = self.coordinates_en_canonica(punt)
		self.reset()
		self.draw_components(p,color="Magenta",name="Coordenades en referència canònica")
	#
	# El·lipse
	#
	def ellipse(self,center=Vector([0,0,0]),a=8,b=5,canonica=True):
		"""
 		Draws the ellipse of equation (x-x0)^2/a^2 + (y-y0)^2/b^2 == 1
		Parameters:
			centre: center of the ellipse

			a, b: semiaxis of the ellipse

			canonica: if True, draws the x and y axis
		"""
		if len(center) == 2:
			center = (center[0],center[1],0)
		if not isinstance(center,Vector):
			center = Vector(center)
		if a >= b:
			c = math.sqrt(a**2 - b**2)
			f1 = Vector([c,0,0])
			f2 = Vector([-c,0,0])
		else:
			c = math.sqrt(b**2 - a**2)
			f1 = Vector([0,c,0])
			f2 = Vector([0,-c,0])
		if canonica:
			self.referencia_canonica(zaxis=False)
		self.draw_ellipse(center=center,a=a,b=b,thickness=0.02,steps=128,axis=False)
		self.draw_point(radius=0.167,location=(0,0,0),name="Centre",color="White")
		self.draw_point(radius=0.167,location=f1,name="F1",color="Black")
		self.draw_point(radius=0.167,location=f2,name="F2",color="Black")
		self.set_origin()
	#
	# Hipèrbola
	#
	def hiperbola(self,center=Vector([0,0,0]),a=8,b=5,negatiu=False,canonica=True):
		"""
 		Draws the hyperbole of equation (x-x0)^2/a^2 - (y-y0)^2/b^2 == 1 (or -1)
		Parameters:
			centre: center of the hyperbole

			a, b: semiaxis of the hyperbole

			canonica: if True, draws the x and y axis

			negatiu: if True, draws the hyperbole (x-x0)^2/a^2 - (y-y0)^2/b^2 == -1
		"""
		if len(center) == 2:
			center = (center[0],center[1],0)
		if not isinstance(center,Vector):
			center = Vector(center)
		u1 = Vector([a,b,0])
		u2 = Vector([a,-b,0])
		c = math.sqrt(a**2 + b**2)
		f1 = [c,0,0]
		f2 = [-c,0,0]
		if canonica:
			self.referencia_canonica(zaxis=False)
		v1 = Vector([1,0,0])
		v2 = Vector([0,1,0])
		if negatiu:
			self.set_base(base=[[0,1,0],[-1,0,0],[0,0,1]])
			v1 = Vector([0,1,0])
			v2 = Vector([-1,0,0])
			u1 = Vector([b,a,0])
			u2 = Vector([b,-a,0])
		self.draw_hyperbole(center=center,u1=v1,u2=v2,a=a,b=b,ymax=14,thickness=0.02,steps=128,axis=False)
		self.draw_point(radius=0.167,location=(0,0,0),name="Centre",color="White")
		self.draw_point(radius=0.167,location=f1,name="F1",color="Black")
		self.draw_point(radius=0.167,location=f2,name="F2",color="Black")
		self.draw_line(start=-5*u1,end=5*u1,color="Blue",scale=0.03,name="Asímptota 1")
		self.draw_line(start=-5*u2,end=5*u2,color="Blue",scale=0.03,name="Asímptota 2")
		self.set_origin()
		self.set_base()
		self.set_rotation()
	#
	# Paràbola
	#
	def parabola(self,vertex=Vector([0,0,0]),p=5,xmax=15,eixos='XY',canonica=True):
		"""
		Draws the parabola of equation y - y0 = (x-x0)^2/(2*p) or x - x0 = (y-y0)^2/(2*p)
		Parameters:
			vertex: vertex of the parabola

			p: parameter of the parabola

			pmax: maximum value of the independent variable

			eixos: 'XY', draws y - y0 = (x-x0)^2/(2*p)
				   'YX', draws x - x0 = (y-y0)^2/(2*p)

			canonica: if True, draws the x and y axis
		"""
		if len(vertex) == 2:
			vertex = (vertex[0],vertex[1],0)
		if not isinstance(vertex,Vector):
			vertex = Vector(vertex)
		f = [0,p/2,0]
		if canonica:
			self.referencia_canonica(zaxis=False)
		u1 = Vector([1,0,0])
		u2 = Vector([0,1,0])
		if eixos == 'YX' or eixos == 'yx':
			self.set_base(base=[[0,1,0],[1,0,0],[0,0,-1]])
			u1 = Vector([0,1,0])
			u2 = Vector([1,0,0])
		self.draw_parabola(vertex=vertex,a=1/(2*p),u1=u1,u2=u2,xmax=xmax,thickness=0.02,steps=128,axis=False)
		self.reset_rotation()
		self.draw_point(radius=0.167,location=f,name="Focus",color="Black")
		self.draw_point(radius=0.167,location=(0,0,0),name="Vèrtex",color="White")
		self.draw_line(start=[-xmax-3,-p/2,0],end=[xmax+3,-p/2,0],color="Blue",scale=0.04,name="Recta directriu")
		self.set_origin()
		self.set_base()
		self.set_rotation()
	#
	# El·lipsoide de revolucio
	#
	def ellipsoide_revolucio(self,a=12,b=8,direccio='Z',punt=None):
		"""
		Draws an animation showing an ellipsoid of revolution
			a, b: semiaxis of the initial ellipse

			direccio: 'X', the initial ellipse is in the plane XZ and rotates around the X axis
					  'Y', the initial ellipse is in the plane YZ and rotates around the Y axis
					  'Z', the initial ellipse is in the plane ZX and rotates around the Z axis

			punt: if it's a value between 0 and pi, the animation shows a rotating point
		"""
		if direccio == 'X' or direccio == 'x':
			F = lambda t: (a*math.cos(t),0,b*math.sin(t))
		elif direccio == 'Y' or direccio == 'y':
			F = lambda t: (0,a*math.cos(t),b*math.sin(t))
		else:
			F = lambda t: (b*math.sin(t),0,a*math.cos(t))
		self.base_canonica()
		self.animate_revolution_surface(F,tmin=0,tmax=math.pi,steps=128,axis=direccio,point=punt)
	#
	# Hiperboloide d'una fulla de revolució
	#
	def hiperboloide_una_fulla_revolucio(self,a=3,b=2,pmax=8,direccio='Z',punt=None):
		"""
		Draws an animation showing an one sheet hyperboloid of revolution
			a, b: semiaxis of the initial hyperbole

			pmax: maximum value of the independent variable

			direccio: 'X', the initial hyperbole is in the plane XZ and rotates around the X axis
			          'Y', the initial hyperbole is in the plane YX and rotates around the Y axis
				      'Z', the initial hyperbole is in the plane ZX and rotates around the Z axis

			punt: if it's a value between 0 and pi, the animation shows a rotating point
		"""
		if direccio == 'X' or direccio == 'x':
			F = lambda t: (t,0,a*math.sqrt(1+t**2/b**2))
		elif direccio == 'Y' or direccio == 'y':
			F = lambda t: (a*math.sqrt(1+t**2/b**2),t,0)
		else:
			F = lambda t: (a*math.sqrt(1+t**2/b**2),0,t)
		self.base_canonica()
		self.animate_revolution_surface(F,tmin=-pmax,tmax=pmax,steps=128,axis=direccio,point=punt)
	#
	# Hiperboloide de dues fulles de revolució
	#
	def hiperboloide_dues_fulles_revolucio(self,a=3,b=2,pmax=8,direccio='Z',punt=None):
		"""
		Draws an animation showing a two sheet hyperboloid of revolution
			a, b: semiaxis of the initial hyperbole

			pmax: maximum value of the independent variable

			direccio: 'X', the initial hyperbole is in the plane YX and rotates around the X axis
			          'Y', the initial hyperbole is in the plane ZY and rotates around the Y axis
				      'Z', the initial hyperbole is in the plane XZ and rotates around the Z axis

			punt: if it's a value between 0 and pi, the animation shows a rotating point
		"""
		if direccio == 'X' or direccio == 'x':
			s = 'Z'
			F = lambda t: (a*math.sqrt(1+t**2/b**2),t,0)
		elif direccio == 'Y' or direccio == 'y':
			F = lambda t: (0,a*math.sqrt(1+t**2/b**2),t)
			s = 'Z'
		else:
			F = lambda t: (t,0,a*math.sqrt(1+t**2/b**2))
			s = 'X'
		self.base_canonica()
		self.animate_revolution_surface(F,tmin=0,tmax=pmax,steps=128,axis=direccio,symmetry=s,point=punt)
	#
	# Con de revolució
	#
	def con_revolucio(self,a=1.5,pmax=8,direccio='Z',punt=None):
		"""
		Draws an animation showing a cone of revolution
			a: slope of the initial straight line

			pmax: maximum value of the independent variable

			direccio: 'X', the initial line is in the plane YX and rotates around the X axis
			          'Y', the initial line is in the plane ZY and rotates around the Y axis
				      'Z', the initial line is in the plane XZ and rotates around the Z axis

			punt: if it's a value between -pmax and pmax, the animation shows a rotating point
		"""
		if direccio == 'X' or direccio == 'x':
			F = lambda t: (a*t,t,0)
		elif direccio == 'Y' or direccio == 'y':
			F = lambda t: (0,a*t,t)
		else:
			F = lambda t: (t,0,a*t)
		self.base_canonica()
		self.animate_revolution_surface(F,tmin=-pmax,tmax=pmax,steps=128,axis=direccio,point=punt)
	#
	# Paraboloide el·líptic de revolució
	#
	def paraboloide_elliptic_revolucio(self,a=0.5,pmax=5,direccio='Z',punt=None):
		"""
		Draws an animation showing an elliptic paraboloid of revolution
			a: The constant of the initial parabola

			pmax: maximum value of the independent variable

			direccio: 'X', the initial parabola is in the plane YX and rotates around the X axis
			          'Y', the initial parabola is in the plane ZY and rotates around the Y axis
				      'Z', the initial parabola is in the plane XZ and rotates around the Z axis

			punt: if it's a value between -pmax and pmax, the animation shows a rotating point
		"""
		if direccio == 'X' or direccio == 'x':
			F = lambda t: (a*t**2,t,0)
		elif direccio == 'Y' or direccio == 'y':
			F = lambda t: (0,a*t**2,t)
		else:
			F = lambda t: (t,0,a*t**2)
		self.base_canonica()
		self.animate_revolution_surface(F,tmin=0,tmax=pmax,steps=128,axis=direccio,point=punt)
	#
	# Paraboloide hiperbòlic
	#
	def paraboloide_hiperbolic_simple(self,a=3,b=4,xmax=12,ymax=12):
		"""
		Draws the hyperbolic paraboloid of equation z = x^2/a^2 - y^2/b^2
		Parameters:
			a, b: constants the defines he hyperbolic paraboloid

			xmax, ymax: maximun values of the x and y coordinates
		"""
		return self.hyperbolic_paraboloid(a2=a**2,b2=b**2,xmax=xmax,ymax=ymax,canonica=True,principal=False)
	#
	# Paraboloide elliptic
	#
	def paraboloide_elliptic_simple(self,a=3,b=4,direccio='Z',xmax=12):
		"""
		Draws the hyperbolic paraboloid of equation z = x^2/a^2 - y^2/b^2
		Parameters:
			a, b: constants the defines he hyperbolic paraboloid

			xmax, ymax: maximun values of the x and y coordinates
		"""
		if direccio == 'X' or direccio == 'x':
			u1 = Vector([0,0,1])
			u2 = Vector([0,1,0])
		elif direccio == 'Y' or direccio == 'y':
			u1 = Vector([1,0,0])
			u2 = Vector([0,0,-1])
		else:
			u1 = Vector([1,0,0])
			u2 = Vector([0,1,0])
		el = self.elliptic_paraboloid(a2=a**2,b2=b**2,u1=u1,u2=u2,xmax=xmax,cmax=xmax,canonica=True,principal=False)
		self.reset()
		return el
	#
	# Cilindre el·líptic
	#
	def cilindre_elliptic_simple(self,a=10,b=6,direccio='Z',pmax=20):
		"""
		Draws an elliptic cylinder with direction X, Y or Z
		Parameters:
			a, b: semiaxis of the ellipse

			direction: direction of translation of the ellipse

			pmax = height of the cylindrer
		"""
		if direccio == 'X' or direccio == 'x':
			u1 = Vector([0,0,1])
			u2 = Vector([0,1,0])
		elif direccio == 'Y' or direccio == 'y':
			u1 = Vector([1,0,0])
			u2 = Vector([0,0,1])
		else:
			u1 = Vector([1,0,0])
			u2 = Vector([0,1,0])
		cy = self.elliptic_cylinder(a2=a**2,b2=b**2,u1=u1,u2=u2,zmax=pmax,canonica=True,principal=False)
		el = self.draw_ellipse(a=a,b=b,u1=u1,u2=u2,thickness=0.02,steps=128,axis=False)
		self.reset()
		return list(cy) + [el]
	#
	# Cilindre hiperbòlic
	#
	def cilindre_hiperbolic_simple(self,a=4,b=3,direccio='Z',pmax=15,hmax=20):
		"""
		Draws an hyperbolic cylinder with direction X, Y or Z
		Parameters:
			a, b: semiaxis of the hyperbole

			direccio: direction of translation of the hyperbole

			pmax = maximum value of the independent variable

			hmax = height of the cylindrer
		"""
		if direccio == 'X' or direccio == 'x':
			u1 = Vector([0,0,1])
			u2 = Vector([0,1,0])
		elif direccio == 'Y' or direccio == 'y':
			u1 = Vector([1,0,0])
			u2 = Vector([0,0,1])
		else:
			u1 = Vector([1,0,0])
			u2 = Vector([0,1,0])
		cy = self.hyperbolic_cylinder(a2=a**2,b2=b**2,u1=u1,u2=u2,xmax=pmax,zmax=hmax,canonica=True,principal=False)
		hy = self.draw_hyperbole(a=a,b=b,u1=u1,u2=u2,thickness=0.02,ymax=b*math.sqrt(-1+(pmax/a)**2),steps=128,axis=False)
		self.reset()
		return list(cy) + [hy]
	#
	# Cilindre parabòlic
	#
	def cilindre_parabolic_simple(self,a=3,direccio='Z',pmax=12,hmax=45):
		r"""
		Draws a parabolic cylinder with direction X, Y or Z
		Parameters:
			a: the initial parabola has equation of type z=\pm x^2/a^2

			direccio: direction of translation of the parabola

			pmax = maximum value of the independent variable

			hmax = height of the cylindrer
		"""
		if a == 0:
			return
		if direccio == 'X' or direccio == 'x':
			u1 = Vector([0,0,1])
			u2 = Vector([0,-1,0])
			v1 = Vector([0,0,1])
			v2 = Vector([1,0,0])
		elif direccio == 'Y' or direccio == 'y':
			u1 = Vector([1,0,0])
			u2 = Vector([0,0,-1])
			v1 = Vector([1,0,0])
			v2 = Vector([0,1,0])
		else:
			u1 = Vector([1,0,0])
			u2 = Vector([0,1,0])
			v1 = Vector([1,0,0])
			v2 = Vector([0,0,1])
		s = 1
		if a < 0:
			s = -1
		cy = self.parabolic_cylinder(p=a**2/2,u1=u1,u2=u2,xmax=pmax,ymax=hmax,canonica=True,principal=False)
		pa = self.draw_parabola(a=s/a**2,u1=v1,u2=v2,thickness=0.02,xmax=pmax,steps=128,axis=False)
		self.reset()
		return list(cy) + [pa]
	#
	# Con
	#
	def con_simple(self,a=4,b=3,c=2,direccio='Z',pmax=12):
		"""
		Draws a con with direction X, Y or Z
		Parameters:
			a, b, c: semiaxis of the cone

			direccio: direction of the negative coefficient

			pmax = maximum value of the independent variables

			hmax = height of the cone
		"""
		if direccio == 'X' or direccio == 'x':
			u1 = Vector([0,0,1])
			u2 = Vector([0,-1,0])
			v1 = Vector([0,0,1])
			v2 = Vector([1,0,0])
		elif direccio == 'Y' or direccio == 'y':
			u1 = Vector([1,0,0])
			u2 = Vector([0,0,-1])
			v1 = Vector([1,0,0])
			v2 = Vector([0,1,0])
		else:
			u1 = Vector([1,0,0])
			u2 = Vector([0,1,0])
			v1 = Vector([1,0,0])
			v2 = Vector([0,0,1])
		co = self.cone(a2=a**2,b2=b**2,c2=c**2,u1=u1,u2=u2,xmax=pmax,canonica=True,principal=False)
		self.reset()
		return co
	#
	# Cilindre fitat
	#
	def cilindre(self,centre=Vector([0,0,0]),radi=1,height=5,eix='Z',color="AzureBlueDark",circlecolor="Blue"):
		"""
		Draws a bounded cylinder with direction eix
		Parameters:

		centre: center of the cylinder

		radi: radius

		height: height

		eix: X, Y, Z or a vector

		color: color of the cylinder

		circlecolor: color of the two circles of a bounded cylinder 
		"""
		if not isinstance(centre,Vector):
			centre = Vector(centre)
		if isinstance(eix,str):
			eix = eix.strip().upper()
		if eix == 'X':
			u = Vector([1,0,0])
		elif eix == 'Y':
			u = Vector([0,1,0])
		elif eix == 'Z':
			u = Vector([0,0,1])
		elif isinstance(eix,Vector):
			u = eix
		else:
			u = Vector(eix)
		
		u1 = u.orthogonal().normalized()
		u2 = u.normalized().cross(u1)
		center1 = centre + height/2 * u.normalized()
		center2 = centre - height/2 * u.normalized()
		
		c1, d1 = self.draw_circle(center=center1,radius=radi,u1=u1,u2=u2,axis=False,zaxis=False,steps=128,thickness=0.02,name="Circumferències",fillcolor=color,color=circlecolor)
		c2, d2 = self.draw_circle(center=center2,radius=radi,u1=u1,u2=u2,axis=False,zaxis=False,steps=128,thickness=0.02,name="Circumferència 2",fillcolor=color,color=circlecolor)
		_, _, cil = self.elliptic_cylinder(o=centre,a2=radi**2,b2=radi**2,u1=u1,u2=u2,principal=False,canonica=False,zmax=height/2,color=color,thickness=0.01,name="Cilindre")
		self.join([cil,d1,d2])
		self.join([c1,c2])
		self.reset()
		return cil, c1
	#
	# Esfera
	#
	def esfera(self,centre=Vector([0,0,0]),radi=10,cmax=20,name="Esfera"):
		"""
		Draws a sphere
		Parametre:
			centre: center of the sphere

			radi: radius of the sphere

			cmax: maximum values of the x, y and z coordinates
		"""
		return self.sphere(o=centre,r2=radi**2,canonica=True,principal=False,cmax=cmax,preserve=False,name=name,thickness=0.001)
	#
	# Tor
	#
	def tor(self,centre=Vector([8,0,3]),radi=3,cmax=15,punt=None):
		"""
		Draws a torus of revolution from a circumference
		Parameters:
			centre: center of the circumference

			radi: radius of the circumference

			cmax: maximum values of the x, y and z coordinates

			punt: if it's a float value, draws a moving poing
		"""
		self.base_canonica(length=cmax)
		if len(centre) == 2:
			centre = (centre[0],0,centre[1])
		if not isinstance(centre,Vector):
			centre = Vector(centre)
		def F(t):
			return (centre + Vector([radi*math.cos(t),0,radi*math.sin(t)]))
		self.animate_revolution_surface(F,tmin=0,tmax=2*math.pi,steps=128,axis='Z',point=punt)
	#
	# Revolució d'una paràbola que no és un paraboloide
	#
	def superficie_revolucio_parabola(self,a=0.2,vertex=Vector([0,0,0]),pmax=8,pla='XZ',punt=None):
		"""
		Draws an animation of a revolution surface from a paràbola
		Parameters:
			a: the paràbola is of the form y = a*x^2

			vertex: vertex of the parabola

			pmax: maximum value of the independent variable

			pla: a value from the list ('XY','YX','XZ','ZX','YZ','ZY') representing
			     the variables for the equation
				 'XY' y = a*x^2 and rotaqtion around the X axis
				 'YX' x = a*y^2 and rotaqtion around the Y axis
				 'XZ' z = a*x^2 and rotaqtion around the X axis
				 'ZX' x = a*x^2 and rotaqtion around the Z axis
				 'YZ' z = a*y^2 and rotaqtion around the Y axis
				 'ZY' y = a*z^2 and rotaqtion around the Z axis

			punt: punt: if it's a float value, draws a moving poing
		"""
		self.base_canonica()
		if not isinstance(vertex,Vector):
			vertex = Vector(vertex)
		def F(t):
			if pla.upper() == 'XZ':
				return (vertex + Vector([t,0,a*t**2]))
			if pla.upper() == 'XY':
				return (vertex + Vector([t,a*t**2,0]))
			if pla.upper() == 'ZX':
				return (vertex + Vector([a*t**2,0,t]))
			if pla.upper() == 'ZY':
				return (vertex + Vector([0,a*t**2,t]))
			if pla.upper() == 'YZ':
				return (vertex + Vector([0,t,a*t**2]))
			if pla.upper() == 'YX':
				return (vertex + Vector([a*t**2,t,0]))
		self.animate_revolution_surface(F,tmin=-pmax,tmax=pmax,steps=128,axis=pla[0],point=punt)
	#
	# Rotació d'un ortoedre
	#
	def rotacio_ortoedre(self,centre=Vector([0,0,0]),costats=Vector([8,5,4]),eix='Z',opacity=1):
		"""
		Draws an animation of an orthohedron rotating around a vectorial line
		Parameters:
			centre: center of the orthohedron

			costats: half sides of the orthohedron

			eix: axis of rotation

			opacity: opacity of the orthohedron
		"""
		self.base_canonica()
		if not isinstance(centre,Vector):
			centre = Vector(centre)
		if not isinstance(costats,Vector):
			costats = Vector(costats)
		ortoedre = self.draw_cube(origin=centre,scale=costats,color="AzureBlueDark",opacity=opacity,thickness=0.015,scalelines=0.025,linecolor="Orange",name="Ortoedre")
		self.rotate_object(ortoedre,axis=eix,draw=False)
	#
	# Rotació d'un vector
	#
	def rotacio_vector(self,vector=Vector([6,8,5]),eix=Vector([1,1,1]),adaptada=False):
		"""
		Draws an animation of a vector rotating around a vectorial line
		Parameters:
			vector: vector to rotate

			eix: axis of rotation, given by a vector or by X, Y or Z

			adaptada: if True, draws a base adapted to the rotation
		"""
		if not isinstance(vector,Vector):
			vector = Vector(vector)
		if eix == 'X':
			u = Vector([1,0,0])
		elif eix == 'Y':
			u = Vector([0,1,0])
		elif eix == 'Z':
			u = Vector([0,0,1])
		elif isinstance(eix,Vector):
			u = eix
		else:
			u = Vector(eix)
		e = vector.project(eix)
		l = e.length
		if l < 18:
			l = 18
		if adaptada:
			self.base_adaptada(axis=eix,length=l)
		self.base_canonica(length=l)
		self.rotate_vector(vector,eix,length=l)
    # 
	# Rotació d'un punt al voltant d'un eix
	#
	def rotacio_punt(self,punt=Vector([6,8,5]),origen=Vector([4,3,0]),eix=Vector([1,1,1]),vectors=True):
		"""
		Draws an animation of a point rotating around an afine line
		Parameters:
			punt: point to rotate

			origen: point of the affine line

			eix: axis of rotation, given by a vector or by X, Y or Z 
		"""
		if not isinstance(punt,Vector):
			punt = Vector(punt)
		if eix == 'X':
			u = Vector([1,0,0])
		elif eix == 'Y':
			u = Vector([0,1,0])
		elif eix == 'Z':
			u = Vector([0,0,1])
		elif isinstance(eix,Vector):
			u = eix
		else:
			u = Vector(eix)

		if not isinstance(origen,Vector):
			origen = Vector(origen)
		e = (punt-origen).project(u)
		l = e.length
		if l < 18:
			l = 18
		self.base_canonica(length=l)
		self.rotate_point(punt,origen,u,length=l,vectors=vectors)
	#
	# Rotació d'un ortoedre a partir dels angles d'Euler
	#
	def rotacio_ortoedre_angles_euler(self,centre=Vector([0,0,0]),costats=Vector([8,5,4]),psi=90,theta=60,phi=45,radians=False,opacity=1,eixos='zxz'):
		"""
		Draws an animation of an orthohedron rotating given the Euler's angles
		Parameters:
			centre: center of the orthohedron

			costats: half sides of the orthohedron

			psi, theta, phi: Euler's angles

			radians: if True the Euler's angles must in radians. If False in degrees

			opacity: opacity of the orthohedron

			eixos: axis of the three rotations
		"""
		if not isinstance(centre,Vector):
			centre = Vector(centre)
		if not isinstance(costats,Vector):
			costats = Vector(costats)
		ortoedre = self.draw_cube(origin=centre,scale=costats,color="AzureBlueDark",opacity=opacity,thickness=0.015,scalelines=0.025,linecolor="Orange",name="Ortoedre")
		self.rotate_euler(ortoedre,psi,theta,phi,radians=radians,axis=eixos)
	#
	# Rotació d'un ortoedre al voltant d'un eix i angles d'Euler
	#
	def rotacio_ortoedre_voltant_vector(self,centre=Vector([0,0,0]),costats=Vector([8,5,4]),angle=80,radians=False,vector=Vector([1,-2,1]),opacity=0.7,euler=None,reverse=False):
		"""
		Draws an animation of a vector rotating around a vectorial line
		Parameters:
			centre: center of the orthohedron

			costats: half sides of the orthohedron

			angle: angle of rotation

			radians: if True the Euler's angles must in radians. If False in degrees

			vector: generator of the vectorial line

			opacity: opacity of the orthohedron

			euler: None or the value of the three Euler's axis

			reverse: if True, shows the rotation with Euler's angles in reverse order
		"""
		if not isinstance(centre,Vector):
			centre = Vector(centre)
		if not isinstance(costats,Vector):
			costats = Vector(costats)
		if not isinstance(vector,Vector):
			vector = Vector(vector)
		ortoedre = self.draw_cube(origin=centre,scale=costats,color="AzureBlueDark",opacity=opacity,thickness=0.015,scalelines=0.025,linecolor="Orange",name="Primer ortoedre")
		if euler is not None:
			ortoedre2 = self.draw_cube(origin=centre,scale=costats,color="Green",opacity=opacity,thickness=0.015,scalelines=0.025,linecolor="Orange",name="Segon ortoedre")
		self.rotate_object_by_axis_angle(obj=ortoedre,axis=vector,angle=angle,frames=3)
		if euler is not None:
			R = Rotation(angle=angle,vector=vector)
			psi, theta, phi = R.to_euler_angles(axis=euler)
			self.rotate_euler(ortoedre2,psi=psi,theta=theta,phi=phi,axis=euler,canonica=False,reverse=reverse)
	#
	# Rotation or helical motion
	#
	def moviment_helicoidal_ortoedre(self,centre=Vector([0,0,0]),costats=Vector([3,5,2]),opacity=1,origen=Vector([4,3,0]),eix='Z',rounds=1,translacio=0.0,aligned=False):
		"""
		Draws an animation of the helical motion of an orthohedron around an affine line
		Parameters:
			centre: center of the orthohedron

			costats: half sides of the orthohedron

			origen: point of the affine line

			eix: axis of rotation

			opacity: opacity of the orthohedron

			translation: translation of the helical motion (distance by round)
			             if translation = 0.0, it's a rotation motion

			aligned: if True, aligns the orthohedron with the axis of rotation
		"""
		if isinstance(eix,str):
			eix = eix.strip().upper()
		if eix == 'X':
			u = Vector([1,0,0])
		elif eix == 'Y':
			u = Vector([0,1,0])
		elif eix == 'Z':
			u = Vector([0,0,1])
		elif isinstance(eix,Vector):
			u = eix
		else:
			u = Vector(eix)
		w1 = u.normalized()
		w2 = u.orthogonal().normalized()
		w3 = w1.cross(w2)
		self.base_canonica()
		if not isinstance(centre,Vector):
			centre = Vector(centre)
		if not isinstance(costats,Vector):
			costats = Vector(costats)
		if not isinstance(origen,Vector):
			origen = Vector(origen)
		ortoedre = self.draw_cube(origin=centre,scale=costats,color="AzureBlueDark",opacity=opacity,thickness=0.015,scalelines=0.025,linecolor="Orange",name="Ortoedre")
		if aligned:
			ortoedre.rotation_mode = 'QUATERNION'
			x = Vector([1,0,0])
			quaternion = x.rotation_difference(w1)
			ortoedre.rotation_quaternion.rotate(quaternion)
		self.rotate_object(ortoedre,axis=eix,origin=origen,translation=translacio,rounds=rounds)
	#
	# Rotation or helical motion of a cylinder
	#
	def moviment_helicoidal_cilindre(self,centre=Vector([0,0,0]),radi=3,altura=12,opacity=1,origen=Vector([4,3,0]),eix='Z',rounds=1,translacio=0.0,aligned=False,reverse=False):
		"""
		Draws an animation of the helical motion of an orthohedron around an affine line
		Parameters:
			centre: center of the cylinder

			radi: radius of the cylinder

			altura: height of the cylinder

			origen: point of the affine line

			eix: axis of rotation

			opacity: opacity of the orthohedron

			translation: translation of the helical motion (distance by round)
			             if translation = 0.0, it's a rotation motion

			aligned: if True, aligns the orthohedron with the axis of rotation
		"""
		if isinstance(eix,str):
			eix = eix.strip().upper()
		if eix == 'X':
			u = Vector([1,0,0])
		elif eix == 'Y':
			u = Vector([0,1,0])
		elif eix == 'Z':
			u = Vector([0,0,1])
		elif isinstance(eix,Vector):
			u = eix
		else:
			u = Vector(eix)
		
		w1 = u.normalized()
		w2 = u.orthogonal().normalized()
		w3 = w1.cross(w2)
		self.base_canonica()
		if not isinstance(centre,Vector):
			centre = Vector(centre)
		if not isinstance(origen,Vector):
			origen = Vector(origen)
		cil, cir = self.cilindre(centre=centre,radi=radi,height=altura,eix='Z',color="AzureBlueDark",circlecolor="Blue")
		if aligned:
			cil.rotation_mode = 'QUATERNION'
			cir.rotation_mode = 'QUATERNION'
			x = Vector([0,0,1])
			quaternion = x.rotation_difference(w1)
			cil.rotation_quaternion.rotate(quaternion)
			cir.rotation_quaternion.rotate(quaternion)
			cir.location = cil.location + altura/2 * w1
		if reverse:
			u *= -1
		self.rotate_objects([cil,cir],axis=u,origin=origen,translation=translacio,rounds=rounds,draw=True)
	#
	# Rotation or helical motion of a point
	#
	def moviment_helicoidal_punt(self,punt=Vector([0,0,0]),origen=Vector([-3,-3,-4]),eix='Z',rounds=5,translacio=2,vectors=True,reverse=False):
		"""
		Draws an animation of the helical motion of an orthohedron around an affine line
		Parameters:
			punt: posició inicial del punt

			origen: point of the affine line

			eix: axis of rotation

			rounds: rounds of the point aroud the axis

			translation: translation of the helical motion (distance by frame)
			             if translation = 0.0, it's a rotation motion
		"""
		if isinstance(eix,str):
			eix = eix.strip().upper()
		if eix == 'X':
			u = Vector([1,0,0])
		elif eix == 'Y':
			u = Vector([0,1,0])
		elif eix == 'Z':
			u = Vector([0,0,1])
		elif isinstance(eix,Vector):
			u = eix
		else:
			u = Vector(eix)
		self.base_canonica()
		if not isinstance(punt,Vector):
			punt = Vector(punt)
		if not isinstance(origen,Vector):
			origen = Vector(origen)
		self.draw_point(radius=0.2,location=punt,name="Blue",color="Blue")
		obj = self.draw_point(radius=0.2,location=punt,name="Red",color="Red")
		obj2 = None
		if vectors:
			self.set_origin(origen)
			self.draw_vector(punt-origen,name="VBlack",color="Black")
			obj2 = self.draw_vector(punt-origen,name="VRed",color="Red")
		if obj2 is None:
			if reverse:
				self.rotate_object(obj,axis=-u,origin=origen,translation=translacio,rounds=rounds,draw=True)
			else:
				self.rotate_object(obj,axis=u,origin=origen,translation=translacio,rounds=rounds,draw=True)
		else:
			if reverse:
				self.rotate_objects([obj,obj2],axis=-u,origin=origen,translation=translacio,rounds=rounds,draw=True)
			else:
				self.rotate_objects([obj,obj2],axis=u,origin=origen,translation=translacio,rounds=rounds,draw=True)
		vec1 = (punt-origen).project(u)
		center = origen + vec1
		w1 = (punt-center).normalized()
		w3 = u.normalized()
		w2 = w3.cross(w1)
		radius = (center-punt).length
		self.curve(lambda t: (radius*math.cos(t),radius*math.sin(t),translacio*t/(2*math.pi)),tmin=-2*rounds*math.pi,tmax=2*rounds*math.pi,steps=128*rounds,thickness=0.005,name="Hèlix",color="Yellow",o=center,u1=w1,u2=w2)
		self.reset()
	#
	# Gir en el pla d'un poligon
	#
	def gir_poligon(self,centre=Vector([0,0,0]),costats=6,origen=Vector([0,0,0]),radi=8):
		"""
		Draws an animation of the rotation around a point of a polygon in the plane XY
		Parameters:
			centre: center of the polygon

			costats: sides of the polygon

			origen: center of the rotation

			radi: radius of the polygon
		"""
		if len(centre) == 2:
			centre = [centre[0],centre[1],0]
		if len(origen) == 2:
			origen = [origen[0],origen[1],0]
		if not isinstance(centre,Vector):
			centre = Vector(centre)
		if not isinstance(origen,Vector):
			origen = Vector(origen)
		self.base_canonica(zaxis=False)
		self.draw_point(radius=0.167,location=origen,name="Centre del gir",color="White")
		poligon = self.draw_regular_polygon(origin=centre,vertexs=costats,radius=radi,name="Polígon regular")
		self.rotate_object(poligon,axis='Z',origin=origen,draw=False)
	#
	# Quàdriques
	#
	ellipsoide = ellipsoid
	hiperboloide_dues_fulles = two_sheets_hyperboloid
	hiperboloide_una_fulla = one_sheet_hyperboloid
	con = cone
	paraboloide_elliptic = elliptic_paraboloid
	paraboloide_hiperbolic = hyperbolic_paraboloid
	cilindre_elliptic = elliptic_cylinder
	cilindre_hiperbolic = hyperbolic_cylinder
	cilindre_parabolic = parabolic_cylinder
	#
	# Esfera i cilindre el·liptic
	#
	def esfera_cilindre_elliptic(self,radi=10,x0=5,a=5,b=5):
		"""
		Draws an sphere centered at (0,0,0), an elliptic cylinder and their intersection
		Parameters:
			radi: radius of the sphere

			x0: (x0,0,0) is the center of the ellipse in the plain XY

			a, b: semiaxis of this ellipse
		"""
		if radi <= 0:
			return
		def F(t):
			x = x0 + a*math.cos(t)
			y = b*math.sin(t)
			z = radi**2 - x**2 - y**2
			if z < 0:
				z  = 0
			z = math.sqrt(z)
			return (x,y,z)
		self.sphere(r2=radi**2,canonica=True,color="GrayLight",thickness=0.0001,pmax=3*radi+3,name="Esfera")
		self.elliptic_cylinder(o=[x0,0,0],a2=a**2,b2=b**2,principal=False,canonica=False,zmax=3*radi,thickness=0.01,name="Cilindre")
		x, y = symbols('x y',real=True)
		sol = solve([x**2 + y**2 - radi**2, (x-x0)**2/a**2 + y**2/b**2 - 1],[x,y],dict=True)
		#
		# 1. solve retorna una única solució
		# La solució és el punt (x0+a,0) o (x0-a,0,0)
		#
		if len(sol) == 1:
			#
			# L'altre vèrtex està dins o fora de la circumferència x^2 + y^2 = radi^2
			#
			if (sol[0][x] == radi and abs(x0 - a) < radi) or (sol[0][x] == - radi and abs(x0 + a) < radi):
				self.curve(F,tmin=0,tmax=2*math.pi,steps=512,thickness=0.05,color="Black",symmetry='XY',name="Corba intersecció")
			else:
				self.draw_point(radius=0.2,location=(sol[0][x],sol[0][y],0),name="Punt intersecció",color="Black",opacity=1.0)
		#
		# 2. solve retorna dues solucions
		#
		if len(sol) == 2:
			try:
				sol[0][x]
				sol[0][y]
				sol[1][x]
				sol[1][y]
				circ = False
			except:
				circ = True
			if circ:
				#
				# El cilindre és de revolució i les circumferències al pla XY coincideixen
				#
				self.draw_circle(radius=radi,steps=64,thickness=0.05,name="Circumferència",color="Black")
			else:
				#
				# Tenim dues solucions diferents, que han de ser (radi,0) i (-radi,0)
				#
				if abs(b) < radi:
					theta = [math.atan2(sol[i][y]/b,(sol[i][x] - x0)/a) for i in range(2)]
					theta.sort()
					if x0 > 0:
						self.curve(F,tmin=theta[1],tmax=2*math.pi-theta[1],steps=512,thickness=0.05,color="Black",symmetry='XY',name="Corba intersecció")
					else:
						self.curve(F,tmin=theta[0],tmax=theta[1],steps=512,thickness=0.05,color="Black",symmetry='XY',name="Corba intersecció")
				else:
					self.draw_point(radius=0.2,location=(sol[0][x],sol[0][y],0),name="Punt intersecció 1",color="Black",opacity=1.0)
					self.draw_point(radius=0.2,location=(sol[1][x],sol[1][y],0),name="Punt intersecció 2",color="Black",opacity=1.0)
		#
		# 2. solve retorna tres solucions
		#
		if len(sol) == 3:
			theta = [math.atan2(sol[i][y]/b,(sol[i][x] - x0)/a) for i in range(3)]
			theta.sort()
			if theta[1] == 0.0:
				self.curve(F,tmin=theta[0],tmax=theta[2],steps=512,thickness=0.05,color="Black",symmetry='XY',name="Corba intersecció")
			if theta[2] == math.pi:
				self.curve(F,tmin=theta[1],tmax=theta[0]+2*math.pi,steps=512,thickness=0.05,color="Black",symmetry='XY',name="Corba intersecció")
		#
		# 2. solve retorna quatre solucions
		#
		if len(sol) == 4:
			theta = [math.atan2(sol[i][y]/b,(sol[i][x] - x0)/a) for i in range(4)]
			theta.sort()
			self.curve(F,tmin=theta[2],tmax=theta[3],steps=512,thickness=0.05,color="Black",symmetry=('XY','XZ','X'),name="Corba intersecció")
	#
	# Con i cilindre el·liptic
	#
	def con_cilindre_elliptic(self,a2=1,b2=1,c2=1,x0=5,a=8,b=5,zmax=15):
		"""
		Draws a cone with vertex at (0,0,0) and equation x^2/a2 + y^2/b2 - z^2/c2 == 0,
		an elliptic cylinder and their intersection
		Parameters:
			a2, b2, c2: coefficients of the equation of the cone

			x0: (x0,0,0) is the center of the ellipse in the plain XY

			a, b: semiaxis of this ellipse

			zmax: maximum value of the z coordinate
		"""
		a2, b2, c2 = abs(a2), abs(b2), abs(c2)
		if a2*b2*c2 == 0:
			return
		xmax = zmax*math.sqrt(a2/c2)
		def F(t):
			x = x0 + a*math.cos(t)
			y = b*math.sin(t)
			z = math.sqrt(c2*(x**2/a2 + y**2/b2))
			return (x,y,z)
		self.cone(a2=a2,b2=b2,c2=c2,principal=False,canonica=True,color="GrayLight",thickness=0.0001,name="Con",xmax=xmax,cmax=xmax+5,opacity=1.0)
		self.elliptic_cylinder(o=[x0,0,0],a2=a**2,b2=b**2,principal=False,canonica=False,zmax=2*(zmax+3),thickness=0.01,name="Cilindre")
		self.curve(F,tmin=0,tmax=2*math.pi,steps=512,thickness=0.05,color="Black",symmetry='XY',name="Corba intersecció")
	#
	# Segment esfèric
	#
	def segment_esferic(self,r=10,p1=math.pi/2,s1=0,p2=math.pi/2,s2=math.pi/2,name="Segment"):
		"""
		Draws an spheric segment in a sphere centered at origin with radius r from the point
		whith spherical coordinates (radi,p1,s1) to the point (radi,p2,s2).
		Parameters:
		   r: radius of the sphere
		   p1: polar angle of the first point
		   s1: azimuthal angle of the first point
		   p2: polar angle of the second point
		   s2: azimuthal angle of the second point
		"""
		x = Vector([r*math.sin(p1)*math.cos(s1),r*math.sin(p1)*math.sin(s1),r*math.cos(p1)])
		y = Vector([r*math.sin(p2)*math.cos(s2),r*math.sin(p2)*math.sin(s2),r*math.cos(p2)])
		R = EuclideanReference(u1=x,u2=y)
		x1 = R.coordinates(x)
		y1 = R.coordinates(y)
		b = R.base()
		t0 = math.atan2(x1[1],x1[0])
		t1 = math.atan2(y1[1],y1[0])
		def F(t):
			x = r*math.cos(t)
			y = r*math.sin(t)
			z = 0
			return (x,y,z)
		c = self.draw_curve(F,tmin=t0,tmax=t1,steps=256,thickness=0.05,color="Red",name=name,u1=b[0],u2=b[1])
		return c
	#
	# Triangle esfèric
	#
	def triangle_esferic(self,r=10,p1=math.pi/2,s1=0,p2=math.pi/2,s2=math.pi/2,p3=0,s3=0):
		"""
		Draws an spheric triangle in a sphere centered at origin with radius r  with vetices
		whith spherical coordinates (radi,p1,s1), (radi,p2,s2) and (radi,p2,s2).
		Parameters:
		   r: radius of the sphere
		   p1: polar angle of the first point
		   s1: azimuthal angle of the first point
		   p2: polar angle of the second point
		   s2: azimuthal angle of the second point
		   p3: polar angle of the third point
		   s3: azimuthal angle of the third point
		"""
		es = self.esfera(r2=r**2,canonica=False,principal=False,thickness=0.001,name="Esfera")
		c1 = self.segment_esferic(r=r,p1=p1,s1=s1,p2=p2,s2=s2,name="Costat 1")
		c2 = self.segment_esferic(r=r,p1=p2,s1=s2,p2=p3,s2=s3,name="Costat 2")
		c3 = self.segment_esferic(r=r,p1=p3,s1=s3,p2=p1,s2=s1,name="Costat 3")
	#
	# Triangle esfèric aleatori
	#
	def triangle_esferic_aleatori(self,r=10):
		"""
		Draws a random spheric triangle in a sphere centered at origin with radius r 
		Parameters:
		   r: radius of the sphere
		"""
		std = math.pi/9
		mean = math.pi/2
		nums = np.random.normal(loc=mean, scale=std, size=20)
		nums = [x for x in nums if x > 0 and x < math.pi]
		p1, p2, p3 = nums[0:3]

		std = math.pi/6
		mean = 0
		nums = np.random.normal(loc=mean, scale=std, size=20)
		nums = [x for x in nums if x < math.pi/2 and x > -math.pi/2]
		s1, s2, s3 = nums[0:3]
		print(s1,s2,s3)
		self.triangle_esferic(r=r,p1=p1,s1=s1,p2=p2,s2=s2,p3=p3,s3=s3)

