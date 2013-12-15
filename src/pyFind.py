#!/usr/bin/python3
'''
********************************************************************************
 Author: Emmanuel Odeke <odeke@ualberta.ca>
 pyFind v1.1 

 For help: ./pyFind.py -h 

    Pass a regular expression/pattern for a file to search for.
 pyFind recursively searches through a tree; the maxDepth option
 controls how deep pyFind searches.

 Acts as a filter in case no input arguments are passed in, taking input from
 standard input e.g
     ls | ./pyFind.py -r "*.c$" ##To search for all files with a .c extension
********************************************************************************
'''
import os, re, sys
 
from time import sleep
from stat import S_ISDIR
from subprocess import Popen 

from parserCLI import cli_parser #Local module
import pathFuncs

###############################START_OF_CONSTANTS###############################
YELLOW  = "YELLOW"
GREEN   = "GREEN"
RED     = "RED"
WHITE   = "WHITE"
SUB_KEY = "{}" #This key will be used to substitute all occurances of matched
               #patterns in the 'action' string. The action string is the 
               #argument passed into the program that contains the generic
               #action to be performed on all matches.

POSIX_BASED_OS = "posix"
WINDOWS_NT     = "nt"

#Codes for colors on posix-based terminals
POSIX_COLORS  = { 
     WHITE  : 0,
     RED    : 91,
     GREEN  : 92,
     YELLOW : 93
}

HIGHLIGHT = '\033['
OS_NAME   = os.name
DEFAULT_SLEEP_TIMEOUT = 1

intRegCompile = re.compile("^(\d+)$",re.UNICODE)
intAble = lambda s : hasattr(s, '__divmod__') or intRegCompile.search(s)
SUPPORTS_TERMINAL_COLORING = (re.match(POSIX_BASED_OS, OS_NAME)!= None)
###############################END_OF_CONSTANTS################################

#Writes a message to a stream and flushes the stream. Default stream is standard
#error
streamPrintFlush = lambda msg,stream=sys.stderr:\
                     msg and stream.write(msg) and stream.flush()

#Sub an asterik "*" that was included without a "." preceding it
#The presence of the above condition could potentially poison the regex
#Matcher to keep a greedy search going on and consuming endless memory
def clearRegexRecur(inRegex):
  #Input: A potential regular expression as a string
  #Convert an orphaned asterik "*" ie without a preceeding dot "." to ".*"
  #Returns: the sanitized regex
  try:
    regex = re.sub('^\.+$|^\*+$','^.*$',inRegex)
    regex = re.sub('(^\*)|(^\.+[\.]+)|(\s*\*+)','.*', regex)
    
    regCompile = re.compile(regex)
  except:
    return None
  else:
    return regCompile


def handlePrint(queriedContent):
  "Handles printing of data with the assumption that data types 'str', 'int',\
   'tuple' can be printed on a single line without a lot of distortion and \
   scrolling. The method: hasattr(queriedContent,'__iter__') could be used to\
   check for elements but then tuples would be included, invalidating the\
   first assumption.\
   Input: A subject object to print\
   Output: Printed form of the object\
   Returns: None"
  if (not queriedContent):  return
  

  singleLinePrintable = (isinstance(queriedContent, str))or \
                        (isinstance(queriedContent, int))or \
                        (isinstance(queriedContent, tuple))

  if singleLinePrintable:
    try:
      streamPrintFlush("%s\n"%(queriedContent), stream=sys.stdout)
    except UnicodeEncodeError as e:
      streamPrintFlush(
        "UnicodeEncodeError encode while trying to print\n%s\n"%(e.__str__())
      )
      return

  elif (isinstance(queriedContent , list)):
    for item in queriedContent:
      handlePrint(item)

  elif (isinstance(queriedContent, dict)):
    for key in queriedContent.keys():
      handlePrint(queriedContent[key])

  else: #The queriedContent should have hooks: __str__() and __repr__() defined
    streamPrintFlush(queriedContent)

#Sandwiches and highlights the text subject with the colorKey, in between white
#color patterns
colorPatterns = lambda colorKey, text : \
          '{hlight}{color:2<}m{text}{hlight}{white:2<}m'.format(
          hlight=HIGHLIGHT,color=POSIX_COLORS.get(colorKey,GREEN),
          text=text,white=POSIX_COLORS[WHITE])

def matchPatterns(
    regexCompile, text, verbosity, onlyPatternsPrinted, colorOn, colorKey
  ):
  regMatches = regexCompile.findall(text)
  PATTERNS_MATCHED=False
  if (regMatches):
    PATTERNS_MATCHED=True

    if onlyPatternsPrinted:
      joinedPatterns = ' '.join(regMatches)

      if (colorOn and SUPPORTS_TERMINAL_COLORING):
         handlePrint(colorPatterns(colorKey,joinedPatterns))

      else: #At this point just print the matched patterns
         handlePrint(joinedPatterns)

      return PATTERNS_MATCHED 

    if (verbosity):
      if (colorOn and SUPPORTS_TERMINAL_COLORING):
        for item in regMatches:
          text = text.replace(item,colorPatterns(colorKey,item))

      handlePrint(text)

  return PATTERNS_MATCHED

def treeTraverse(thePath, recursionDepth=1, regexCompile=None,
     action=None,verbosity=True,onlyMatches=False,baseTime=None,colorOn=True,colorKey=RED):
    "Traverse a given path. A negative recursion depth terminates the tree\
     traversal dive.\
     Input: Path, match parameters and action to be performed\
     'baseTime' is an unsigned number(float/int) parameter for which matches\
      will have to be newer.\
     Output: Results from pattern matching and generic action application\
     Returns: None"
    #Catch invalid regexCompiles
    if (not hasattr(regexCompile,'match')):
      streamPrintFlush("Invalid regexCompile: %s\n"%(regexCompile))
      return

    if (recursionDepth < 0):
      return

    if (not pathFuncs.existantPath(thePath)):
      streamPrintFlush("%s doesn't exist\n"%(thePath))
      return

    if (not pathFuncs.hasReadPerm(thePath)):
      streamPrintFlush("No read access to path %s\n"%(thePath))
      return

    statDict = pathFuncs.getStatDict(thePath)
    recursionDepth -= 1
    #If the path is newer, it's creation time should be greater than baseTime
    if (baseTime and (baseTime >= 0) and (statDict.st_ctime < baseTime)):
      return

    patternMatchedTrue = \
      matchPatterns(
        regexCompile,thePath, verbosity,onlyMatches, colorOn, colorKey
      )
                           
    
    if (patternMatchedTrue):
      if (action):#Expecting a generic terminal based action eg cat, cp
        handleFunctionExecution(action, subject=thePath)

    
    if (S_ISDIR(statDict.st_mode)):

      for child in pathFuncs.dirListing(thePath):
        fullChildPath = pathFuncs.afixPath(thePath, child)
        treeTraverse(
          fullChildPath,recursionDepth,regexCompile,
          action,verbosity,onlyMatches,baseTime,colorOn, colorKey
        )

def resolveBaseTime(path):
  #Input: A path -- directory/pipe or regular file
  #Return the creation time for the path if it is valid, else return -1
  if not pathFuncs.existantPath(path):
    return -1
  try:
    statInfo = pathFuncs.getStatDict(path)
  except:
    return -1
  else:
    return statInfo.st_ctime

def main():
    argc = len(sys.argv)
    if (argc <= 1):
       sys.argv.append('-h')

    parser       = cli_parser()
    options,args = parser

    targetPath   = options.targetPath
    regex        = options.regex
    verbosity    = options.verbosity
    action       = options.action
    maxDepth     = options.maxDepth
    onlyMatches  = options.onlyMatches
    ignoreCase   = options.ignoreCase
    newerFile    = options.newerFile
    colorOn	 = options.colorOn

    if not intAble(maxDepth):
      streamPrintFlush("MaxDepth should be an integer >= 0.\nExiting...\n")
      sys.exit(-1)

    maxDepth = int(maxDepth)
    
    regexArgs = re.UNICODE #Cases to be toggled in the match eg:
                           #Unicode character handling,case sensitivity etc
    if (ignoreCase):
       regexArgs |= re.IGNORECASE
    

    #Case for when only the regex and path have been entered eg: 
    # ./pyFind.py books .
    # if (argc == 3):
    #   targetPath = sys.argv[2]
    #   argc -= 1 #Reduction in-order to catch argument 2 in the argument vector
  
    #Case for when only the regex has been entered eg: 
    # ./pyFind.py books
    # if (argc == 2):
    #   regex = sys.argv[1]

    regCompile = clearRegexRecur(regex)

    if (targetPath):
       baseTime = resolveBaseTime(newerFile)
       treeTraverse(
         targetPath, maxDepth, regCompile, action,
         verbosity, onlyMatches, baseTime, colorOn
       )
    else:
       #Time for program to act as a filter
       filterStdin(regCompile, action, verbosity, onlyMatches, colorOn)

def handleFunctionExecution(action, subject):
  "Performs a generic action on the subject eg a terminal based action eg cat, cp.\
    Input: An action and a subject eg action=>'ls', subject=>'../'\
    Output: Terminal output from performing action on subject.\
    Returns: None"
  cmdText = action.replace(SUB_KEY,subject)
  if (re.search(WINDOWS_NT, OS_NAME)): #Handling for windows to be explained
    popenObj = os.popen(cmdText)
    handlePrint(popenObj.read())
    return

  cmdList = list(filter(lambda item: item, cmdText.split(" "))) 
  popenObj= Popen(cmdList,stdin=sys.stdin,stdout=sys.stdout,stderr=sys.stderr)

  #Do something here if you want
  #try:
  #  while (popenObj.wait()):
  #    sleep(DEFAULT_SLEEP_TIMEOUT)
  #    popenObj.kill()
  #except OSError as e:#An externally induced kill to the process occured
  #  pass

def filterStdin(
    regexCompile, action, verbosity, onlyMatches, colorOn=True, colorKey=RED
  ):
  "Enables data to come from the standard input instead.\
   Read lines from standard input until a blank line is encountered\
   Input:  Match parameters and action variables\
   Output: Generic action applied to all matched subjects\
   Returns: None"

  stdinReading = True
  while stdinReading:
    try:
      lineIn = sys.stdin.readline()
      if (lineIn == ""):#EOF equivalent here, time to end reading
        break
    except KeyboardInterrupt as e:
      if False: #This clause will be taken out soon
        handlePrint("Ctrl-C applied.\nExiting now...")
      stdinReading = False
    except Exception as e:
      handlePrint(e.__str__())
      stdinReading = False
    else:
      lineIn = lineIn.strip('\n')
      patternMatchedTrue = matchPatterns(
        regexCompile, lineIn, verbosity, onlyMatches, colorOn, colorKey
      )

      if (patternMatchedTrue and action):
        handleFunctionExecution(action,subject=lineIn)
      
if __name__ == '__main__':
  main()
