import tkinter as tk
import db

def show_leaderboard_window(parent):
    board = tk.Toplevel(parent)
    board.title("Leaderboard")
    board.geometry("640x480")
    board.config(bg="black")

    title = tk.Label(board, text="LEADERBOARD", font=("Franklin Gothic Heavy", 36), fg="red", bg="black")
    title.place(relx=0.5, y=50, anchor="center")

    list_frame = tk.Frame(board, bg="black")
    list_frame.place(relx=0.5, y=120, anchor="n", width=500, height=280)

    conn = db.get_connection()
    if conn is None:
        error_label = tk.Label(list_frame, text="Gak bisa konek ke database.", font=("Franklin Gothic Heavy", 14), fg="red", bg="black")
        error_label.pack(pady=10)
    else:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT username, score FROM users ORDER BY score DESC LIMIT 10")
            results = cursor.fetchall()

            if not results:
                empty_label = tk.Label(list_frame, text="Belum ada data leaderboard.", font=("Franklin Gothic Heavy", 14), fg="gray", bg="black")
                empty_label.pack(pady=10)
            else:
                for rank, (username, score) in enumerate(results, start=1):
                    row_text = f"{rank}. {username} - {score}"
                    row_label = tk.Label(
                        list_frame, text=row_text,
                        font=("Franklin Gothic Heavy", 16),
                        fg="red" if rank == 1 else "gray",
                        bg="black", anchor="w"
                    )
                    row_label.pack(fill="x", pady=4)

        except Exception as e:
            error_label = tk.Label(list_frame, text=f"Error: {e}", font=("Franklin Gothic Heavy", 12), fg="red", bg="black")
            error_label.pack(pady=10)
        finally:
            cursor.close()
            conn.close()

    close_button = tk.Button(
        board, text="Tutup", font=("Franklin Gothic Heavy", 18),
        fg="gray", bg="black", command=board.destroy
    )
    close_button.place(relx=0.5, y=420, anchor="center", width=150, height=40)

    board.transient(parent)
    board.grab_set()
