from __future__ import division
import time
from thread import *
from threading import Thread
import math
import socket
import datetime
import numpy as np
import Adafruit_GPIO.SPI as SPI
import Adafruit_MCP3008
from hs5645mg_servo_sdk.hs5645mg_servo_controller import HS5645MGServoController

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

# Hardware SPI configuration:
SPI_PORT   = 0
SPI_DEVICE = 0
mcp = Adafruit_MCP3008.MCP3008(spi=SPI.SpiDev(SPI_PORT, SPI_DEVICE))


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

                    if abs(servo_x)<=90:
                        servo_controller.set_degrees_bb(servo_x)


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
    global _connected, _try_reconnect, data, _close_signal
    # try:
    while True:
        if _close_signal:
            break
        if _connected:
            # Receiving from client
            if _connected and send_position:

                data_x_raw =  mcp.read_adc(0)
                #data_x_servo = "{:.4f}".format(ctrllrclass.current_servo_positions[0])
                #data_y_servo = "{:.4f}".format(ctrllrclass.current_servo_positions[1])
                data = "position," + data_x_raw + "\n"

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
print("Closing controller object")
servo_controller.close()