import cv2
import numpy as np

white = (255, 255, 255)
black = (0, 0, 0)
blue = (255, 0, 0)
green = (0, 255, 0)
red = (0, 0, 255)
grey = (190, 190, 190)

border = int(2)
length = int(24)
width = int(10)


line_color = white
vehicle_box_color = red
vehicle_future_position_color = blue
vehicle_past_position_color = grey
background_color = black
img = (background_color * np.ones((100, 100, 3))).astype(np.uint8)
'''
draw map in img
'''
# 水平 下1
cv2.line(img, (8, 0), (30, 0), line_color, 1, cv2.LINE_AA)
cv2.line(img, (8, 4), (32, 4), line_color, 1, cv2.LINE_AA)
cv2.line(img, (8, 8), (32, 8), line_color, 1, cv2.LINE_AA)
# 水平 下2
cv2.line(img, (39, 0), (49, 0), line_color, 1, cv2.LINE_AA)
cv2.line(img, (42, 4), (53, 4), line_color, 1, cv2.LINE_AA)
cv2.line(img, (42, 8), (56, 8), line_color, 1, cv2.LINE_AA)
# 水平 中1
cv2.line(img, (8, 20), (30, 20), line_color, 1, cv2.LINE_AA)
cv2.line(img, (7, 24), (29, 24), line_color, 1, cv2.LINE_AA)
cv2.line(img, (7, 28), (29, 28), line_color, 1, cv2.LINE_AA)
# 水平 中2
cv2.line(img, (44, 20), (56, 20), line_color, 1, cv2.LINE_AA)
cv2.line(img, (44, 24), (56, 24), line_color, 1, cv2.LINE_AA)
cv2.line(img, (44, 28), (56, 28), line_color, 1, cv2.LINE_AA)
# 水平 上1
cv2.line(img, (9, 40), (18, 40), line_color, 1, cv2.LINE_AA)
cv2.line(img, (9, 45), (18, 45), line_color, 1, cv2.LINE_AA)
cv2.line(img, (9, 50), (18, 50), line_color, 1, cv2.LINE_AA)
# 水平 上2
cv2.line(img, (32, 40), (53, 40), line_color, 1, cv2.LINE_AA)
cv2.line(img, (32, 44), (53, 44), line_color, 1, cv2.LINE_AA)
cv2.line(img, (32, 48), (53, 48), line_color, 1, cv2.LINE_AA)
# 竖直 下 1
cv2.line(img, (0, 8), (0, 20), line_color, 1, cv2.LINE_AA)
cv2.line(img, (3, 8), (3, 20), line_color, 1, cv2.LINE_AA)
cv2.line(img, (6, 8), (6, 20), line_color, 1, cv2.LINE_AA)
# 竖直 下 2
cv2.line(img, (34, 8), (34, 20), line_color, 1, cv2.LINE_AA)
cv2.line(img, (37, 8), (37, 20), line_color, 1, cv2.LINE_AA)
cv2.line(img, (40, 8), (40, 20), line_color, 1, cv2.LINE_AA)
# 竖直 下 3
cv2.line(img, (58, 8), (58, 20), line_color, 1, cv2.LINE_AA)
cv2.line(img, (61, 8), (61, 20), line_color, 1, cv2.LINE_AA)
cv2.line(img, (64, 8), (64, 20), line_color, 1, cv2.LINE_AA)
# 竖直 上 1
cv2.line(img, (0, 29), (0, 40), line_color, 1, cv2.LINE_AA)
cv2.line(img, (3, 29), (3, 40), line_color, 1, cv2.LINE_AA)
cv2.line(img, (6, 29), (6, 40), line_color, 1, cv2.LINE_AA)
# 斜
cv2.line(img, (58, 29), (58, 40), line_color, 1, cv2.LINE_AA)
cv2.line(img, (61, 29), (61, 40), line_color, 1, cv2.LINE_AA)
cv2.line(img, (64, 29), (64, 40), line_color, 1, cv2.LINE_AA)
# 竖直 上 3
cv2.line(img, (32, 29), (20, 40), line_color, 1, cv2.LINE_AA)
cv2.line(img, (37, 29), (25, 40), line_color, 1, cv2.LINE_AA)
cv2.line(img, (42, 29), (30, 40), line_color, 1, cv2.LINE_AA)
# TODO(yxb): img和车道线的绘制应该放在初始化函数中，因为他们一经确定就不变更

'''
draw vehicle box in img
'''
length = 7
width = 2
vehicle_center_position = (4, 4)


def draw_vehicle_box(vertex, color):
    cv2.rectangle(img, vertex, (vertex[0] + width, vertex[0] + length), color, -1)


# 车
draw_vehicle_box(vehicle_center_position, vehicle_box_color)


def draw_vehicle_position(vertex, color):
    cv2.rectangle(img, vertex, (vertex[0] + 1, vertex[0] + 1), color, -1)


'''
draw vehicle future position in img
draw vehicle past position in img
'''
vertex_1 = (10, 10)
draw_vehicle_position(vertex_1, vehicle_future_position_color)
vertex_2 = (7, 7)
draw_vehicle_position(vertex_2, vehicle_past_position_color)
# TODO(yxb): 传入多个点，一次画出

# 显示
cv2.namedWindow('map', 0)
cv2.resizeWindow('map', int(48 * 35 + 2 * 35), int(20 * 35 + 2 * 35))
cv2.imshow('map', img)
cv2.waitKey(0)
cv2.destroyAllWindows()

# 存储
cv2.imwrite("map.jpg", img)
