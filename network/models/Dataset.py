import numpy as np
from torch.utils.data import Dataset
from math import *
from config import Config
if not Config.linux_env:
    import matplotlib.pyplot as plt
from simulator.UI.Record import EventBag
from simulator.util.World import World
from simulator.util.Vehicle import Vehicle
from simulator.util.Path import Path
import cv2
from simulator.util.Camera import Camera
from simulator.util.LaneMarking import LaneMarking
from simulator.util.TrafficLight import TrafficLight

class EnumIndices:
    turn_angle_start_idx = 0
    future_points_start_idx = 1
    end_idx = int(future_points_start_idx + 2 * (40 / 5)) #LOOK IN Path class to know how many points there are

class DrivingDataset(Dataset):

    def __init__(self, event_bag_path, world_path, debug = False):
        """
        Args:
            hdf5_file (string): Path to the hdf5 file with annotations.
        """

        self.debug = debug
        self.world = World(world_path=world_path)
        self.world.load_world()
        self.camera = self.world.get_camera_from_actors()
        self.vehicle = Vehicle(self.camera, play=False)
        self.world.actors.append(self.vehicle)
        self.traffic_lights = self.world.get_traffic_lights()

        self.event_bag = EventBag(event_bag_path, record=False)
        self.path = Path(self.event_bag.list_states, debug=debug)

        self.num_channels = 6

    def __len__(self):
        return len(self.event_bag) - Config.num_future_poses

    def add_noise_over_camera(self):
        def get_sin_noise():
            noise = np.sin(self.iter / 10)  # * 5 (increase amplitude)
            return noise
        cam_params = list(self.camera.get_transform())
        noise = get_sin_noise()
        #cam_params[0] += noise * 10 #x
        #cam_params[2] += noise * 10 #z
        cam_params[4] += noise / 20 #yaw
        self.camera.set_transform(*cam_params)

    def future_penalty_map(self, points):

        #TODO points received in here should be in the full resolution. when downsampled to the network output, only then I should apply the fractional part regression

        points = points / Config.scale_factor
        radius = int(ceil(20 / Config.o_ratio))
        sigma = 0.3333 * radius


        points = np.reshape(points,(-1,2))
        num_points = points.shape[0]
        future_poses = np.zeros((num_points, 1, Config.o_res[0], Config.o_res[1]), np.float32)
        # 代码作者解释2：
        # 关键路点是使用softmax后得到的空间的argmax。假如我们预测了5个关键路点，那我们需要5对xy坐标的真值来求解交叉熵。
        # 然而我认为假如网络预测了xy，这个结果不应该被过多惩罚，因此我需要一个在真值xy附近建立惩罚地图，
        # 它应该是一个gaussian zone of reduced penalty. 我从CornerNet paper得到的这个灵感。
        # 因为网络是对缩减分辨率以后的空间做softmax，分辨率为原来的3倍，因此预测结果是粗糙的
        # 为了改善预测结果，对于每一个关键路点，网络学习预测x和y的argmax位置的偏置
        # 因此每一个关键路点包含3个feature地图，其中一个对x和y应用了空间的softmax，另一个对x进行回归偏置，还有一个对y进行回归偏置
        # 在训练的时候，仅与真值进行损失计算。用哪一个与真值计算损失？
        future_poses_regr_offset = np.zeros((num_points, 2, Config.o_res[0], Config.o_res[1]), np.float32)

        for i in range(num_points):
            x_i,y_i = int(points[i,0]), int(points[i,1])
            if x_i > Config.o_res[1] - radius:continue
            if x_i < radius:continue
            if y_i > Config.o_res[0] - radius:continue
            if y_i < radius:continue
            for col in range(x_i - radius, x_i + radius):
                for row in range(y_i - radius, y_i + radius):
                    centred_col = col - x_i
                    centred_row = row - y_i
                    future_poses[i, 0, row, col] = exp(-((centred_col ** 2 + centred_row ** 2)) / (2 * sigma ** 2))

            future_poses_regr_offset[i, 0, y_i, x_i] = points[i,0] - x_i
            future_poses_regr_offset[i, 1, y_i, x_i] = points[i,1] - y_i

        if False:
            # fig, (ax1) = plt.subplots(1, 1)
            # for i in range(8):
            #     ax1.clear()
            #     image_plot1 = ax1.imshow(np.squeeze(future_poses[i, 0, ...]))
            #     plt.colorbar(image_plot1, ax = ax1)
            #     plt.show()
            for i in range(8):
                plt.imshow(np.squeeze(future_poses[i, 0, ...]))
                plt.show()
        return future_poses, future_poses_regr_offset

    def __getitem__(self, idx):
        state = self.event_bag[idx]
        self.vehicle.T = state["vehicle"]["T"]
        self.camera.C = self.camera.create_cammera_matrix(state["vehicle"]["cameraT"], self.camera.K)
        self.vehicle.camera.C = self.camera.C
        self.vehicle.vertices_W = self.vehicle.T.dot(self.vehicle.vertices_L)
        self.vehicle.speed = state["vehicle"]["speed"]
        self.vehicle.set_transform(*self.vehicle.get_transform())
        for tl_tuple in state["traffic_lights"]:
            tl_name, colour = tl_tuple[0], tl_tuple[1]
            for tl_instance in self.traffic_lights:
                if tl_instance.obj_name == tl_name:
                    tl_instance.c = colour
                    break
        #move active tl on top for rendering. no need to move the car on top becuase it is drawn on a separate plane
        for actor in self.world.actors[:]:
            if type(actor) is TrafficLight:
                if actor.c != (15,15,15):
                    self.world.actors.remove(actor)
                    self.world.actors.append(actor)

        # def render_on_top(self, traffic_light):
        #     for actor in self.all_actors[:]:
        #         if actor == traffic_light:
        #             self.all_actors.remove(actor)
        #             self.all_actors.append(actor)
        #             print("Moved traffic light on top of other traffic lights")
        #             break
        #     for actor in self.all_actors[:]:
        #         if actor == self:
        #             self.all_actors.remove(actor)
        #             self.all_actors.append(actor)
        #             print("Moved vehicle on top of all traffic lights")
        #             break
        if self.vehicle.speed > 4:
            self.path.apply_dropout(idx, self.vehicle)

        input_planes = DrivingDataset.render_inputs_on_separate_planes(self.world, self.vehicle, self.path, idx)
        data = (DrivingDataset.prepare_images(input_planes, self.debug).astype(np.float32) - 128) / 128
        future_points = self.prepare_labels(self.path, idx)

        steering = self.vehicle.turn_angle
        speed = np.array(self.vehicle.speed / Config.normalizing_speed, dtype=np.float32)

        future_penalty_maps, future_poses_regr_offset = self.future_penalty_map(future_points)

        if False:
            debug_penalty_maps = (np.sum(np.squeeze(future_penalty_maps),axis=0) * 255).astype(np.uint8)
            cv2.imshow("debug_penalty_maps", debug_penalty_maps)
            cv2.waitKey(1000)


        sample = {'data': data,
                  'steering': steering,
                  "future_penalty_maps": future_penalty_maps,
                  "future_poses_regr_offset":future_poses_regr_offset,
                  'speed':speed}
        return sample

    @staticmethod
    def render_inputs_on_separate_planes(world, vehicle, path, path_idx, mode="train"):
        image_lanes = np.zeros((Config.r_res[0], Config.r_res[1], 3), np.uint8)
        image_vehicle = np.zeros((Config.r_res[0], Config.r_res[1], 3), np.uint8)
        image_path = np.zeros((Config.r_res[0], Config.r_res[1], 3), np.uint8)
        image_agent_past_poses = np.zeros((Config.r_res[0], Config.r_res[1], 3), np.uint8)

        for actor in world.actors:
            if type(actor) is Camera: continue
            if type(actor) is LaneMarking:
                image_lanes = actor.render(image_lanes, vehicle.camera)
            if type(actor) is TrafficLight:
                image_lanes = actor.render(image_lanes, vehicle.camera, simulation_time=False)

        image_vehicle = vehicle.render(image_vehicle, vehicle.camera)
        image_path = path.render(image_path, vehicle.camera, path_idx, vehicle)

        if mode == "test":
            image_agent_past_poses = vehicle.render_past_locations_func(image_agent_past_poses)
        elif mode =="train":
            image_agent_past_poses = path.render_past_locations_func(image_agent_past_poses, vehicle.camera, path_idx)
        if False:
            image_lanes = vehicle.render(image_lanes, vehicle.camera)

        input_planes = {"image_lanes": image_lanes,
                        "image_vehicle": image_vehicle,
                        "image_path": image_path,
                        "image_agent_past_poses": image_agent_past_poses}
        if mode =="train":
            return input_planes
        else:
            return input_planes, path_idx

    @staticmethod
    def prepare_images(images, debug):

        image_lanes = images["image_lanes"]

        image_vehicle = images["image_vehicle"]
        image_vehicle = cv2.cvtColor(image_vehicle, cv2.COLOR_BGR2GRAY)

        image_path = images["image_path"]
        image_path = cv2.cvtColor(image_path, cv2.COLOR_BGR2GRAY)

        image_agent_past_poses = images["image_agent_past_poses"]
        image_agent_past_poses = cv2.cvtColor(image_agent_past_poses, cv2.COLOR_BGR2GRAY)

        image_concatenated = np.empty((6, Config.r_res[0], Config.r_res[1]), np.uint8)
        # 代码作者解释1：
        # 前三个通道是车道线和交通灯，车道线是灰度图，红绿灯是rbg彩色图，那车道线和红绿灯分别占几个channel？
        # 第4个通道是带有车辆当前位置和航向矩形框
        # 第5个通道是route，在ui中是粗线
        # 第6个通道是车辆前一个时间步的位置和航向，建议每隔5帧或更多帧采一个点，这样在ui中看就是一串散点
        image_concatenated[0, ...] = image_lanes[..., 0]
        image_concatenated[1, ...] = image_lanes[..., 1]
        image_concatenated[2, ...] = image_lanes[..., 2]
        image_concatenated[3, ...] = image_vehicle
        image_concatenated[4, ...] = image_path
        image_concatenated[5, ...] = image_agent_past_poses
        # TODO add the future pose here

        if False:
            cv2.imshow("image1", image_lanes)
            cv2.imshow("image4", image_vehicle)
            cv2.imshow("image5", image_path)
            cv2.imshow("image6", image_agent_past_poses)
            cv2.waitKey(1000)
        return image_concatenated

    def prepare_labels(self, path, path_idx):

        future_pose_states = []
        # TODO I also have to add to the future pose states the angle prediction, or head orientation predicition
        for i in range(Config.horizon_future):
            point = path.project_future_poses(self.vehicle.camera, path_idx, i * Config.num_skip_poses)
            future_pose_states.append(point)
        future_pose_states = np.squeeze(np.array(future_pose_states))
        return future_pose_states
