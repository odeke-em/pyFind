
pyFind v0.0.1
==============

 pyFind is meant to be a hybrid between UNIX utilities 'grep' and 'find'.

  The motivation is to provide a cross-platform tool for both the novice

and experienced programmer, in the field of file and pattern manipulation.

 All you'll need would be an installation of Python, and a little knowledge of 

regular expressions. For the advanced, the concept of piping is useful.



Example usage:
=================

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
