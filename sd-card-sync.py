#!/usr/bin/python -tt

import sys
import os
import time
import re
import subprocess

def main():

  SPECIALDIR_CANONMSC = 'CANONMSC'

  # 1) read contents of SYNC.ME
  # 2) sync all folders on card that aren't named in SYNC.ME
  # 3) but do sync the last folder named in SYNC.ME (could have changed since last sync)   
  # 4) After sync remove lines in SYNC.ME if that folder no longer exists to keep size of SYNC.ME file down
  # 5) umount sd card

  src = "/media/tv/CANON_DC/"
  trg = "/media/data/photos/"
  syncFilePath = src + "SYNC.ME"
  srcImagePath = src + "DCIM/"

  # wait for udev rules to mount sd card
  mountTries = 30
  while (mountTries > 0) & (not os.path.exists(syncFilePath)):
    time.sleep(2)
    mountTries -= 1
  if not os.path.exists(syncFilePath):
    sys.exit()

  # 1) read contents of SYNC.ME
  if os.path.exists(syncFilePath):
    syncFile = open(syncFilePath, 'r')
    copiedDirs = syncFile.readlines()
    copiedDirs = [item.replace('\n','') for item in copiedDirs]
    syncFile.close()
  else:
    copiedDirs = []

  # 3) but do sync the last folder named in SYNC.ME (could 
  #    have changed since last sync)
  #    So remove last entry in copiedDirs
  if len(copiedDirs) > 0:
    copiedDirs.pop()

  # Also want to ignore the 'CANONMSC' directory
  copiedDirs.insert(0, SPECIALDIR_CANONMSC)

  # 2) sync all folders on card that aren't named in SYNC.ME
  cardDirs = os.listdir(srcImagePath)
  toCopyDirs = [item for item in cardDirs if not item in copiedDirs]

  # Do copy
  for dir in toCopyDirs:
    fullSrcDir = srcImagePath + dir + "/"
    fullTrgDir = getFullTargetDir(fullSrcDir, trg)
    copyDir(fullSrcDir, fullTrgDir)

  # Sort before writing to SYNC.ME, most recent last
  cardDirs.sort()

  # 4) After sync remove lines in SYNC.ME if that folder
  #    no longer exists to keep size of SYNC.ME file down
  syncFile = open(syncFilePath, 'w')
  syncFile.truncate(0)
  for dir in cardDirs:
    if dir != SPECIALDIR_CANONMSC:
      syncFile.write(dir + '\n')
  syncFile.flush()
  syncFile.close()

  # 5) umount sd card
  umountArgs = ['umount', src]
  subprocess.call(umountArgs)

def copyDir(src, trg):
  if not os.path.exists(trg):
    os.makedirs(trg)

  # -arW = archive, recursive, Whole (not delta copy)
  rsyncArgs = ['rsync','-arW', src, trg]
  subprocess.call(rsyncArgs)

# expands /src/139_1604/ to /trg/2011/04/16/
def getFullTargetDir(fullSrcDir, targetRoot):
  date = getDate(fullSrcDir)
  day = date[0]
  month = date[1]
  year = time.localtime(os.path.getctime(fullSrcDir)).tm_year
  return targetRoot + str(year) + "/" + str(month) + "/" + str(day) + "/"

# gets day and month from src dir name
def getDate(src):
  # src is like '/some_path/139_1604', want [16, 04]
  m = re.search('([0-9]{2})([0-9]{2})', src[src.rfind('_')+1:])
  print (src)
  return [m.group(1), m.group(2)]

# Standard boilerplate to call the main() function.
if __name__ == '__main__':
  main()


