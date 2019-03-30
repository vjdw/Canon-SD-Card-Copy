#!/usr/bin/python -tt

import sys
import os
import time
import re
import subprocess
import shutil

SPECIALFILE_SYNCME = 'SYNC.ME'

# Where to save photos to.
trgPathRoot = "/home/vin/fileshare/photos/camera/"
trgSyncDir = "sdSyncTarget/"
trgHost = "hunchcorn"
# Olympus source paths.
srcOlympusRoot = "/media/vin/OLYMPUS"
srcOlympus = srcOlympusRoot + "/DCIM/100OLYMP/"
syncFilePathOlympus = srcOlympus + SPECIALFILE_SYNCME

def main():

  print ('start')
  # 1) Try to mount Olympus SD card.
  # 2) Read contents of SYNC.ME
  # 3) Sync files Olympus, except those named in the SYNC.ME file.   
  # 4) Update contents of SYNC.ME file and unmount SD card.

  # wait for udev rules to mount sd card
  mountTries = 20
  print ('test mount start')
  while (mountTries > 0) & (not os.path.exists(syncFilePathOlympus)):
    time.sleep(1)
    mountTries -= 1

  if os.path.exists(syncFilePathOlympus):
    print ('found Olympus SD card')
    doSyncOlympus(srcOlympus, trgHost, trgPathRoot)
    subprocess.check_call(['umount', srcOlympusRoot])
    print ('unmounted')
  else:
    print ('give up no mount')
    sys.exit()

def doSyncOlympus(srcImagePath, trgHost, trgPath):
  syncFilePath = trgPath + SPECIALFILE_SYNCME
  print ('reading SYNC.ME file from ' + trgHost + ':' + syncFilePath)
  copiedFiles = readSyncMeFile(trgHost, syncFilePath)
  print ('SYNC.ME contains ' + str(len(copiedFiles)) + ' filenames')
  # Also want to ignore the 'SYNC.ME' file
  copiedFiles.insert(0, SPECIALFILE_SYNCME)

  # Sync all files on card that aren't named in SYNC.ME
  cardFiles = os.listdir(srcImagePath)
  print ('cardFiles contains ' + str(len(cardFiles)) + ' filenames')
  toCopyFiles = [item for item in cardFiles if not item in copiedFiles and not item.endswith('.ORF')]
  print ('toCopyFiles contains ' + str(len(toCopyFiles)) + ' filenames')

  # Do copy
  for file in toCopyFiles:
    fullSrcPath = srcImagePath + file
    fullTrgPath = getFullTargetDirOlympus(fullSrcPath, trgPath + trgSyncDir)
    copyFile(fullSrcPath, trgHost, fullTrgPath)

  writeSyncMeFile(syncFilePath, cardFiles, trgHost)

def writeSyncMeFile(syncFilePath, cardFiles, host):
    print ('writing sync file')
    syncFileLocalPath = '/tmp/' + SPECIALFILE_SYNCME
    syncFile = open(syncFileLocalPath, 'w')
    syncFile.truncate(0)

    cardFiles.sort()
    for file in cardFiles:
      if file != SPECIALFILE_SYNCME:
        syncFile.write(file + '\n')

    syncFile.flush()
    syncFile.close()
    print ('closed sync file')

    subprocess.check_call(['scp', syncFileLocalPath, host + ':' + syncFilePath])
    print ('copied sync file to ' + host)

def readSyncMeFile(host, syncFilePath):
  syncFileLocalPath = '/tmp/' + SPECIALFILE_SYNCME
  subprocess.check_call(['scp', host + ':' + syncFilePath, syncFileLocalPath])
  
  if os.path.exists(syncFileLocalPath):
    syncFile = open(syncFileLocalPath, 'r')
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

def copyFile(src, host, trg):
  fullRemotePath = host + ':' + trg 
  print ('copying src: ' + src + ' trg: ' + fullRemotePath)
  subprocess.check_call(['ssh', host, 'mkdir', '-p', trg])
  subprocess.check_call(['rsync', '-Pradt', src, fullRemotePath])

# expands to /trg/2011/04/16/ based on file's modified date.
def getFullTargetDirOlympus(fullSrcFilePath, targetRoot):
  fileDateTime = time.localtime(os.path.getmtime(fullSrcFilePath))
  day = str(fileDateTime.tm_mday).zfill(2)
  month = str(fileDateTime.tm_mon).zfill(2)
  year = str(fileDateTime.tm_year)
  return targetRoot + year + "/" + month + "/" + day + "/"

# gets day and month from src dir name
def getDate(src):
  # src is like '/some_path/139_1604', want [16, 04]
  m = re.search('([0-9]{2})([0-9]{2})', src[src.rfind('_')+1:])
  print (src)
  return [m.group(1), m.group(2)]

# Standard boilerplate to call the main() function.
if __name__ == '__main__':
  main()
