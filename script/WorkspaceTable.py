#!/usr/bin/env python
from __future__ import division

import pybullet as p
import pybullet_data

from collections import OrderedDict
import os
import math
import numpy as np
import time
import IPython
from random import uniform, random

from CollisionChecker import CollisionChecker

from uniform_object_rearrangement.msg import CylinderObj

### This file defines workspace for the table ###

class WorkspaceTable(object):
    def __init__(self,
        robotBasePosition,
        standingBase_dim, table_dim, table_offset_x, 
        mesh_path, isPhysicsTurnOn, server):
        ### get the server
        self.server = server
        self.mesh_path = mesh_path
        self.known_geometries = []
        self.object_geometries = OrderedDict()
        self.createRobotStandingBase(robotBasePosition, standingBase_dim, isPhysicsTurnOn)
        self.createTableScene(robotBasePosition, table_dim, table_offset_x, isPhysicsTurnOn)
        self.table_offset_x = table_offset_x
        self.collisionAgent = CollisionChecker(self.server)

    def createRobotStandingBase(self, robotBasePosition, standingBase_dim, isPhysicsTurnOn):
        ################ create the known geometries - standingBase  ####################
        self.standingBase_dim = np.array(standingBase_dim)
        self.standingBasePosition = [
            robotBasePosition[0], robotBasePosition[1], robotBasePosition[2]-self.standingBase_dim[2]/2-0.005]
        self.standingBase_c = p.createCollisionShape(shapeType=p.GEOM_BOX,
                                    halfExtents=self.standingBase_dim/2, physicsClientId=self.server)
        self.standingBase_v = p.createVisualShape(shapeType=p.GEOM_BOX,
                                    halfExtents=self.standingBase_dim/2, physicsClientId=self.server)
        if isPhysicsTurnOn == True:
            self.standingBaseM = p.createMultiBody(
                baseCollisionShapeIndex=self.standingBase_c, baseVisualShapeIndex=self.standingBase_v,
                basePosition=self.standingBasePosition, physicsClientId=self.server)
        else:
            self.standingBaseM = p.createMultiBody(
                baseCollisionShapeIndex=self.standingBase_c, baseVisualShapeIndex=self.standingBase_v,
                basePosition=self.standingBasePosition, physicsClientId=self.server)            
        print("standing base: " + str(self.standingBaseM))
        self.known_geometries.append(self.standingBaseM)
        #################################################################################

    def createTableScene(self, 
        robotBasePosition, table_dim, table_offset_x, isPhysicsTurnOn):

        ################ create the known geometries - table  ###########################
        print("---------Enter to table scene!----------")
        # self.table_dim = np.array([table_dim[0], table_dim[1], table_dim[2]+self.standingBase_dim[2]+0.005])
        self.table_dim = np.array([table_dim[0], table_dim[1], table_dim[2]])
        self.tablePosition = [
            table_offset_x+self.table_dim[0]/2, robotBasePosition[1], robotBasePosition[2]+(self.table_dim[2]/2-self.standingBase_dim[2]-0.005)]

        self.table_c = p.createCollisionShape(shapeType=p.GEOM_BOX,
                                halfExtents=self.table_dim/2, physicsClientId=self.server)
        self.table_v = p.createVisualShape(shapeType=p.GEOM_BOX,
                                halfExtents=self.table_dim/2, physicsClientId=self.server)
        self.tableM = p.createMultiBody(baseCollisionShapeIndex=self.table_c, baseVisualShapeIndex=self.table_v,
                                            basePosition=self.tablePosition, physicsClientId=self.server)
        print("table: " + str(self.tableM))
        self.known_geometries.append(self.tableM)

        # print("inner edge of the table: ")
        # print(self.tablePosition[0]-table_dim[0]/2)
        # print("table surface: ")
        # print(self.tablePosition[2]+table_dim[2]/2)
        # print("left side of the table: ")
        # print(self.tablePosition[1]+table_dim[1]/2)
        # print("right side of the table: ")
        # print(self.tablePosition[1]-table_dim[1]/2)
        #################################################################################

    def addConstrainedArea(self, ceiling_height, thickness_flank):
        self.ceiling_height = ceiling_height
        self.thickness_flank = thickness_flank
        print("---------Add constrained area!----------")
        ################ add a constrained area - a transparent box  ####################
        self.flankColor = [111/255.0, 78/255.0, 55/255.0, 0.3]
        self.sideFlank_dim = np.array([self.table_dim[0], thickness_flank, ceiling_height])
        self.backFlank_dim = np.array([thickness_flank, self.table_dim[1]-thickness_flank*2, ceiling_height])
        self.topFlank_dim = np.array([self.table_dim[0], self.table_dim[1], thickness_flank])
        self.sideFlank_c = p.createCollisionShape(shapeType=p.GEOM_BOX,
                                    halfExtents=self.sideFlank_dim/2, physicsClientId=self.server)
        self.sideFlank_v = p.createVisualShape(shapeType=p.GEOM_BOX,
                            halfExtents=self.sideFlank_dim/2, rgbaColor=self.flankColor, physicsClientId=self.server)
        self.leftFlankPosition = [self.tablePosition[0],
                                  self.tablePosition[1] + self.table_dim[1] / 2 - thickness_flank / 2,
                                  self.tablePosition[2] + self.table_dim[2] / 2 + self.sideFlank_dim[2] / 2]
        self.rightFlankPosition = [self.tablePosition[0],
                                  self.tablePosition[1] - self.table_dim[1] / 2 + thickness_flank / 2,
                                  self.tablePosition[2] + self.table_dim[2] / 2 + self.sideFlank_dim[2] / 2]
        self.leftFlankM = p.createMultiBody(
            baseCollisionShapeIndex=self.sideFlank_c, baseVisualShapeIndex=self.sideFlank_v,
            basePosition=self.leftFlankPosition, physicsClientId=self.server)
        self.rightFlankM = p.createMultiBody(
            baseCollisionShapeIndex=self.sideFlank_c, baseVisualShapeIndex=self.sideFlank_v,
            basePosition=self.rightFlankPosition, physicsClientId=self.server)
        self.known_geometries.append(self.leftFlankM)
        self.known_geometries.append(self.rightFlankM)

        self.backFlank_c = p.createCollisionShape(shapeType=p.GEOM_BOX,
                                    halfExtents=self.backFlank_dim/2, physicsClientId=self.server)
        self.backFlank_v = p.createVisualShape(shapeType=p.GEOM_BOX,
                            halfExtents=self.backFlank_dim/2, rgbaColor=self.flankColor, physicsClientId=self.server)
        self.backFlankPosition = [self.tablePosition[0] + self.table_dim[0] / 2 - thickness_flank / 2,
                                  self.tablePosition[1], self.tablePosition[2] + self.table_dim[2] / 2 + self.backFlank_dim[2] / 2]
        self.backFlankM = p.createMultiBody(
            baseCollisionShapeIndex=self.backFlank_c, baseVisualShapeIndex=self.backFlank_v,
            basePosition=self.backFlankPosition, physicsClientId=self.server)
        self.known_geometries.append(self.backFlankM)

        self.topFlank_c = p.createCollisionShape(shapeType=p.GEOM_BOX,
                                    halfExtents=self.topFlank_dim/2, physicsClientId=self.server)
        self.topFlank_v = p.createVisualShape(shapeType=p.GEOM_BOX,
                            halfExtents=self.topFlank_dim/2, rgbaColor=self.flankColor, physicsClientId=self.server)
        self.topFlankPosition = [self.tablePosition[0], self.tablePosition[1], 
                                 self.tablePosition[2] + self.table_dim[2] / 2 + ceiling_height + thickness_flank / 2]
        self.topFlankM = p.createMultiBody(
            baseCollisionShapeIndex=self.topFlank_c, baseVisualShapeIndex=self.topFlank_v,
            basePosition=self.topFlankPosition, physicsClientId=self.server)
        self.known_geometries.append(self.topFlankM)

        self.constrained_area_center = [self.tablePosition[0]-thickness_flank/2, 0.0]
        self.constrained_area_x_limit = [self.tablePosition[0]-self.table_dim[0]/2, \
                                         self.tablePosition[0]+self.table_dim[0]/2-thickness_flank]
        self.constrained_area_y_limit = [self.tablePosition[1]-self.table_dim[1]/2+thickness_flank, \
                                         self.tablePosition[1]+self.table_dim[1]/2-thickness_flank]
        self.constrained_area_dim = [self.constrained_area_x_limit[1]-self.constrained_area_x_limit[0], \
                                     self.constrained_area_y_limit[1]-self.constrained_area_y_limit[0]]

        print("left flank: " + str(self.leftFlankM))
        print("right flank: " + str(self.rightFlankM))
        print("back flank: " + str(self.backFlankM))
        print("top flank: " + str(self.topFlankM))
        # print("constrained_area_center: ", str(self.constrained_area_center))
        # print("constrained_area_x_limit", str(self.constrained_area_x_limit))
        # print("constrained_area_y_limit", str(self.constrained_area_y_limit))
        # print("constrained_area_dim", str(self.constrained_area_dim))
        ###########################################################################################


    def generateInstance_cylinders(self, cylinder_radius, cylinder_height, num_objects):
        ### return: success (bool)

        self.num_objects = num_objects ### obtain the number of objects
        self.cylinder_radius = cylinder_radius
        self.cylinder_height = cylinder_height
        print("--------generate an instance---------")

        cylinder_c = p.createCollisionShape(shapeType=p.GEOM_CYLINDER,
                                    radius=cylinder_radius, height=cylinder_height, physicsClientId=self.server)

        for obj_i in range(num_objects):
            isCollision = True
            timeout = 20
            while isCollision and timeout > 0:
                print("generate the {}th object".format(obj_i))
                timeout -= 1
                ### generate the center of an object with uniform distribution
                start_pos = [
                    round(uniform(self.constrained_area_x_limit[0] + 2*cylinder_radius, self.constrained_area_x_limit[1] - 2*cylinder_radius), 3),
                    round(uniform(self.constrained_area_y_limit[0] + 2*cylinder_radius, self.constrained_area_y_limit[1] - 2*cylinder_radius), 3),
                    round(self.tablePosition[2] + self.table_dim[2] / 2 + cylinder_height / 2, 3)
                ]
                rgbacolor = [round(random(), 3), round(random(), 3), round(random(), 3), 1.0]
                cylinder_v = p.createVisualShape(shapeType=p.GEOM_CYLINDER,
                                radius=cylinder_radius, length=cylinder_height, rgbaColor=rgbacolor, physicsClientId=self.server)
                cylinder_objectM = p.createMultiBody(
                    baseCollisionShapeIndex=cylinder_c, baseVisualShapeIndex=cylinder_v,
                    basePosition=start_pos, physicsClientId=self.server)
                isCollision = self.collisionAgent.collisionCheck_instance_cylinder_objects(
                                        cylinder_objectM, [obj_geo.geo for obj_geo in self.object_geometries.values()], cylinder_radius)
                if isCollision:
                    ### remove that mesh as it is invalid (collision with existing object meshes)
                    p.removeBody(cylinder_objectM)
            
            if isCollision:
                return False
            else:
                ### congrats, the object's location is accepted
                self.object_geometries[obj_i] = CylinderObject(
                            obj_i, start_pos, cylinder_objectM, cylinder_radius, cylinder_height, rgbacolor)
        
        ### generate goal positions
        n_y = int(np.floor(self.constrained_area_dim[1] / (4*cylinder_radius) - 0.5))
        n_x = int(np.floor(self.constrained_area_dim[0] / (4*cylinder_radius) - 0.5))
        obj_idx = 0
        for x_i in range(n_x):
            for y_j in range(n_y):
                goal_pos = [
                    round(self.constrained_area_x_limit[0] + 3 * cylinder_radius + 4 * cylinder_radius * x_i, 3),
                    round(self.constrained_area_y_limit[0] + 3 * cylinder_radius + 4 * cylinder_radius * y_j, 3),
                    round(self.tablePosition[2] + self.table_dim[2] / 2 + cylinder_height / 2, 3)
                ]
                self.object_geometries[obj_idx].setGoalPosition(goal_pos)
                ### visualize it for confirmation
                temp_rgbacolor = [self.object_geometries[obj_idx].rgbacolor[0], self.object_geometries[obj_idx].rgbacolor[1], 
                                  self.object_geometries[obj_idx].rgbacolor[2], 0.25]
                temp_cylinder_v = p.createVisualShape(shapeType=p.GEOM_CYLINDER,
                        radius=cylinder_radius, length=cylinder_height, rgbaColor=temp_rgbacolor, physicsClientId=self.server)
                temp_cylinder_objectM = p.createMultiBody(
                     baseVisualShapeIndex=temp_cylinder_v,
                    basePosition=goal_pos, physicsClientId=self.server)                
                obj_idx += 1
                if (obj_idx >= self.num_objects):
                    break
            if (obj_idx >= self.num_objects):
                break

        ############## printing test ##############
        for obj_idx in range(self.num_objects):
            print(obj_idx)
            print(self.object_geometries[obj_idx].start_pos)
            print(self.object_geometries[obj_idx].goal_pos)
            print(self.object_geometries[obj_idx].rgbacolor)
        return True


    def reproduceInstance_cylinders(self, cylinder_objects):
        ### input: cylinder_objects (CylinderObj[])
        ### output: success (bool)

        print("--------reproduce an instance---------")

        for cylinder_obj in cylinder_objects:
            cylinder_radius = round(cylinder_obj.radius, 3)
            cylinder_height = round(cylinder_obj.height, 3)
            cylinder_rgbacolor = [
                round(cylinder_obj.rgbacolor.r, 3), round(cylinder_obj.rgbacolor.g, 3), 
                round(cylinder_obj.rgbacolor.b, 3), round(cylinder_obj.rgbacolor.a, 3)]
            cylinder_start_position = [cylinder_obj.start_position.x, cylinder_obj.start_position.y, cylinder_obj.start_position.z]
            cylinder_goal_position = [cylinder_obj.goal_position.x, cylinder_obj.goal_position.y, cylinder_obj.goal_position.z]
            cylinder_c = p.createCollisionShape(shapeType=p.GEOM_CYLINDER,
                radius=cylinder_radius, height=cylinder_height, physicsClientId=self.server)
            cylinder_v = p.createVisualShape(shapeType=p.GEOM_CYLINDER,
                radius=cylinder_radius, length=cylinder_height, rgbaColor=cylinder_rgbacolor, physicsClientId=self.server)
            cylinder_objectM = p.createMultiBody(baseCollisionShapeIndex=cylinder_c, baseVisualShapeIndex=cylinder_v,
                basePosition=cylinder_start_position, physicsClientId=self.server)
            self.object_geometries[cylinder_obj.obj_idx] = CylinderObject(
                cylinder_obj.obj_idx, cylinder_start_position, cylinder_objectM, 
                cylinder_obj.radius, cylinder_obj.height, cylinder_rgbacolor)
            self.object_geometries[cylinder_obj.obj_idx].setGoalPosition(cylinder_goal_position)
        
        return True

    
    def obtainCylinderObjectsInfo(self):
        cylinder_objects = []
        for obj_i in range(self.num_objects):
            cylinder_object = CylinderObj()
            ### fill in the data
            cylinder_object.obj_idx = obj_i
            cylinder_object.start_position.x = self.object_geometries[obj_i].start_pos[0]
            cylinder_object.start_position.y = self.object_geometries[obj_i].start_pos[1]
            cylinder_object.start_position.z = self.object_geometries[obj_i].start_pos[2]
            cylinder_object.goal_position.x = self.object_geometries[obj_i].goal_pos[0]
            cylinder_object.goal_position.y = self.object_geometries[obj_i].goal_pos[1]
            cylinder_object.goal_position.z = self.object_geometries[obj_i].goal_pos[2]
            cylinder_object.radius = self.cylinder_radius
            cylinder_object.height = self.cylinder_height
            cylinder_object.rgbacolor.r = self.object_geometries[obj_i].rgbacolor[0]
            cylinder_object.rgbacolor.g = self.object_geometries[obj_i].rgbacolor[1]
            cylinder_object.rgbacolor.b = self.object_geometries[obj_i].rgbacolor[2]
            cylinder_object.rgbacolor.a = self.object_geometries[obj_i].rgbacolor[3]
            cylinder_objects.append(cylinder_object)
        return cylinder_objects


    def generateInstance_fix(self, cylinder_radius, cylinder_height, num_objects):
        self.num_objects = num_objects ### obtain the number of objects
        self.cylinder_radius = cylinder_radius
        self.cylinder_height = cylinder_height
        print("--------generate an instance---------")

        self.cylinder_c = p.createCollisionShape(shapeType=p.GEOM_CYLINDER,
                                    radius=cylinder_radius, height=cylinder_height, physicsClientId=self.server)

        ### so far hard-code three cylinder_object
        object1_start_pos = [0.9, 0.127, 0.73]
        object1_rgbacolor = [0.988, 0.76, 0.435, 1.0]
        cylinder_object1_v = p.createVisualShape(shapeType=p.GEOM_CYLINDER,
                                    radius=cylinder_radius, length=cylinder_height, rgbaColor=object1_rgbacolor, physicsClientId=self.server)
        self.cylinder_object1M = p.createMultiBody(
            baseCollisionShapeIndex=self.cylinder_c, baseVisualShapeIndex=cylinder_object1_v,
            basePosition=object1_start_pos, physicsClientId=self.server)
        self.object_geometries[0] = CylinderObject(
            0, object1_start_pos, self.cylinder_object1M, cylinder_radius, cylinder_height, object1_rgbacolor)

        object2_start_pos = [1.102, -0.207, 0.73]
        object2_rgbacolor = [0.076, 0.117, 0.261, 1.0]
        cylinder_object2_v = p.createVisualShape(shapeType=p.GEOM_CYLINDER,
                                    radius=cylinder_radius, length=cylinder_height, rgbaColor=object2_rgbacolor, physicsClientId=self.server)
        self.cylinder_object2M = p.createMultiBody(
            baseCollisionShapeIndex=self.cylinder_c, baseVisualShapeIndex=cylinder_object2_v,
            basePosition=object2_start_pos, physicsClientId=self.server)
        self.object_geometries[1] = CylinderObject(
            0, object2_start_pos, self.cylinder_object2M, cylinder_radius, cylinder_height, object2_rgbacolor)

        object3_start_pos = [0.96, -0.061, 0.73]
        object3_rgbacolor = [0.298, 0.117, 0.344, 1.0]
        cylinder_object3_v = p.createVisualShape(shapeType=p.GEOM_CYLINDER,
                                    radius=cylinder_radius, length=cylinder_height, rgbaColor=object3_rgbacolor, physicsClientId=self.server)
        self.cylinder_object3M = p.createMultiBody(
            baseCollisionShapeIndex=self.cylinder_c, baseVisualShapeIndex=cylinder_object3_v,
            basePosition=object3_start_pos, physicsClientId=self.server)
        self.object_geometries[2] = CylinderObject(
            0, object3_start_pos, self.cylinder_object3M, cylinder_radius, cylinder_height, object3_rgbacolor)

        # object1_goal_pos = [0.862-0.1, -0.295, 0.73]
        object1_goal_pos = [0.862, -0.295, 0.73]
        object1_goal_v = p.createVisualShape(shapeType=p.GEOM_CYLINDER,
                        radius=cylinder_radius, length=cylinder_height, 
                        rgbaColor=object1_rgbacolor[0:3]+[0.25], physicsClientId=self.server)
        self.cylinder_object1M_goal = p.createMultiBody(
            baseCollisionShapeIndex=self.cylinder_c, baseVisualShapeIndex=object1_goal_v,
            basePosition=object1_goal_pos, physicsClientId=self.server)
        self.object_geometries[0].setGoalPosition(object1_goal_pos)

        object2_goal_pos = [0.862, -0.155, 0.73]
        object2_goal_v = p.createVisualShape(shapeType=p.GEOM_CYLINDER,
                        radius=cylinder_radius, length=cylinder_height, 
                        rgbaColor=object2_rgbacolor[0:3]+[0.25], physicsClientId=self.server)
        self.cylinder_object2M_goal = p.createMultiBody(
            baseCollisionShapeIndex=self.cylinder_c, baseVisualShapeIndex=object2_goal_v,
            basePosition=object2_goal_pos, physicsClientId=self.server)
        self.object_geometries[1].setGoalPosition(object2_goal_pos)

        object3_goal_pos = [0.862, -0.015, 0.73]
        object3_goal_v = p.createVisualShape(shapeType=p.GEOM_CYLINDER,
                        radius=cylinder_radius, length=cylinder_height, 
                        rgbaColor=object3_rgbacolor[0:3]+[0.25], physicsClientId=self.server)
        self.cylinder_object3M_goal = p.createMultiBody(
            baseCollisionShapeIndex=self.cylinder_c, baseVisualShapeIndex=object3_goal_v,
            basePosition=object3_goal_pos, physicsClientId=self.server)
        self.object_geometries[2].setGoalPosition(object3_goal_pos)

        ############## printing test ##############
        for obj_idx in range(3):
            print(obj_idx)
            print(self.object_geometries[obj_idx].start_pos)
            print(self.object_geometries[obj_idx].goal_pos)
            print(self.object_geometries[obj_idx].rgbacolor)
        return True


    def deployAllGoalPositions(self, object_interval, side_clearance, cylinder_radius, cylinder_height):
        ################ This function calculate all possible postions (x,y) ################
        ############### given the constrained area + distance between objects ###############
        self.all_goal_positions = OrderedDict()
        ### formula for compute n_y and n_x (number of objects in y and x direction)
        ### 2*r + gc + (2r+oi)*(n_y-1) + gc = |y|
        ### 2*r + gc + (2r+oi)*(n_x-1) + gc = |x|
        n_y = int(np.floor((self.constrained_area_dim[1]-2*(cylinder_radius+side_clearance)) \
                / (2*cylinder_radius+object_interval) + 1))
        n_x = int(np.floor((self.constrained_area_dim[0]-2*(cylinder_radius+side_clearance)) \
                / (2*cylinder_radius+object_interval) + 1))
        obj_idx = 0
        for x_i in range(n_x):
            for y_j in range(n_y):
                goal_pos = [
                    round(self.constrained_area_x_limit[0] + side_clearance + cylinder_radius + (2*cylinder_radius+object_interval) * x_i, 3),
                    round(self.constrained_area_y_limit[0] + side_clearance + cylinder_radius + (2*cylinder_radius+object_interval) * y_j, 3),
                    round(self.tablePosition[2] + self.table_dim[2] / 2 + cylinder_height / 2, 3)
                ]
                self.all_goal_positions[obj_idx] = goal_pos
                obj_idx += 1
        # print("print all goal positions")
        # print(self.all_goal_positions)


### general class of object in the workspace
class AnyObject(object):
    def __init__(self, index, start_pos, geo):
        self.object_index = index
        self.start_pos = start_pos
        self.geo = geo

    def setPos(pos):
        self.pos = pos
    
class CylinderObject(AnyObject):
    def __init__(self, index, start_pos, geo, cylinder_radius, cylinder_height, rgbacolor):
        ### invoking the __init__ of the parent class
        AnyObject.__init__(self, index, start_pos, geo)
        self.cylinder_radius = cylinder_radius
        self.cylinder_height = cylinder_height
        self.rgbacolor = rgbacolor

    def setGoalPosition(self, goal_pos):
        self.goal_pos = goal_pos




'''  below is not used but kept for legacy or in case of future use 
def dropObjectOnTable(self, obj_name, dropHeight):
    ### This function drop an obj of a specified configs and random position (table region)
    ### on the table
    ### input -> mesh_folder, the directory where the meshes are stored
    ###          obj_name, the name of the object you want to drop
    ###          tablePosition: [x, y, z(height)]
    ###          table_dim: np.array([x, y, z(height)])
    ###          dropHeight: float value, indicating at what height will the object be dropped
    ###          server: specified which server to use
    ### Output -> object mesh produced which is on the table
    ###           (but you should no access to the ground truth pose so as to mimic the reality)


    object_configs_angles = {
        "003_cracker_box": [[-0.035, -0.336, 87.775], [89.801, -2.119, 112.705], [-25.498, -84.700, 110.177]],
        "004_sugar_box": [[-0.166, -0.100, -144.075], [90.822, -1.909, 67.882], [-7.177, -79.030, 102.698]],
        "006_mustard_bottle": [[0.006, 0.061, -135.114], [87.134, -1.560, 89.805]],
        "008_pudding_box": [[89.426, 0.412, -96.268], [-0.721, 0.300, -138.733]],
        "010_potted_meat_can": [[-0.131, -0.061, 97.479], [87.863, -1.266, -65.330]],
        "021_bleach_cleanser": [[-0.103, -0.082, -39.439], [-84.349, -1.891, -177.925]]
    }

    massList = {
        "003_cracker_box": 2.32,
        "004_sugar_box": 1.7,
        "005_tomato_soup_can": 3.5,
        "006_mustard_bottle": 1.9,
        "008_pudding_box": 1.1,
        "009_gelatin_box": 0.8,
        "010_potted_meat_can": 2.8,
        "011_banana": 1.0,
        "019_pitcher_base": 1.6,
        "021_bleach_cleanser": 2.7
    }

    obj_path = os.path.join(self.mesh_path, obj_name, "google_16k/textured.obj")
    _c = p.createCollisionShape(shapeType=p.GEOM_MESH, fileName=obj_path, meshScale=[1, 1, 1], physicsClientId=self.server)
    _v = p.createVisualShape(shapeType=p.GEOM_MESH, fileName=obj_path, meshScale=[1, 1, 1], physicsClientId=self.server)
    ### random position given the table position and table_dim
    temp_pos = [random.uniform(self.tablePosition[0]-self.table_dim[0]/2+0.1, self.tablePosition[0]+self.table_dim[0]/2-0.1), \
                random.uniform(self.tablePosition[1]+0.1, self.tablePosition[1]+self.table_dim[1]/2-0.1), \
                self.tablePosition[2]+self.table_dim[2]/2+dropHeight]
    print("temp_pos")
    print(temp_pos)

    ### select one configuration
    temp_angles = random.choice(object_configs_angles[obj_name])
    ### add some randomness on the orientation around z-axis
    temp_angles[2] = temp_angles[2] + random.uniform(-180, 180)
    temp_quat = p.getQuaternionFromEuler([i*math.pi/180 for i in temp_angles])
    ### create the mesh for the object
    # _m = p.createMultiBody(baseCollisionShapeIndex=_c, baseVisualShapeIndex=_v,
    #                         basePosition=pos, baseOrientation=quat, physicsClientId=server)
    _m = p.createMultiBody(baseMass=massList[obj_name], baseCollisionShapeIndex=_c, baseVisualShapeIndex=_v,
                            basePosition=temp_pos, baseOrientation=temp_quat, physicsClientId=self.server)

    ### ready to drop the object
    p.setGravity(0.0, 0.0, -9.8, physicsClientId=self.server)
    p.setRealTimeSimulation(enableRealTimeSimulation=1, physicsClientId=self.server)
    ### wait for one second after the drop
    time.sleep(1.5)
    p.setRealTimeSimulation(enableRealTimeSimulation=0, physicsClientId=self.server)

    ### register this object
    self.obj_name = obj_name
    self.object_geometries[_m] = self.obj_name


def fixAnObjectOnTable(self, obj_name):

    ### This is just a test function

    object_configs_angles = {
        "003_cracker_box": [[-0.035, -0.336, 87.775], [89.801, -2.119, 112.705], [-25.498, -84.700, 110.177]],
        "004_sugar_box": [[-0.166, -0.100, -144.075], [90.822, -1.909, 67.882], [-7.177, -79.030, 102.698]],
        "006_mustard_bottle": [[0.006, 0.061, -135.114], [87.134, -1.560, 89.805]],
        "008_pudding_box": [[89.426, 0.412, -96.268], [-0.721, 0.300, -138.733]],
        "010_potted_meat_can": [[-0.131, -0.061, 97.479], [87.863, -1.266, -65.330]],
        "021_bleach_cleanser": [[-0.103, -0.082, -39.439], [-84.349, -1.891, -177.925]]
    }

    massList = {
        "003_cracker_box": 2.32,
        "004_sugar_box": 1.7,
        "005_tomato_soup_can": 3.5,
        "006_mustard_bottle": 1.9,
        "008_pudding_box": 1.1,
        "009_gelatin_box": 0.8,
        "010_potted_meat_can": 2.8,
        "011_banana": 1.0,
        "019_pitcher_base": 1.6,
        "021_bleach_cleanser": 2.7
    }

    obj_path = os.path.join(self.mesh_path, obj_name, "google_16k/textured.obj")
    _c = p.createCollisionShape(shapeType=p.GEOM_MESH, fileName=obj_path, meshScale=[1, 1, 1], physicsClientId=self.server)
    _v = p.createVisualShape(shapeType=p.GEOM_MESH, fileName=obj_path, meshScale=[1, 1, 1], physicsClientId=self.server)
    ### random position given the table position and table_dim
    # temp_pos = [random.uniform(self.tablePosition[0]-self.table_dim[0]/2+0.1, self.tablePosition[0]+self.table_dim[0]/2-0.1), \
    #             random.uniform(self.tablePosition[1]+0.1, self.tablePosition[1]+self.table_dim[1]/2-0.1), \
    #             self.tablePosition[2]+self.table_dim[2]/2]
    temp_pos = [0.80, 0.45, self.tablePosition[2] + self.table_dim[2]/2 + 0.03]
    temp_quat = [0.0, 0.707, 0.0, 0.707]


    ### select one configuration
    # temp_angles = object_configs_angles[obj_name][0]
    ### add some randomness on the orientation around z-axis
    # temp_angles[2] = temp_angles[2] + random.uniform(-180, 180)
    # temp_quat = p.getQuaternionFromEuler([i*math.pi/180 for i in temp_angles])
    ### create the mesh for the object
    # _m = p.createMultiBody(baseCollisionShapeIndex=_c, baseVisualShapeIndex=_v,
    #                         basePosition=pos, baseOrientation=quat, physicsClientId=server)
    _m = p.createMultiBody(baseMass=massList[obj_name], baseCollisionShapeIndex=_c, baseVisualShapeIndex=_v,
                            basePosition=temp_pos, baseOrientation=temp_quat, physicsClientId=self.server)

    ### ready to drop the object
    # p.setGravity(0.0, 0.0, -9.8, physicsClientId=self.server)
    # p.setRealTimeSimulation(enableRealTimeSimulation=1, physicsClientId=self.server)
    ### wait for one second after the drop
    time.sleep(1.5)
    # p.setRealTimeSimulation(enableRealTimeSimulation=0, physicsClientId=self.server)

    ### register this object
    self.obj_name = obj_name
    self.object_geometries[_m] = self.obj_name

### This function is disabled
def getObjectInfo(self):
    ### this function is called to get the object information
    ### which includes (1) the object name
    ### (2) current object pose
    obj_pose = p.getBasePositionAndOrientation(
        self.object_geometries.keys()[0], physicsClientId=self.server)
    obj_pose = [list(obj_pose[0]), list(obj_pose[1])]
    return self.obj_name, obj_pose


def updateObjectMesh(self, object_pose):
    ### this function is called to update the object pose
    ### NOTE: it should be only called by planning scene
    ### here the object_pose is a msg of ObjectPoseBox (dims, position, orientation)

    ### first check if the object is already in the scene
    if not self.object_geometries:
        ### no object is registered, so we need to add the object
        _c = p.createCollisionShape(
            shapeType=p.GEOM_BOX, halfExtents=np.array(object_pose.dims)/2, 
                        meshScale=[1, 1, 1], physicsClientId=self.server)
        _v = p.createVisualShape(
            shapeType=p.GEOM_BOX, halfExtents=np.array(object_pose.dims)/2, 
                    meshScale=[1, 1, 1], rgbaColor=[0.35, 0.35, 0.35, 1], physicsClientId=self.server)
        _m = p.createMultiBody(
            baseCollisionShapeIndex=_c, baseVisualShapeIndex=_v,
            basePosition=object_pose.position, baseOrientation=object_pose.orientation, 
            physicsClientId=self.server)
        self.object_geometries[_m] = [[list(object_pose.position), list(object_pose.orientation)], object_pose.dims]
        # print(self.object_geometries)

    else:
        ### we first need to remove the current object mesh
        # print(self.object_geometries.keys()[0])
        p.removeBody(self.object_geometries.keys()[0], physicsClientId=self.server)
        self.object_geometries = OrderedDict()
        ### generate the new object mesh
        _c = p.createCollisionShape(
            shapeType=p.GEOM_BOX, halfExtents=np.array(object_pose.dims)/2, 
                        meshScale=[1, 1, 1], physicsClientId=self.server)
        _v = p.createVisualShape(
            shapeType=p.GEOM_BOX, halfExtents=np.array(object_pose.dims)/2, 
                    meshScale=[1, 1, 1], rgbaColor=[0.35, 0.35, 0.35, 1], physicsClientId=self.server)
        _m = p.createMultiBody(
            baseCollisionShapeIndex=_c, baseVisualShapeIndex=_v,
            basePosition=object_pose.position, baseOrientation=object_pose.orientation, 
            physicsClientId=self.server)
        self.object_geometries[_m] = [[list(object_pose.position), list(object_pose.orientation)], object_pose.dims]
        # print(self.object_geometries)


def detectHeight(self):
    ### this function check the shortest distance between the object and the table
    pts = p.getClosestPoints(
        bodyA=self.known_geometries[-1], bodyB=self.object_geometries.keys()[0], distance=20)
    print("pts")
    print(pts)
    return pts[0][8] ### shortest contactDistance between the table and the object


def updateObjectGeomeotry_BoundingBox(self, object_pose, object_dim):
    ### This function update the object given
    ### (1) object_pose Pose3D (position(x,y,z), orientation(x,y,z,w))
    ### (2) object_dim BoundingBox3D (x, y, z)
    ### we assume the object is modelled as the bounding box in the planning scene
    object_dim = np.array([object_dim[0], object_dim[1], object_dim[2]])
    object_pose = [[object_pose.position.x, object_pose.position.y, object_pose.position.z], \
        [object_pose.orientation.x, object_pose.orientation.y, object_pose.orientation.z, object_pose.orientation.w]]

    if not bool(self.object_geometries):
        ### no object geometries has been introduced before
        ### then create the object geometry
        geo_c = p.createCollisionShape(shapeType=p.GEOM_BOX,
                            halfExtents=object_dim/2, physicsClientId=self.server)
        geo_v = p.createVisualShape(shapeType=p.GEOM_BOX, halfExtents=object_dim/2,
                    rgbaColor=[128.0/255.0, 128.0/255.0, 128.0/255.0, 0.8], physicsClientId=self.server)
        tableM = p.createMultiBody(baseCollisionShapeIndex=geo_c, baseVisualShapeIndex=geo_v,
                basePosition=object_pose[0], baseOrientation=object_pose[1], physicsClientId=self.server)
    else:
        print("The idea is to update the mesh")
        print("will come back later")


def enablePhysicsEnv(self):
    p.setGravity(0.0, 0.0, -9.8, physicsClientId=self.server)
    p.setRealTimeSimulation(enableRealTimeSimulation=1, physicsClientId=self.server)


def disablePhysicsEnv(self):
    p.setRealTimeSimulation(enableRealTimeSimulation=0, physicsClientId=self.server)
'''