#!/usr/bin/python3
#Author: Emmanuel Odeke <odeke@ualberta.ca>

import sys
import os

from hashlib import md5

afixPath = lambda root, path : os.path.join(root, path)
getDirContent = lambda path : os.walk(path)

def dirListing(targetPath):
  return os.listdir(targetPath)

def getMD5(path):
  if not (path and os.path.exists(path)): return None

  fP = open(path, "rb")
  fData = fP.read()
  fileMd5 = md5(fData)
  fP.close()
  
  formattedMD5 = "%s : %s"%(path, fileMd5.hexdigest())
  return formattedMD5

def crawlAndMap(targetPath, functor):
  #Given a path and a generic function to apply to each
  #Return a generator whose content is the result of mapping each
  #path within nodes of the targetPath
  curDirGenerator = getDirContent(targetPath)

  try:
    for root, dirs, regFiles in curDirGenerator:
      afixedPaths = map(lambda path: afixPath(root, path), regFiles)
      functorMapping = map(lambda path: functor(path), afixedPaths)

      yield functorMapping

  except StopIteration: pass
  else: pass

def main():
  #Sample run
  argc = len(sys.argv)
  if argc <= 1:
    sys.stderr.write("Usage: \033[33m./md5sumer.py <paths> [...]\033[00m\n")
    return

  for eachPath in sys.argv[1:]:
    md5s = crawlAndMap(eachPath, getMD5)
    for hashesList in md5s:
      listedHashes = list(hashesList)
      if listedHashes:
        print("\n".join(listedHashes))
      
if __name__ == "__main__":
  main()
