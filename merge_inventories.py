

import glob
import os
import sys

from optparse import OptionParser

import mtgutil.inv

if __name__ == "__main__":
  merged = mtgutil.inv.Inventory()

  parser = OptionParser()
  parser.add_option("--output_file", dest="output_file", help="output file")

  (options, args) = parser.parse_args()

  if not options.output_file:
    print >>sys.stderr, "no --output_file specified"
    sys.exit(1)

  if len(args) < 1:
    print >>sys.stderr, "no files specified"
    sys.exit(1)

  for pattern in args:
    for filename in glob.glob(pattern):
      if not os.path.exists(filename):
        print >>sys.stderr, "failed to read filename: %s" % filename
        sys.exit(-1)
      if os.path.isdir(filename):
        continue
      print "Reading file: %s" % filename
      inven = mtgutil.inv.Inventory()
      inven.ReadFromFile(filename)
      merged.Merge(inven)

  nameCount = 0
  cardCount = 0
  for (n, s, q) in merged.GetContents():
    nameCount += 1
    cardCount += q
  print "Read %d cards with %d distinct names" % (cardCount, nameCount)
  merged.WriteToFile(options.output_file)
  
