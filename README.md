# arm-disassembler
CS4099 Project - A program to disassemble arm instructions given the formal specification

Known issues:
- #num - num patterns present in disassembly instead of resolving these equations
- or support - should pick one or the other with |. unsure how to pick which?
- fix up the encoding error - choose option and explanation based off the option in the header!
-  mls insutrcitons have binary given at the end, should convert to decimal perhaps
- count UXTW #0 etc, as defaults to not be shown - LDR <Wt>, [<Xn|SP>, (<Wm>|<Xm>){, <extend> {<amount>}}] this complicates things a bit
- msr? should be a tag, instead is nothing
  ^ THIS IS DUE TO INCORRECT ORDER OF VARS TO TABLE VARS. SHOULD MAKE MORE ROBUST
    ^ ACTUALLY, i think its due to it being a custom label so not in the table!
    OHH cause it should be aliased but isnt so nothing is defined for it!!!
- LDRH  w22, [x12, #2254] - should be negative! signed not unsighned - how to tell? uimm vs imm/pimm?
- general aliases not being matched correctly as condiitons not supported