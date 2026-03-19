'''
menymp mar 2026

mock script to emulate a device with sensors and actuators

'''

import time
from node_bridge import node_bridge

broker = "localhost"
node_name = "MockMenyNode1"
motor_command = "OFF"
counter = 0

def get_temp_sensor_value():
    print("get sensor value")
    return 69.69

def get_counter_value():
    global counter
    print("get counter value %s" % counter)
    return counter

def get_motor_command():
    global motor_command
    print("reading motor command %s" % motor_command)
    return motor_command

def set_motor_command(value):
    global motor_command
    print("setting new motor command %s" % value)
    motor_command = value
    pass

if __name__ == "__main__":

    nodeBridgeObj = node_bridge(node_name, broker, 1883, 60, 6)
    nodeBridgeObj.acknowledge()
    #acknowledge completed for our name, now adding devices
    nodeBridgeObj.add_publisher_device("TempSensor", "INT", get_temp_sensor_value)
    nodeBridgeObj.add_publisher_device("InternalCounter", "INT", get_counter_value)
    nodeBridgeObj.add_subscriber_device("PumpMotor", "STRING", get_motor_command, set_motor_command  )

    nodeBridgeObj.start_server()

    
    try:
        while True:
            time.sleep(2)
            counter += 1
            nodeBridgeObj.send_event("InternalCounter", str(counter))
            if counter > 100:
                counter = 0
    except KeyboardInterrupt:
        nodeBridgeObj.disable()
        print("Stopped cleanly")