    # 代码作者解释8：
    # 我创建了3个控制器：
    # BagEventController用来回放你录制好的包（.pkl）；
    # Live controller供用户使用鼠标和键盘去控制车辆；
    # NeuralController被用来测试模型；
    # TODO(yxb): 要在simulator中去控制车辆，那么我需要一个仿真世界，这个世界中应该有路、车道、人行横道红绿灯等交通标识
    # TODO(yxb): 1. 我需要从代码中判定，我是否一定需要它们，代码能不能帮我构建它们？
    # TODO(yxb): 2. 如果代码能不能帮我构建它们，我需要知道它们的数据结构
    # TODO(yxb): 3. 然后调查carla的输出接口
    # TODO(yxb): 4. 然后对比两者，进行融合


class Controller:

    def __init__(self, actor, world):
        """
        :param actor:
        """
        self.registered_actor = actor
        self.world = world

    def step(self):
        # Apply operations on self.registered_actor
        pass