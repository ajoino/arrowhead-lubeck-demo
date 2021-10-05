import itertools
import json

ROOM_NAMES = ('A11', 'A12', 'A13', 'A14', 'A21', 'A22', 'A23', 'A24')
ROOM_COORDINATES = ((0, 0), (1, 0), (2, 0), (3, 0), (1, 1), (2, 1), (3, 1), (4, 1))

def get_core_config():
    with open('core_config.json', 'r') as config_json:
        config = json.load(config_json)


address = '172.16.1.1'
sensor_a_ports = lambda: itertools.count(5000)
actuator_a_ports = lambda: itertools.count(5100)
controller_a_ports = lambda: itertools.count(5200)
sensor_b_ports = lambda: itertools.count(5010)
actuator_b_ports = lambda: itertools.count(5110)
controller_b_ports = lambda: itertools.count(5210)
zipped_ports = lambda: zip(
        ROOM_NAMES,
        sensor_a_ports(),
        actuator_a_ports(),
        controller_a_ports(),
        sensor_b_ports(),
        actuator_b_ports(),
        controller_b_ports()
)