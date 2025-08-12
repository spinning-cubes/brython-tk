# Import Brython's browser-specific modules
from browser import document, html, window

# =======================================================
# tk_lib.py - This section contains the library classes.
# =======================================================

class Tk:
    """Represents the main window, styled with 7.css."""
    def __init__(self, title="tk"):
        self.main_window = document.select_one('#myWindow')
        self.title_bar_text = self.main_window.select_one('.title-bar-text')
        self.window_body = self.main_window.select_one('.window-body')

        self.title = title
        self.title_bar_text.text = self.title
        self.widgets = []
        
        # This is the fix for the AttributeError.
        # The Tk object's "element" is its body, which is where widgets are attached.
        self.element = self.window_body
        
    def add_widget(self, widget):
        """Adds a widget to the window body."""
        self.window_body.attach(widget.element)
        self.widgets.append(widget)

    def mainloop(self):
        # Brython handles the event loop, so this is just a placeholder
        pass
    
    def config(self, **kwargs):
        if 'menu' in kwargs:
            menu_bar = kwargs['menu']
            # Add the menubar as a regular widget to the window body
            self.add_widget(menu_bar)


class Toplevel:
    def __init__(self, parent, title="toplevel"):
        self.parent = parent
        self.title = title
        self.widgets = []

        self.element = html.DIV(Class="window active", style="position: absolute; top: 100px; left: 100px; min-width: 250px; min-height: 200px; display: flex; flex-direction: column;")
        
        self.title_bar = html.DIV(Class="title-bar")
        self.title_bar_text = html.DIV(title, Class="title-bar-text")
        self.title_bar_controls = html.DIV(Class="title-bar-controls")
        self.close_button = html.BUTTON(aria_label="Close")
        self.close_button.bind("click", self.destroy)

        self.title_bar_controls.attach(self.close_button)
        self.title_bar.attach(self.title_bar_text)
        self.title_bar.attach(self.title_bar_controls)
        
        # Use a consistent name for the container body
        self.body = html.DIV(Class="window-body has-space", style="flex-grow: 1;")
        
        self.element.attach(self.title_bar)
        self.element.attach(self.body)

        document.body.attach(self.element)

        # Dragging functionality
        self.is_dragging = False
        self.offset_x, self.offset_y = 0, 0
        self.title_bar.bind('mousedown', self.start_drag)
        self.parent_body = document.select_one('body')

    def start_drag(self, event):
        if event.target.tagName == 'BUTTON': return
        self.is_dragging = True
        self.element.classList.add('dragging')
        self.offset_x = event.clientX - self.element.offsetLeft
        self.offset_y = event.clientY - self.element.offsetTop
        self.parent_body.bind('mousemove', self.do_drag)
        self.parent_body.bind('mouseup', self.stop_drag)
        
    def do_drag(self, event):
        if self.is_dragging:
            self.element.style.left = f"{event.clientX - self.offset_x}px"
            self.element.style.top = f"{event.clientY - self.offset_y}px"

    def stop_drag(self, event):
        self.is_dragging = False
        self.element.classList.remove('dragging')
        self.parent_body.unbind('mousemove', self.do_drag)
        self.parent_body.unbind('mouseup', self.stop_drag)

    def add_widget(self, widget):
        self.body.attach(widget.element)
        self.widgets.append(widget)

    def destroy(self, event):
        self.element.remove()

class Widget:
    """Base class for all widgets."""
    def __init__(self, parent):
        self.parent = parent
        self.element = None
    
    def pack(self, **kwargs):
        # Determine the correct parent element to attach to.
        # Use the 'body' attribute for Toplevel and the 'element' for others.
        if isinstance(self.parent, Toplevel):
            parent_element = self.parent.body
        else:
            parent_element = self.parent.element
        
        # Corrected: Remove all layout-related styling from pack method
        parent_element.attach(self.element)

class Frame(Widget):
    """A container widget to group other widgets."""
    def __init__(self, parent, **kwargs):
        super().__init__(parent)
        self.element = html.DIV(**kwargs)

class Notebook(Widget):
    """A notebook widget for a tabbed interface, similar to Tkinter's."""
    def __init__(self, parent):
        super().__init__(parent)
        self.element = html.DIV(Class="tabs")
        self.menu = html.MENU(role="tablist")
        
        self.element.attach(self.menu)
        self.tabs = {}
        self.selected_tab = None

        self.menu.bind("click", self._on_tab_click)

    def add_tab(self, title):
        """Adds a new tab to the notebook and returns its corresponding panel (a Frame)."""
        tab_id = f"tab-{title.lower().replace(' ', '-')}"
        
        # Create the tab button
        is_first_tab = not self.tabs
        tab_button = html.BUTTON(
            title, 
            role="tab", 
            aria_controls=tab_id, 
            aria_selected=str(is_first_tab).lower()
        )
        self.menu.attach(tab_button)

        # Create the tab panel (a Frame) and add it as a sibling to the menu
        tab_panel_frame = Frame(self)
        tab_panel_frame.element = html.ARTICLE(role="tabpanel")
        tab_panel_frame.element.id = tab_id
        if not is_first_tab:
            tab_panel_frame.element.hidden = True

        self.element.attach(tab_panel_frame.element)
        self.tabs[tab_id] = {'button': tab_button, 'panel': tab_panel_frame}

        if is_first_tab:
            self.selected_tab = tab_id

        return tab_panel_frame

    def _on_tab_click(self, event):
        """Handles the click event for tab buttons."""
        clicked_button = event.target
        if clicked_button.tagName == "BUTTON":
            tab_id = clicked_button.getAttribute("aria-controls")
            self._select_tab(tab_id)

    def _select_tab(self, tab_id):
        """Switches the active tab."""
        if self.selected_tab:
            self.tabs[self.selected_tab]['button'].setAttribute('aria-selected', 'false')
            self.tabs[self.selected_tab]['panel'].element.hidden = True

        self.tabs[tab_id]['button'].setAttribute('aria-selected', 'true')
        self.tabs[tab_id]['panel'].element.hidden = False
        self.selected_tab = tab_id


class Label(Widget):
    """A simple label widget."""
    def __init__(self, parent, text, **kwargs):
        super().__init__(parent)
        self.text = text
        self.element = html.P(self.text, **kwargs)

    def config(self, **kwargs):
        """Updates the label's properties."""
        if 'text' in kwargs:
            self.element.text = kwargs['text']

class Button(Widget):
    """A simple button widget."""
    def __init__(self, parent, text, command, **kwargs):
        super().__init__(parent)
        self.element = html.BUTTON(text, **kwargs)
        self.element.bind("click", command)

class Entry(Widget):
    """A simple entry widget (text input)."""
    def __init__(self, parent, **kwargs):
        super().__init__(parent)
        self.element = html.INPUT(type="text", **kwargs)

    def get(self):
        """Returns the current text in the entry box."""
        return self.element.value
    
class Checkbutton(Widget):
    """A checkbutton widget."""
    def __init__(self, parent, text, variable, command=None, **kwargs):
        super().__init__(parent)
        
        self.element = html.DIV()
        self.variable = variable
        self.command = command

        self.input_element = html.INPUT(
            type="checkbox", 
            id=f"{self.variable.name}-{text.replace(' ', '-')}",
            **kwargs
        )
        self.label_element = html.LABEL(text, **{'for': f"{self.variable.name}-{text.replace(' ', '-')}"})

        self.element.attach(self.input_element)
        self.element.attach(self.label_element)
        
        self.input_element.bind("change", self.update_variable)
        self.input_element.checked = self.variable.get()
    
    def update_variable(self, event):
        self.variable.set(self.input_element.checked)
        if self.command:
            self.command(event)

class Radiobutton(Widget):
    """A radiobutton widget."""
    def __init__(self, parent, text, variable, value, command=None, **kwargs):
        super().__init__(parent)
        self.element = html.DIV()
        
        self.variable = variable
        self.command = command

        self.input_element = html.INPUT(
            type="radio",
            name=variable.name,
            value=value,
            id=f"{variable.name}-{value}",
            **kwargs
        )
        self.label_element = html.LABEL(text, **{'for': f"{variable.name}-{value}"})

        self.element.attach(self.input_element)
        self.element.attach(self.label_element)
        
        self.input_element.bind("change", self.update_variable)
        if self.variable.get() == value:
            self.input_element.checked = True

    def update_variable(self, event):
        self.variable.set(self.input_element.value)
        if self.command:
            self.command(event)

class Text(Widget):
    """A multi-line text input widget."""
    def __init__(self, parent, **kwargs):
        super().__init__(parent)
        self.element = html.TEXTAREA(**kwargs)
    
    def get(self):
        return self.element.value

    def insert(self, text):
        self.element.value += text

class Listbox(Widget):
    """A listbox widget for displaying a list of options."""
    def __init__(self, parent, multiple=False, **kwargs):
        super().__init__(parent)
        if multiple:
            kwargs['multiple'] = True
        self.element = html.SELECT(**kwargs)

    def insert(self, index, item):
        self.element.append(html.OPTION(item))
    
    def get(self):
        if self.element.multiple:
            return [option.text for option in self.element.options if option.selected]
        else:
            selected_option = self.element.options[self.element.selectedIndex]
            return selected_option.text if selected_option else None

class Select(Widget):
    """A dropdown menu widget."""
    def __init__(self, parent, options, variable, command=None, **kwargs):
        super().__init__(parent)
        self.variable = variable
        self.command = command
        
        self.element = html.SELECT(**kwargs)
        for option in options:
            self.element.append(html.OPTION(option, value=option))

        self.element.bind("change", self._on_select_change)
        
        # Set initial value if provided
        self.variable.set(self.element.value)

    def _on_select_change(self, event):
        self.variable.set(self.element.value)
        if self.command:
            self.command(event)

    def get(self):
        return self.element.value

class Canvas(Widget):
    """A canvas widget for drawing shapes."""
    def __init__(self, parent, width, height, **kwargs):
        super().__init__(parent)
        self.element = html.CANVAS(width=width, height=height, **kwargs)
        self.ctx = self.element.getContext("2d")
        self.width = width
        self.height = height

    def create_rectangle(self, x1, y1, x2, y2, fill="black", outline="black"):
        self.ctx.fillStyle = fill
        self.ctx.strokeStyle = outline
        self.ctx.fillRect(x1, y1, x2-x1, y2-y1)
        self.ctx.strokeRect(x1, y1, x2-x1, y2-y1)

    def create_oval(self, x1, y1, x2, y2, fill="black", outline="black"):
        self.ctx.fillStyle = fill
        self.ctx.strokeStyle = outline
        self.ctx.beginPath()
        # The HTML canvas arcTo function is a bit different, so we'll approximate with ellipse
        # or calculate the control points for a bezier curve.
        # This is a simplified version using arc to draw a circle for now
        self.ctx.ellipse((x1 + x2) / 2, (y1 + y2) / 2, (x2-x1)/2, (y2-y1)/2, 0, 0, 2 * window.Math.PI)
        self.ctx.fill()
        self.ctx.stroke()

    def create_line(self, *coords, fill="black", width=1):
        self.ctx.strokeStyle = fill
        self.ctx.lineWidth = width
        self.ctx.beginPath()
        self.ctx.moveTo(coords[0], coords[1])
        for i in range(2, len(coords), 2):
            self.ctx.lineTo(coords[i], coords[i+1])
        self.ctx.stroke()

class Scale(Widget):
    """A scale widget (slider)."""
    def __init__(self, parent, from_, to, variable=None, command=None, **kwargs):
        super().__init__(parent)
        self.element = html.INPUT(
            type="range",
            min=from_,
            max=to,
            **kwargs
        )
        self.variable = variable
        if self.variable:
            self.element.value = self.variable.get()
            self.element.bind("input", self._update_variable)
        
        if command:
            self.command = command
            self.element.bind("input", self.command)

    def _update_variable(self, event):
        if self.variable:
            self.variable.set(self.element.value)
    
    def get(self):
        return int(self.element.value)

class Menubar:
    def __init__(self, parent):
        self.parent = parent
        self.element = html.UL(role="menubar", Class="can-hover")
    
    def add_menu(self, label, menu_obj):
        menu_item = html.LI(role="menuitem", tabindex="0", aria_haspopup="true")
        menu_item.attach(html.SPAN(label))
        menu_item.attach(menu_obj.element)
        self.element.attach(menu_item)

class Menu:
    def __init__(self, parent):
        self.parent = parent
        self.element = html.UL(role="menu")
    
    def add_command(self, label, command=None, accelerator=None, **kwargs):
        item = html.LI(role="menuitem")
        
        link = html.A(href="#")
        link.attach(label)
        if accelerator:
            link.attach(html.SPAN(accelerator))

        if command:
            link.bind("click", lambda event: (event.preventDefault(), command()))

        item.attach(link)
        self.element.attach(item)
    
    def add_separator(self):
        item = html.LI(Class="has-divider")
        self.element.attach(item)

    def add_cascade(self, label, menu_obj):
        item = html.LI(role="menuitem", tabindex="0", aria_haspopup="true")
        item.attach(html.SPAN(label))
        item.attach(menu_obj.element)
        self.element.attach(item)

class StringVar:
    """A variable class to hold and track strings."""
    def __init__(self, initial_value=""):
        self._value = initial_value
        self.name = f"var_{id(self)}"

    def get(self):
        return self._value

    def set(self, value):
        self._value = value

class IntVar:
    """A variable class to hold and track integers."""
    def __init__(self, initial_value=0):
        self._value = initial_value
        self.name = f"var_{id(self)}"

    def get(self):
        return self._value

    def set(self, value):
        self._value = int(value)

class BooleanVar:
    """A variable class to hold and track booleans."""
    def __init__(self, initial_value=False):
        self._value = initial_value
        self.name = f"var_{id(self)}"

    def get(self):
        return self._value

    def set(self, value):
        self._value = bool(value)
    
# =======================================================
# main.py - This section contains the main application code.
# =======================================================

# Create the main window
root = Tk("Dynamic Widgets App")


# This function definition has been moved here to fix the NameError.
def create_new_window():
    new_window = Toplevel(root, title="New Window")
    new_label = Label(new_window, "This is a new Toplevel window!")
    new_label.pack()
    new_label2 = Label(new_window, "It can be dragged!")
    new_label2.pack()


# Create a menu bar
menubar = Menubar(root)

# Create File menu
file_menu = Menu(menubar)
file_menu.add_command(label="New Window", command=lambda: create_new_window())
file_menu.add_separator()
file_menu.add_command(label="Exit", command=lambda: window.close())
menubar.add_menu("File", file_menu)

# Create Edit menu
edit_menu = Menu(menubar)
edit_menu.add_command(label="Undo")
edit_menu.add_command(label="Copy")
edit_menu.add_command(label="Cut")
edit_menu.add_separator()
edit_menu.add_command(label="Paste")
edit_menu.add_command(label="Delete")
edit_menu.add_command(label="Find...")
edit_menu.add_command(label="Replace...")
edit_menu.add_command(label="Go to...")
menubar.add_menu("Edit", edit_menu)

# Create View menu
view_menu = Menu(menubar)
zoom_menu = Menu(view_menu)
zoom_menu.add_command(label="Zoom In", command=lambda: print("Zoom In"))
zoom_menu.add_command(label="Zoom Out", command=lambda: print("Zoom Out"))
view_menu.add_cascade(label="Zoom", menu_obj=zoom_menu)
view_menu.add_command(label="Status Bar")
menubar.add_menu("View", view_menu)

# Create Help menu
help_menu = Menu(menubar)
help_menu.add_command(label="View Help")
help_menu.add_command(label="About")
menubar.add_menu("Help", help_menu)

root.config(menu=menubar)

# Create a notebook widget and add it to the main window
notebook = Notebook(root)
notebook.pack(expand=True, side="top")

# Create tabs within the notebook
greetings_tab = notebook.add_tab("Greetings")
widgets_tab = notebook.add_tab("Widgets")
new_widgets_tab = notebook.add_tab("New Widgets")
canvas_tab = notebook.add_tab("Canvas")
toplevel_tab = notebook.add_tab("Toplevel")
scale_tab = notebook.add_tab("Scale")

# --- Widgets for the Greetings Tab ---
greeting_label = Label(greetings_tab, "Hello! Please enter your name below.")
greeting_label.pack()

name_entry = Entry(greetings_tab)
name_entry.pack()

def update_greeting(event):
    """Function to be called when the button is clicked."""
    name = name_entry.get()
    if name:
        greeting_label.config(text=f"Hello, {name}!")
    else:
        greeting_label.config(text="Hello there!")

greet_button = Button(greetings_tab, "Greet", update_greeting)
greet_button.pack()

# --- Widgets for the "Widgets" Tab ---
header_label = Label(widgets_tab, text="Select your options:")
header_label.pack()

checkbox_frame = Frame(widgets_tab)
checkbox_frame.pack()

checkbox_var1 = BooleanVar(initial_value=False)
def on_checkbox1_toggle(event):
    print(f"Checkbox 1 state: {checkbox_var1.get()}")

checkbox1 = Checkbutton(checkbox_frame, text="Enable Feature X", variable=checkbox_var1, command=on_checkbox1_toggle)
checkbox1.pack()

checkbox_var2 = BooleanVar(initial_value=False)
def on_checkbox2_toggle(event):
    print(f"Checkbox 2 state: {checkbox_var2.get()}")

checkbox2 = Checkbutton(checkbox_frame, text="Enable Feature Y", variable=checkbox_var2, command=on_checkbox2_toggle)
checkbox2.pack()

radio_frame = Frame(widgets_tab)
radio_frame.pack()

radio_var = StringVar(initial_value="Option A")
def on_radio_select(event):
    print(f"Selected option: {radio_var.get()}")

radio1 = Radiobutton(radio_frame, text="Option A", variable=radio_var, value="Option A", command=on_radio_select)
radio2 = Radiobutton(radio_frame, text="Option B", variable=radio_var, value="Option B", command=on_radio_select)
radio3 = Radiobutton(radio_frame, text="Option C", variable=radio_var, value="Option C", command=on_radio_select)

radio1.pack()
radio2.pack()
radio3.pack()

# --- Widgets for the "New Widgets" Tab ---
new_widgets_label = Label(new_widgets_tab, "These are some new widgets:")
new_widgets_label.pack()

text_widget = Text(new_widgets_tab, placeholder="Type something here...")
text_widget.pack()

def insert_text(event):
    text_widget.insert("Hello from the button!\n")

insert_button = Button(new_widgets_tab, "Insert Text", insert_text)
insert_button.pack()

listbox_label = Label(new_widgets_tab, "Select an item:")
listbox_label.pack()

listbox = Listbox(new_widgets_tab)
listbox.insert(0, "Apple")
listbox.insert(1, "Banana")
listbox.insert(2, "Cherry")
listbox.pack()

# Dropdown example
dropdown_label = Label(new_widgets_tab, "Rate your experience:")
dropdown_label.pack()

dropdown_options = ["5 - Incredible!", "4 - Great!", "3 - Pretty good", "2 - Not so great", "1 - Unfortunate"]
dropdown_var = StringVar(initial_value=dropdown_options[0])

def on_dropdown_select(event):
    print(f"Selected rating: {dropdown_var.get()}")

dropdown = Select(new_widgets_tab, dropdown_options, dropdown_var, command=on_dropdown_select)
dropdown.pack()

# Multi-select listbox example
multi_listbox_label = Label(new_widgets_tab, "Select multiple fruits:")
multi_listbox_label.pack()

multi_listbox = Listbox(new_widgets_tab, multiple=True)
multi_listbox.insert(0, "Apple")
multi_listbox.insert(1, "Banana")
multi_listbox.insert(2, "Cherry")
multi_listbox.insert(3, "Orange")
multi_listbox.insert(4, "Grape")
multi_listbox.pack()

def show_selected_items(event):
    selected_items = multi_listbox.get()
    print(f"Selected items: {selected_items}")

show_selected_button = Button(new_widgets_tab, "Show Selected", show_selected_items)
show_selected_button.pack()

# --- Widgets for the "Canvas" Tab ---
canvas_label = Label(canvas_tab, "A simple drawing canvas:")
canvas_label.pack()

drawing_canvas = Canvas(canvas_tab, width=300, height=150, style="border:1px solid black;")
drawing_canvas.pack()

# Draw some shapes
drawing_canvas.create_rectangle(10, 10, 60, 60, fill="blue", outline="red")
drawing_canvas.create_oval(70, 10, 120, 60, fill="green", outline="black")
drawing_canvas.create_line(130, 10, 180, 60, 130, 60, fill="purple", width=3)


# --- Widgets for the "Toplevel" Tab ---
toplevel_label = Label(toplevel_tab, "Click the button below to open a new window:")
toplevel_label.pack()

open_window_button = Button(toplevel_tab, "Open New Window", lambda event: create_new_window())
open_window_button.pack()

# --- Widgets for the "Scale" Tab ---
scale_label = Label(scale_tab, "Scale Value: 50")
scale_label.pack()

scale_var = IntVar(initial_value=50)

def on_scale_change(event):
    scale_label.config(text=f"Scale Value: {scale_var.get()}")

my_scale = Scale(scale_tab, from_=0, to=100, variable=scale_var, command=on_scale_change)
my_scale.pack()

# Main loop
root.mainloop()
