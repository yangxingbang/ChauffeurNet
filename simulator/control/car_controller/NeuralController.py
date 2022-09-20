from simulator.control.Controller import Controller
from network.models.SimpleConv import ChauffeurNet
from network.models.Dataset import DrivingDataset
from network.train import Config as TrainingConfig
from simulator.UI.GUI import GUI
import numpy as np
import torch

class NeuralController(Controller):
    """
    This controller should receive a path idx based on which it will render the image, forward into net, and apply output to kinematic model of the car
    """

    def __init__(self, vehicle, world, model_path, recorded_path):
        """
        :param vehicle:         vehicle object to control
        :param world:           world necessary for rendering
        :param model_path:      path to neuralnet weights
        :param recorded_path:   Path object (contains previously recorded steps, necessary for GPS like directions)
        """
        super(NeuralController, self).__init__(actor=vehicle, world=world)

        self.config = TrainingConfig()
        model = ChauffeurNet(self.config)
        model.load_state_dict(torch.load(model_path, map_location='cpu'))
        model.eval()
        self.model = model.to(self.config.device)
        self.path = recorded_path
        self.vehicle = self.registered_actor

    def step(self, path_idx):

        print(self.path.vertices_L.shape[1], path_idx)
        # 代码作者解释9：
        # 训练和测试网络的时候，神经网络需要全局路径
        # 全局路径存在于pkl文件中，已经被录制下来
        # pickle包含一个状态的列表，这些状态包括把车辆画下来的车辆的坐标
        # 我们需要找到哪些被录制下来的状态是靠近车辆的，把当前状态和未来长度的所有状态都画出来
        # TODO(yxb): 探究一下pkl中都有什么，具体是什么数据结构

        # 代码作者解释10：
        # 把训练和测试的全局路径解耦是一件好事情，之前我做的时候不太关注过拟合
        # 假如你使用了同样的数据去训练新模型，必须先要保证仿真器被初始化过了，对于pkl的相对路径可以被找到和加载，你不需要录制新数据
        # 如果你用我的源码去修改，我来指导你可能更好
        # yxb：这个作者人太好了，可惜我来晚了！
        path_idx = self.path.get_point_idx_close_to_car(self.vehicle, path_idx)
        nn_input = self.render_neural_input(path_idx)

        nn_outputs = self.model(nn_input)
        waypoints_2D = self.model.process_waypoints(nn_outputs["waypoints"])
        waypoints_3D = []
        for waypoint in waypoints_2D:
            # mouse on world needs order x, y but the model returns y and x
            y, x = waypoint[0], waypoint[1]
            waypoints_3D.append(GUI.mouse_on_world((x, y), self.vehicle.camera))
        ones = np.ones((1, len(waypoints_3D)))
        waypoints_3D = np.squeeze(np.array(waypoints_3D)).T
        waypoints_3D = np.vstack((waypoints_3D, ones))

        self.vehicle.simulate_given_waypoints(waypoints_3D)


        return waypoints_2D, path_idx

    def render_neural_input(self, path_idx):
        input_planes = DrivingDataset.render_inputs_on_separate_planes(self.world, self.vehicle, self.path, path_idx)
        input_planes_concatenated = DrivingDataset.prepare_images(input_planes, debug=False)
        input_planes_concatenated = input_planes_concatenated[np.newaxis]
        input_planes_concatenated = torch.from_numpy((input_planes_concatenated.astype(np.float32) - 128) / 128).to(self.config.device)

        return input_planes_concatenated
