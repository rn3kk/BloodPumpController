import numpy as np

board_status = 'Not found'
min_value = '-'
max_value = '-'
rate = '-'
changed = False

MAX_GRAPH_COUNT = 1000
graph_y1 = np.array([]) * 0
graph_y2 = np.array([]) * 0
graph_y3 = np.array([]) * 0

potok1 = ''
potok2 = ''
potok3 = ''

from matplotlib import pyplot as plt

fig, axis = plt.subplots()
a1 = axis.plot(np.arange(0, MAX_GRAPH_COUNT), [0, 140] * (MAX_GRAPH_COUNT // 2))
a2 = axis.plot(np.arange(0, MAX_GRAPH_COUNT), [0, 140] * (MAX_GRAPH_COUNT // 2))
a3 = axis.plot(np.arange(0, MAX_GRAPH_COUNT), [0, 140] * (MAX_GRAPH_COUNT // 2))
plt.yticks(np.arange(0, 140, 5))