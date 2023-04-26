from simulator.util.Vehicle import Vehicle
from simulator.UI.GUI import GUI
import pickle
from simulator.control.car_controller.LiveController import LiveController

help_recorder = """
W increase speed
S decrease speed
A increase turn angle left
D increase turn angle right
Mouse  control turn angle
ESC save driving session

Note! You should drive for a bit more than Config.horizon*Config.num_skip_poses frames (otherwise error at training)
"""


class Recorder(GUI): # GUI是Recorder的基类
    # Recorder包含车辆，GUI(包含鼠标订阅器，world(包含actor， world文件的路径， 交通灯文件的路径)，摄像头，按键，图片显示，窗口名，是否运行，时间步)
    # 还包含在线控制器，事件包
    def __init__(self, event_bag_path="", world_path=""):
        super(Recorder, self).__init__("Simulator", world_path=world_path)
        # 交通灯列表
        self.traffic_lights = self.world.get_traffic_lights()
        # self为什么能有成员world?
        self.vehicle = Vehicle(camera=self.camera, play=True, traffic_lights=self.traffic_lights, all_actors=self.world.actors)
        self.world.actors.append(self.vehicle)
        self.vehicle.is_active = True
        self.vehicle.render_next_locations_by_steering = True
        self.vehicle.render_past_locations = True
        self.camera.is_active = False

        print (help_recorder)

        self.live_controller = LiveController(self.vehicle, self.world)
        self.event_bag = EventBag(event_bag_path, record=True)

    # @Override
    def interpret_key(self):
        key = self.pressed_key
        if key == 27:
            self.running = False

    def run(self):
        while self.running:
            super(Recorder, self).interpretIO_and_render()

            self.live_controller.step(self.pressed_key, GUI.mouse)
            to_save_dict = {}
            to_save_dict["pressed_key"] = self.pressed_key
            to_save_dict["mouse"] = (GUI.mouse[0], GUI.mouse[1])
            to_save_dict["vehicle"] = self.vehicle.get_relevant_states()
            to_save_dict["traffic_lights"] = [(tl.obj_name,tl.c) for tl in self.traffic_lights]

            self.event_bag.append(to_save_dict)
        self.event_bag.cleanup()
        print ("Game over")

class EventBag:

    def __init__(self, file_path, record = True):
        self.record = record
        if record == True:
            self.file = open( file_path, "wb" )
            self.list_states = []
        else:
            #TODO warning. This file must be deleted after cration. in multi-workers training, pickle cannot serialzie buffered reader
            self.file = open( file_path, "rb" )
            self.list_states = pickle.load(self.file)
            self.file.close()
            del self.file
        self.crt_idx = 0

    def append(self, events):
        if self.record == True:
            self.list_states.append(events)
            self.crt_idx +=1
        else:
            raise ValueError("EventBag opened as read mode")

    def __len__(self):
        return len(self.list_states)

    def next_event(self):
        if self.record == False:
            event = self.list_states[self.crt_idx]

            self.crt_idx +=1
        else:
            raise ValueError("EventBag opened as write mode")
        return event

    def __getitem__(self, idx):
        if self.record == False:
            event = self.list_states[idx]
        else:
            raise ValueError("EventBag opened as write mode")
        return event

    def reset(self):
        self.crt_idx = 0

    def cleanup(self):
        if self.record == True:
            pickle.dump(self.list_states, self.file)
            self.file.close()
            print ("saved driving session")


if __name__ == "__main__":
    recorder = Recorder(event_bag_path="../../data/recorded_states.pkl", world_path="../../data/world.obj")
    recorder.run()
