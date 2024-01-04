import tkinter as tk
from tkinter import ttk
import tkinter.filedialog
from tkinter import messagebox
import os
from hashlib import md5
from pygments import highlight
import re
from pygments.formatters import get_formatter_by_name
class Notebook(ttk.Notebook):
    def __init__(self, *args):
        ttk.Notebook.__init__(self, *args)
        self.enable_traversal()
        self.pack(expand=1, fill="both")
        self.bind("<B1-Motion>", self.move_tab)

    # Get the object of the current tab.
    def current_tab(self):
        return self.nametowidget( self.select() )

    def indexed_tab(self, index):
        return self.nametowidget( self.tabs()[index] )

    # Move tab position by dragging tab
    def move_tab(self, event):
        '''
        Check if there is more than one tab.

        Use the y-coordinate of the current tab so that if the user moves the mouse up / down
        out of the range of the tabs, the left / right movement still moves the tab.
        '''
        if self.index("end") > 1:
            y = self.current_tab().winfo_y() - 5

            try:
                self.insert( min( event.widget.index('@%d,%d' % (event.x, y)), self.index('end')-2), self.select() )
            except tk.TclError:
                pass

class Tab(ttk.Frame):
    def __init__(self, *args, FileDir):
        ttk.Frame.__init__(self, *args)
        self.textbox = self.create_text_widget()
        self.file_dir = None
        self.file_name = os.path.basename(FileDir)
        self.status = md5(self.textbox.get(1.0, 'end').encode('utf-8'))
        
        # Button to toggle bold
        bold_button = ttk.Button(self, text="Bold", command=self.toggle_bold)
        bold_button.pack(side='left')

        # Combobox for font selection
        font_options = ['Courier New', 'Arial', 'Times New Roman']
        self.font_combobox = ttk.Combobox(self, values=font_options, state='readonly', width=15)
        self.font_combobox.set('Courier New')
        self.font_combobox.bind("<<ComboboxSelected>>", self.change_font)
        self.font_combobox.pack(side='left')

    def create_text_widget(self):
        # Horizontal Scroll Bar
        xscrollbar = tk.Scrollbar(self, orient='horizontal')
        xscrollbar.pack(side='bottom', fill='x')

        # Vertical Scroll Bar
        yscrollbar = tk.Scrollbar(self)
        yscrollbar.pack(side='right', fill='y')

        # Create Text Editor Box
        textbox = tk.Text(self, relief='sunken', borderwidth=0, wrap='none')
        textbox.config(xscrollcommand=xscrollbar.set, yscrollcommand=yscrollbar.set, undo=True, autoseparators=True)

        # Pack the textbox
        textbox.pack(fill='both', expand=True)

        # Configure Scrollbars
        xscrollbar.config(command=textbox.xview)
        yscrollbar.config(command=textbox.yview)

        return textbox

    def toggle_bold(self):
        try:
            # Get selected text indices
            start_index = self.textbox.index(tk.SEL_FIRST)
            end_index = self.textbox.index(tk.SEL_LAST)

            # Toggle bold tag
            current_tags = self.textbox.tag_names(start_index)
            if 'bold' in current_tags:
                self.textbox.tag_remove('bold', start_index, end_index)
            else:
                self.textbox.tag_add('bold', start_index, end_index)
                self.textbox.tag_configure('bold', font=(self.font_combobox.get(), 10, 'bold'))
        except tk.TclError:
            pass

    def change_font(self, event):
        try:
            # Get selected text indices
            start_index = self.textbox.index(tk.SEL_FIRST)
            end_index = self.textbox.index(tk.SEL_LAST)

            # Change font
            self.textbox.tag_add('font_change', start_index, end_index)
            self.textbox.tag_configure('font_change', font=(self.font_combobox.get(), 10, 'normal'))
        except tk.TclError:
            pass

class Editor:
    def __init__(self, master):
        self.master = master
        self.master.title("Notepad+=1")
        self.frame = tk.Frame(self.master)
        self.frame.pack()
        
        self.filetypes = (("Normal text file", "*.txt"), ("all files", "*.*"))
        self.init_dir = os.path.join(os.path.expanduser('~'), 'Desktop')
        self.untitled_count = 1
        
        # Create Notebook ( for tabs ).
        self.nb = Notebook(master)
        self.nb.bind("<Button-2>", self.close_tab)
        self.nb.bind('<<NotebookTabChanged>>', self.tab_change)
        self.nb.bind('<Button-3>', self.right_click_tab)

        # Override the X button.
        self.master.protocol('WM_DELETE_WINDOW', self.exit)
        
        # Create Menu Bar
        menubar = tk.Menu(self.master)
        
        # Create File Menu
        filemenu = tk.Menu(menubar, tearoff=0)
        filemenu.add_command(label="New", command=self.new_file)
        filemenu.add_command(label="Open", command=self.open_file)
        filemenu.add_command(label="Save", command=self.save_file)
        filemenu.add_command(label="Save As...", command=self.save_as)
        filemenu.add_command(label="Close", command=self.close_tab)
        filemenu.add_separator()
        filemenu.add_command(label="Exit", command=self.exit)
        
        # Create Edit Menu
        editmenu = tk.Menu(menubar, tearoff=0)
        editmenu.add_command(label="Undo", command=self.undo)
        editmenu.add_separator()
        editmenu.add_command(label="Cut", command=self.cut)
        editmenu.add_command(label="Copy", command=self.copy)
        editmenu.add_command(label="Paste", command=self.paste)
        editmenu.add_command(label="Delete", command=self.delete)
        editmenu.add_command(label="Select All", command=self.select_all)
        editmenu.add_separator()
        editmenu.add_command(label="Search and Replace", command=self.search_replace_dialog)
        # Create Format Menu, with a check button for word wrap.
        formatmenu = tk.Menu(menubar, tearoff=0)
        self.word_wrap = tk.BooleanVar()
        formatmenu.add_checkbutton(label="Word Wrap", onvalue=True, offvalue=False, variable=self.word_wrap, command=self.wrap)
        
        # Attach to Menu Bar
        menubar.add_cascade(label="File", menu=filemenu)
        menubar.add_cascade(label="Edit", menu=editmenu)
        menubar.add_cascade(label="Format", menu=formatmenu)
        self.master.config(menu=menubar)
        
        # Create right-click menu.
        self.right_click_menu = tk.Menu(self.master, tearoff=0)
        self.right_click_menu.add_command(label="Undo", command=self.undo)
        self.right_click_menu.add_separator()
        self.right_click_menu.add_command(label="Cut", command=self.cut)
        self.right_click_menu.add_command(label="Copy", command=self.copy)
        self.right_click_menu.add_command(label="Paste", command=self.paste)
        self.right_click_menu.add_command(label="Delete", command=self.delete)
        self.right_click_menu.add_separator()
        self.right_click_menu.add_command(label="Select All", command=self.select_all)
        
        # Create tab right-click menu
        self.tab_right_click_menu = tk.Menu(self.nb, tearoff=0)
        self.tab_right_click_menu.add_command(label="New Tab", command=self.new_file)

        # Keyboard / Click Bindings
        self.master.bind_class('Text', '<Control-s>', self.save_file)
        self.master.bind_class('Text', '<Control-o>', self.open_file)
        self.master.bind_class('Text', '<Control-n>', self.new_file)
        self.master.bind_class('Text', '<Control-a>', self.select_all)
        self.master.bind_class('Text', '<Control-w>', self.close_tab)
        self.master.bind_class('Text', '<Button-3>', self.right_click)
        
        # Create initial tab and 'Add' tab
        self.nb.add(Tab(FileDir='Untitled'), text='Untitled')
        self.nb.add(Tab(FileDir='f'), text=' + ')

    def open_file(self, *args):        
        # Open a window to browse to the file you would like to open, returns the directory.
        file_dir = (tkinter
         .filedialog
         .askopenfilename(initialdir=self.init_dir, title="Select file", filetypes=self.filetypes))
        
        # If directory is not the empty string, try to open the file. 
        if file_dir:
            try:
                # Open the file.
                file = open(file_dir)
                
                # Create a new tab and insert at end.
                new_tab = Tab(FileDir=file_dir)
                self.nb.insert( self.nb.index('end')-1, new_tab, text=os.path.basename(file_dir))
                self.nb.select( new_tab )
                            
                # Puts the contents of the file into the text widget.
                self.nb.current_tab().textbox.insert('end', file.read())
                
                # Update hash
                self.nb.current_tab().status = md5(self.nb.current_tab().textbox.get(1.0, 'end').encode('utf-8'))
            except:
                return

    def save_as(self):
        curr_tab = self.nb.current_tab()
    
        # Gets file directory and name of file to save.
        file_dir = (tkinter
         .filedialog
         .asksaveasfilename(initialdir=self.init_dir, title="Select file", filetypes=self.filetypes, defaultextension='.txt'))
        
        # Return if directory is still empty (user closes window without specifying file name).
        if not file_dir:
            return False
         
        # Adds .txt suffix if not already included.
        if file_dir[-4:] != '.txt':
            file_dir += '.txt'
            
        curr_tab.file_dir = file_dir
        curr_tab.file_name = os.path.basename(file_dir)
        self.nb.tab( curr_tab, text=curr_tab.file_name)
            
        # Writes text widget's contents to file.
        file = open(file_dir, 'w')
        file.write(curr_tab.textbox.get(1.0, 'end'))
        file.close()
        
        # Update hash
        curr_tab.status = md5(curr_tab.textbox.get(1.0, 'end').encode('utf-8'))
        
        return True
        
    def save_file(self, *args):
        curr_tab = self.nb.current_tab()
        
        # If file directory is empty or Untitled, use save_as to get save information from user. 
        if not curr_tab.file_dir:
            return self.save_as()

        # Otherwise save file to directory, overwriting existing file or creating a new one.
        else:
            with open(curr_tab.file_dir, 'w') as file:
                file.write(curr_tab.textbox.get(1.0, 'end'))
                
            # Update hash
            curr_tab.status = md5(curr_tab.textbox.get(1.0, 'end').encode('utf-8'))
            
            return True
                
    def new_file(self, *args):                
        # Create new tab
        new_tab = Tab(FileDir=self.default_filename())
        new_tab.textbox.config(wrap= 'word' if self.word_wrap.get() else 'none')
        self.nb.insert( self.nb.index('end')-1, new_tab, text=new_tab.file_name)
        self.nb.select( new_tab )
        
    def copy(self):
        # Clears the clipboard, copies selected contents.
        try: 
            sel = self.nb.current_tab().textbox.get(tk.SEL_FIRST, tk.SEL_LAST)
            self.master.clipboard_clear()
            self.master.clipboard_append(sel)
        # If no text is selected.
        except tk.TclError:
            pass
    def get_current_tab(self):
        """Get the currently selected tab."""
        current_tab_index = self.nb.index(self.nb.select())
        return self.nb.winfo_children()[current_tab_index]
            
    def delete(self):
        # Delete the selected text.
        try:
            self.nb.current_tab().textbox.delete(tk.SEL_FIRST, tk.SEL_LAST)
        # If no text is selected.
        except tk.TclError:
            pass
            
    def cut(self):
        # Copies selection to the clipboard, then deletes selection.
        try: 
            sel = self.nb.current_tab().textbox.get(tk.SEL_FIRST, tk.SEL_LAST)
            self.master.clipboard_clear()
            self.master.clipboard_append(sel)
            self.nb.current_tab().textbox.delete(tk.SEL_FIRST, tk.SEL_LAST)
        # If no text is selected.
        except tk.TclError:
            pass
    def search_replace_dialog(self):
        # Create a simple search and replace dialog
        dialog = tk.Toplevel(self.master)
        dialog.title("Search and Replace")

        # Labels and Entry widgets for search and replace strings
        tk.Label(dialog, text="Search:").grid(row=0, column=0, sticky="e")
        search_entry = tk.Entry(dialog)
        print(search_entry)
        search_entry.grid(row=0, column=1, padx=5, pady=5)

        tk.Label(dialog, text="Replace:").grid(row=1, column=0, sticky="e")
        replace_entry = tk.Entry(dialog)
        replace_entry.grid(row=1, column=1, padx=5, pady=5)

        # Buttons for performing search and replace
        search_button = ttk.Button(dialog, text="Search", command=lambda: self.search_text(search_entry.get()))
        search_button.grid(row=0, column=2, padx=5, pady=5)

        replace_button = ttk.Button(dialog, text="Replace", command=lambda: self.replace_text(search_entry.get(), replace_entry.get()))
        replace_button.grid(row=1, column=2, padx=5, pady=5)

    def search_text(self, search_str):
        curr_tab = self.nb.current_tab()
        content = curr_tab.textbox.get("1.0", "end-1c")
        curr_tab.textbox.tag_remove('search', '1.0', 'end')
       
        start_index = '1.0'
        while True:
            start_index = curr_tab.textbox.search(search_str, start_index, stopindex=tk.END)
            if not start_index:
                break

            end_index = curr_tab.textbox.index(f"{start_index}+{len(search_str)}c")

        # Apply the 'search' tag to highlight the match
            curr_tab.textbox.tag_add('search', start_index, end_index)

        # Move to the next character after the current match
            start_index = end_index
        curr_tab.textbox.tag_configure('search', background='yellow', foreground='black')

    def replace_text(self, search_str, replace_str):
        # Replace occurrences of search string with replace string in the current tab's text
        curr_tab = self.nb.current_tab()
        start_index = '1.0'

        # Use regular expression for case-insensitive search
        

        while True:
            start_index = curr_tab.textbox.search(search_str, start_index, stopindex=tk.END)
            print(start_index)
            if not start_index:
                break

            end_index = curr_tab.textbox.index(f"{start_index}+{len(search_str)}c")
            curr_tab.textbox.delete(start_index, end_index)
            curr_tab.textbox.insert(start_index, replace_str)
            start_index = end_index

    def wrap(self):
        if self.word_wrap.get() == True:
            for i in range(self.nb.index('end')-1):
                self.nb.indexed_tab(i).textbox.config(wrap="word")
        else:
            for i in range(self.nb.index('end')-1):
                self.nb.indexed_tab(i).textbox.config(wrap="none")
            
    def paste(self):
        try: 
            self.nb.current_tab().textbox.insert(tk.INSERT, self.master.clipboard_get())
        except tk.TclError:
            pass
            
    def select_all(self, *args):
        curr_tab = self.nb.current_tab()
        
        # Selects / highlights all the text.
        curr_tab.textbox.tag_add(tk.SEL, "1.0", tk.END)
        
        # Set mark position to the end and scroll to the end of selection.
        curr_tab.textbox.mark_set(tk.INSERT, tk.END)
        curr_tab.textbox.see(tk.INSERT)

    def undo(self):
        self.nb.current_tab().textbox.edit_undo()

    def right_click(self, event):
        self.right_click_menu.post(event.x_root, event.y_root)
        
    def right_click_tab(self, event):
        self.tab_right_click_menu.post(event.x_root, event.y_root)
        
    def close_tab(self, event=None):
        # Close the current tab if close is selected from file menu, or keyboard shortcut.
        if event is None or event.type == str( 2 ):
            selected_tab = self.nb.current_tab()
        # Otherwise close the tab based on coordinates of center-click.
        else:
            try:
                index = event.widget.index('@%d,%d' % (event.x, event.y))
                selected_tab = self.nb.indexed_tab( index )
                
                if index == self.nb.index('end')-1:
                    return False

            except tk.TclError:
                return False

        # Prompt to save changes before closing tab
        if self.save_changes(selected_tab):
            # if the tab next to '+' is selected, select the previous tab to prevent
            # automatically switching to '+' tab when current tab is closed
            if self.nb.index('current') > 0 and self.nb.select() == self.nb.tabs()[-2]:
                self.nb.select(self.nb.index('current')-1)
            self.nb.forget( selected_tab )
        else:
            return False

        # Exit if last tab is closed
        if self.nb.index("end") <= 1:
            self.master.destroy()
            
        return True
        
    def exit(self):        
        # Check if any changes have been made.
        for i in range(self.nb.index('end')-1):
            if self.close_tab() is False:
                break
               
    def save_changes(self, tab):
        # Check if any changes have been made, returns False if user chooses to cancel rather than select to save or not.
        if md5(tab.textbox.get(1.0, 'end').encode('utf-8')).digest() != tab.status.digest():
            # Select the tab being closed is not the current tab, select it.
            if self.nb.current_tab() != tab:
                self.nb.select(tab)
        
            m = messagebox.askyesnocancel('Editor', 'Do you want to save changes to ' + tab.file_name + '?' )
            
            # If None, cancel.
            if m is None:
                return False
            # else if True, save.
            elif m is True:
                return self.save_file()
            # else don't save.
            else:
                pass
                
        return True

    def default_filename(self):
        self.untitled_count += 1
        return 'Untitled' + str(self.untitled_count-1)

    def tab_change(self, event):
        # If last tab was selected, create new tab
        if self.nb.select() == self.nb.tabs()[-1]:
            self.new_file()


def main(): 
    root = tk.Tk()
    app = Editor(root)
    root.mainloop()

if __name__ == '__main__':
    main()
    