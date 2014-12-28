#!/usr/bin/env python
'''
*******************************************************************************
 Author: Emmanuel Odeke <odeke@ualberta.ca>

 For help: ./pyFind.py -h 

    Pass a regular expression/pattern for a file to search for.
 pyFind recursively searches through a tree; the maxDepth option
 controls how deep pyFind searches.

 Acts as a filter in case no input arguments are passed in, taking input from
 standard input e.g
     ls | ./pyFind.py -r "*.c$" ##To search for all files with a .c extension
*******************************************************************************
'''
import os, re, sys
from time import sleep
from subprocess import Popen 

import pathFuncs # Local module
from parserCLI import cli_parser # Local module

############################# START_OF_CONSTANTS ##############################
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

# Codes for colors on posix-based terminals
POSIX_COLORS  = {
     WHITE  : 0,
     RED    : 91,
     GREEN  : 92,
     YELLOW : 93
}

HIGHLIGHT = '\033['
OS_NAME   = os.name
DEFAULT_SLEEP_TIMEOUT = 1

intRegCompile = re.compile("^(\d+)$", re.UNICODE)
intAble = lambda s: isCallable(s, '__divmod__') or intRegCompile.search(s)
SUPPORTS_TERMINAL_COLORING = re.match(POSIX_BASED_OS, OS_NAME) != None

def isCallable(obj, attrKey):
  attr = getattr(obj, attrKey, None) 
  if attr is None:
    return False

  return hasattr(attr, '__call__')

############################## END_OF_CONSTANTS ################################
# Writes a message to a stream and flushes the stream.
# Default stream is standard error
streamPrintFlush = lambda msg,stream=sys.stderr:\
                     msg and stream.write(msg) and stream.flush()

# Sub an asterik "*" that was included without a "." preceding it
# The presence of the above condition could potentially poison the regex
# Matcher to keep a greedy search going on and consuming endless memory
def clearRegexRecur(inRegex):
  # Input: A potential regular expression as a string
  # Convert an orphaned asterik "*" ie without a preceeding dot "." to ".*"
  # Returns: the sanitized regex
  try:
    regex = re.sub('^\.+$|^\*+$|^$','^.*$',inRegex)
    regex = re.sub('(^\*)|(^\.+[\.]+)|(\s*\*+)','.*', regex)
    
    regCompile = re.compile(regex)
  except Exception:
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
  if not queriedContent:
    return
  
  singleLinePrintable = isinstance(queriedContent, str)\
                    or isCallable(queriedContent, '__divmod__') \
                    or isinstance(queriedContent, tuple)

  if singleLinePrintable:
    try:
      streamPrintFlush("%s\n"%(queriedContent), stream=sys.stdout)
    except UnicodeEncodeError:
      streamPrintFlush("UnicodeEncodeError encode while printing\n")
    return

  if isinstance(queriedContent , list):
    for item in queriedContent:
      handlePrint(item)

  elif isinstance(queriedContent, dict):
    for value in queriedContent.values():
      handlePrint(value)

  else:
    # The queriedContent should have hooks: __str__ and __repr__ defined
    streamPrintFlush(queriedContent)

# Sandwiches and highlights the text subject with
# the colorKey, in between white color patterns
def colorPatterns(colorKey, text):
  return '{h}{c:2<}m{t}{h}{w:2<}m'.format(
     h=HIGHLIGHT, w=POSIX_COLORS[WHITE],
     c=POSIX_COLORS.get(colorKey,GREEN), t=text
  )

def matchPatterns(regCompile, text, verbosity, onlyPatternsPrinted,
                            colorOn, colorKey, linenoBool=False, lineno=0):

  regMatches = regCompile.findall(text)
  PATTERNS_MATCHED=False
  if regMatches:
    PATTERNS_MATCHED=True

    if onlyPatternsPrinted:
      joinedPatterns = ' '.join(regMatches)

      if (colorOn and SUPPORTS_TERMINAL_COLORING):
         handlePrint(colorPatterns(colorKey,joinedPatterns))

      else:
         # At this point just print the matched patterns
         handlePrint(joinedPatterns)

      return PATTERNS_MATCHED 

    else:
      if colorOn and SUPPORTS_TERMINAL_COLORING:
        # Take out non empty sequences
        regMatches = set(filter(lambda value: value, regMatches))
        for item in regMatches:
          text = text.replace(item, colorPatterns(colorKey, item))

      handlePrint('{l}: {t}'.format(l=lineno, t=text) if linenoBool else text)

  return PATTERNS_MATCHED

def treeTraverse(thePath, rDepth=1, regCompile=None, action=None,
                    verbosity=True, onlyMatches=False, baseTime=None,
                    colorOn=True, colorKey=RED, noDirsWanted=False):
    "Traverse a given path. A negative recursion depth terminates the"\
    "tree traversal dive.\n"\
    "Input: Path, match parameters and action to be performed 'baseTime' "\
    "is an unsigned number(float/int) parameter for which matches  will have "\
    "to be newer.\n"\
    "Output: Results from pattern matching and generic action application.\n"\
    "Returns: None"

    canTraverse = isCallable(rDepth, '__divmod__') and rDepth >= 0
    if not canTraverse:
      return

    # Catch invalid regCompiles
    if not isCallable(regCompile, 'match'):
      streamPrintFlush("Invalid regCompile: %s\n"%(regCompile))

    elif not pathFuncs.existantPath(thePath):
      verbosity and streamPrintFlush("%s doesn't exist\n"%(thePath))

    elif not pathFuncs.hasReadPerm(thePath):
      verbosity and streamPrintFlush("No read access to path %s\n"%(thePath))

    else:
      # Check if path is newer than base time.
      if not isCallable(baseTime, '__divmod__'):
        baseTime = 0
      elif os.path.getctime(thePath) < baseTime:
        return

      rDepth -= 1
      patternMatchedTrue = matchPatterns(
        regCompile,thePath, verbosity,onlyMatches, colorOn, colorKey
      )
    
      if patternMatchedTrue:
        if action: # Expecting a generic terminal based action eg cat, cp
           handleFunctionExecution(action, subject=thePath)

      if os.path.isdir(thePath):
        if not noDirsWanted: # Only non-dirs wanted
          iterator = pathFuncs.pickRegularItemsFromWalk(os.walk(thePath))
        else:
          iterator = pathFuncs.dirListing(thePath)

        for fullChildPath in iterator:
          treeTraverse(
            fullChildPath, rDepth, regCompile, action, verbosity,
            onlyMatches, baseTime, colorOn, colorKey, noDirsWanted=noDirsWanted
          )

def main():
    argc = len(sys.argv)
    if argc <= 1:
       sys.argv.append('-h')

    parser = cli_parser()
    options, args = parser

    action       = options.action
    colorOn      =  options.colorOn
    ignoreCase   = options.ignoreCase
    maxDepth     = options.maxDepth
    newerFile    = options.newerFile
    noDirsWanted = not options.files
    onlyMatches  = options.onlyMatches
    regex        = options.regex
    targetPath   = options.targetPath
    verbosity    = options.verbosity

    if not intAble(maxDepth):
      streamPrintFlush("MaxDepth should be an integer >= 0.\nExiting...\n")
      sys.exit(-1)

    maxDepth = int(maxDepth)
    regexArgs = re.UNICODE # Cases to be toggled in the match eg:
                           # Unicode character handling,case sensitivity etc
    if ignoreCase:
       regexArgs |= re.IGNORECASE

    regCompile = clearRegexRecur(regex)

    if targetPath:
       baseTime = -1
       if newerFile and os.path.exists(newerFile):
         baseTime = os.path.getctime(newerFile)

       treeTraverse(
         targetPath, maxDepth, regCompile, action,
         verbosity, onlyMatches, baseTime, colorOn, noDirsWanted=noDirsWanted
       )
    else:
       # Time for program to act as a filter
       filterStdin(regCompile, action, verbosity, onlyMatches, colorOn, linenoOn=options.lineno)

def handleFunctionExecution(action, subject):
  "Performs a generic action on the subject eg a terminal based action eg cat, cp.\
  Input: An action and a subject eg action=>'ls', subject=>'../'\
  Output: Terminal output from performing action on subject.\
  Returns: None"
  cmdText = action.replace(SUB_KEY,subject)
  if re.search(WINDOWS_NT, OS_NAME): # Handling for windows to be explained
    popenObj = os.popen(cmdText)
    handlePrint(popenObj.read())
  else:
    cmdList = list(filter(lambda item: item, cmdText.split(" "))) 
    popenObj= Popen(cmdList,stdin=sys.stdin,stdout=sys.stdout,stderr=sys.stderr)
    # Do something here if you want
    # try:
    #  while (popenObj.wait()):
    #    sleep(DEFAULT_SLEEP_TIMEOUT)
    #    popenObj.kill()
    # except OSError as e: # An externally induced kill to the process occured
    #  pass

def filterStdin(
    regCompile, action, verbosity, onlyMatches, colorOn=True, colorKey=RED, linenoOn=False
):
  "Enables data to come from the standard input instead.\
   Read lines from standard input until a blank line is encountered\
   Input:  Match parameters and action variables\
   Output: Generic action applied to all matched subjects\
   Returns: None"

  stdinReading = True
  lineno = 0
  while stdinReading:
    try:
      lineIn = sys.stdin.readline()
      if lineIn == "": # EOF equivalent here, time to end reading
        break
    except KeyboardInterrupt:
      if False: # This clause will be taken out soon
        handlePrint("Ctrl-C applied.\nExiting now...")
      stdinReading = False
    except Exception:
      handlePrint('Unhandled exception')
      stdinReading = False
    else:
      lineIn = lineIn.strip('\n')
      lineno += 1
      patternMatchedTrue =\
        matchPatterns(
            regCompile, lineIn, verbosity, onlyMatches, colorOn, colorKey, linenoOn, lineno
        )

      if patternMatchedTrue and action:
        handleFunctionExecution(action, subject=lineIn)
      
if __name__ == '__main__':
  try:
    main()
  except:
    if False: # This clause will soon be taken out
      handlePrint('Unhandled exception')
