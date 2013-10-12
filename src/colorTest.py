#!/usr/bin/python3

def main():
  testPhrase = "helloColor"
  for index in range(0, 110):
    paddedColor = "{:0>2}".format(index)
    print("\033[{pC}m{phrase} : {pi}".format(
      pC=paddedColor, phrase=testPhrase, pi=index
    ))

  print("\033[00m") #Revert to whitener color

if __name__ == '__main__':
  main()
