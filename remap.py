import omg
import copy
import sys
from omg import txdef

DEBUG=0

if len(sys.argv) < 3:
    print("Usage: {sys.argv[0]} src.wad dst.wad")
    print("Steps the program will take:")
    print("1. Open each map in src.wad")
    print("2. Remap the textures to those from dst.wad")
    print("3. Write the result to out.wad")
    sys.exit(1)

a = omg.WAD(sys.argv[1])
b = omg.WAD(sys.argv[2])

ta = txdef.Textures(a.txdefs)
tb = txdef.Textures(b.txdefs)

mapper = {}

def dprint(string):
    global DEBUG
    if DEBUG:
        print(string)

def patch_match(patch, collection):
    for p in collection:
        if p.name == patch.name and p.x == patch.x and p.y == patch.y:
            # match found
            collection.remove(p)
            return True

def compare_tex(t1, t2):
    p1 = copy.deepcopy(t1.patches)
    p2 = copy.deepcopy(t2.patches)

    matches = True
    for p in p1:
        if not patch_match(p, p2):
            matches = False
            break

    return matches

def get_tex_match(tex, within):
    global mapper
    for t in within:
        if compare_tex(tex, within[t]):
            dprint(f"Mapping {tex.name} --> {within[t].name}")
            mapper[tex.name] = within[t].name
            return

    print(f"!! WARNING !! No match found for {tex.name}")

def build_map(tta,ttb):
    for t in tta:
        get_tex_match(tta[t],ttb)

def maptex(texture):
    # blank textures go out as-is
    if texture == '-':
        return texture

    if texture in mapper:
        dprint(f"MAP CHANGE: Remapping {texture} --> {mapper[texture]}")
        return mapper[texture]

    # if not in the mapping, return it as-is
    return texture

# program here
dprint("Building texture map...")
build_map(ta,tb)
dprint("Map built. Searching maps..")
for m in a.maps:
    ed = omg.MapEditor(a.maps[m])
    s = ed.sidedefs
    dprint("Processing map...")
    for side in s:
        side.tx_low = maptex(side.tx_low)
        side.tx_mid = maptex(side.tx_mid)
        side.tx_up = maptex(side.tx_up)
    b.maps[m] = ed.to_lumps()

b.to_file("out.wad")
print("Remap complete, result written to \"out.wad\"")
