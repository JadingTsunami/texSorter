import omg
import copy
import sys
from omg import txdef

DEBUG=1

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

fa = a.flats
fb = b.flats

mapper = {}
flatmapper = {}

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

def compare_flat(f1, f2):
    return f1.data == f2.data

def get_tex_match(tex, within):
    global mapper
    for t in within:
        if tex.name == within[t].name:
            dprint(f"(Tex) Name match found for {tex.name}, skipping...")
            return
        if compare_tex(tex, within[t]):
            dprint(f"(Tex) Mapping {tex.name} --> {within[t].name}")
            mapper[tex.name] = within[t].name
            return

    print(f"!! WARNING !! No match found for {tex.name}")

def get_flat_match(flat, within, name):
    global flatmapper
    for f in within:
        if compare_flat(flat, within[f]):
            dprint(f"(Flat) Mapping {name} --> {f}")
            flatmapper[name] = f
            return

    print(f"!! WARNING !! No match found for {name}")

def build_tex_map(tta,ttb):
    for t in tta:
        get_tex_match(tta[t],ttb)

def build_flat_map(ffa,ffb):
    for f in ffa:
        get_flat_match(ffa[f],ffb,f)

def maptex(texture):
    # blank textures go out as-is
    if texture == '-':
        return texture

    if texture in mapper:
        dprint(f"MAP CHANGE: Remapping {texture} --> {mapper[texture]}")
        return mapper[texture]

    # if not in the mapping, return it as-is
    return texture

def mapflat(flat):
    if flat in flatmapper:
        dprint(f"MAP CHANGE: Remapping {flat} --> {flatmapper[flat]}")
        return flatmapper[flat]

    # if not in the mapping, return it as-is
    return flat

# program here
dprint("Building texture map...")
build_tex_map(ta,tb)
dprint("Building flat map...")
build_flat_map(fa,fb)
dprint("Map built. Searching maps..")
for m in a.maps:
    ed = omg.MapEditor(a.maps[m])
    dprint(f"{m}: Processing map textures...")
    for side in ed.sidedefs:
        side.tx_low = maptex(side.tx_low)
        side.tx_mid = maptex(side.tx_mid)
        side.tx_up = maptex(side.tx_up)
    dprint(f"{m}: Processing map flats...")
    for sector in ed.sectors:
        sector.tx_ceil = mapflat(sector.tx_ceil)
        sector.tx_floor = mapflat(sector.tx_floor)
    b.maps[m] = ed.to_lumps()
    dprint(f"{m}: Remap complete")

b.to_file("out.wad")
print("Remap complete, result written to \"out.wad\"")
