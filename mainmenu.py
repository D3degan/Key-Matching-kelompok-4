import tkinter as tk

root = tk.Tk()
root.title("Main Menu")
root.geometry("640x480")
root.config(bg="black")

tittle = tk.Label(root, text="KEY BOO", font=("Franklin Gothic Heavy", 60), fg="red", bg="black")
tittle.place (x=150, y=50)

placeholder = "insert name."
nameentry = tk.Entry(root, font=("Franklin Gothic Heavy", 20), fg="gray", bg="black", insertbackground="white")
nameentry.place(x=190, y=200, width=250, height=50)
nameentry.insert(0, placeholder)


def on_entry_focus_in(event):
    if nameentry.get() == placeholder:
        nameentry.delete(0, tk.END)
        nameentry.config(fg="white")


def on_entry_focus_out(event):
    if not nameentry.get():
        nameentry.insert(0, placeholder)
        nameentry.config(fg="gray")

nameentry.bind("<FocusIn>", on_entry_focus_in)
nameentry.bind("<FocusOut>", on_entry_focus_out)

button = tk.Button(root, text="Play", font=("Franklin Gothic Heavy", 20), fg="red", bg="black")
button.place(x=270, y=300, width=100, height=50)

root.mainloop()