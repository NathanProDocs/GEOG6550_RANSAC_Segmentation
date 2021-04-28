import json, os, platform, sys, io
from os import path
from pathlib import Path
from sys import platform as _platform
import tkinter as tk
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText
from tkinter import filedialog
from tkinter import messagebox
from tkinter import PhotoImage
from subprocess import CalledProcessError, Popen, PIPE, STDOUT

class FileSelector(tk.Frame):
    def __init__(self, json_str, runner, master=None, tooltip_label=None):
        self.tooltip_label = tooltip_label

        # first make sure that the json data has the correct fields
        j = json.loads(json_str)
        self.name = j['name']
        self.description = j['description']
        self.flag = j['flags'][len(j['flags']) - 1]
        self.parameter_type = j['parameter_type']
        self.file_type = ""
        if "ExistingFile" in self.parameter_type:
            self.file_type = j['parameter_type']['ExistingFile']
        elif "NewFile" in self.parameter_type:
            self.file_type = j['parameter_type']['NewFile']
        self.optional = j['optional']
        default_value = j['default_value']

        self.runner = runner

        ttk.Frame.__init__(self, master, padding='0.02i')
        self.grid()

        self.bind("<Enter>", self.onEnter)
        self.bind("<Leave>", self.onLeave)

        self.label = ttk.Label(self, text=self.name, justify=tk.LEFT)
        self.label.grid(row=0, column=0, sticky=tk.W)
        self.label.columnconfigure(0, weight=1)

        if not self.optional:
            self.label['text'] = self.label['text'] + "*"

        fs_frame = ttk.Frame(self, padding='0.0i')
        self.value = tk.StringVar()
        self.entry = ttk.Entry(
            fs_frame, width=45, justify=tk.LEFT, textvariable=self.value)
        self.entry.grid(row=0, column=0, sticky=tk.NSEW)
        self.entry.columnconfigure(0, weight=1)
        if default_value:
            self.value.set(default_value)

        # self.open_button = ttk.Button(fs_frame, width=4, image = self.open_file_icon, command=self.select_file, padding = '0.02i')
        self.open_button = ttk.Button(fs_frame, width=4, text="...", command=self.select_file, padding = '0.02i')
        self.open_button.grid(row=0, column=1, sticky=tk.E)
        self.open_button.columnconfigure(0, weight=1)

        fs_frame.grid(row=1, column=0, sticky=tk.NSEW)
        fs_frame.columnconfigure(0, weight=10)
        fs_frame.columnconfigure(1, weight=1)
        # self.pack(fill=tk.BOTH, expand=1)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        # Add the bindings
        if _platform == "darwin":
            self.entry.bind("<Command-Key-a>", self.select_all)
        else:
            self.entry.bind("<Control-Key-a>", self.select_all)
        
    def onEnter(self, event=None):
        self.tooltip_label.configure(text=self.description)
        # self.update()  # this is needed for cancelling and updating the progress bar

    def onLeave(self, event=None):
        self.tooltip_label.configure(text="")
        # self.update()  # this is needed for cancelling and updating the progress bar

    def select_file(self):
        try:
            result = self.value.get()
            if self.parameter_type == "Directory":
                result = filedialog.askdirectory()
                
            elif "ExistingFile" in self.parameter_type:
                ftypes = [('All files', '*.*')]
                if 'Lidar' in self.file_type:
                    ftypes = [("LiDAR files", ('*.las', '*.zip'))]

                result = filedialog.askopenfilename(initialdir=self.runner.working_dir, title="Select file", filetypes=ftypes)
                
            elif "NewFile" in self.parameter_type:
                result = filedialog.asksaveasfilename()
                
            self.value.set(result)
            # update the working directory
            self.runner.working_dir = os.path.dirname(result)
            # print(self.runner.working_dir)

        except:
            t = "file"
            if self.parameter_type == "Directory":
                t = "directory"
            messagebox.showinfo("Warning", "Could not find {}".format(t))

    def get_value(self):
        if self.value.get():
            v = self.value.get()
            # Do some quality assurance here.
            # Is there a directory included?
            if not path.dirname(v):
                v = path.join(self.runner.working_dir, v)

            # What about a file extension?
            ext = os.path.splitext(v)[-1].lower().strip()
            if not ext:
                ext = ""
                if 'Lidar' in self.file_type:
                    ext = '.las'
                v += ext
            v = path.normpath(v)

            return "{}='{}'".format(self.flag, v)
        else:
            t = "file"
            if self.parameter_type == "Directory":
                t = "directory"
            if not self.optional:
                messagebox.showinfo(
                    "Error", "Unspecified {} parameter {}.".format(t, self.flag))
        return None

    def select_all(self, event):
        self.entry.select_range(0, tk.END)
        return 'break'

class DataInput(tk.Frame):
    def __init__(self, json_str, master=None, tooltip_label=None):
        self.tooltip_label = tooltip_label

        # first make sure that the json data has the correct fields
        j = json.loads(json_str)
        self.name = j['name']
        self.description = j['description']
        self.flag = j['flags'][len(j['flags']) - 1]
        self.parameter_type = j['parameter_type']
        self.optional = j['optional']
        default_value = j['default_value']

        ttk.Frame.__init__(self, master)
        self.grid()
        self['padding'] = '0.1i'

        self.bind("<Enter>", self.onEnter)
        self.bind("<Leave>", self.onLeave)

        self.label = ttk.Label(self, text=self.name, justify=tk.LEFT)
        self.label.grid(row=0, column=0, sticky=tk.W)
        self.label.columnconfigure(0, weight=1)

        self.value = tk.StringVar()
        if default_value:
            self.value.set(default_value)
        else:
            self.value.set("")

        self.entry = ttk.Entry(self, justify=tk.LEFT, textvariable=self.value)
        self.entry.grid(row=0, column=1, sticky=tk.NSEW)
        self.entry.columnconfigure(1, weight=10)

        if not self.optional:
            self.label['text'] = self.label['text'] + "*"

        if ("Integer" in self.parameter_type or
            "Float" in self.parameter_type or
                "Double" in self.parameter_type):
            self.entry['justify'] = 'right'

        # Add the bindings
        if _platform == "darwin":
            self.entry.bind("<Command-Key-a>", self.select_all)
        else:
            self.entry.bind("<Control-Key-a>", self.select_all)

        # self.pack(fill=tk.BOTH, expand=1)
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=10)
        self.rowconfigure(0, weight=1)

    def onEnter(self, event=None):
        self.tooltip_label.configure(text=self.description)
        # self.update()  # this is needed for cancelling and updating the progress bar

    def onLeave(self, event=None):
        self.tooltip_label.configure(text="")
        self.update()  # this is needed for cancelling and updating the progress bar

    def RepresentsInt(self, s):
        try:
            int(s)
            return True
        except ValueError:
            return False

    def RepresentsFloat(self, s):
        try:
            float(s)
            return True
        except ValueError:
            return False

    def get_value(self):
        v = self.value.get()
        if v:
            if "Integer" in self.parameter_type:
                if self.RepresentsInt(self.value.get()):
                    return "{}={}".format(self.flag, self.value.get())
                else:
                    messagebox.showinfo(
                        "Error", "Error converting parameter {} to type Integer.".format(self.flag))
            elif "Float" in self.parameter_type:
                if self.RepresentsFloat(self.value.get()):
                    return "{}={}".format(self.flag, self.value.get())
                else:
                    messagebox.showinfo(
                        "Error", "Error converting parameter {} to type Float.".format(self.flag))
            elif "Double" in self.parameter_type:
                if self.RepresentsFloat(self.value.get()):
                    return "{}={}".format(self.flag, self.value.get())
                else:
                    messagebox.showinfo(
                        "Error", "Error converting parameter {} to type Double.".format(self.flag))
            else:  # String or StringOrNumber types
                return "{}='{}'".format(self.flag, self.value.get())
        else:
            if not self.optional:
                messagebox.showinfo(
                    "Error", "Unspecified non-optional parameter {}.".format(self.flag))
        return None

    def select_all(self, event):
        self.entry.select_range(0, tk.END)
        return 'break'

class Gui(tk.Frame):
    def __init__(self, tool_name=None, master=None):
        if platform.system() == 'Windows':
            self.ext = '.exe'
        else:
            self.ext = ''
        self.exe_name = "./Ransac_seg{}".format(self.ext) 

        self.exe_path = path.dirname(path.abspath(__file__))

        self.cancel_op = False

        ttk.Frame.__init__(self, master)
        self.script_dir = os.path.dirname(os.path.realpath(__file__))
        self.grid()
        self.tool_name = tool_name
        self.master.title("RANSAC PLANE SEGMENTATION")
        # if _platform == "darwin":
        #     os.system(
        #         '''/usr/bin/osascript -e 'tell app "Finder" to set frontmost of process "Python" to true' ''')
        
        #########################################################
        #              Overall/Top level Frame                  #
        #########################################################     
        #define left-side frame (toplevel_frame) and right-side frame (overall_frame)
        # toplevel_frame = ttk.Frame(self, padding='0.1i')
        overall_frame = ttk.Frame(self, padding='0.1i')
        #set-up layout
        overall_frame.grid(row=0, column=0, sticky=tk.NSEW)
        # toplevel_frame.grid(row=0, column=0, sticky=tk.NSEW) 

        ##################
        # Tool tip label #
        ##################
        tooltip_frame = ttk.Frame(overall_frame, padding='0.1i')
        self.tt_label = ttk.Label(tooltip_frame, text="")
        style = ttk.Style()
        style.configure("Blue.Label", foreground="dark blue")
        self.tt_label.configure(style="Blue.Label")
        self.tt_label.grid(row=0, column=0, sticky=tk.W)
        tooltip_frame.grid(row=4, column=0, columnspan=2, sticky=tk.NSEW)
        
        # Add GUI elements
        self.elements_frame = ttk.Frame(overall_frame, padding='0.1i')

        # input file:
        param_num = 0
        # input file:
        param_str = '{ "name":"Input File (*.las)",  "description": "Name of the input points .las file.", "flags": ["-i", "--lidarFile"], "parameter_type": {"ExistingFile":"Lidar"}, "optional": "False", "default_value": null}'
        fs1 = FileSelector(param_str, self, self.elements_frame, self.tt_label)
        fs1.grid(row=param_num, column=0, sticky=tk.NSEW)
        param_num += 1 

        # Outputfile:
        param_str = '{ "name":"Output File",  "description": "Name of the output points .las file.", "flags": ["-o", "--outputFile"], "parameter_type": {"NewFile":"Lidar"}, "optional": "False", "default_value": null}'
        fs2 = FileSelector(param_str, self, self.elements_frame, self.tt_label)
        fs2.grid(row=param_num, column=0, sticky=tk.NSEW)
        param_num += 1

        # Search Distance:
        param_str = '{ "name":"Search Distance (m)",  "description": "Point neighbourhood Search Distance.", "flags": ["--searchDist"], "parameter_type": "Float", "optional": "False", "default_value": "1.50"}'
        di3 = DataInput(param_str, self.elements_frame, self.tt_label)
        di3.grid(row=param_num, column=0, sticky=tk.NSEW)
        param_num += 1 

        # Iterations: 
        param_str = '{ "name":"Number of Iterations",  "description": "How many times would you like to iterate (Default: 50).", "flags": ["--iterations"], "parameter_type": "Integer", "optional": "False", "default_value": "50"}'
        di4 = DataInput(param_str, self.elements_frame, self.tt_label)
        di4.grid(row=param_num, column=0, sticky=tk.NSEW)
        param_num += 1 

        # Threshold Residuals:
        param_str = '{ "name":"Residual Threshold Value",  "description": "Minimum Threshold (Default: 0.15).", "flags": ["--threshold"], "parameter_type": "Float", "optional": "False", "default_value": "0.15"}'
        di5 = DataInput(param_str, self.elements_frame, self.tt_label)
        di5.grid(row=param_num, column=0, sticky=tk.NSEW)
        param_num += 1 

        # Max Slope:
        param_str = '{ "name":"Max Plane Slope (Degrees)",  "description": "Maximum Slope of Plane (Displayed in Degrees).", "flags": ["--maxSlope"], "parameter_type": "Float", "optional": "False", "default_value": "75.0"}'
        di6 = DataInput(param_str, self.elements_frame, self.tt_label)
        di6.grid(row=param_num, column=0, sticky=tk.NSEW)
        param_num += 1 

        # Number of Samples:
        param_str = '{ "name":"Number of Samples (Per Neighbourhood)",  "description": "Number of Samples (Default: 10).", "flags": ["--numSamples"], "parameter_type": "Integer", "optional": "False", "default_value": "5"}'
        di7 = DataInput(param_str, self.elements_frame, self.tt_label)
        di7.grid(row=param_num, column=0, sticky=tk.NSEW)
        param_num += 1

        # Acceptable Model Size:
        param_str = '{ "name":"Desired Model Size (Num Points)",  "description": "Minimum number of points in the model.", "flags": ["--acceptableModelSize"], "parameter_type": "Integer", "optional": "False", "default_value": "10"}'
        di8 = DataInput(param_str, self.elements_frame, self.tt_label)
        di8.grid(row=param_num, column=0, sticky=tk.NSEW)
        param_num += 1
        self.elements_frame.grid(row=0, column=0, sticky=tk.NSEW)

        #########################################################
        #                   Buttons Frame                       #
        #########################################################

        #Create the elements of the buttons frame
        buttons_frame = ttk.Frame(overall_frame, padding='0.1i')
        self.run_button = ttk.Button(buttons_frame, text="Run", width=8, command=self.run_tool)
        self.quit_button = ttk.Button(buttons_frame, text="Cancel", width=8, command=self.cancel_operation)
        self.close_button = ttk.Button(buttons_frame, text="Close", width=8, command=self.quit)

        #Define layout of the frame
        self.run_button.grid(row=0, column=0)
        self.quit_button.grid(row=0, column=1)
        self.close_button.grid(row=0, column=2)
        buttons_frame.grid(row=1, column=0, columnspan=2, sticky=tk.E)

        #########################################################
        #                  Output Frame                         #
        #########################################################              
        #Create the elements of the output frame
        output_frame = ttk.Frame(overall_frame)
        outlabel = ttk.Label(output_frame, text="Output:", justify=tk.LEFT)
        self.out_text = ScrolledText(output_frame, width=63, height=8, wrap=tk.NONE, padx=7, pady=7, exportselection = 0)
        output_scrollbar = ttk.Scrollbar(output_frame, orient=tk.HORIZONTAL, command = self.out_text.xview)
        self.out_text['xscrollcommand'] = output_scrollbar.set
        #Retreive and insert the text for the current tool
        # k = wbt.tool_help(self.tool_name)   
        # self.out_text.insert(tk.END, k)
        #Define layout of the frame
        outlabel.grid(row=0, column=0, sticky=tk.NW)
        self.out_text.grid(row=1, column=0, sticky=tk.NSEW)
        output_frame.grid(row=2, column=0, columnspan = 2, sticky=(tk.NS, tk.E))
        output_scrollbar.grid(row=2, column=0, sticky=(tk.W, tk.E))

        #Configure rows and columns of the frame
        self.out_text.columnconfigure(0, weight=1)
        output_frame.columnconfigure(0, weight=1)
        # Add the binding
        if _platform == "darwin":
            self.out_text.bind("<Command-Key-a>", self.select_all)
        else:
            self.out_text.bind("<Control-Key-a>", self.select_all)
            
        #########################################################
        #                  Progress Frame                       #
        #########################################################        
        #Create the elements of the progress frame
        progress_frame = ttk.Frame(overall_frame, padding='0.1i')
        self.progress_label = ttk.Label(progress_frame, text="Progress:", justify=tk.LEFT)
        self.progress_var = tk.DoubleVar()
        self.progress = ttk.Progressbar(progress_frame, orient="horizontal", variable=self.progress_var, length=200, maximum=100)

        #Define layout of the frame
        self.progress_label.grid(row=0, column=0, sticky=tk.E, padx=5)
        self.progress.grid(row=0, column=1, sticky=tk.E)
        progress_frame.grid(row=3, column=0, columnspan = 2, sticky=tk.SE)

        self.working_dir = str(Path.home())

    def run_tool(self):
        try:
            args = []
            for widget in self.elements_frame.winfo_children():
                v = widget.get_value()
                if v:
                    args.append(v)
                elif not widget.optional:
                    messagebox.showinfo(
                        "Error", "Non-optional tool parameter not specified.")
                    return

            ''' 
            Runs a tool and specifies tool arguments.
            Returns 0 if completes without error.
            Returns 1 if error encountered (details are sent to callback).
            Returns 2 if process is cancelled by user.
            '''

            os.chdir(self.exe_path)
            args2 = []
            
            args2.append("." + path.sep + self.exe_name)
            # args2.append("--run=\"{}\"".format(to_camelcase(tool_name)))
            args2.append("run")

            if self.working_dir not in args2:
                args2.append("--wd=\"{}\"".format(self.working_dir)) 

            for arg in args:
                args2.append(arg)

            cl = ""
            for v in args2:
                cl += v + " "
            self.custom_callback(cl.strip() + "\n")

            proc = Popen(args2, shell=False, stdout=PIPE, stderr=STDOUT, bufsize=1, universal_newlines=True)

            while True:
                line = proc.stdout.readline()
                sys.stdout.flush()
                if line != '':
                    if not self.cancel_op:
                        self.custom_callback(line.strip())
                    else:
                        self.cancel_op = False
                        proc.terminate()
                        return 2

                else:
                    break

            return 0
        except (OSError, ValueError, CalledProcessError) as err:
            self.custom_callback(str(err))
            return 1
        finally:
            self.progress_var.set(0)
            self.progress_label['text'] = "Completion:"

    def custom_callback(self, value):
        ''' A custom callback for dealing with tool output.
        '''
        if "%" in value:
            try:
                str_array = value.split(" ")
                label = value.replace(
                    str_array[len(str_array) - 1], "").strip()
                progress = float(
                    str_array[len(str_array) - 1].replace("%", "").strip())
                self.progress_var.set(int(progress))
                self.progress_label['text'] = label
            except ValueError as e:
                print("Problem converting parsed data into number: ", e)
            except Exception as e:
                print(e)
        else:
            self.print_line_to_output(value)

        self.update()  # this is needed for cancelling and updating the progress bar

    def print_to_output(self, value):
        self.out_text.insert(tk.END, value)
        self.out_text.see(tk.END)

    def print_line_to_output(self, value):
        self.out_text.insert(tk.END, value + "\n")
        self.out_text.see(tk.END)
        
    def cancel_operation(self):
        # wbt.cancel_op = True
        self.print_line_to_output("Cancelling operation...")
        self.progress.update_idletasks()

    def select_all(self, event):
        self.out_text.tag_add(tk.SEL, "1.0", tk.END)
        self.out_text.mark_set(tk.INSERT, "1.0")
        self.out_text.see(tk.INSERT)
        return 'break'

def main():
    gui = Gui()
    gui.mainloop()
main()
