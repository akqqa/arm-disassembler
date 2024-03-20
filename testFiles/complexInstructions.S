adcs w15, w20, wzr
sys #0x3, c7, c9, #0x2, x3
at s1e1wp, x10
bic v13.16b, v22.16b, v13.16b
sbfx x14, x20, #0x3, #0x1b
subs w29, w13, w18, uxtx #0x2
uunpkhi z15.d, z23.s