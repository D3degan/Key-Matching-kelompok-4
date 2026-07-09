import tkinter as tk
from tkinter import messagebox
import db


def show_register_window(parent=None):
    root = tk.Toplevel(parent) if parent is not None else tk.Tk()
    root.title("Register")
    root.geometry("640x480")
    root.config(bg="black")

    title = tk.Label(root, text="WHO ARE U", font=("Franklin Gothic Heavy", 60), fg="GRAY", bg="black")
    title.place(x=50, y=50)

    placeholder = "your name."
    nameentry = tk.Entry(root, font=("Franklin Gothic Heavy", 20), fg="gray", bg="black", insertbackground="white")
    nameentry.place(x=190, y=200, width=250, height=50)
    nameentry.insert(0, placeholder)

    placeholder2 = "ur secret fav thing?"
    passwd = tk.Entry(root, font=("Franklin Gothic Heavy", 20), fg="gray", bg="black", insertbackground="white")
    passwd.place(x=190, y=260, width=250, height=50)
    passwd.insert(0, placeholder2)

    status_label = tk.Label(root, text="", font=("Franklin Gothic Heavy", 14), fg="red", bg="black")
    status_label.place(x=150, y=400, width=350, height=30)

    def on_entry_focus_in(event):
        if nameentry.get() == placeholder:
            nameentry.delete(0, tk.END)
            nameentry.config(fg="Gray")

    def on_entry_focus_out(event):
        if not nameentry.get():
            nameentry.insert(0, placeholder)
            nameentry.config(fg="gray")

    def on_passwd_focus_in(event):
        if passwd.get() == placeholder2:
            passwd.delete(0, tk.END)
            passwd.config(fg="gray", show="")

    def on_passwd_focus_out(event):
        if not passwd.get():
            passwd.insert(0, placeholder2)
            passwd.config(fg="gray", show="")

    def backbutton():
        root.destroy()

    def register_action():
        username = nameentry.get().strip()
        password = passwd.get().strip()

        if username == "" or username == placeholder or password == "" or password == placeholder2:
            status_label.config(text="still empty??", fg="red")
            return

        conn = db.get_connection()
        if conn is None:
            status_label.config(text="database lostconn", fg="red")
            messagebox.showerror("Database Error", "Failed to connect to the database.")
            return

        try:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
            if cursor.fetchone() is not None:
                status_label.config(text="u not him dawg..", fg="red")
                return

            cursor.execute(
                "INSERT INTO users (username, password, score) VALUES (%s, %s, %s)",
                (username, password, 0)
            )
            conn.commit()

            cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
            result = cursor.fetchone()

            if result is not None:
                status_label.config(text="welcome.", fg="red")
            else:
                status_label.config(text="Data gagal disimpan, coba lagi.", fg="red")

        except Exception as e:
            status_label.config(text=f"Error: {e}", fg="red")
        finally:
            cursor.close()
            conn.close()

    nameentry.bind("<FocusIn>", on_entry_focus_in)
    nameentry.bind("<FocusOut>", on_entry_focus_out)
    passwd.bind("<FocusIn>", on_passwd_focus_in)
    passwd.bind("<FocusOut>", on_passwd_focus_out)

    button1 = tk.Button(root, text="yES", font=("Franklin Gothic Heavy", 20), fg="red", bg="black", command=register_action)
    button1.place(x=150, y=330, width=100, height=50)
    button2 = tk.Button(root, text="no (BACK)", font=("Franklin Gothic Heavy", 20), fg="gray", bg="black", command=backbutton)
    button2.place(x=310, y=330, width=200, height=50)

    if parent is not None:
        root.transient(parent)
        root.grab_set()

    if parent is None:
        root.mainloop()


if __name__ == "__main__":
    show_register_window()