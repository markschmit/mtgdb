

import string
import os
import sys





def parse(file):

  card_array = []
  card_dict = {}

  card_ref = open(file)

  
  current_card = []
  
  #line = card_ref.readline()
  lines  = card_ref.readlines()
  i = 0


  #while line != "":
  while i < len(lines):

    line = lines[i].strip()
    current_card = []

    while len(current_card) == 0: 
      if line == "":
        #line = card_ref.readline().strip()
        i += 1
        line = lines[i].strip()
      while line != "":
        #detect missing linebreak in oracle file
        if (len(current_card) > 2
          and ((line[0] == '{' and line[-1] == '}')    #cc, or 
          or (len(line) >= 4 and line[-4:] == 'Land'))):  #type
            
          #sys.stderr.write("Problem found: "+line+"\n")
          #sys.stderr.write("Card: "+current_card[0]+"\n")
          #sys.stderr.write("Last line: "+current_card[-2]+"\n")
          current_card = current_card[:-1]

          i -= 1
          #sys.stderr.write(lines[i]+"\n")
          line = lines[i].strip()
          break
        current_card.append(line)
        #line = card_ref.readline().strip()
        i += 1
        if i<len(lines):
          line = lines[i].strip()
        else:
          break


    # Process Card

    if len(current_card) == 0:
      #print 'blah'
      continue

    name = current_card[0]
    supertype = ""
    subtype = ""
    text = ""
    power = toughness = ""
    #print "Processing:", name
    
    if string.find(current_card[1], "Land") >= 0:
      cost = ""
      type = current_card[1]
      text_start = 2
    else:
      cost = string.replace(string.replace(current_card[1], '{',''), '}', '')
      type = current_card[2]
      if string.find(type,"Creat") >= 0 and string.find(type,"Ench") < 0:
        power, toughness = string.split(current_card[3], "/")
        text_start = 4
      else:
        text_start = 3
      
    if string.find(type, "Legendary") >= 0:
      supertype = "Legendary"
      type = string.replace(type, "Legendary ", "")
    elif string.find(type, "Basic") >= 0:
      supertype = "Basic"
      type = string.replace(type, "Basic ", "")

    if string.find(type, " -- ") >= 0:
      type, subtype = string.split(type, " -- ")
      
    # type should be fine now
    for l in current_card[text_start:]:
      text += l + "\n"
    text = text.strip()


    card_dict[name] = [name, cost, supertype, type, subtype, power, toughness, text]
    card_array.append(card_dict[name])
      
    # Prep next line
    
    line = card_ref.readline()

  return card_dict




#array = parse(sys.argv[1])
#print "Array: length = ", len(array)


if __name__ == "__main__":

  dict = parse(sys.argv[1])

  keys = dict.keys()
  keys.sort()

  for k in keys:

    print repr(string.join(dict[k],'|'))[1:-1]
    continue


  sys.exit()

  print "Name: \t\t", dict[k][0]
  print "Cost: \t\t", dict[k][1]
  print "Supertype: \t", dict[k][2]
  print "Type: \t\t", dict[k][3]
  print "Subtype: \t", dict[k][4]
  print "P/T: \t\t", dict[k][5], "/", dict[k][6]
  print "Text: \t\t", dict[k][7]
  print ""

  sys.exit()



