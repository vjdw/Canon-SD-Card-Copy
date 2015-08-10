#!/usr/bin/python -tt

import subprocess

def main():
  # SD card isn't mounted until this script (called by udev rule) exits
  # So just start sd-card-sync.py, which waits for card to be mounted.
  subprocess.Popen(["/usr/bin/sd-card-sync.py"])

# Standard boilerplate to call the main() function.
if __name__ == '__main__':
  main()

