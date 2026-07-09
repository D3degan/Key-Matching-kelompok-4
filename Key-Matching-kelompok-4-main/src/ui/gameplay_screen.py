import os
import tkinter as tk
from tkinter import messagebox
from typing import Callable

# Inisialisasi pygame mixer secara aman untuk audio yang ringan
try:
    import pygame
    pygame.mixer.init()
    PYGAME_AVAILABLE = True
except Exception:
    PYGAME_AVAILABLE = False

# Import GameEngine untuk keperluan type hinting yang eksplisit
from src.core import GameEngine


class GameplayScreen:
    """Mengelola komponen visual Tkinter berbasis Canvas, cache asset PNG, pembaruan tampilan,

    kontrol waktu (timer), serta penghentian aman pada modul gameplay.
    """

    # Path absolut menuju root project, dihitung dari lokasi file ini sendiri
    _BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    PROJECT_ROOT = os.path.dirname(os.path.dirname(_BASE_DIR))

    # Konstanta untuk manajemen path asset gambar dan sfx
    ASSET_ROOT = os.path.join(PROJECT_ROOT, "assets")
    DOOR_ASSET_FOLDER = "doors"
    KEY_ASSET_FOLDER = "keys"
    UI_ASSET_FOLDER = "ui"
    SFX_ASSET_FOLDER = "sfx"

    # Pemetaan nama SFX ke nama file fisik .wav demi kemudahan perawatan
    SFX_FILES = {
        "nbt": "nbt.wav",
        "ubtr": "ubtr.wav",
        "ubtff": "ubtff.wav",
    }

    # Konstanta waktu untuk interaksi UI (dalam milidetik)
    COOLDOWN_DURATION = 3000
    TIMER_INTERVAL = 1000
    TRANSITION_DELAY = 500

    # Konstanta ukuran window & canvas sesuai mockup (640 x 480)
    WINDOW_WIDTH = 640
    WINDOW_HEIGHT = 480
    CANVAS_LEFT_WIDTH = 284
    CANVAS_RIGHT_WIDTH = 356
    CANVAS_HEIGHT = 480
    PANEL_BG_COLOR = "#ffffff"

    # Konstanta posisi komponen pada canvas kiri (koordinat lokal 284x480)
    DOOR_IMAGE_POS = {"x": 0, "y": 0, "anchor": "nw"}

    # Konstanta posisi komponen pada canvas kanan (koordinat lokal 356x480)
    PANEL_BG_POS = {"x": 0, "y": 0, "anchor": "nw"}
    TIMER_POS = {"x": 336, "y": 20, "anchor": "ne"}
    KEY_IMAGE_POS = {"x": 178, "y": 260, "anchor": "center"}
    LEFT_BTN_POS = {"x": 88, "y": 330, "anchor": "center"}
    RIGHT_BTN_POS = {"x": 268, "y": 330, "anchor": "center"}
    UNLOCK_BTN_POS = {"x": 178, "y": 432, "anchor": "center"}

    # Tag khusus untuk item Canvas yang bersifat interaktif (dipakai oleh tag_bind)
    TAG_LEFT_BTN = "btn_left"
    TAG_RIGHT_BTN = "btn_right"
    TAG_UNLOCK_BTN = "btn_unlock"

    def __init__(
        self,
        master: tk.Widget,
        engine: GameEngine,
        on_victory_callback: Callable[[int], None],
        on_game_over_callback: Callable[[], None],
    ) -> None:
        """Inisialisasi komponen screen, cache, menyiapkan layout Canvas, menghubungkan

        event handler, menampilkan keadaan awal, dan langsung memulai timer permainan.
        """
        self.master: tk.Widget = master
        self.engine: GameEngine = engine
        self.on_victory_callback: Callable[[int], None] = on_victory_callback
        self.on_game_over_callback: Callable[[], None] = on_game_over_callback

        # Lifecycle tracker untuk Tkinter after() callbacks
        self.timer_id: str | None = None
        self.cooldown_id: str | None = None
        self.transition_id: str | None = None

        # State internal UI untuk penanda penalti tombol unlock
        self.is_ui_locked: bool = False

        # Guard tambahan untuk mencegah ghost callback dari event Canvas setelah cleanup()
        self.is_interaction_enabled: bool = True

        # Cache dictionary untuk menyimpan objek tk.PhotoImage di memori RAM
        self.door_cache: dict[int, tk.PhotoImage] = {}
        self.key_cache: dict[int, tk.PhotoImage] = {}
        self.ui_cache: dict[str, tk.PhotoImage] = {}

        # Cache untuk objek pygame Sound
        self.sfx_cache: dict[str, any] = {}

        # Deklarasi referensi widget utama
        self.main_frame: tk.Frame
        self.canvas_left: tk.Canvas
        self.canvas_right: tk.Canvas

        # Deklarasi referensi ID item Canvas yang perlu diperbarui atau diberi event
        self.door_image_id: int
        self.panel_bg_id: int
        self.timer_text_id: int
        self.key_image_id: int
        self.left_btn_id: int
        self.right_btn_id: int
        self.unlock_btn_id: int

        # Membangun struktur interface dan memuat aset gambar serta suara ke memori RAM
        self.preload_all_assets()
        self.build_layout()
        self.bind_events()

        # GameplayScreen bertanggung jawab penuh memastikan engine siap
        self.engine.initialize_game()

        # Menampilkan state awal permainan setelah inisialisasi data engine dipastikan aman
        self.update_door_image()
        self.update_key_image()
        self.update_timer_display()

        # Memulai siklus waktu permainan secara otomatis
        self.start_timer()

    def build_layout(self) -> None:
        """Membangun posisi antar komponen menggunakan dua Canvas sesuai rancangan mockup."""
        self.main_frame = tk.Frame(
            self.master,
            width=self.WINDOW_WIDTH,
            height=self.WINDOW_HEIGHT,
        )
        self.main_frame.place(x=0, y=0, width=self.WINDOW_WIDTH, height=self.WINDOW_HEIGHT)
        self.main_frame.pack_propagate(False)

        # ---------------------------------------------------------------------
        # CANVAS KIRI: hanya menampilkan gambar pintu
        # ---------------------------------------------------------------------
        self.canvas_left = tk.Canvas(
            self.main_frame,
            width=self.CANVAS_LEFT_WIDTH,
            height=self.CANVAS_HEIGHT,
            highlightthickness=0,
            borderwidth=0,
        )
        self.canvas_left.place(x=0, y=0, width=self.CANVAS_LEFT_WIDTH, height=self.CANVAS_HEIGHT)

        self.door_image_id = self.canvas_left.create_image(
            self.DOOR_IMAGE_POS["x"],
            self.DOOR_IMAGE_POS["y"],
            image=None,
            anchor=self.DOOR_IMAGE_POS["anchor"],
        )

        # ---------------------------------------------------------------------
        # CANVAS KANAN: seluruh komponen kontrol (background, timer, kunci, tombol)
        # ---------------------------------------------------------------------
        self.canvas_right = tk.Canvas(
            self.main_frame,
            width=self.CANVAS_RIGHT_WIDTH,
            height=self.CANVAS_HEIGHT,
            highlightthickness=0,
            borderwidth=0,
            bg=self.PANEL_BG_COLOR,
        )
        self.canvas_right.place(
            x=self.CANVAS_LEFT_WIDTH,
            y=0,
            width=self.CANVAS_RIGHT_WIDTH,
            height=self.CANVAS_HEIGHT,
        )

        # Layer 1 (paling bawah): background panel kanan
        self.panel_bg_id = self.canvas_right.create_image(
            self.PANEL_BG_POS["x"],
            self.PANEL_BG_POS["y"],
            image=self.ui_cache["rbg"],
            anchor=self.PANEL_BG_POS["anchor"],
        )

        # Layer 2: timer (Warna diubah menjadi #AE0000)
        self.timer_text_id = self.canvas_right.create_text(
            self.TIMER_POS["x"],
            self.TIMER_POS["y"],
            text="00:00",
            anchor=self.TIMER_POS["anchor"],
            font=("Helvetica", 20, "bold"),
            fill="#AE0000",
        )

        # Layer 3: gambar kunci
        self.key_image_id = self.canvas_right.create_image(
            self.KEY_IMAGE_POS["x"],
            self.KEY_IMAGE_POS["y"],
            image=None,
            anchor=self.KEY_IMAGE_POS["anchor"],
        )

        # Layer 4: tombol kiri
        self.left_btn_id = self.canvas_right.create_image(
            self.LEFT_BTN_POS["x"],
            self.LEFT_BTN_POS["y"],
            image=self.ui_cache["lbt"],
            anchor=self.LEFT_BTN_POS["anchor"],
            tags=(self.TAG_LEFT_BTN,),
        )

        # Layer 5: tombol kanan
        self.right_btn_id = self.canvas_right.create_image(
            self.RIGHT_BTN_POS["x"],
            self.RIGHT_BTN_POS["y"],
            image=self.ui_cache["rbt"],
            anchor=self.RIGHT_BTN_POS["anchor"],
            tags=(self.TAG_RIGHT_BTN,),
        )

        # Layer 6 (paling atas): tombol unlock
        self.unlock_btn_id = self.canvas_right.create_image(
            self.UNLOCK_BTN_POS["x"],
            self.UNLOCK_BTN_POS["y"],
            image=self.ui_cache["ubt"],
            anchor=self.UNLOCK_BTN_POS["anchor"],
            tags=(self.TAG_UNLOCK_BTN,),
        )

    def preload_all_assets(self) -> None:
        """Membaca aset Gambar (PNG) dan SFX (Audio WAV) satu kali ke dalam memory RAM."""
        try:
            start_id = GameEngine.MIN_KEY_ID
            end_id = GameEngine.MAX_KEY_ID + 1

            for i in range(start_id, end_id):
                door_path = os.path.join(self.ASSET_ROOT, self.DOOR_ASSET_FOLDER, f"{i}d.png")
                if not os.path.exists(door_path):
                    raise FileNotFoundError(f"Aset pintu hilang: {door_path}")
                self.door_cache[i] = tk.PhotoImage(file=door_path)

            for i in range(start_id, end_id):
                key_path = os.path.join(self.ASSET_ROOT, self.KEY_ASSET_FOLDER, f"{i}k.png")
                if not os.path.exists(key_path):
                    raise FileNotFoundError(f"Aset kunci hilang: {key_path}")
                self.key_cache[i] = tk.PhotoImage(file=key_path)

            ui_asset_files = {
                "rbg": "rbg.png",
                "lbt": "lbt.png",
                "lbt_h": "lbth.png",
                "rbt": "rbt.png",
                "rbt_h": "rbth.png",
                "ubt": "ubt.png",
                "ubt_h": "ubth.png",
                "ubt_f": "ubtf.png",
            }
            for asset_key, filename in ui_asset_files.items():
                ui_path = os.path.join(self.ASSET_ROOT, self.UI_ASSET_FOLDER, filename)
                if not os.path.exists(ui_path):
                    raise FileNotFoundError(f"Aset UI hilang: {ui_path}")
                self.ui_cache[asset_key] = tk.PhotoImage(file=ui_path)

            # Memuat aset SFX secara fleksibel menggunakan dictionary pemetaan file .wav
            if PYGAME_AVAILABLE:
                for sound_name, filename in self.SFX_FILES.items():
                    sfx_path = os.path.join(
                        self.ASSET_ROOT,
                        self.SFX_ASSET_FOLDER,
                        filename,
                    )
                    try:
                        if os.path.exists(sfx_path):
                            self.sfx_cache[sound_name] = pygame.mixer.Sound(sfx_path)
                    except Exception:
                        # Mencegah crash jika terjadi galat saat instansiasi Sound objek individual
                        pass

        except (FileNotFoundError, tk.TclError) as error:
            messagebox.showerror(
                "Error Memuat Aset",
                f"Aplikasi gagal dimulai karena masalah pada berkas aset.\n\nDetail: {error}",
            )
            raise

    def play_sfx(self, sfx_name: str) -> None:
        """Helper method tunggal untuk memutar sound effect secara aman tanpa membuat aplikasi crash."""
        if PYGAME_AVAILABLE and sfx_name in self.sfx_cache:
            try:
                self.sfx_cache[sfx_name].play()
            except Exception:
                # Menangkap error runtime pemutaran audio agar tidak menghentikan jalannya game
                pass

    def bind_events(self) -> None:
        """Menghubungkan aksi klik dan efek hover mouse pada item Canvas."""
        # Event Klik Kiri Mouse
        self.canvas_right.tag_bind(
            self.TAG_LEFT_BTN, "<Button-1>", lambda event: self.on_left_click()
        )
        self.canvas_right.tag_bind(
            self.TAG_RIGHT_BTN, "<Button-1>", lambda event: self.on_right_click()
        )
        self.canvas_right.tag_bind(
            self.TAG_UNLOCK_BTN, "<Button-1>", lambda event: self.on_unlock_click()
        )

        # Event Hover Entry (<Enter>)
        self.canvas_right.tag_bind(
            self.TAG_LEFT_BTN, "<Enter>", lambda event: self.on_button_hover(self.left_btn_id, "lbt_h")
        )
        self.canvas_right.tag_bind(
            self.TAG_RIGHT_BTN, "<Enter>", lambda event: self.on_button_hover(self.right_btn_id, "rbt_h")
        )
        self.canvas_right.tag_bind(
            self.TAG_UNLOCK_BTN, "<Enter>", lambda event: self.on_unlock_hover_enter()
        )

        # Event Hover Leave (<Leave>)
        self.canvas_right.tag_bind(
            self.TAG_LEFT_BTN, "<Leave>", lambda event: self.on_button_hover(self.left_btn_id, "lbt")
        )
        self.canvas_right.tag_bind(
            self.TAG_RIGHT_BTN, "<Leave>", lambda event: self.on_button_hover(self.right_btn_id, "rbt")
        )
        self.canvas_right.tag_bind(
            self.TAG_UNLOCK_BTN, "<Leave>", lambda event: self.on_unlock_hover_leave()
        )

    def on_button_hover(self, canvas_item_id: int, asset_key: str) -> None:
        """Mengganti state gambar tombol saat dilewati mouse (efek hover global)."""
        if not self.is_interaction_enabled:
            return
        self.canvas_right.itemconfig(canvas_item_id, image=self.ui_cache[asset_key])

    def on_unlock_hover_enter(self) -> None:
        """Mengaktifkan hover eksklusif tombol unlock hanya saat tidak dalam masa cooldown penalti."""
        if not self.is_interaction_enabled or self.is_ui_locked:
            return
        self.canvas_right.itemconfig(self.unlock_btn_id, image=self.ui_cache["ubt_h"])

    def on_unlock_hover_leave(self) -> None:
        """Mengembalikan asset normal tombol unlock saat kursor menjauh (menyesuaikan status lock)."""
        if not self.is_interaction_enabled:
            return
        if self.is_ui_locked:
            self.canvas_right.itemconfig(self.unlock_btn_id, image=self.ui_cache["ubt_f"])
        else:
            self.canvas_right.itemconfig(self.unlock_btn_id, image=self.ui_cache["ubt"])

    def update_door_image(self) -> None:
        """Mengganti gambar pada item Canvas pintu mengambil dari cache."""
        current_door_id = self.engine.get_current_door_id()
        photo = self.door_cache[current_door_id]
        self.canvas_left.itemconfig(self.door_image_id, image=photo)

    def update_key_image(self) -> None:
        """Mengganti gambar pada item Canvas kunci mengambil dari cache."""
        current_key_id = self.engine.current_key_id
        photo = self.key_cache[current_key_id]
        self.canvas_right.itemconfig(self.key_image_id, image=photo)

    def update_timer_display(self) -> None:
        """Mengambil sisa waktu numerik dari GameEngine lalu memperbarui teks digital."""
        total_seconds = self.engine.remaining_time
        minutes = total_seconds // 60
        seconds = total_seconds % 60
        time_string = f"{minutes:02d}:{seconds:02d}"
        self.canvas_right.itemconfig(self.timer_text_id, text=time_string)

    def start_timer(self) -> None:
        """Memulai loop hitung mundur waktu permainan dan menjadwalkan siklus detik pertama."""
        self.timer_id = self.master.after(self.TIMER_INTERVAL, self.tick_timer)

    def tick_timer(self) -> None:
        """Dipanggil berkala setiap 1000 ms untuk menggerakkan logika sisa waktu permainan."""
        if not self.master.winfo_exists() or not self.main_frame.winfo_exists():
            return

        is_time_valid = self.engine.tick_second()
        self.update_timer_display()

        if is_time_valid:
            self.timer_id = self.master.after(self.TIMER_INTERVAL, self.tick_timer)
        else:
            self.handle_game_over()

    def on_left_click(self) -> None:
        """Menangani interaksi klik pada tombol navigasi kiri."""
        if not self.is_interaction_enabled:
            return
        self.play_sfx("nbt")
        self.engine.rotate_key_prev()
        self.update_key_image()

    def on_right_click(self) -> None:
        """Menangani interaksi klik pada tombol navigasi kanan."""
        if not self.is_interaction_enabled:
            return
        self.play_sfx("nbt")
        self.engine.rotate_key_next()
        self.update_key_image()

    def on_unlock_click(self) -> None:
        """Menangani validasi kecocokan kunci dengan pintu saat tombol Unlock diklik."""
        if not self.is_interaction_enabled or self.is_ui_locked:
            return

        if self.engine.is_match():
            self.play_sfx("ubtr")
            is_game_finished = self.engine.advance_to_next_door()
            
            # Berikan penundaan 500ms non-blocking agar SFX ubtr terdengar jelas sampai selesai
            if is_game_finished:
                self.transition_id = self.master.after(self.TRANSITION_DELAY, self.handle_victory)
            else:
                self.transition_id = self.master.after(self.TRANSITION_DELAY, self.deferred_door_update)
        else:
            self.play_sfx("ubtff")
            self.start_unlock_cooldown()

    def deferred_door_update(self) -> None:
        """Melakukan update pintu secara bertahap setelah penundaan animasi/sfx selesai."""
        if not self.master.winfo_exists() or not self.main_frame.winfo_exists():
            return
        self.update_door_image()

    def start_unlock_cooldown(self) -> None:
        """Mengaktifkan masa penalti pembatasan interaksi tombol unlock."""
        if self.cooldown_id is not None:
            return

        self.is_ui_locked = True
        self.canvas_right.itemconfig(self.unlock_btn_id, image=self.ui_cache["ubt_f"])
        self.cooldown_id = self.master.after(self.COOLDOWN_DURATION, self.end_unlock_cooldown)

    def end_unlock_cooldown(self) -> None:
        """Mengembalikan keadaan interface menjadi interaktif kembali dan mereset tombol unlock."""
        self.is_ui_locked = False
        self.cooldown_id = None
        self.canvas_right.itemconfig(self.unlock_btn_id, image=self.ui_cache["ubt"])

    def handle_victory(self) -> None:
        """Menutup seluruh loop interaksi internal, dan melempar nilai ke callback victory."""
        self.cleanup()
        final_score = self.engine.calculate_score()
        self.on_victory_callback(final_score)

    def handle_game_over(self) -> None:
        """Menutup seluruh loop interaksi internal, dan memicu callback game over."""
        self.cleanup()
        self.on_game_over_callback()

    def cleanup(self) -> None:
        """Membatalkan seluruh antrean callback hantu pada Tkinter loop."""
        if self.timer_id is not None:
            self.master.after_cancel(self.timer_id)
            self.timer_id = None

        if self.cooldown_id is not None:
            self.master.after_cancel(self.cooldown_id)
            self.cooldown_id = None

        if self.transition_id is not None:
            self.master.after_cancel(self.transition_id)
            self.transition_id = None

        self.is_interaction_enabled = False

        if self.canvas_right.winfo_exists():
            self.canvas_right.tag_unbind(self.TAG_LEFT_BTN, "<Button-1>")
            self.canvas_right.tag_unbind(self.TAG_RIGHT_BTN, "<Button-1>")
            self.canvas_right.tag_unbind(self.TAG_UNLOCK_BTN, "<Button-1>")