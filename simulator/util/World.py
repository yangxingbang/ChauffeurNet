from .Actor import Actor
from .Camera import Camera

#import util.Actor #Keep in mind that this is how you can import this package, among the other ways above
# print (sys.modules[__name__])
# print (dir(sys.modules[__name__]))
# print (sys.modules[__name__].__package__)
import sys
import os
import random
import string
import h5py
import numpy as np
from config import Config
import importlib


import threading
import functools
import time
def synchronized(wrapped):
    lock = threading.Lock()
    # print lock, id(lock)
    @functools.wraps(wrapped)
    def _wrap(*args, **kwargs):
        with lock:
            # print ("Calling '%s' with Lock %s from thread %s [%s]"
            #        % (wrapped.__name__, id(lock),
            #        threading.current_thread().name, time.time()))
            result = wrapped(*args, **kwargs)
            # print ("Done '%s' with Lock %s from thread %s [%s]"
            #        % (wrapped.__name__, id(lock),
            #        threading.current_thread().name, time.time()))
            return result
    return _wrap


class World(Actor):
    # world中包含actor， world文件的路径， 交通灯文件的路径
    def __init__(self, actors = [], world_path = "", traffic_lights_path = "" ):
        # init创建了一个actor,它包括颜色，局部到全局的转换矩阵，局部的坐标，全局的坐标，画多边形，渲染的厚度（？），是否激活，是否能用鼠标操作
        # 但是初始化的Actor没有被用到，而是使用外部传进来的Actor
        super().__init__()
        self.actors = actors
        self.save_path = world_path
        self.traffic_lights_path = traffic_lights_path
        print("world path: ", world_path)
        print("traffic_lights_path: ", traffic_lights_path)
        # Python pass 是空语句，是为了保持程序结构的完整性
        # pass 不做任何事情，一般用做占位语句
        pass

    #@Override
    def render(self, image = None, C = None, reset_image=True):
        if reset_image:
            image.fill(0)
        for actor in self.actors:
            image = actor.render(image, C)
        return image


    # @Override
    def simulate(self, pressed_key=None, mouse=None):
        for actor in self.actors:
            actor.simulate(pressed_key, mouse)

    def save_world(self, overwrite = False):
        for actor in self.actors:
            actor.set_inactive()
        directory = os.path.dirname(self.save_path)
        if not os.path.exists(directory):
            os.mkdir(directory)
        if os.path.exists(self.save_path) and not overwrite:
            filename_ext = os.path.basename(self.save_path)
            filename, ext = os.path.splitext(filename_ext)
            UID = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
            filename = filename + UID + ".h5"
            self.save_path = os.path.join(directory, filename)

        # The following spagetti code, takes the class names of all actors, counts the actors, and and creates a dataset for each type in h5py
        # No need to save the vehicle state (to_h5py), because in WorldEditor there is no vehicle
        dict_datasets = {} #{"name":[]}
        for actor in self.actors:
            if not actor.__class__.__name__ in dict_datasets.keys():
                dict_datasets[actor.__class__.__name__] = []
            actor_vect = actor.to_h5py()
            dict_datasets[actor.__class__.__name__].append(actor_vect)
        file = h5py.File(self.save_path, "w")
        print (dict_datasets.keys())
        print (len(dict_datasets["LaneMarking"]))
        print (len(dict_datasets["Camera"]))
        for class_name in dict_datasets.keys():

            list_actors_for_class_name = dict_datasets[class_name]
            all_actors = np.array(list_actors_for_class_name )
            dset = file.create_dataset(class_name, all_actors.shape,dtype=np.float32 )

            dset[...] = all_actors
        file.close()
        print ("world saved")

    def get_camera_from_actors(self):
        camera = None
        for actor in self.actors:
            if type(actor) is Camera:
                camera = actor
                camera.C = camera.create_cammera_matrix(camera.T,camera.K)
                # when camera is loaded from hdf5, the object of type camera is created, then only the T is initialized from hdf5, C remains uninitialized
        if camera is None:
            camera = Camera()
            self.actors.append(camera)
            print("No camera")
        return camera

    def read_obj_file(self, path):

        #TODO might need to read the lines between vertices

        '''
        从下边的代码我发现，读取的obj文件中是一系列字符串加数值的组合，字符（串）后边会跟着表示位置的数值
        然后通过字符（串）的解析，把这些值读出来，放进all_objects里边
        '''

        with open(path) as file:
            # 读取文件的所有行
            all_lines = file.readlines()
            file.close()

        all_objects = {}
        # 这个while循环是读取了一系列点和线，相当于构建了地图中的点和线吗？
        # 线最可能是车道线，那么点是什么？
        i = 0
        # yxb: fake length：10
        # while i < len(all_lines):
        while i < 100000:
            print(i)
            line = all_lines[i]

            # 某行的第一个元素，如果是字母o，
            # 猜测：object？
            if line[0] == "o":
                object_name = line.split(" ")[-1].replace("\n", "")
                object_vertices = []
                object_lines = []
                i += 1
                # 如果某行的第一个元素是v，代表点vertex
                while i < len(all_lines) and all_lines[i][0] == "v":
                    object_vertices.append(all_lines[i])
                    i += 1
                # 如果某行的第一个元素是l，代表线line
                while i < len(all_lines) and all_lines[i][0] == "l":
                    object_lines.append(all_lines[i])
                    i +=1

                all_objects[object_name] = {"verts":object_vertices,
                                            "lines":object_lines}
            else:
                i += 1

        for objname in all_objects.keys():
            # 用objname和它的键值verts就能取到所有的点
            ##### 获取所有点的坐标
            object_vertices = all_objects[objname]["verts"]
            vertices_numeric = []
            for vertex in object_vertices:
                # 遍历每个点，给它们加上坐标
                coords_str = vertex.replace("v ", "").replace("\n", "").split(" ") + ["1.0"]
                # 把一串坐标中的每一个值都存起来
                coords_numeric = [float(value) for value in coords_str]
                # 添加到另一个list中
                vertices_numeric.append(coords_numeric)
            vertices_numeric = np.array(vertices_numeric).T
            # 把第0，1，2行的点的坐标乘以世界的比例因子
            vertices_numeric[:3,:] *= Config.world_scale_factor
            # 把第0行的点的坐标全部赋为-1，这表示世界的边界吗？
            vertices_numeric[0,:] *= Config.scale_x

            all_objects[objname]["verts"] = vertices_numeric

            ##### 获取所有线的数值量
            object_lines = all_objects[objname]["lines"]
            lines_numeric = []
            for line in object_lines:
                lines_str = line.replace("l ", "").replace("\n", "").split(" ")
                lines_inds_numeric = [int(value) for value in lines_str]
                lines_numeric.append(lines_inds_numeric)
            lines_numeric = np.array(lines_numeric)
            lines_numeric -= lines_numeric.min()
            all_objects[objname]["lines"] = lines_numeric

        return all_objects

    def get_traffic_lights(self):
        from simulator.util.TrafficLight import TrafficLight
        list_traffic_lights  = []
        for actor in self.actors:
            if type(actor) is TrafficLight:
                list_traffic_lights.append(actor)
        return list_traffic_lights

    def load_world(self):
        from simulator.util.LaneMarking import LaneMarking
        from simulator.util.TrafficLight import TrafficLight
        if not os.path.exists(self.save_path):
            raise ("No world available")
            print("No world available")
        all_objects = self.read_obj_file(self.save_path)

        # yxb
        if all_objects == {}:
            print("world is empty!")

        for obj_name in all_objects.keys():
            if "lane" in obj_name:
                lane_instance = LaneMarking()
                lane_instance.vertices_W = all_objects[obj_name]["verts"]
                self.actors.append(lane_instance)
            if  "tl" in obj_name:
                traffic_light_instance = TrafficLight(obj_name)
                traffic_light_instance.vertices_W = all_objects[obj_name]["verts"]
                traffic_light_instance.line_pairs = all_objects[obj_name]["lines"]
                self.actors.append(traffic_light_instance)

        # file = h5py.File(self.save_path, "r")
        # for class_name in file.keys():
        #     # module_imported =importlib.import_module("util")
        #     #If error while doing instance = class_(). Check if the imported class is listed in __init__.py
        #     module_imported =importlib.import_module(sys.modules[__name__].__package__)
        #     class_ = getattr(module_imported, class_name)
        #     for i in range(file[class_name].shape[0]):
        #         instance = class_()
        #
        #         instance.from_h5py(file[class_name][i])
        #         self.actors.append(instance)
        # file.close()

