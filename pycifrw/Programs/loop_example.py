#
# An example of how to output a subset of looped items.
#
from CifFile import CifFile, CifBlock
cf = CifFile("loop_example.cif")["some_stuff"] # open and parse our cif, 
                                      #we want data block named "some_stuff".
# --- Optional section
# Check that all our data
# items exist before attempting to access them
needed_items = [
          "_atom_site_label",
          "_atom_site_type_symbol",
          "_atom_site_fract_x",
          "_atom_site_fract_y",
          "_atom_site_fract_z"]

loopkeys = cf.GetLoopNames("_atom_site_label")  #get co-looped names 
if len(filter(lambda a,b=loopkeys:a not in b, needed_items)) != 0:
    print "Error: one or more items missing from atom_site_label loop"
    exit                        
#
# ----- End of optional section

nb = CifBlock()                   # create a new block 
map(lambda a:nb.AddItem(a,cf[a]),needed_items)  #set new values
nb.CreateLoop(needed_items)               # create the loop
df = CifFile()                    # create a new cif object
df.NewBlock("changed",nb)             # and add our new block
outfile = open("updated.cif",'w')      #open a file to write to
outfile.write (df.WriteOut(comment="# This file has been updated"))

