import os
import tkinter as tk
from tkinter import messagebox
from typing import Callable

# Import GameEngine untuk keperluan type hinting yang eksplisit
from src.core import GameEngine


class GameplayScreen:
    """Mengelola komponen visual Tkinter berbasis Canvas, cache asset PNG, pembaruan tampilan,

    kontrol waktu (timer), serta penghentian aman pada modul gameplay.
    """

    # Path absolut menuju root project, dihitung dari lokasi file ini sendiri
    # (src/ui/gameplay_screen.py -> naik 2 folder -> root project)
    _BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    PROJECT_ROOT = os.path.dirname(os.path.dirname(_BASE_DIR))

    # Konstanta untuk manajemen path asset gambar
    ASSET_ROOT = os.path.join(PROJECT_ROOT, "assets")
    DOOR_ASSET_FOLDER = "doors"
    KEY_ASSET_FOLDER = "keys"
    UI_ASSET_FOLDER = "ui"

    # Konstanta waktu untuk interaksi UI (dalam milidetik)
    COOLDOWN_DURATION = 3000
    TIMER_INTERVAL = 1000

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

        Args:
            master (tk.Widget): Parent widget Tkinter tempat frame utama akan
              ditempel.
            engine (GameEngine): Instansiasi objek logika bisnis utama permainan.
            on_victory_callback (Callable[[int], None]): Callback eksternal saat
              menang.
            on_game_over_callback (Callable[[], None]): Callback eksternal saat
              kalah.
        """
        self.master: tk.Widget = master
        self.engine: GameEngine = engine
        self.on_victory_callback: Callable[[int], None] = on_victory_callback
        self.on_game_over_callback: Callable[[], None] = on_game_over_callback

        # Lifecycle tracker untuk Tkinter after() callbacks
        self.timer_id: str | None = None
        self.cooldown_id: str | None = None

        # State internal UI untuk penanda penalti tombol unlock
        self.is_ui_locked: bool = False

        # Guard tambahan untuk mencegah ghost callback dari event Canvas setelah cleanup()
        # dipanggil (Canvas tidak memiliki state DISABLED seperti Button).
        self.is_interaction_enabled: bool = True

        # Cache dictionary untuk menyimpan objek tk.PhotoImage di memori RAM
        self.door_cache: dict[int, tk.PhotoImage] = {}
        self.key_cache: dict[int, tk.PhotoImage] = {}
        self.ui_cache: dict[str, tk.PhotoImage] = {}

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

        # Membangun struktur interface dan memuat aset gambar ke memori RAM
        self.preload_all_assets()
        self.build_layout()
        self.bind_events()

        # [REVISI 1] GameplayScreen bertanggung jawab penuh memastikan engine siap
        # sebelum UI membaca state datanya, mencegah RuntimeError akibat urutan pintu kosong.
        self.engine.initialize_game()

        # Menampilkan state awal permainan setelah inisialisasi data engine dipastikan aman
        self.update_door_image()
        self.update_key_image()
        self.update_timer_display()

        # Memulai siklus waktu permainan secara otomatis
        self.start_timer()

    def build_layout(self) -> None:
        """Membangun posisi antar komponen menggunakan dua Canvas sesuai rancangan mockup

        (Canvas kiri untuk pintu, Canvas kanan untuk seluruh komponen kontrol).

        Seluruh komponen digambar sebagai item Canvas (create_image/create_text) agar

        transparansi alpha PNG dapat ditampilkan dengan benar.
        """
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

        # Layer 2: timer
        self.timer_text_id = self.canvas_right.create_text(
            self.TIMER_POS["x"],
            self.TIMER_POS["y"],
            text="00:00",
            anchor=self.TIMER_POS["anchor"],
            font=("Helvetica", 20, "bold"),
            fill="#1a1a1a",
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
        """Membaca aset PNG satu kali berdasarkan rentang nilai dinamis yang ditentukan

        oleh GameEngine, ditambah aset UI statis (background panel dan tombol),

        untuk menghindari hardcoded magic numbers. Seluruh aset dimuat sebagai

        tk.PhotoImage sehingga transparansi alpha PNG tetap terjaga saat digambar

        pada Canvas.

        Raises:
            FileNotFoundError: Jika berkas gambar tidak ditemukan pada lokasi path.
            tk.TclError: Jika berkas gambar korup atau tidak dapat dibaca Tkinter.
        """
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
                "rbt": "rbt.png",
                "ubt": "ubt.png",
            }
            for asset_key, filename in ui_asset_files.items():
                ui_path = os.path.join(self.ASSET_ROOT, self.UI_ASSET_FOLDER, filename)
                if not os.path.exists(ui_path):
                    raise FileNotFoundError(f"Aset UI hilang: {ui_path}")
                self.ui_cache[asset_key] = tk.PhotoImage(file=ui_path)

        except (FileNotFoundError, tk.TclError) as error:
            messagebox.showerror(
                "Error Memuat Aset",
                f"Aplikasi gagal dimulai karena masalah pada berkas aset gambar.\n\nDetail: {error}",
            )
            # [REVISI 4] Menggunakan bare raise untuk melestarikan original stack trace/traceback asli
            raise

    def bind_events(self) -> None:
        """Menghubungkan aksi klik pada item Canvas ke method penangan masing-masing

        menggunakan Canvas.tag_bind(), sebagai pengganti command Button bawaan Tkinter.
        """
        self.canvas_right.tag_bind(
            self.TAG_LEFT_BTN, "<Button-1>", lambda event: self.on_left_click()
        )
        self.canvas_right.tag_bind(
            self.TAG_RIGHT_BTN, "<Button-1>", lambda event: self.on_right_click()
        )
        self.canvas_right.tag_bind(
            self.TAG_UNLOCK_BTN, "<Button-1>", lambda event: self.on_unlock_click()
        )

    def update_door_image(self) -> None:
        """Mengganti gambar pada item Canvas pintu mengambil dari cache menggunakan

        itemconfig(), sebagai pengganti config() pada Label.
        """
        current_door_id = self.engine.get_current_door_id()
        photo = self.door_cache[current_door_id]

        self.canvas_left.itemconfig(self.door_image_id, image=photo)

    def update_key_image(self) -> None:
        """Mengganti gambar pada item Canvas kunci mengambil dari cache menggunakan

        itemconfig(), sebagai pengganti config() pada Label.
        """
        current_key_id = self.engine.current_key_id
        photo = self.key_cache[current_key_id]

        self.canvas_right.itemconfig(self.key_image_id, image=photo)

    def update_timer_display(self) -> None:
        """Mengambil sisa waktu numerik dari GameEngine lalu memperbarui teks item Canvas

        timer menjadi format waktu digital string MM:SS menggunakan itemconfig().
        """
        total_seconds = self.engine.remaining_time

        minutes = total_seconds // 60
        seconds = total_seconds % 60

        time_string = f"{minutes:02d}:{seconds:02d}"
        self.canvas_right.itemconfig(self.timer_text_id, text=time_string)

    def start_timer(self) -> None:
        """Memulai loop hitung mundur waktu permainan dan menjadwalkan siklus detik pertama."""
        self.timer_id = self.master.after(self.TIMER_INTERVAL, self.tick_timer)

    def tick_timer(self) -> None:
        """Dipanggil berkala setiap 1000 ms untuk menggerakkan logika sisa waktu permainan

        dan menangani kondisi interupsi penutupan window secara aman.
        """
        # Proteksi pencegahan exception: jika window master atau widget utama sudah hancur, hentikan siklus.
        if not self.master.winfo_exists() or not self.main_frame.winfo_exists():
            return

        is_time_valid = self.engine.tick_second()
        self.update_timer_display()

        if is_time_valid:
            self.timer_id = self.master.after(self.TIMER_INTERVAL, self.tick_timer)
        else:
            self.handle_game_over()

    def on_left_click(self) -> None:
        """Menangani interaksi klik pada tombol navigasi kiri untuk merotasi kunci mundur.

        Pemain tetap diizinkan mengganti pilihan kunci meskipun tombol unlock sedang cooldown.
        """
        if not self.is_interaction_enabled:
            return

        self.engine.rotate_key_prev()
        self.update_key_image()

    def on_right_click(self) -> None:
        """Menangani interaksi klik pada tombol navigasi kanan untuk merotasi kunci maju.

        Pemain tetap diizinkan mengganti pilihan kunci meskipun tombol unlock sedang cooldown.
        """
        if not self.is_interaction_enabled:
            return

        self.engine.rotate_key_next()
        self.update_key_image()

    def on_unlock_click(self) -> None:
        """Menangani validasi kecocokan kunci dengan pintu saat tombol Unlock diklik.

        Memicu pergantian ruangan, pemanggilan callback kemenangan, atau penalti cooldown.

        Karena tombol berbasis Canvas tidak memiliki state DISABLED seperti Button,

        pemblokiran interaksi saat cooldown maupun setelah cleanup() dilakukan melalui

        pengecekan flag is_ui_locked dan is_interaction_enabled pada event handler ini.
        """
        if not self.is_interaction_enabled:
            return

        if self.is_ui_locked:
            return

        if self.engine.is_match():
            is_game_finished = self.engine.advance_to_next_door()

            if is_game_finished:
                self.handle_victory()
            else:
                # Sesuai aturan permainan, gambar pintu diperbarui ke ruangan berikutnya,
                # namun gambar kunci sengaja tidak di-reset agar mempertahankan pilihan terakhir pemain.
                self.update_door_image()
        else:
            self.start_unlock_cooldown()

    def start_unlock_cooldown(self) -> None:
        """Mengaktifkan masa penalti pembatasan interaksi tombol unlock dan menjadwalkan

        pembukaan kembali interface setelah durasi yang ditentukan.

        Karena tombol unlock berbasis Canvas, pemblokiran klik dilakukan melalui

        flag is_ui_locked yang diperiksa pada on_unlock_click(), bukan melalui state Button.
        """
        # Proteksi idempotensi menggunakan variabel tracking cooldown_id untuk mencegah double scheduling
        if self.cooldown_id is not None:
            return

        self.is_ui_locked = True

        # Menjadwalkan pembebasan status kunci dengan Tkinter after loop
        self.cooldown_id = self.master.after(self.COOLDOWN_DURATION, self.end_unlock_cooldown)

    def end_unlock_cooldown(self) -> None:
        """Mengembalikan keadaan interface menjadi interaktif kembali dan membersihkan

        tracker id callback cooldown.
        """
        self.is_ui_locked = False
        self.cooldown_id = None

    def handle_victory(self) -> None:
        """Menutup seluruh loop interaksi internal, membersihkan tracker penjadwalan,

        dan melemparkan skor akhir menuju callback penanganan kemenangan eksternal.
        """
        self.cleanup()
        final_score = self.engine.calculate_score()
        # [REVISI 3] Eksekusi callback eksternal; GameplayScreen siap dihancurkan dari luar (parent controller)
        self.on_victory_callback(final_score)

    def handle_game_over(self) -> None:
        """Menutup seluruh loop interaksi internal, membersihkan tracker penjadwalan,

        dan memicu callback penanganan kekalahan eksternal.
        """
        self.cleanup()
        # [REVISI 3] Eksekusi callback eksternal; GameplayScreen siap dihancurkan dari luar (parent controller)
        self.on_game_over_callback()

    def cleanup(self) -> None:
        """Membatalkan seluruh antrean callback hantu (ghost callbacks) pada Tkinter loop

        yang masih aktif berjalan dan mematikan seluruh interaksi Canvas secara permanen.

        Karena item Canvas tidak memiliki state DISABLED seperti Button, pemblokiran

        interaksi dilakukan dengan menonaktifkan flag is_interaction_enabled serta

        melepas seluruh tag_bind yang masih terpasang pada tombol.
        """
        if self.timer_id is not None:
            self.master.after_cancel(self.timer_id)
            self.timer_id = None

        if self.cooldown_id is not None:
            self.master.after_cancel(self.cooldown_id)
            self.cooldown_id = None

        # [REVISI 2] Menonaktifkan interaksi kontrol saja, tidak melakukan destroy widget di sini.
        self.is_interaction_enabled = False

        if self.canvas_right.winfo_exists():
            self.canvas_right.tag_unbind(self.TAG_LEFT_BTN, "<Button-1>")
            self.canvas_right.tag_unbind(self.TAG_RIGHT_BTN, "<Button-1>")
            self.canvas_right.tag_unbind(self.TAG_UNLOCK_BTN, "<Button-1>")