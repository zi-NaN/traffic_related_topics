'''
Author:          ZHAO Zinan
Written:         2018-07-04
Last Updated:    03-Oct-2018

run the pedetrian remaining time prediction program
'''

import configparser
import argparse

from cameraFeed import CameraFeed
from mqttReceiver import ReceiveClient

# read the given config path or use the default config path settings.ini
parser = argparse.ArgumentParser()
parser.add_argument("--config", help="path to config file of pedestrian tracking")

args = parser.parse_args()
config_path = args.config if args.config else 'settings.ini'

# read the config from config file
config = configparser.ConfigParser()
try:
    config.read(config_path)
except Exception as e:
    print(e)
    print("PATH ERROR: The config path is invalid")
    exit(0)

server = config['mqtt']['start_sender']
path = config['mqtt']['start_path']

camerafeed = CameraFeed()

# receive the start/stop signal from the master RPi
if config['platform']['pi'] == 'True':
    receiver = ReceiveClient()
    receiver.connect(server, 1883, 60)
    receiver.add_path([path])
    receiver.loop_start()

    message = '0'

    while (True):
        if path in receiver.message.keys(): 
            receive_msg = receiver.message['start']

            # time to start the program
            if receiver_msg == '1' and message == '0':            
                camerafeed.go_config(config_path = config_path)
                message = '1'
            
            # stop the camerafeed
            elif receiver_msg == '0' and message == '1':
                camerafeed.change_running_state()
                message = '0'
else:
    camerafeed.go_config(config_path = config_path)

