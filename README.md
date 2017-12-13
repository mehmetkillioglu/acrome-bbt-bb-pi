Acrome BBT-BB Binder Script
==================

This scripts will let you control ACROME Ball Balancing Table & ACROME Ball and Beam robots from MATLAB, LABView or another programming language with TCP Socket feature.

Installation
------------

You can install this library just like any other Python library using pip3. 

You can use:

sudo python setup.py install

Afterwards, you can launch main_control_bb or main_control_bbt depending on your hardware. You can also add this scripts to boot. 


Usage
-----

TO INSTALL:

sudo python setup.py install

TO RUN SCRIPT:

sudo python main_control_bb.py 

or:

sudo python main_control_bbt.py


Requirements
-----

Evdev driver
PiGpio library
Adafruit-MCP3008 driver

setup.py will get these requirements from Pip if internet connection is available.

