#!/usr/bin/python3
#Parser for pyFind

from optparse import OptionParser

def cli_parser():
  "The commandline parser.\
   Input: None\
   Output: None\
   Returns: the parser's options and arguments"
  parser = OptionParser()

  parser.add_option('-a','--action',dest='action',
  default="",help="Action to be executed\nUsage: <cmd> {} <....>\;")

  parser.add_option('-c', '--colorOn',dest='colorOn',default=True,
  help="Turn off match coloring",action='store_false')
  
  parser.add_option('-i','--ignoreCase',dest='ignoreCase',default=True,
  help="Turn-off case sensitive matches",action="store_false")

  parser.add_option('-m', '--maxDepth', dest='maxDepth',
  default=1,help="Set maximum recursion depth")

  parser.add_option('-n','--newer',dest='newerFile',
  default=None,help="Any paths newer than this path will be matched")

  parser.add_option('-o', '--onlyMatches', dest='onlyMatches',default=False,
  help="Set whether to only print the grouped/matched regex patterns",
  action='store_true')

  parser.add_option('-p', '--path', dest='targetPath',
  default="",help="Option for choosing the directory to search from")

  parser.add_option('-r','--regex',dest='regex',
  default=".*",help="The regular expression expected")

  parser.add_option('-l', '--lineno', dest='lineno',
  default=False, help="Toggle printing of line number occurances", action='store_true')

  parser.add_option('-v','--verbose',dest='verbosity',default=True,
  help="Set whether to display output.", action='store_false')

  parser.add_option('-f', '--files', dest='files', default=False,
  help="Toggle retrieval of only files", action='store_true')

  options,args = parser.parse_args()

  return options,args
