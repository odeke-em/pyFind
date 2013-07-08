#!/usr/bin/python3
'''
*****************************************************************************
 Author: Emmanuel Odeke <odeke@ualberta.ca>
 pyFind v1.1 

 For help: ./pyFind.py -h 

    Pass a regular expression/pattern for a file to search for.
 pyFind recursively searches through a tree; the maxdepth option
 controls how deep pyFind searches.

 Acts as a filter in case no input arguments are passed in, taking input from
 standard input e.g
     ls | ./pyFind.py -r "*.c$" ##To search for all files with a .c extension

*****************************************************************************
'''
import os, re,sys
from stat import S_ISDIR
 
from subprocess import Popen 

from optparse import OptionParser
from time import sleep

###############################START_OF_CONSTANTS##############################
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
     RED    : 31,
     GREEN  : 32,
     YELLOW : 33
}

OS_NAME   = os.name
SUPPORTS_TERMINAL_COLORING = (re.match(POSIX_BASED_OS,OS_NAME)!= None)
HIGHLIGHT = '\033['
DEFAULT_SLEEP_TIMEOUT = 1
###############################END_OF_CONSTANTS################################

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


#Returns True if a non-empty string is queried, and the string is a valid path
existantPath   = lambda aPath : aPath and os.path.exists(aPath)

#Permission and path associated functions, each of these functions
#returns True if the user has the specific permissions and if the path exists
hasReadPerm    = lambda aPath : existantPath(aPath) and os.access(aPath, os.R_OK)
hasWritePerm   = lambda aPath : existantPath(aPath) and os.access(aPath, os.W_OK)
hasXecutePerm  = lambda aPath : existantPath(aPath) and os.access(aPath, os.X_OK)
hasRWXPerms    = lambda aPath : hasReadPerm(aPath)  and hasWritePerms(aPath)\
                                and hasXecutePerm(aPath)

def handlePrint(queriedContent):
  "Handles printing of data with the assumption that data types 'str', 'int',\
   'tuple' can be printed on a single line without a lot of distortion and \
   scrolling. The method: hasattr(queriedContent,'__iter__') could be used to\
   check for elements but then 'tuple'-s would be included, invalidating the\
   first assumption.\
   Input: A subject object to print\
   Output: Printed form the object\
   Returns: None"
  if (not queriedContent):
    return            

  singleLinePrintable = (isinstance(queriedContent, str))or \
                        (isinstance(queriedContent, int))or \
                        (isinstance(queriedContent, tuple))

  if singleLinePrintable:
    try:
      sys.stdout.write("%s\n"%(queriedContent))
    except UnicodeEncodeError as e:
      sys.stderr.write("UnicodeEncodeError encode while trying to print\n")
      sys.stderr.write(e.__str__())
      return

  elif (isinstance(queriedContent , list)):
    for item in queriedContent:
      handlePrint(item)

  elif (isinstance(queriedContent, dict)):
    for key in queriedContent.keys():
      handlePrint(queriedContent[key])

  else: #The queriedContent should have hooks: __str__() and __repr__() defined
    sys.stderr.write(queriedContent)
    sys.stderr.write("\n")

def cli_parser():
    "The commandline parser.\
     Input: None\
     Output: None\
     Returns: the parser's options and arguments"
    parser = OptionParser()

    parser.add_option('-p', '--path', dest='targetPath',
    default="",help="Option for choosing the directory to search from")

    parser.add_option('-a','--action',dest='action',
    default="",help="Action to be executed\nUsage: <cmd> {} <....>\;")

    parser.add_option('-r','--regex',dest='regular_expression',
    default=".*",help="The regular expression expected")

    parser.add_option('-n','--newer',dest='newer_file',
    default=None,help="Any paths newer than this path will be matched")

    parser.add_option('-v','--verbose',dest='verbosity',default=True,
    help="Set whether to display output. Expected sanitizedChildPaths: "+\
      "True or False",
    action='store_false')
    
    parser.add_option('-i','--ignoreCase',dest='ignoreCase',default=True,
    help="Turn-off case sensitive matches",action="store_false")

    parser.add_option('-m', '--maxdepth', dest='maxdepth',
    default=1,help="Set maximum recursion depth")

    parser.add_option('-o', '--onlyMatches',dest='onlyMatches',default=False,
    help="Set whether to only print the match patterns",action='store_true')

    options,args = parser.parse_args()
    return options,args

#Sandwiches and highlights the text subject with the colorKey, in between white
#color patterns
colorPatterns = lambda colorKey, text : \
          '{hlight}{color:2<}m{text}{hlight}{white:2<}m'.format(
          hlight=HIGHLIGHT,color=POSIX_COLORS.get(colorKey,GREEN),
          text=text,white=POSIX_COLORS[WHITE])

def matchPatterns(regexCompile, text, verbosity, onlyPatternsPrinted, colorKey):
  regMatches = regexCompile.findall(text)
  PATTERNS_MATCHED=False
  if (regMatches):
    PATTERNS_MATCHED=True

    if onlyPatternsPrinted:
      joinedPatterns = ' '.join(regMatches)

      if (SUPPORTS_TERMINAL_COLORING):
         handlePrint(colorPatterns(colorKey,joinedPatterns))

      else: #At this point just print the matched patterns
         handlePrint(joinedPatterns)
      return PATTERNS_MATCHED 

    if (verbosity):
      if (SUPPORTS_TERMINAL_COLORING):
        for item in regMatches:
          text = text.replace(item,colorPatterns(colorKey,item))

      handlePrint(text)

  return PATTERNS_MATCHED

def treeTraverse(thePath, recursionDepth=1, regexCompile=None,
      action=None,verbosity=True,onlyMatches=False,baseTime=None,colorKey=RED):
    "Traverse a given path. A negative recursion depth terminates the tree\
     traversal dive.\
     Input: Path, match parameters and action to be performed\
     'baseTime' is an unsigned number(float/int) parameter for which matches\
      will have to be newer.\
     Output: Results from pattern matching and generic action application\
     Returns: None"
    #Catch invalid regexCompiles
    if (not hasattr(regexCompile,'match')):
      sys.stderr.write("Invalid regexCompile: %s\n"%(regexCompile))
      return

    if (recursionDepth < 0):
      return

    if (not existantPath(thePath)):
      sys.stderr.write("%s doesn't exist\n"%(thePath))
      return

    if (not hasReadPerm(thePath)):
      sys.stderr.write("No read access to path %s\n"%(thePath))
      return

    statDict = os.stat(thePath)
    recursionDepth -= 1

    #If the path is newer, it's creation time should be greater than baseTime
    if (baseTime and (baseTime >= 0) and (statDict.st_ctime < baseTime)):
      return

    patternMatchedTrue = matchPatterns(regexCompile,thePath,
                            verbosity,onlyMatches,colorKey)
    
    if (patternMatchedTrue):
      if (action):#Expecting a generic terminal based action eg cat, cp
        handleFunctionExecution(action, subject=thePath)

    if (S_ISDIR(statDict.st_mode)):
      for child in os.listdir(thePath):
        fullChildPath = os.path.join(thePath,child)
        treeTraverse(
            fullChildPath,recursionDepth,regexCompile,
            action,verbosity,onlyMatches,baseTime,colorKey
       )

def resolveBaseTime(path):
  #Input: A path -- directory/pipe or regular file
  #Return the creation time for the path if it is valid, else return -1
  if not existantPath(path):
    return -1
  try:
    statInfo = os.stat(path)
  except:
    return -1
  else:
    return statInfo.st_ctime

def main():
    if (len(sys.argv)== 1):
       sys.argv.append('-h')

    parser       = cli_parser()
    options,args = parser
    targetPath   = options.targetPath
    regex        = options.regular_expression
    verbosity    = options.verbosity
    action       = options.action
    maxdepth     = options.maxdepth
    onlyMatches  = options.onlyMatches
    ignoreCase   = options.ignoreCase
    newer_file   = options.newer_file

    try:
      maxdepth  = int(maxdepth)
    except ValueError as e:
      sys.stderr.write("MaxDepth should be an integer.\nExiting...\n")
      sys.exit(-1)

    if (maxdepth < 0):
       handlePrint("Illegal maxdepth: range should be >= 0.\nExiting..")
       sys.exit(-2)
    regexArgs = re.UNICODE #Cases to be toggled in the match eg:
                           #Unicode character handling,case sensitivity etc
    if (ignoreCase):
       regexArgs |= re.IGNORECASE
    
    regCompile = clearRegexRecur(regex)

    if targetPath:
       baseTime = resolveBaseTime(newer_file)
       treeTraverse(targetPath,maxdepth,regCompile,action,verbosity,
          onlyMatches,baseTime)
    else:
       #Time for program to act as a filter
       filterStdin(regCompile,action,verbosity,onlyMatches)

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

def filterStdin(regexCompile,action,verbosity,onlyMatches,colorKey=RED):
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
        stdinReading = False
    except KeyboardInterrupt as e:
      handlePrint("Ctrl-C applied.\nExiting now...")
      stdinReading = False
    except Exception as e:
      handlePrint(e.__str__())
      stdinReading = False
    else:
      lineIn = lineIn.strip('\n')
      patternMatchedTrue = matchPatterns(regexCompile,lineIn,
                            verbosity,onlyMatches,colorKey)

      if (patternMatchedTrue and action):
        handleFunctionExecution(action,subject=lineIn)
      
if __name__ == '__main__':
    main()
