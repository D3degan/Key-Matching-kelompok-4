import os
import tkinter as tk
from typing import Callable, Optional

# Inisialisasi pygame mixer secara aman untuk audio yang ringan
try:
    import pygame
    pygame.mixer.init()
    PYGAME_AVAILABLE = True
except Exception:
    PYGAME_AVAILABLE = False


class EndScreen:
    """Mengelola tampilan akhir permainan (menang maupun kalah) menggunakan Canvas.

    Class ini bersifat generik: satu implementasi dipakai untuk kedua kondisi
    (kemenangan dan kekalahan), dibedakan hanya melalui flag `is_victory` yang
    menentukan background yang ditampilkan dan apakah skor akhir ikut digambar.

    Class ini tidak berinteraksi dengan GameEngine maupun GameplayScreen sama
    sekali; seluruh data yang dibutuhkan (status menang/kalah dan skor akhir)
    diterima langsung melalui constructor.
    """

    # Path absolut menuju root project, dihitung dari lokasi file ini sendiri
    # (src/ui/end_screen.py -> naik 2 folder -> root project)
    _BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    PROJECT_ROOT = os.path.dirname(os.path.dirname(_BASE_DIR))

    # Konstanta untuk manajemen path asset gambar dan sfx
    ASSET_ROOT = os.path.join(PROJECT_ROOT, "assets")
    UI_ASSET_FOLDER = "ui"
    SFX_ASSET_FOLDER = "sfx"

    # Nama berkas asset normal
    VICTORY_BG_FILE = "wbg.png"
    DEFEAT_BG_FILE = "lbg.png"
    MENU_BTN_FILE = "mbt.png"
    RETRY_BTN_FILE = "rtbt.png"

    # Nama berkas asset hover baru
    MENU_HOVER_FILE = "mbth.png"
    RETRY_HOVER_FILE = "rtbth.png"

    # Berkas efek suara klik
    CLICK_SFX_FILE = "ubtff.wav"

    # Konstanta ukuran window, tetap konsisten dengan screen lain (640 x 480)
    WINDOW_WIDTH = 640
    WINDOW_HEIGHT = 480

    # Konstanta posisi background (memenuhi seluruh Canvas)
    BACKGROUND_POS = {"x": 0, "y": 0, "anchor": "nw"}

    # Konstanta posisi skor, warna diperbarui menjadi #AE0000
    SCORE_FONT = ("Helvetica", 28, "bold")
    SCORE_TEXT_COLOR = "#AE0000"
    SCORE_LABEL_TEMPLATE = "Score: {score}"

    # Konstanta posisi komponen saat kondisi MENANG (Layout digeser ke kiri sekitar 30-35% window)
    VICTORY_X_ALIGN = int(WINDOW_WIDTH * 0.33)  # Posisi horizontal di ~33% lebar layar
    SCORE_POS_VICTORY = {"x": VICTORY_X_ALIGN, "y": 110, "anchor": "center"}
    RETRY_POS_VICTORY = {"x": VICTORY_X_ALIGN, "y": 280, "anchor": "center"}
    MENU_POS_VICTORY = {"x": VICTORY_X_ALIGN, "y": 350, "anchor": "center"}

    # Konstanta posisi komponen saat kondisi KALAH (Mendatar di tengah sesuai posisi bawaan asli)
    DEFEAT_X_ALIGN = WINDOW_WIDTH // 2
    RETRY_POS_DEFEAT = {"x": DEFEAT_X_ALIGN, "y": 240, "anchor": "center"}
    MENU_POS_DEFEAT = {"x": DEFEAT_X_ALIGN, "y": 310, "anchor": "center"}

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
        event klik tombol Retry dan Main Menu beserta hover dan audio.
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

        # Cache objek audio suara klik tombol
        self.click_sound: any = None

        # Deklarasi referensi widget utama
        self.main_frame: tk.Frame
        self.canvas: tk.Canvas

        # Deklarasi referensi ID item Canvas
        self.background_image_id: int
        self.score_text_id: Optional[int] = None
        self.retry_btn_id: int
        self.menu_btn_id: int

        # Membangun struktur interface dan memuat aset gambar serta suara ke memori RAM
        self.preload_all_assets()
        self.build_layout()
        self.bind_events()

    def preload_all_assets(self) -> None:
        """Membaca aset PNG (background, normal, dan versi hover) serta berkas audio .wav

        ke dalam memory RAM satu kali saja tanpa muat ulang dinamis.
        """
        background_file = self.VICTORY_BG_FILE if self.is_victory else self.DEFEAT_BG_FILE

        # Daftar seluruh asset yang harus dipreload ke memori RAM
        asset_files = {
            "background": background_file,
            "retry_normal": self.RETRY_BTN_FILE,
            "menu_normal": self.MENU_BTN_FILE,
            "retry_hover": self.RETRY_HOVER_FILE,
            "menu_hover": self.MENU_HOVER_FILE,
        }

        try:
            for asset_key, filename in asset_files.items():
                asset_path = os.path.join(self.ASSET_ROOT, self.UI_ASSET_FOLDER, filename)
                if not os.path.exists(asset_path):
                    raise FileNotFoundError(f"Aset UI hilang: {asset_path}")
                self.image_cache[asset_key] = tk.PhotoImage(file=asset_path)

            # Memuat aset audio klik tombol secara aman
            if PYGAME_AVAILABLE:
                sfx_path = os.path.join(self.ASSET_ROOT, self.SFX_ASSET_FOLDER, self.CLICK_SFX_FILE)
                try:
                    if os.path.exists(sfx_path):
                        self.click_sound = pygame.mixer.Sound(sfx_path)
                except Exception:
                    pass

        except (FileNotFoundError, tk.TclError) as error:
            messagebox.showerror(
                "Error Memuat Aset",
                f"Aplikasi gagal dimulai karena masalah pada berkas aset.\n\nDetail: {error}",
            )
            raise

    def play_click_sound(self) -> None:
        """Helper method internal untuk memutar suara klik secara aman tanpa membuat aplikasi crash."""
        if PYGAME_AVAILABLE and self.click_sound is not None:
            try:
                self.click_sound.play()
            except Exception:
                pass

    def build_layout(self) -> None:
        """Membangun layout Canvas tunggal yang memenuhi seluruh window, lalu menggambar

        background, skor, serta tombol Retry dan Main Menu sesuai kondisi layout state.
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

        # Menentukan posisi komponen berdasarkan state kemenangan
        if self.is_victory:
            score_pos = self.SCORE_POS_VICTORY
            retry_pos = self.RETRY_POS_VICTORY
            menu_pos = self.MENU_POS_VICTORY

            # Layer 2: skor akhir, hanya digambar saat kondisi menang dengan warna diperbarui (#AE0000)
            score_label = self.SCORE_LABEL_TEMPLATE.format(score=self.score)
            self.score_text_id = self.canvas.create_text(
                score_pos["x"],
                score_pos["y"],
                text=score_label,
                anchor=score_pos["anchor"],
                font=self.SCORE_FONT,
                fill=self.SCORE_TEXT_COLOR,
            )
        else:
            retry_pos = self.RETRY_POS_DEFEAT
            menu_pos = self.MENU_POS_DEFEAT

        # Layer 3: tombol Retry
        self.retry_btn_id = self.canvas.create_image(
            retry_pos["x"],
            retry_pos["y"],
            image=self.image_cache["retry_normal"],
            anchor=retry_pos["anchor"],
            tags=(self.TAG_RETRY_BTN,),
        )

        # Layer 4 (paling atas): tombol Main Menu
        self.menu_btn_id = self.canvas.create_image(
            menu_pos["x"],
            menu_pos["y"],
            image=self.image_cache["menu_normal"],
            anchor=menu_pos["anchor"],
            tags=(self.TAG_MENU_BTN,),
        )

    def bind_events(self) -> None:
        """Menghubungkan aksi klik dan efek hover mouse pada item Canvas."""
        # Event Klik Kiri Mouse
        self.canvas.tag_bind(
            self.TAG_RETRY_BTN, "<Button-1>", lambda event: self.on_retry_click()
        )
        self.canvas.tag_bind(
            self.TAG_MENU_BTN, "<Button-1>", lambda event: self.on_menu_click()
        )

        # Event Hover Entry (<Enter>) untuk mengganti aset gambar ke versi hover
        self.canvas.tag_bind(
            self.TAG_RETRY_BTN, "<Enter>", lambda event: self.on_button_hover(self.retry_btn_id, "retry_hover")
        )
        self.canvas.tag_bind(
            self.TAG_MENU_BTN, "<Enter>", lambda event: self.on_button_hover(self.menu_btn_id, "menu_hover")
        )

        # Event Hover Leave (<Leave>) untuk mengembalikan aset gambar ke versi normal
        self.canvas.tag_bind(
            self.TAG_RETRY_BTN, "<Leave>", lambda event: self.on_button_hover(self.retry_btn_id, "retry_normal")
        )
        self.canvas.tag_bind(
            self.TAG_MENU_BTN, "<Leave>", lambda event: self.on_button_hover(self.menu_btn_id, "menu_normal")
        )

    def on_button_hover(self, canvas_item_id: int, cache_key: str) -> None:
        """Mengganti state gambar tombol saat dilewati mouse (efek hover global)."""
        if not self.is_interaction_enabled:
            return
        self.canvas.itemconfig(canvas_item_id, image=self.image_cache[cache_key])

    def on_retry_click(self) -> None:
        """Menangani klik tombol Retry dengan memutar sfx ubtff.wav secara langsung

        diikuti pengeksekusian callback eksternal asli.
        """
        if not self.is_interaction_enabled:
            return

        self.play_click_sound()
        self.on_retry_callback()

    def on_menu_click(self) -> None:
        """Menangani klik tombol Main Menu dengan memputar sfx ubtff.wav secara langsung

        diikuti pengeksekusian callback eksternal asli.
        """
        if not self.is_interaction_enabled:
            return

        self.play_click_sound()
        self.on_menu_callback()

    def cleanup(self) -> None:
        """Membersihkan resource dan mematikan seluruh interaksi tag_bind milik EndScreen."""
        self.is_interaction_enabled = False

        if self.canvas.winfo_exists():
            self.canvas.tag_unbind(self.TAG_RETRY_BTN, "<Button-1>")
            self.canvas.tag_unbind(self.TAG_MENU_BTN, "<Button-1>")
            
            self.canvas.tag_unbind(self.TAG_RETRY_BTN, "<Enter>")
            self.canvas.tag_unbind(self.TAG_MENU_BTN, "<Enter>")
            
            self.canvas.tag_unbind(self.TAG_RETRY_BTN, "<Leave>")
            self.canvas.tag_unbind(self.TAG_MENU_BTN, "<Leave>")