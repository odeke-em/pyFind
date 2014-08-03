
pyFind
==============

 pyFind is meant to be a hybrid between UNIX utilities 'grep' and 'find'.

  The motivation is to provide a cross-platform tool for both the novice

and experienced programmer, in the field of file and pattern manipulation.

 All you'll need would be an installation of Python, and a little knowledge of 

regular expressions. For the advanced, the concept of piping is useful.


Example usage:
=================

  For options do: ./pyFind.py -h or ./pyFind.py --help
    Usage: pyFind.py [options]

    Options:
        -h, --help            show this help message and exit
        -a ACTION, --action=ACTION
                              Action to be executed Usage: <cmd> {} <....>\;
        -c, --colorOn         Turn off match coloring
        -i, --ignoreCase      Turn-off case sensitive matches
        -m MAXDEPTH, --maxDepth=MAXDEPTH
                              Set maximum recursion depth
        -n NEWERFILE, --newer=NEWERFILE
                              Any paths newer than this path will be matched
        -o, --onlyMatches     Set whether to only print the grouped/matched regex
                              patterns
        -p TARGETPATH, --path=TARGETPATH
                              Option for choosing the directory to search from
        -r REGEX, --regex=REGEX
                              The regular expression expected
        -l, --lineno          Toggle printing of line number occurances
        -v, --verbose         Set whether to display output.


  To find all files with a python extension in the current directory

    ./pyFind.py -p . -r ".*py$"

  --within a sub-directory max-depth of 2

    ./pyFind.py -p . -r "*.py$" -m 2

  To get all occurances of 'include' library files as received from standard input, 

    printing only the matches as specified by the input regular expression

      cat * | ./pyFind.py -r "include\s<(.*)>" -o

  To copy all header files( \*.h ) in directory '/usr/include' to directory '/home/headerCollection'
  
    ./pyFind.py -p /usr/include -r ".*h$" -a "cp {} /home/headerCollection"

  Get yourself all usages of 'git' in your history

    history | ./pyFind.py -r "git"

  Clean up all the swap files within a depth of 2 sub-directories of your current directory

    ./pyFind.py -p . -r ".*swp$" -a "rm {}"

  To find all .py files newer than 'pyFind.py' within a sub-directory depth of 9,

  and copy them to directory '../newest\_pys'

    ./pyFind.py -p .. -m 9 -r "*py$" -a "cp {} ../newest_pys" -n "pyFind.py"

  To turn off pattern-coloring:

    ./pyFind.py -c -p .. -r "*.h"

  If no command line arguments are passed in, it will assume the order

    <regex/pattern> <path>

  For the traditional grep users:

    ./pyFind.py foo <==> grep foo <==> ./pyFind.py -r foo

    ls | ./pyFind.py  foo <==> ls | grep foo

    ./pyFind.py foo . <==> grep foo . <==> ./pyFind.py -r foo -p .


   Find a sequence and line number for text read from stdin:

    eg after a cat of pyFind.py

        cat pyFind.py | pyFind.py -r 'search' -l

        9:     Pass a regular expression/pattern for a file to search for.

        10:  pyFind recursively searches through a tree; the maxDepth option

        11:  controls how deep pyFind searches.

        15:      ls | ./pyFind.py -r "*.c$" ##To search for all files with a .c extension

        51: intAble = lambda s: hasattr(s, '__divmod__') or intRegCompile.search(s)

        62: # Matcher to keep a greedy search going on and consuming endless memory

        243:   if re.search(WINDOWS_NT, OS_NAME): # Handling for windows to be explained

[ ![Codeship Status for odeke-em/pyFind](https://www.codeship.io/projects/c6e59ed0-fd82-0131-5044-1ea35c716b39/status)](https://www.codeship.io/projects/29440)
