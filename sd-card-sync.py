#!/usr/bin/python -tt

import sys
import os
import time
import re
import subprocess
import shutil

SPECIALDIR_CANONMSC = 'CANONMSC'
SPECIALFILE_SYNCME = 'SYNC.ME'

def main():

  # 1) Try to mount either Canon or Olympus SD card.
  # 2) Read contents of SYNC.ME
  # 3) Sync files (Olympus) or directories (Canon), except those named in the SYNC.ME file.   
  # 4) Update contents of SYNC.ME file and unmount SD card.

  # Where to save photos to.
  trg = "/media/data/photos/"
  # Canon source paths.
  srcCanon = "/media/tv/CANON_DC/"
  syncFilePathCanon = srcCanon + SPECIALFILE_SYNCME
  # Olympus source paths.
  srcOlympus = "/media/tv/OLYMPUS/DCIM/100OLYMP/"
  syncFilePathOlympus = srcOlympus + SPECIALFILE_SYNCME

  # wait for udev rules to mount sd card
  mountTries = 30
  while (mountTries > 0) & (not os.path.exists(syncFilePathCanon)) & (not os.path.exists(syncFilePathOlympus)):
    time.sleep(2)
    mountTries -= 1

  if os.path.exists(syncFilePathCanon):
    srcImagePath = srcCanon + "DCIM/"
    doSyncCanon(srcImagePath, syncFilePathCanon, trg)
    umountArgs = ['umount', srcCanon]
    subprocess.call(umountArgs)
  elif os.path.exists(syncFilePathOlympus):
    doSyncOlympus(srcOlympus, trg)
    umountArgs = ['umount', srcOlympus]
    subprocess.call(umountArgs)
  else:
    sys.exit()

def doSyncCanon(srcImagePath, syncFilePathCanon, trg):
  copiedDirs = readSyncMeFile(syncFilePathCanon)

  # Include in sync the last folder named in SYNC.ME (could 
  #    have changed since last sync)
  #    So remove last entry in copiedDirs
  if len(copiedDirs) > 0:
    copiedDirs.pop()
  # Also want to ignore the 'CANONMSC' directory
  copiedDirs.insert(0, SPECIALDIR_CANONMSC)

  # Also sync all folders on card that aren't named in SYNC.ME
  cardDirs = os.listdir(srcImagePath)
  toCopyDirs = [item for item in cardDirs if not item in copiedDirs]

  # Do copy
  for dir in toCopyDirs:
    fullSrcDir = srcImagePath + dir + "/"
    fullTrgDir = getFullTargetDirCanon(fullSrcDir, trg)
    copyDir(fullSrcDir, fullTrgDir)

  # Sort before writing to SYNC.ME, most recent last
  cardDirs.sort()

  # After sync remove lines in SYNC.ME if that folder
  # no longer exists to keep size of SYNC.ME file down
  syncFile = open(syncFilePathCanon, 'w')
  syncFile.truncate(0)
  for dir in cardDirs:
    if dir != SPECIALDIR_CANONMSC:
      syncFile.write(dir + '\n')
  syncFile.flush()
  syncFile.close()

def doSyncOlympus(srcImagePath, trg):
  syncFilePath = srcImagePath + SPECIALFILE_SYNCME

  copiedFiles = readSyncMeFile(syncFilePath)
  # Also want to ignore the 'SYNC.ME' file
  copiedFiles.insert(0, SPECIALFILE_SYNCME)

  # Sync all files on card that aren't named in SYNC.ME
  cardFiles = os.listdir(srcImagePath)
  toCopyFiles = [item for item in cardFiles if not item in copiedFiles and not item.endswith('.ORF') and not item.endswith('.pp3')]

  # Do copy
  for file in toCopyFiles:
    fullSrcPath = srcImagePath + file
    fullTrgPath = getFullTargetDirOlympus(fullSrcPath, trg)
    copyFile(fullSrcPath, fullTrgPath)

  # Sort before writing to SYNC.ME, most recent last
  cardFiles.sort()

  # After sync remove lines in SYNC.ME if that folder
  # no longer exists to keep size of SYNC.ME file down
  syncFile = open(syncFilePath, 'w')
  syncFile.truncate(0)
  for file in cardFiles:
    if file != SPECIALFILE_SYNCME:
      syncFile.write(file + '\n')
  syncFile.flush()
  syncFile.close()

def readSyncMeFile(syncFilePath):
  # 1) read contents of SYNC.ME
  if os.path.exists(syncFilePath):
    syncFile = open(syncFilePath, 'r')
    copiedDirs = syncFile.readlines()
    copiedDirs = [item.replace('\n','') for item in copiedDirs]
    syncFile.close()
  else:
    copiedDirs = []

  return copiedDirs

def copyDir(src, trg):
  if not os.path.exists(trg):
    os.makedirs(trg)
  # -arW = archive, recursive, Whole (not delta copy)
  rsyncArgs = ['rsync','-arW', src, trg]
  subprocess.call(rsyncArgs)

def copyFile(src, trg):
  trgDir = os.path.dirname(trg)
  if not os.path.exists(trgDir):
    os.makedirs(trgDir)
  shutil.copy2(src, trg)

# expands to /trg/2011/04/16/ based on file's modified date.
def getFullTargetDirOlympus(fullSrcFilePath, targetRoot):
  fileDateTime = time.localtime(os.path.getmtime(fullSrcFilePath))
  day = str(fileDateTime.tm_mday).zfill(2)
  month = str(fileDateTime.tm_mon).zfill(2)
  year = str(fileDateTime.tm_year)
  return targetRoot + year + "/" + month + "/" + day + "/"

# expands /src/139_1604/ to /trg/2011/04/16/
def getFullTargetDirCanon(fullSrcDir, targetRoot):
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
