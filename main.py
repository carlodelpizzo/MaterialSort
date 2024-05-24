import os.path
import shutil
import tkinter as tk
from tkinter import (NORMAL, DISABLED, END, Checkbutton, IntVar,
                     Menu, Toplevel, Listbox, filedialog)
from tkinterdnd2 import DND_FILES, TkinterDnD


def list_all_sub_directories(directory: str, include_root_dir=False):
    subs = [path for dir_name in os.listdir(directory) if os.path.isdir(path := ''.join([directory, '/', dir_name]))]
    for sub_sub in [list_all_sub_directories(sub_dir) for sub_dir in [*subs]]:
        subs.extend(sub_sub)
    return [directory, *sorted(subs)] if include_root_dir else sorted(subs)  # I don't remember why I used sort here


class MaterialSort:
    def __init__(self):
        self.source = ''
        self.destination = ''
        self.files = []
        self.materials = ['A12', 'A14', 'C11', 'C14', 'C16', 'C18', 'S18']
        self.edit_window = None

        self.root = TkinterDnD.Tk()
        self.root.geometry(f'{(app_width := 325)}x{(app_height := 287)}')
        self.root.resizable(False, False)
        self.root.title('Material Sort')

        self.source_entry = tk.Entry(self.root, width=50, takefocus=0)
        self.source_entry.place(x=app_width / 2, y=17, anchor='n')
        self.source_entry.insert(0, 'Drop Source Folder Here')
        self.source_entry.config(justify='center')
        self.source_entry['state'] = DISABLED
        self.source_entry.drop_target_register(DND_FILES)
        self.source_entry.dnd_bind('<<Drop>>', lambda e: self.drop_func('s', e))

        self.browse_button_s = tk.Button(self.root, text='Source Folder', width=11,
                                         command=lambda: self.browse('s'))
        self.browse_button_s.place(x=app_width / 2, y=42, anchor='n')

        self.destination_entry = tk.Entry(self.root, width=50, takefocus=0)
        self.destination_entry.place(x=app_width / 2, y=107, anchor='n')
        self.destination_entry.insert(0, 'Drop Destination Folder Here')
        self.destination_entry.config(justify='center')
        self.destination_entry['state'] = DISABLED
        self.destination_entry.drop_target_register(DND_FILES)
        self.destination_entry.dnd_bind('<<Drop>>', lambda e: self.drop_func('d', e))

        self.browse_button_d = tk.Button(self.root, text='Destination Folder', width=14,
                                         command=lambda: self.browse('d'))
        self.browse_button_d.place(x=app_width / 2, y=132, anchor='n')

        self.overwrite_files = IntVar(value=0)
        self.overwrite_files_check = Checkbutton(self.root, text='overwrite existing files',
                                                 variable=self.overwrite_files, takefocus=0)
        self.overwrite_files_check.place(x=15, y=195, anchor='nw')

        self.start_button = tk.Button(self.root, text='Start', width=10, command=self.material_sort)
        self.start_button.place(x=325 / 2, y=260, anchor='s')

        self.menu = Menu(self.root)
        self.file = Menu(self.menu, tearoff=0)
        self.file.add_command(label='Edit Materials', command=self.edit_materials)
        self.menu.add_cascade(label='File', menu=self.file)
        self.root.config(menu=self.menu)

        # Main Loop
        self.root.mainloop()

    class EditWindow:
        def __init__(self, main):
            self.main = main
            self.window = Toplevel(self.main.root)
            self.window.focus()
            self.window.protocol('WM_DELETE_WINDOW', self.main.close_edit_window)
            self.window.title('Edit Materials')
            self.window.geometry('250x250')
            self.window.geometry(f'+{self.main.root.winfo_rootx()}+{self.main.root.winfo_rooty()}')
            self.window.resizable(False, False)

            self.listbox = Listbox(self.window)
            self.listbox.place(x=10, y=10)

            self.materials = [*main.materials]

            for i, material in enumerate(self.materials):
                self.listbox.insert(i+1, material)

    def edit_materials(self):
        if self.edit_window:
            self.edit_window.window.deiconify()
            self.edit_window.window.focus()
            return
        self.edit_window = self.EditWindow(self)

    def close_edit_window(self):
        if self.edit_window is None:
            return
        self.edit_window.window.destroy()
        del self.edit_window
        self.edit_window = None

    def drop_func(self, caller, event):
        event_data = event.data
        brkt_i = [i for i in range(len(event_data)) if event_data[i] in ['{', '}']]
        items = [event_data[brkt_i[ii - 1] + 1:i] for ii, i in enumerate(brkt_i) if ii % 2]
        for item in items:
            if os.path.isdir(item):
                if caller == 's':
                    self.set_source(item)
                elif caller == 'd':
                    self.set_destination(item)
                return

    def browse(self, caller):
        if caller == 's':
            self.set_source(filedialog.askdirectory())
        elif caller == 'd':
            self.set_destination(filedialog.askdirectory())

    def set_source(self, path):
        if os.path.isdir(path):
            self.source = path
            self.source_entry['state'] = NORMAL
            self.source_entry.delete(0, END)
            self.source_entry.insert(0, path)
            self.source_entry['state'] = DISABLED

    def set_destination(self, path):
        if os.path.isdir(path):
            self.destination = path
            self.destination_entry['state'] = NORMAL
            self.destination_entry.delete(0, END)
            self.destination_entry.insert(0, path)
            self.destination_entry['state'] = DISABLED

    def material_sort(self):
        if not self.source and not self.destination:
            return
        files = []
        sorted_files = {material: [] for material in self.materials}
        for directory in list_all_sub_directories(self.source):
            for item in os.listdir(directory):
                if os.path.isfile(path := f'{directory}/{item}'):
                    files.append((path, item))
        for file in files:
            if 'PVLIB' in file[1]:
                continue
            for material in self.materials:
                if material in file[1]:
                    sorted_files[material].append(file)
                    break
        for material in self.materials:
            if not sorted_files[material]:
                continue
            if not os.path.isdir(path := f'{self.destination}/{material}'):
                os.mkdir(path)
            for file in sorted_files[material]:
                if not self.overwrite_files.get() and os.path.isfile(f'{path}/{file[1]}'):
                    continue
                shutil.copyfile(file[0], f'{path}/{file[1]}')


if __name__ == '__main__':
    MaterialSort()
