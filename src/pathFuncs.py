#!/usr/bin/python3
#Author: Emmanuel Odeke <odeke@ualberta.ca>

import sys
import os

afixPath = lambda root, path : os.path.join(root, path)
getDirContent = lambda path : os.walk(path)

#Returns True if a non-empty string is queried, and the string is a valid path
existantPath  = lambda aPath : aPath and os.path.exists(aPath)

#Permission and path associated functions, each of these functions
#returns True if the user has the specific permissions and if the path exists
hasReadPerm   = lambda aPath : existantPath(aPath) and os.access(aPath, os.R_OK)
hasWritePerm  = lambda aPath : existantPath(aPath) and os.access(aPath, os.W_OK)
hasXecutePerm = lambda aPath : existantPath(aPath) and os.access(aPath, os.X_OK)
hasRWXPerms   = lambda aPath : hasReadPerm(aPath) and hasWritePerms(aPath)\
                                and hasXecutePerm(aPath)

def getStatDict(path):
  if path and os.path.exists(path):
    return os.stat(path)

def dirListing(targetPath):
  iterator = os.listdir(targetPath)
  for child in iterator:
    yield afixPath(targetPath, child)

def pickRegularItemsFromWalk(walkGenerator):
  for root, dirs, regs in walkGenerator:
    if root is '.' or root is './':
      root = ''
       
    for reg in regs:
      yield os.path.join(root, reg)

def crawlAndMap(targetPath, functor):
  # Given a path and a generic function to apply to each
  # Return a generator whose content is the result of mapping each
  # path within nodes of the targetPath
  curDirGenerator = getDirContent(targetPath)

  try:
    for root, dirs, regFiles in curDirGenerator:
      afixedPaths = map(lambda path: afixPath(root, path), regFiles)
      functorMapping = map(lambda path: functor(path), afixedPaths)
      yield functorMapping
  except StopIteration:
    pass

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
