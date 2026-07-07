import os
import tkinter as tk
from typing import Callable, Optional


class EndScreen:
    """Mengelola tampilan akhir permainan (menang maupun kalah) menggunakan Canvas.

    Class ini bersifat generik: satu implementasi dipakai untuk kedua kondisi

    (kemenangan dan kekalahan), dibedakan hanya melalui flag `is_victory` yang

    menentukan background yang ditampilkan dan apakah skor akhir ikut digambar.

    Class ini tidak berinteraksi dengan GameEngine maupun GameplayScreen sama

    sekali; seluruh data yang dibutuhkan (status menang/kalah dan skor akhir)

    diterima langsung melalui constructor.
    """

    # Konstanta untuk manajemen path asset gambar
    ASSET_ROOT = "assets"
    UI_ASSET_FOLDER = "ui"

    # Nama berkas asset (tidak di-hardcode langsung di badan method)
    VICTORY_BG_FILE = "wbg.png"
    DEFEAT_BG_FILE = "lbg.png"
    MENU_BTN_FILE = "mbt.png"
    RETRY_BTN_FILE = "rtbt.png"

    # Konstanta ukuran window, tetap konsisten dengan screen lain (640 x 480)
    WINDOW_WIDTH = 640
    WINDOW_HEIGHT = 480

    # Konstanta posisi background (memenuhi seluruh Canvas)
    BACKGROUND_POS = {"x": 0, "y": 0, "anchor": "nw"}

    # Konstanta posisi skor (tengah-atas), hanya dipakai saat menang
    SCORE_POS = {"x": WINDOW_WIDTH // 2, "y": 110, "anchor": "center"}
    SCORE_FONT = ("Helvetica", 28, "bold")
    SCORE_TEXT_COLOR = "#1a1a1a"
    SCORE_LABEL_TEMPLATE = "Score: {score}"

    # Konstanta posisi tombol saat kondisi MENANG (skor mengambil ruang di atas)
    RETRY_POS_VICTORY = {"x": WINDOW_WIDTH // 2, "y": 280, "anchor": "center"}
    MENU_POS_VICTORY = {"x": WINDOW_WIDTH // 2, "y": 350, "anchor": "center"}

    # Konstanta posisi tombol saat kondisi KALAH (tanpa skor, tombol lebih ke tengah)
    RETRY_POS_DEFEAT = {"x": WINDOW_WIDTH // 2, "y": 240, "anchor": "center"}
    MENU_POS_DEFEAT = {"x": WINDOW_WIDTH // 2, "y": 310, "anchor": "center"}

    # Tag khusus untuk item Canvas interaktif (dipakai oleh tag_bind)
    TAG_RETRY_BTN = "btn_retry"
    TAG_MENU_BTN = "btn_menu"

    def __init__(
        self,
        master: tk.Widget,
        is_victory: bool,
        score: Optional[int],
        on_retry_callback: Callable[[], None],
        on_menu_callback: Callable[[], None],
    ) -> None:
        """Inisialisasi komponen screen akhir permainan, memuat asset yang relevan,

        menyiapkan layout Canvas sesuai kondisi menang/kalah, serta menghubungkan

        event klik tombol Retry dan Main Menu.

        Args:
            master (tk.Widget): Parent widget Tkinter tempat frame utama akan
              ditempel.
            is_victory (bool): True jika pemain menang, False jika kalah.
              Menentukan background yang dipakai dan apakah skor ditampilkan.
            score (Optional[int]): Skor akhir permainan. Wajib diisi (bukan None)
              saat is_victory bernilai True. Diabaikan (boleh None) saat kalah.
            on_retry_callback (Callable[[], None]): Callback eksternal yang
              dipanggil saat tombol Retry diklik.
            on_menu_callback (Callable[[], None]): Callback eksternal yang
              dipanggil saat tombol Main Menu diklik.
        """
        self.master: tk.Widget = master
        self.is_victory: bool = is_victory
        self.score: Optional[int] = score
        self.on_retry_callback: Callable[[], None] = on_retry_callback
        self.on_menu_callback: Callable[[], None] = on_menu_callback

        # Guard untuk mencegah ghost callback dari event Canvas setelah cleanup() dipanggil
        self.is_interaction_enabled: bool = True

        # Cache dictionary untuk menyimpan objek tk.PhotoImage di memori RAM
        self.image_cache: dict[str, tk.PhotoImage] = {}

        # Deklarasi referensi widget utama, sesuai konvensi GameplayScreen agar
        # MainApplication dapat menghancurkan screen ini dengan cara yang sama.
        self.main_frame: tk.Frame
        self.canvas: tk.Canvas

        # Deklarasi referensi ID item Canvas
        self.background_image_id: int
        self.score_text_id: Optional[int] = None
        self.retry_btn_id: int
        self.menu_btn_id: int

        # Membangun struktur interface dan memuat aset gambar ke memori RAM
        self.preload_all_assets()
        self.build_layout()
        self.bind_events()

    def preload_all_assets(self) -> None:
        """Membaca aset PNG yang relevan sesuai kondisi menang/kalah ke dalam cache.

        Hanya background yang sesuai dengan `is_victory` yang dimuat, sementara

        tombol Retry dan Main Menu selalu dimuat karena selalu ditampilkan pada

        kedua kondisi.

        Raises:
            FileNotFoundError: Jika berkas gambar tidak ditemukan pada lokasi path.
            tk.TclError: Jika berkas gambar korup atau tidak dapat dibaca Tkinter.
        """
        background_file = self.VICTORY_BG_FILE if self.is_victory else self.DEFEAT_BG_FILE

        asset_files = {
            "background": background_file,
            "retry": self.RETRY_BTN_FILE,
            "menu": self.MENU_BTN_FILE,
        }

        for asset_key, filename in asset_files.items():
            asset_path = os.path.join(self.ASSET_ROOT, self.UI_ASSET_FOLDER, filename)
            if not os.path.exists(asset_path):
                raise FileNotFoundError(f"Aset UI hilang: {asset_path}")
            self.image_cache[asset_key] = tk.PhotoImage(file=asset_path)

    def build_layout(self) -> None:
        """Membangun layout Canvas tunggal yang memenuhi seluruh window, lalu menggambar

        background, skor (jika menang), serta tombol Retry dan Main Menu.

        Urutan layer dari bawah ke atas: background, skor (opsional), tombol Retry,

        tombol Main Menu.
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

        # Layer 1 (paling bawah): background, berbeda tergantung menang/kalah
        self.background_image_id = self.canvas.create_image(
            self.BACKGROUND_POS["x"],
            self.BACKGROUND_POS["y"],
            image=self.image_cache["background"],
            anchor=self.BACKGROUND_POS["anchor"],
        )

        # Layer 2: skor akhir, hanya digambar saat kondisi menang
        if self.is_victory:
            score_label = self.SCORE_LABEL_TEMPLATE.format(score=self.score)
            self.score_text_id = self.canvas.create_text(
                self.SCORE_POS["x"],
                self.SCORE_POS["y"],
                text=score_label,
                anchor=self.SCORE_POS["anchor"],
                font=self.SCORE_FONT,
                fill=self.SCORE_TEXT_COLOR,
            )

        # Menentukan posisi tombol berdasarkan kondisi menang/kalah
        retry_pos = self.RETRY_POS_VICTORY if self.is_victory else self.RETRY_POS_DEFEAT
        menu_pos = self.MENU_POS_VICTORY if self.is_victory else self.MENU_POS_DEFEAT

        # Layer 3: tombol Retry
        self.retry_btn_id = self.canvas.create_image(
            retry_pos["x"],
            retry_pos["y"],
            image=self.image_cache["retry"],
            anchor=retry_pos["anchor"],
            tags=(self.TAG_RETRY_BTN,),
        )

        # Layer 4 (paling atas): tombol Main Menu
        self.menu_btn_id = self.canvas.create_image(
            menu_pos["x"],
            menu_pos["y"],
            image=self.image_cache["menu"],
            anchor=menu_pos["anchor"],
            tags=(self.TAG_MENU_BTN,),
        )

    def bind_events(self) -> None:
        """Menghubungkan aksi klik pada item Canvas ke method penangan masing-masing

        menggunakan Canvas.tag_bind(), sebagai pengganti command Button bawaan Tkinter.
        """
        self.canvas.tag_bind(
            self.TAG_RETRY_BTN, "<Button-1>", lambda event: self.on_retry_click()
        )
        self.canvas.tag_bind(
            self.TAG_MENU_BTN, "<Button-1>", lambda event: self.on_menu_click()
        )

    def on_retry_click(self) -> None:
        """Menangani interaksi klik pada tombol Retry dengan memanggil callback

        eksternal `on_retry_callback`.
        """
        if not self.is_interaction_enabled:
            return

        self.on_retry_callback()

    def on_menu_click(self) -> None:
        """Menangani interaksi klik pada tombol Main Menu dengan memanggil callback

        eksternal `on_menu_callback`.
        """
        if not self.is_interaction_enabled:
            return

        self.on_menu_callback()

    def cleanup(self) -> None:
        """Membersihkan resource dan interaksi milik EndScreen sebelum screen ini

        dihancurkan oleh parent controller (MainApplication).

        Saat ini EndScreen tidak memiliki timer maupun after() callback yang

        berjalan, sehingga tidak ada penjadwalan yang perlu dibatalkan. Method ini

        tetap disediakan agar seluruh screen (GameplayScreen, EndScreen, dst.)

        memiliki interface yang konsisten dan dapat dipanggil secara seragam oleh

        MainApplication tanpa perlu mengetahui detail implementasi tiap screen.
        """
        self.is_interaction_enabled = False

        if self.canvas.winfo_exists():
            self.canvas.tag_unbind(self.TAG_RETRY_BTN, "<Button-1>")
            self.canvas.tag_unbind(self.TAG_MENU_BTN, "<Button-1>")