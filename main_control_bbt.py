from __future__ import division
import time
from thread import *
from threading import Thread
import math
import evdev
from evdev import ecodes
import socket
import datetime
import numpy as np
from hs5645mg_servo_sdk.hs5645mg_servo_controller import HS5645MGServoController

# TOUCH_CONTROLLER_NAME = "eGalax Inc. USB TouchController"
TOUCH_CONTROLLER_NAME = "eGalax Inc."
# TOUCH_CONTROLLER_NAME = "Touch__KiT Touch  Computer INC."

servo_controller = HS5645MGServoController()
servo_controller.start()

def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # doesn't even have to be reachable
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP

# TCP variables
_host_ip = get_ip()
_host_port = 1000
_connected = False
_first_init = True
_try_reconnect = True
_close_signal = False
_logger = None
_keep_listening_touch_events = False
_touch_controller_dev = None
_last_ball_position_reading = (0, 0)

def _touch_events_listening_thread_func():
    if _logger is not None:
        _logger.debug("Starting listening to touch events.")
    while _keep_listening_touch_events:
        # This while will run on a different thread.
        try:
            event = _touch_controller_dev.read_one()
            if event is not None:
                if event.type == ecodes.EV_ABS:
                    if event.code == ecodes.ABS_X:
                        _last_ball_position_reading = (event.value, _last_ball_position_reading[1])
                    if event.code == ecodes.ABS_Y:
                        _last_ball_position_reading = (_last_ball_position_reading[0], event.value)
                if event.type == ecodes.EV_KEY:
                    if event.value == 1:
                        ball_contact = True
                    else:
                        ball_contact = False

            else:
                time.sleep(0.001)  # If there is no change from last loop, sleep 1ms
        except OSError:  # Does not catch the error! #TODO
            pass
    if _logger is not None:
        _logger.debug("Stopped listening to touch events.")

def start_listening_touch_events():
    if _logger is not None:
        _logger.info("Touch screen searching...")
    _touch_controller_dev = find_touch_controller_dev()
    if _logger is not None:
        _logger.info("Touch screen found!")
    _keep_listening_touch_events = True
    if _logger is not None:
        _logger.info("Touch screen thread starting...")
    # Start touch panel thread
    _touch_events_listening_thread = Thread(target=_touch_events_listening_thread_func)
    _touch_events_listening_thread.start()
    if _logger is not None:
        _logger.info("Touch screen thread started!")

def find_touch_controller_dev():
    touch_controller_device = None
    # Initialize touch panel device
    devices = [evdev.InputDevice(fn) for fn in evdev.list_devices()]
    for device in devices:
        if TOUCH_CONTROLLER_NAME in device.name:
            touch_controller_device = device
    return touch_controller_device

def get_ball_position_in_raw(): # To read position from outside of class in raw format
    return _last_ball_position_reading

def tcp_start():
    print("Starting TCP Server")
    global _connected, _first_init, _try_reconnect, conn,send_position
    try:
        while True:
            if _close_signal:
                break
            if not _connected and not _close_signal:

                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                s.bind((_host_ip, _host_port))
                print("Socket bind completed")
                s.listen(10)
                print("Socket now listening")
                conn, addr = s.accept()
                print("Connected with " + addr[0] + ":" + str(addr[1]))
                if conn:
                    _connected = True
                    time.sleep(1)
                    # _first_init = False
                    start_new_thread(receiver, (conn,))
                    start_new_thread(sender, (conn,))
                    # time.sleep(1)
                    # if not _connected and _try_reconnect and not _first_init:
                    #     conn, addr = s.accept()
                    #     print("Connected with " + addr[0] + ":" + str(addr[1]))
                    # if conn:
                    #     _connected = True
                    #     _tcp_sender_thread.start()
                    # start_new_thread(receiver, (conn,))
                    # start_new_thread(sender, (conn,))
            time.sleep(1)
    except socket.error as msg:
        print("Couldn't bind server. Error: %s\n " % msg)

start_listening_touch_events()

_tcp_connector_thread = Thread(target=tcp_start)
_tcp_connector_thread.start()

def receiver(conn):
    global _close_signal,_connected,_try_reconnect
    while True:
        if _close_signal:
            break
        if _connected:
            # Receiving from client
            recvdata = None
            try:
                recvdata = conn.recv(100)
            except socket.error:
                pass
            if recvdata:
                parsed = recvdata.split(",")
                if str(parsed[0]) == 'servo_pos':
                    servo_x = float(parsed[1])
                    servo_y = float(parsed[2])

                    if abs(servo_x)<=90 and abs(servo_y)<=90:
                        servo_controller.set_degrees_bbt((servo_x,servo_y))


            if not recvdata and _try_reconnect:
                print("No data received, will try to connect again")
                _connected = False
                break
            elif not recvdata and not _try_reconnect:
                print("No data received, closing application")
                _connected = False
                _close_signal = True
                break

        time.sleep(0.01)

    # except conn.error as msg:
    #     print("Connection Error: %s\n " % msg)
    #     conn.close()

    if conn:
        conn.close()


def sender(conn):
    global _connected, _try_reconnect, data, _close_signal, ctrllrclass,send_position,message_update
    global message_in_queue
    # try:
    while True:
        if _close_signal:
            break
        if _connected:
            # Receiving from client
            if _connected and send_position:
                ball_position_raw = get_ball_position_in_raw()
                data_x_raw = "{:.4f}".format(ball_position_raw[0])
                data_y_raw = "{:.4f}".format(ball_position_raw[1])
                #data_x_servo = "{:.4f}".format(ctrllrclass.current_servo_positions[0])
                #data_y_servo = "{:.4f}".format(ctrllrclass.current_servo_positions[1])
                data = "position," + data_x_raw + "," + data_y_raw + "\n"

                try:
                    conn.send(data)
                except socket.error:
                    time.sleep(0.2)
                    pass
            elif not _connected and _try_reconnect:
                print("Connection is not online, will try to connect again")
                break
            elif not _connected and not _try_reconnect:
                print("Connection is not online, closing application")
                break

        time.sleep(0.01)

    # except conn.error as msg:
    #     print("Connection Error: %s\n " % msg)
    #     _connected = False
    #     conn.close()
    if conn:
        conn.close()


try:
    while True:
        if _close_signal:
            break
        time.sleep(0.5)
except KeyboardInterrupt:
    _close_signal = True
    pass


print("Close interrupt received.")
#_close_signal = True
if not _connected:
    print("No connection, closing socket")
    s1 = socket.socket(socket.AF_INET,
                  socket.SOCK_STREAM).connect((_host_ip, _host_port))
    # s1.close()
print("Closing TCP Server")
time.sleep(1)
servo_controller.close()