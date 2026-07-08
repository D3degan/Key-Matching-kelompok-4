import tkinter as tk
from tkinter import messagebox
import Register
import db
import menuutama


def show_login_window():
    root = tk.Tk()
    root.title("Main Menu")
    root.geometry("640x480")
    root.config(bg="black")

    title = tk.Label(root, text="A KEY", font=("Franklin Gothic Heavy", 60), fg="red", bg="black")
    title.place(x=200, y=50)

    placeholder = "insert name."
    nameentry = tk.Entry(root, font=("Franklin Gothic Heavy", 20), fg="gray", bg="black", insertbackground="white")
    nameentry.place(x=190, y=200, width=250, height=50)
    nameentry.insert(0, placeholder)

    placeholder2 = "ur fav thing?"
    passwd = tk.Entry(root, font=("Franklin Gothic Heavy", 20), fg="gray", bg="black", insertbackground="white")
    passwd.place(x=190, y=260, width=250, height=50)
    passwd.insert(0, placeholder2)

    status_label = tk.Label(root, text="", font=("Franklin Gothic Heavy", 14), fg="red", bg="black")
    status_label.place(x=150, y=390, width=350, height=30)

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
            passwd.config(fg="gray", show="*")

    def on_passwd_focus_out(event):
        if not passwd.get():
            passwd.insert(0, placeholder2)
            passwd.config(fg="gray", show="")

    def login_action():
        username = nameentry.get().strip()
        password = passwd.get().strip()

        if username == "" or username == placeholder or password == "" or password == placeholder2:
            status_label.config(text="still empty..", fg="red")
            return

        conn = db.get_connection()
        if conn is None:
            status_label.config(text="database lostconn", fg="red")
            messagebox.showerror("Database Error", "Failed to connect to the database.")
            return

        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id FROM users WHERE username = %s AND password = %s",
                (username, password)
            )
            result = cursor.fetchone()

            if result is not None:
                user_id = result[0]
                root.destroy()
                menuutama.show_main_menu(user_id)
            else:
                status_label.config(text="theres no such user", fg="red")

        except Exception as e:
            status_label.config(text=f"Error: {e}", fg="red")
        finally:
            cursor.close()
            conn.close()

    nameentry.bind("<FocusIn>", on_entry_focus_in)
    nameentry.bind("<FocusOut>", on_entry_focus_out)
    passwd.bind("<FocusIn>", on_passwd_focus_in)
    passwd.bind("<FocusOut>", on_passwd_focus_out)

    button1 = tk.Button(root, text="Register", font=("Franklin Gothic Heavy", 20), fg="red", bg="black", command=lambda: Register.show_register_window(root))
    button1.place(x=150, y=320, width=200, height=50)
    button2 = tk.Button(root, text="Login", font=("Franklin Gothic Heavy", 20), fg="red", bg="black", command=login_action)
    button2.place(x=390, y=320, width=100, height=50)

    root.mainloop()


if __name__ == "__main__":
    show_login_window()