import tkinter as tk
from src.core import GameEngine
from src.ui.gameplay_screen import GameplayScreen
from src.ui.end_screen import EndScreen
from src.ui.difficulty_screen import DifficultyScreen


class MainApplication:
    """Controller utama (Application Lifecycle Manager) yang mengatur pembuatan window,

    manajemen state game engine, pembersihan screen secara aman, dan transisi layar.
    """

    # Konfigurasi Global Aplikasi (Menghindari Magic Numbers)
    WINDOW_WIDTH = 640
    WINDOW_HEIGHT = 480

    def __init__(self) -> None:
        # Menyiapkan dan mengonfigurasi root window utama sesuai aspek rasio aset
        self.root = tk.Tk()
        self.root.title("Key and Door Puzzle Game")
        self.root.geometry(f"{self.WINDOW_WIDTH}x{self.WINDOW_HEIGHT}")
        self.root.resizable(False, False)

        # Tracker untuk menyimpan referensi objek Screen atau Frame yang sedang aktif
        self.current_screen = None
        self.engine = None

        # Memulai permainan pertama kali dengan menampilkan layar pemilihan difficulty
        self.show_difficulty_screen()

    def clear_screen(self) -> None:
        """Menghentikan seluruh loop asinkronus (after timer/cooldown) secara aman

        dan menghancurkan widget screen lama menggunakan proteksi winfo_exists().
        """
        if self.current_screen is not None:
            # Jika screen memiliki method cleanup() (seperti GameplayScreen), jalankan terlebih dahulu
            if hasattr(self.current_screen, "cleanup"):
                self.current_screen.cleanup()

            # Proteksi berlapis: pastikan widget benar-benar ada sebelum dihancurkan
            if hasattr(self.current_screen, "main_frame"):
                if self.current_screen.main_frame.winfo_exists():
                    self.current_screen.main_frame.destroy()
            elif hasattr(self.current_screen, "winfo_exists"):
                # Penanganan jika current_screen adalah objek tk.Frame placeholder langsung
                if self.current_screen.winfo_exists():
                    self.current_screen.destroy()

        self.current_screen = None

    def show_difficulty_screen(self) -> None:
        """Membersihkan layar lama, membuat instance DifficultyScreen, dan menyimpan

        referensinya ke dalam current_screen.
        """
        self.clear_screen()
        self.current_screen = DifficultyScreen(
            master=self.root,
            on_difficulty_selected=self.on_difficulty_selected,
        )

    def on_difficulty_selected(self, duration: int) -> None:
        """Callback yang dijalankan saat tingkat kesulitan dipilih untuk menginisialisasi

        GameEngine dengan durasi tersebut dan memulai gameplay.
        """
        self.engine = GameEngine(duration)
        self.show_gameplay()

    def show_gameplay(self) -> None:
        """Menginstansiasi dan mengonfigurasi GameplayScreen ke dalam root window."""
        self.clear_screen()

        # Controller memegang kendali penuh atas objek screen secara utuh, bukan hanya frame-nya
        gameplay = GameplayScreen(
            master=self.root,
            engine=self.engine,
            on_victory_callback=self.show_victory,
            on_game_over_callback=self.show_gameover,
        )
        
        self.current_screen = gameplay

    def show_victory(self, score: int) -> None:
        """Menampilkan layar kemenangan menggunakan EndScreen."""
        self.clear_screen()
        self.current_screen = EndScreen(
            master=self.root,
            is_victory=True,
            score=score,
            on_retry_callback=self.restart_game,
            on_menu_callback=self.restart_game,
        )

    def show_gameover(self) -> None:
        """Menampilkan layar kekalahan menggunakan EndScreen."""
        self.clear_screen()
        self.current_screen = EndScreen(
            master=self.root,
            is_victory=False,
            score=None,
            on_retry_callback=self.restart_game,
            on_menu_callback=self.restart_game,
        )

    def restart_game(self) -> None:
        """Mengarahkan kembali pemain ke layar pemilihan tingkat kesulitan ketika ingin mengulang."""
        self.show_difficulty_screen()

    def run(self) -> None:
        """Menjalankan main event loop Tkinter untuk memulai aplikasi."""
        self.root.mainloop()


if __name__ == "__main__":
    app = MainApplication()
    app.run()