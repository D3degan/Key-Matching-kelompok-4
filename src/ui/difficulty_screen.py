import os
import tkinter as tk
from tkinter import messagebox
from typing import Callable


class DifficultyScreen:
    """Mengelola tampilan pemilihan tingkat kesulitan (difficulty) permainan

    menggunakan Tkinter Canvas.

    Class ini murni bertanggung jawab terhadap UI pemilihan difficulty. Class

    ini tidak mengetahui GameEngine, GameplayScreen, maupun apa yang terjadi

    setelah pemain memilih difficulty; seluruh hasil pilihan hanya dikirim

    melalui callback `on_difficulty_selected` berupa durasi permainan dalam
    detik.
    """

    # Path absolut menuju root project, dihitung dari lokasi file ini sendiri
    # (src/ui/difficulty_screen.py -> naik 2 folder -> root project)
    _BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    PROJECT_ROOT = os.path.dirname(os.path.dirname(_BASE_DIR))

    # Konstanta untuk manajemen path asset gambar
    ASSET_ROOT = os.path.join(PROJECT_ROOT, "assets")
    UI_FOLDER = "ui"
    BACKGROUND_IMAGE = "difficulty_bg.png"
    EASY_IMAGE = "easy.png"
    MEDIUM_IMAGE = "medium.png"
    HARD_IMAGE = "hard.png"

    # Konstanta ukuran window, tetap konsisten dengan screen lain (640 x 480)
    WINDOW_WIDTH = 640
    WINDOW_HEIGHT = 480

    # Konstanta durasi permainan (dalam detik) untuk masing-masing tingkat kesulitan
    EASY_DURATION = 120
    MEDIUM_DURATION = 60
    HARD_DURATION = 40

    # Konstanta posisi background (memenuhi seluruh Canvas)
    BACKGROUND_POS = {"x": 0, "y": 0, "anchor": "nw"}

    # Konstanta posisi judul (tengah-atas)
    TITLE_TEXT = "Select Difficulty"
    TITLE_POS = {"x": WINDOW_WIDTH // 2, "y": 90, "anchor": "center"}
    TITLE_FONT = ("Helvetica", 28, "bold")
    TITLE_TEXT_COLOR = "#1a1a1a"

    # Konstanta posisi tombol, tersusun vertikal dan simetris terhadap window
    EASY_BTN_POS = {"x": WINDOW_WIDTH // 2, "y": 210, "anchor": "center"}
    MEDIUM_BTN_POS = {"x": WINDOW_WIDTH // 2, "y": 290, "anchor": "center"}
    HARD_BTN_POS = {"x": WINDOW_WIDTH // 2, "y": 370, "anchor": "center"}

    # Tag khusus untuk item Canvas interaktif (dipakai oleh tag_bind)
    TAG_EASY_BTN = "btn_easy"
    TAG_MEDIUM_BTN = "btn_medium"
    TAG_HARD_BTN = "btn_hard"

    def __init__(
        self,
        master: tk.Widget,
        on_difficulty_selected: Callable[[int], None],
    ) -> None:
        """Inisialisasi komponen screen pemilihan difficulty, memuat seluruh asset

        gambar yang dibutuhkan, menyiapkan layout Canvas, serta menghubungkan

        event klik tombol Easy, Medium, dan Hard.

        Args:
            master (tk.Widget): Parent widget Tkinter tempat frame utama akan
              ditempel.
            on_difficulty_selected (Callable[[int], None]): Callback eksternal
              yang dipanggil saat pemain memilih salah satu tombol difficulty.
              Menerima satu argumen berupa durasi permainan dalam detik.
              DifficultyScreen tidak mengetahui apa yang terjadi setelah
              callback ini dipanggil.
        """
        self.master: tk.Widget = master
        self.on_difficulty_selected: Callable[[int], None] = on_difficulty_selected

        # Guard untuk mencegah ghost callback dari event Canvas setelah cleanup() dipanggil
        self.is_interaction_enabled: bool = True

        # Cache dictionary untuk menyimpan objek tk.PhotoImage di memori RAM,
        # sekaligus disimpan sebagai attribute individual agar konsisten dengan
        # konvensi penamaan yang diminta (self.background_image, self.easy_image, dst.)
        self.background_image: tk.PhotoImage
        self.easy_image: tk.PhotoImage
        self.medium_image: tk.PhotoImage
        self.hard_image: tk.PhotoImage

        # Deklarasi referensi widget utama
        self.main_frame: tk.Frame
        self.canvas: tk.Canvas

        # Deklarasi referensi ID item Canvas
        self.background_image_id: int
        self.title_text_id: int
        self.easy_btn_id: int
        self.medium_btn_id: int
        self.hard_btn_id: int

        # Membangun struktur interface dan memuat aset gambar ke memori RAM
        self.preload_all_assets()
        self.build_layout()
        self.bind_events()

    def preload_all_assets(self) -> None:
        """Membaca seluruh aset PNG yang dibutuhkan (background dan tiga tombol

        difficulty) ke dalam cache berupa tk.PhotoImage.

        Raises:
            FileNotFoundError: Jika berkas gambar tidak ditemukan pada lokasi path.
            tk.TclError: Jika berkas gambar korup atau tidak dapat dibaca Tkinter.
        """
        try:
            background_path = os.path.join(self.ASSET_ROOT, self.UI_FOLDER, self.BACKGROUND_IMAGE)
            if not os.path.exists(background_path):
                raise FileNotFoundError(f"Aset background hilang: {background_path}")
            self.background_image = tk.PhotoImage(file=background_path)

            easy_path = os.path.join(self.ASSET_ROOT, self.UI_FOLDER, self.EASY_IMAGE)
            if not os.path.exists(easy_path):
                raise FileNotFoundError(f"Aset tombol Easy hilang: {easy_path}")
            self.easy_image = tk.PhotoImage(file=easy_path)

            medium_path = os.path.join(self.ASSET_ROOT, self.UI_FOLDER, self.MEDIUM_IMAGE)
            if not os.path.exists(medium_path):
                raise FileNotFoundError(f"Aset tombol Medium hilang: {medium_path}")
            self.medium_image = tk.PhotoImage(file=medium_path)

            hard_path = os.path.join(self.ASSET_ROOT, self.UI_FOLDER, self.HARD_IMAGE)
            if not os.path.exists(hard_path):
                raise FileNotFoundError(f"Aset tombol Hard hilang: {hard_path}")
            self.hard_image = tk.PhotoImage(file=hard_path)

        except (FileNotFoundError, tk.TclError) as error:
            messagebox.showerror(
                "Error Memuat Aset",
                f"Aplikasi gagal dimulai karena masalah pada berkas aset gambar.\n\nDetail: {error}",
            )
            # Menggunakan bare raise untuk melestarikan original stack trace/traceback asli
            raise

    def build_layout(self) -> None:
        """Membangun layout Canvas tunggal yang memenuhi seluruh window, lalu menggambar

        background, judul "Select Difficulty", serta tiga tombol difficulty (Easy,

        Medium, Hard) tersusun vertikal dan simetris terhadap window.
        """
        self.main_frame = tk.Frame(
            self.master,
            width=self.WINDOW_WIDTH,
            height=self.WINDOW_HEIGHT,
        )
        self.main_frame.place(x=0, y=0, width=self.WINDOW_WIDTH, height=self.WINDOW_HEIGHT)
        self.main_frame.pack_propagate(False)

        self.canvas = tk.Canvas(
            self.main_frame,
            width=self.WINDOW_WIDTH,
            height=self.WINDOW_HEIGHT,
            highlightthickness=0,
            borderwidth=0,
        )
        self.canvas.place(x=0, y=0, width=self.WINDOW_WIDTH, height=self.WINDOW_HEIGHT)

        # Layer 1 (paling bawah): background, memenuhi seluruh Canvas
        self.background_image_id = self.canvas.create_image(
            self.BACKGROUND_POS["x"],
            self.BACKGROUND_POS["y"],
            image=self.background_image,
            anchor=self.BACKGROUND_POS["anchor"],
        )

        # Layer 2: judul "Select Difficulty"
        self.title_text_id = self.canvas.create_text(
            self.TITLE_POS["x"],
            self.TITLE_POS["y"],
            text=self.TITLE_TEXT,
            anchor=self.TITLE_POS["anchor"],
            font=self.TITLE_FONT,
            fill=self.TITLE_TEXT_COLOR,
        )

        # Layer 3: tombol Easy
        self.easy_btn_id = self.canvas.create_image(
            self.EASY_BTN_POS["x"],
            self.EASY_BTN_POS["y"],
            image=self.easy_image,
            anchor=self.EASY_BTN_POS["anchor"],
            tags=(self.TAG_EASY_BTN,),
        )

        # Layer 4: tombol Medium
        self.medium_btn_id = self.canvas.create_image(
            self.MEDIUM_BTN_POS["x"],
            self.MEDIUM_BTN_POS["y"],
            image=self.medium_image,
            anchor=self.MEDIUM_BTN_POS["anchor"],
            tags=(self.TAG_MEDIUM_BTN,),
        )

        # Layer 5 (paling atas): tombol Hard
        self.hard_btn_id = self.canvas.create_image(
            self.HARD_BTN_POS["x"],
            self.HARD_BTN_POS["y"],
            image=self.hard_image,
            anchor=self.HARD_BTN_POS["anchor"],
            tags=(self.TAG_HARD_BTN,),
        )

    def bind_events(self) -> None:
        """Menghubungkan aksi klik pada item Canvas ke method penangan masing-masing

        menggunakan Canvas.tag_bind(), sebagai pengganti command Button bawaan Tkinter.
        """
        self.canvas.tag_bind(
            self.TAG_EASY_BTN, "<Button-1>", lambda event: self.on_easy_click()
        )
        self.canvas.tag_bind(
            self.TAG_MEDIUM_BTN, "<Button-1>", lambda event: self.on_medium_click()
        )
        self.canvas.tag_bind(
            self.TAG_HARD_BTN, "<Button-1>", lambda event: self.on_hard_click()
        )

    def on_easy_click(self) -> None:
        """Menangani interaksi klik pada tombol Easy dengan memanggil callback

        `on_difficulty_selected` menggunakan durasi EASY_DURATION.
        """
        if not self.is_interaction_enabled:
            return

        self.on_difficulty_selected(self.EASY_DURATION)

    def on_medium_click(self) -> None:
        """Menangani interaksi klik pada tombol Medium dengan memanggil callback

        `on_difficulty_selected` menggunakan durasi MEDIUM_DURATION.
        """
        if not self.is_interaction_enabled:
            return

        self.on_difficulty_selected(self.MEDIUM_DURATION)

    def on_hard_click(self) -> None:
        """Menangani interaksi klik pada tombol Hard dengan memanggil callback

        `on_difficulty_selected` menggunakan durasi HARD_DURATION.
        """
        if not self.is_interaction_enabled:
            return

        self.on_difficulty_selected(self.HARD_DURATION)

    def cleanup(self) -> None:
        """Membersihkan resource dan interaksi milik DifficultyScreen sebelum screen

        ini dihancurkan oleh parent controller (MainApplication).

        Saat ini DifficultyScreen tidak memiliki timer maupun after() callback

        yang berjalan, sehingga method ini cukup berisi pass. Method ini tetap

        disediakan untuk menjaga konsistensi interface dengan GameplayScreen.
        """
        pass