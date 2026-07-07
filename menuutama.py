import tkinter as tk
import leaderboard
import login


def show_main_menu(user_id):
    root = tk.Tk()
    root.title("Main Menu")
    root.geometry("640x480")
    root.config(bg="black")

    title = tk.Label(root, text="A KEY", font=("Franklin Gothic Heavy", 50), fg="red", bg="black")
    title.place(relx=0.5, y=80, anchor="center")

    def play_action():
        # TODO: nanti panggil file gameplay di sini, misal:
        # import Gameplay  (ganti sesuai nama file game kamu)
        # root.destroy()
        # Gameplay.start_game(user_id)
        print("Play diklik - belum disambung ke file gameplay")

    def leaderboard_action():
        leaderboard.show_leaderboard_window(root)

    def back_to_login_action():
        root.destroy()
        login.show_login_window()

    button_play = tk.Button(
        root, text="PLAY", font=("Franklin Gothic Heavy", 24),
        fg="red", bg="black", command=play_action
    )
    button_play.place(relx=0.5, y=180, anchor="center", width=250, height=60)

    button_leaderboard = tk.Button(
        root, text="LEADERBOARD", font=("Franklin Gothic Heavy", 24),
        fg="gray", bg="black", command=leaderboard_action
    )
    button_leaderboard.place(relx=0.5, y=260, anchor="center", width=250, height=60)

    button_back = tk.Button(
        root, text="BACK TO LOGIN", font=("Franklin Gothic Heavy", 24),
        fg="gray", bg="black", command=back_to_login_action
    )
    button_back.place(relx=0.5, y=340, anchor="center", width=250, height=60)

    root.mainloop()


if __name__ == "__main__":
    show_main_menu(1)  # testing manual, id 1 asumsi ada di DB