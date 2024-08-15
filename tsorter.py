import omg
from omg import txdef
from omg import playpal
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from tkinter import messagebox
import json
import webcolors
from PIL import Image, ImageDraw, ImageTk

listbox = None
wad = None
tex = None
texname = None
img = None
howmany = {}
modified = False

# Adapted from:
# https://stackoverflow.com/questions/9694165/convert-rgb-color-to-english-color-name-like-green-with-python
# https://stackoverflow.com/questions/9694165/convert-rgb-color-to-english-color-name-like-green-with-python/78741669#78741669
def get_color_name(rgb_triplet, myColors):
    # full list: https://www.w3schools.com/tags/ref_colornames.asp

    min_colors = {}
    for name, hex_val in myColors.items():
        r_c, g_c, b_c = webcolors.hex_to_rgb(hex_val)
        rd = (r_c - rgb_triplet[0]) ** 2
        gd = (g_c - rgb_triplet[1]) ** 2
        bd = (b_c - rgb_triplet[2]) ** 2
        min_colors[(rd + gd + bd)] = name

    return min_colors[min(min_colors.keys())]

# https://stackoverflow.com/questions/29726148/finding-average-color-using-python
def average_image_color(image):

    i = image
    h = i.histogram()

    # split into red, green, blue
    r = h[0:256]
    g = h[256:256*2]
    b = h[256*2: 256*3]

    # perform the weighted average of each channel:
    # the *index* is the channel value, and the *value* is its weight
    boost = 1.8
    return (
        sum( i*w*boost for i, w in enumerate(r) ) / max(1,sum(r)),
        sum( i*w*boost for i, w in enumerate(g) ) / max(1,sum(g)),
        sum( i*w*boost for i, w in enumerate(b) ) / max(1,sum(b))
    )

def load_json_data(file_path):
    with open(file_path, 'r') as f:
        data = json.load(f)
    return data

def check_texture(data, tn):
    if len(tn) < 8:
        return False

    prefix = tn[0]
    category = tn[1:5]
    color = tn[5]
    num = tn[6:]

    if prefix != data['Prefix']:
        return False
    if category not in data['Categories']:
        return False
    if color not in data['Colors'].values():
        return False
    if not num.isdigit():
        return False
    return True

def inc_howmany(prefix, category, color):
    cc = prefix + category + color
    cc = cc.upper()
    if cc in howmany:
        howmany[cc] += 1
    else:
        howmany[cc] = 1

def dec_howmany(prefix, category, color):
    cc = prefix + category + color
    cc = cc.upper()
    if cc in howmany:
        howmany[cc] -= 1
    if howmany[cc] < 0:
        del howmany[cc]

def get_howmany(prefix, category, color):
    cc = prefix + category + color
    cc = cc.upper()
    if cc in howmany:
        return howmany[cc]
    else:
        return 0

def register_texture(data, tn):
    if check_texture(data, tn):
        inc_howmany(tn[0], tn[1:5], tn[5])

def unregister_texture(data, tn):
    if check_texture(data, tn):
        dec_howmany(tn[0], tn[1:5], tn[5])

def reset():
    global listbox

    listbox.delete(0, tk.END)
    howmany = {}
    texname = None
    tex = None
    img = None
    wad = None

def load_textures():
    global listbox
    global tex
    global wad
    global data

    reset()

    if 'PLAYPAL' in wad.data:
        playpal.Playpal.from_lump(wad, lump=wad.data['PLAYPAL'])
        wad.palette = wad.palettes[0]
        for p in wad.patches:
            wad.patches[p].palette = wad.palette
    tex = txdef.Textures(wad.txdefs)
    for item in tex:
        listbox.insert(tk.END, item)
        register_texture(data, item)

def load_wad():
    global wad
    file_path = filedialog.askopenfilename(title="Choose a WAD file", filetypes=[("WAD files", "*.wad")])
    if file_path:
        wad = omg.WAD(file_path)
        if wad:
            load_textures()

def save_wad():
    global wad
    global modified
    file_path = filedialog.asksaveasfilename(title="Save to a WAD file", filetypes=[("WAD files", "*.wad")])
    if file_path and wad:
        wad.txdefs = tex.to_lumps()
        wad.to_file(file_path)
        modified = False

def create_gui(data):
    global listbox

    root = tk.Tk()
    root.title("Texture Sorter")
    root.geometry('1024x700')

    def check_exit():
        global modified
        if (modified and messagebox.askyesno("Unsaved Changes", "There are unsaved changes. Do you want to quit?")) or not modified:
            root.quit()

    # Scrollable list
    list_frame = tk.Frame(root)
    list_frame.pack(side=tk.LEFT, fill=tk.Y)
    scrollbar = tk.Scrollbar(list_frame)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set, selectmode=tk.EXTENDED, exportselection=False)
    listbox.pack(side=tk.LEFT, fill=tk.BOTH)
    scrollbar.config(command=listbox.yview)

    # Image block
    image_frame = tk.Frame(root)
    image_frame.pack(side=tk.TOP, anchor=tk.N, fill=tk.BOTH, expand=True)
    image_label = tk.Label(image_frame)
    tex_label = tk.Label(image_frame, font=("Courier", 24))
    tex_label.pack(side=tk.TOP, anchor=tk.N, fill=tk.X, expand=True)
    image_label.pack(side=tk.BOTTOM, fill=tk.BOTH)

    # Buttons
    button_frame = tk.Frame(root)
    button_frame.pack(side=tk.BOTTOM)
    load_button = tk.Button(button_frame, text="Load", command=load_wad)
    load_button.pack(side=tk.LEFT)
    save_button = tk.Button(button_frame, text="Save", command=save_wad)
    save_button.pack(side=tk.LEFT)
    exit_button = tk.Button(button_frame, text="Exit", command=check_exit)
    exit_button.pack(side=tk.LEFT)

    # texture buttons
    button_frame2 = tk.Frame(root)
    button_frame2.pack(side=tk.BOTTOM)
    rename_button = tk.Button(button_frame2, text="Rename")
    rename_button.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)

    # Dropdown menus
    dropdown_frame = tk.Frame(root)
    dropdown_frame.pack(side=tk.BOTTOM, fill=tk.X)

    def create_dropdown(frame, values, title):
        dropdown_frame = tk.Frame(frame)

        scrollbar = tk.Scrollbar(dropdown_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        dropdown = tk.Listbox(dropdown_frame, selectmode=tk.SINGLE, exportselection=False, yscrollcommand=scrollbar.set)
        for value in values:
            dropdown.insert(tk.END, value)
        dropdown.select_set(0)
        dropdown.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar.config(command=dropdown.yview)

        dropdown_frame.pack(side=tk.LEFT, fill=tk.X)

        return dropdown

    dropdown1_values = data['Categories']
    dropdown2_values = data['Colors']

    dropdown1 = create_dropdown(dropdown_frame, dropdown1_values, "Categories")
    dropdown2 = create_dropdown(dropdown_frame, dropdown2_values.keys(), "Colors")

    checkbox_var = tk.BooleanVar()
    checkbox_var.set(True)
    checkbox = tk.Checkbutton(dropdown_frame, variable=checkbox_var, text="Auto-select color")
    checkbox.pack(side=tk.LEFT)

    def generate_texture_name():
        prefix = data['Prefix']
        category = dropdown1.get(dropdown1.curselection()[0])
        color = data['Colors'][dropdown2.get(dropdown2.curselection()[0])]
        number = get_howmany(prefix, category, color)
        return f"{prefix:1s}{category:<4s}{color:1s}{number:02d}".upper()

    def set_texture(*args):
        global texname
        texname = generate_texture_name()
        tex_label.config(text=f"{texname}")

    def select_listbox_item(listbox, item_to_select):
      for i in range(listbox.size()):
        if listbox.get(i) == item_to_select:
          listbox.selection_clear(0, tk.END)
          listbox.selection_set(i)
          break

    def on_list_select(event):
        index = listbox.curselection()
        if index:
            selected_item = listbox.get(index[0])
            # FIXME: Multi-patch and offsets support
            tx = tex[selected_item]
            patch = tx.patches[0]
            if patch.name in wad.patches:
                image = wad.patches[patch.name].to_Image(mode='RGBA')
                image = image.resize((tx.width * 2, tx.height * 2))
                if checkbox_var.get():
                    color = average_image_color(image)
                    color_name = get_color_name(color, data['AutoColors'])
                    if color_name in dropdown2_values.keys():
                        select_listbox_item(dropdown2, color_name)
                    else:
                        select_listbox_item(dropdown2, 'mixed')
                        
                #tex_label.config(text=f"{int(color[0]):02x}:{int(color[1]):02x}:{int(color[2]):02x} -- {generate_texture_name()}")
                set_texture()
                photo = ImageTk.PhotoImage(image)
                image_label.config(image=photo)
                image_label.image = photo
            else:
                image_label.config(image="", text="Not found")

    def rename_texture():
        global listbox
        global modified
        prefix = data['Prefix']

        selected_indices = listbox.curselection()

        for index in selected_indices:
            old_name = listbox.get(index)
            new_name = generate_texture_name()
            # increment index
            category = dropdown1.get(dropdown1.curselection()[0])
            color = data['Colors'][dropdown2.get(dropdown2.curselection()[0])]
            # FIXME: would unregister_texture(data, old_name) here,
            # but would require overwriting all the old textures (boo)
            # so i'll have to fix that later
            inc_howmany(prefix, category, color)
            listbox.delete(index)
            listbox.insert(index, new_name)
            listbox.focus_set()
            # update the WAD texture name
            tex.rename(old_name, new_name)
            tex[new_name].name = new_name
            modified = True

        listbox.selection_clear(0, tk.END)
        listbox.selection_set(min(selected_indices[-1]+1,listbox.size()))
        listbox.event_generate("<<ListboxSelect>>")

    listbox.bind('<<ListboxSelect>>', on_list_select)
    dropdown1.bind('<<ListboxSelect>>', set_texture)
    dropdown2.bind('<<ListboxSelect>>', set_texture)
    rename_button.config(command=rename_texture)
    
    root.mainloop()

if __name__ == "__main__":
    global data
    data_file = 'tsorter.json'  # Replace with your JSON file path
    data = load_json_data(data_file)
    create_gui(data)
