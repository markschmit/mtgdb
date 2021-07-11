
import csv
import sys

from optparse import OptionParser

import mtgutil.sets
import mtgutil.inv

if __name__ == "__main__":
  parser = OptionParser()
  parser.add_option("--output_file", dest="output_file", help="output file")

  (options, args) = parser.parse_args()

  if not options.output_file:
    print >>sys.stderr, "no --output_file specified"
    sys.exit(1)

  if len(args) < 1:
    print >>sys.stderr, "no files specified"
    sys.exit(1)

  db = mtgutil.sets.SetsDB()

  inv = mtgutil.inv.Inventory()
  inv.ReadFromFile(args[0])

  distinct = 0
  total = 0
  with open(options.output_file, 'wb') as output_file:
    writer = csv.DictWriter(output_file, fieldnames=["Card", "Set ID", "Set Name", "Quantity", "Foil"])

    writer.writeheader()
    for (name, set_code, quantity) in inv.GetContents():
      s = db.GetSet(set_code)
      if s == None:
        raise Exception("Unable to find set %s" % set_code)

      mtgo_set_code = s.mtgo_code
      writer.writerow({
        "Card": name,
        "Set ID": s.mtgo_code,
        "Set Name": s.name,
        "Quantity": quantity,
        })
      distinct += 1
      total += quantity

  print "Wrote %d total cards, %d distinct" % (total, distinct)
  sys.exit(0)



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

  for s in db.GetSets():
    print s
