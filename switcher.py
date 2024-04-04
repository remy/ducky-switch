import os
import AppKit
import sys
import struct
import argparse
from Foundation import NSObject
from PyObjCTools import AppHelper
import hid
import time
import json

import getpass

current_user = getpass.getuser()
print(current_user)


PC_TO_DUCKYPAD_HID_BUF_SIZE = 64
DUCKYPAD_TO_PC_HID_BUF_SIZE = 64

seq = 0
h = hid.device()

parser = argparse.ArgumentParser(
   prog='DuckySwitcher',
   description="A ducky pad switcher with a daemonize mode")
parser.add_argument(
   '-t',
   '--test',
   action='store_true',
   help='Test config, HID connection and front app switching')
parser.add_argument(
   '-d',
   '--daemon',
   action='store_true',
   help='Start as daemon')
parser.add_argument(
  '-i',
  '--info',
  action='store_true',
  help='Get duckyPad info')

args = parser.parse_args()

# Get the directory where the script is located
script_dir = os.path.dirname(os.path.abspath(__file__))

# Construct the path to the file in the same directory as the script
file_path = os.path.join(script_dir, 'config.json')

with open(file_path) as config_file:
  file_contents = config_file.read()
  # parse file_contents as json
  config = json.loads(file_contents)
  if args.test:
    print('config:', config)



class DuckyInfoStruct:
    def __init__(self, _, seq, ok, maj, min, pat, serial, profile, status):
        self.ok = ok
        self.version = f"{maj}.{min}.{pat}"
        self.serial = serial
        self.profile = profile
        self.status = status

def get_duckypad_path():
  for device_dict in hid.enumerate():
      if device_dict['vendor_id'] == 0x0483 and \
      device_dict['product_id'] == 0xd11c and \
      device_dict['usage'] == 58:
        return device_dict['path']
  return None

# wait up to 0.5 seconds for response
def hid_read():
  read_start = time.time()
  while time.time() - read_start <= 0.5:
    result = h.read(DUCKYPAD_TO_PC_HID_BUF_SIZE)
    if len(result) > 0:
      return result
    time.sleep(0.01)
  return []

def duckypad_hid_write(hid_buf_64b):
  if len(hid_buf_64b) != PC_TO_DUCKYPAD_HID_BUF_SIZE:
    raise ValueError('PC-to-duckyPad buffer wrong size, should be exactly 64 Bytes')
  duckypad_path = get_duckypad_path()
  if duckypad_path is None:
    raise OSError('duckyPad Not Found!')
  h.open_path(duckypad_path)
  h.set_nonblocking(1)
  h.write(hid_buf_64b)
  result = hid_read()
  h.close()
  return result

def send_to_ducky(command, opt = 0):
  global seq
  buf = [0] * PC_TO_DUCKYPAD_HID_BUF_SIZE
  buf[0] = 5	# HID Usage ID, always 5
  buf[1] = seq	# Sequence Number
  buf[2] = command	# Command type
  buf[3] = opt	# Command option

  # increment sequence number and roll over if it exceeds 255
  seq = (seq + 1) % 256
  if args.test:
    print("\n\nSending to duckyPad:\n", buf)
  duckypad_to_pc_buf = duckypad_hid_write(buf)
  if args.test:
    print("\nduckyPad response:\n", duckypad_to_pc_buf)
  return bytes(duckypad_to_pc_buf)

def goto_profile(profile):
  send_to_ducky(1, profile)

def info():
  return send_to_ducky(0)

class AppDelegate(NSObject):
    def applicationDidActivate_(self, notification):
        app_info = notification.userInfo()["NSWorkspaceApplicationKey"]
        app_name = app_info.localizedName()
        if args.test:
          print(f"foremost app: {app_name}")
        switch_app(app_name)

# a new function that will take a string, search for it in the config and if a match is found, it will use the index of the array to send to the send_to_ducky function
def switch_app(app_name):
  for i in range(len(config)):
    # if the config is empty, skip
    if not config[i]: continue

    # loop through the config, splitting the string by comma and checking if the app_name is in the array of strings

    parts = config[i].split(',')
    for part in parts:
      if args.test:
        print(f"Checking {part.lower()} in {app_name.lower()}")

      if part.lower() not in app_name.lower():
        continue

      if args.test:
        print(f"Match found: {app_name} in {i}")
      goto_profile(i+1)
      break

def monitor():
    app_delegate = AppDelegate.alloc().init()
    nc = AppKit.NSWorkspace.sharedWorkspace().notificationCenter()
    nc.addObserver_selector_name_object_(app_delegate, "applicationDidActivate:", AppKit.NSWorkspaceDidActivateApplicationNotification, None)

    app_name = AppKit.NSWorkspace.sharedWorkspace().activeApplication()['NSApplicationName']
    if args.test:
      print(f"foremost app: {app_name}")
    switch_app(app_name)

    AppHelper.runConsoleEventLoop()

def main():
    if args.info:
      buf = info()
      res = DuckyInfoStruct(*struct.unpack('<BBBBBBxIBB', buf[0:13]))
      sys.exit(f"version: {res.version}\nprofile: {res.profile}\nserial: {format(res.serial, '08X')}\nstatus: {'sleeping' if res.status == 1 else 'awake'}\n")

    monitor()


if __name__ == '__main__':
    main()
