import random
from typing import List


class GameEngine:
    """Mengelola state logika murni dan aturan bisnis permainan puzzle mencocokkan kunci dan pintu.

    Class ini bersifat independen dari interface pengguna (GUI).
    """

    # Konstanta untuk menghindari magic numbers pada penentuan ID kunci dan batas waktu minimal
    MIN_KEY_ID = 1
    MAX_KEY_ID = 10
    TIME_EXHAUSTED = 0

    def __init__(self, total_duration: int) -> None:
        """Inisialisasi awal objek GameEngine dengan validasi durasi waktu permainan.

        Args:
            total_duration (int): Total durasi waktu permainan dalam satuan
              detik.

        Raises:
            ValueError: Jika total_duration bernilai kurang dari atau sama dengan
            0.
        """
        if total_duration <= self.TIME_EXHAUSTED:
            raise ValueError(
                f"Durasi permainan harus lebih besar dari {self.TIME_EXHAUSTED} detik. "
                f"Input yang diterima: {total_duration}"
            )

        self.total_duration: int = total_duration
        self.remaining_time: int = total_duration
        self.door_sequence: List[int] = []
        self.current_door_index: int = 0
        self.current_key_id: int = self.MIN_KEY_ID

    def initialize_game(self) -> None:
        """Menyiapkan state permainan baru dengan mengacak urutan pintu dan

        mengatur ulang indeks permainan serta pilihan kunci.
        """
        self.remaining_time = self.total_duration
        self.current_door_index = 0
        self.current_key_id = self.MIN_KEY_ID

        # Membuat urutan pintu 1-10 lalu mengacaknya tepat satu kali
        self.door_sequence = list(range(self.MIN_KEY_ID, self.MAX_KEY_ID + 1))
        random.shuffle(self.door_sequence)

    def get_current_door_id(self) -> int:
        """Mendapatkan nomor/ID pintu yang sedang dihadapi pemain saat ini.

        Returns:
            int: ID nomor pintu (1 sampai 10) berdasarkan urutan acak.

        Raises:
            RuntimeError: Jika urutan pintu belum diinisialisasi atau indeks
                          permainan berada di luar batas urutan pintu aktual.
        """
        if not self.door_sequence:
            raise RuntimeError(
                "Permainan belum diinisialisasi. Panggil initialize_game() terlebih dahulu."
            )

        if self.current_door_index >= len(self.door_sequence):
            raise RuntimeError(
                f"Indeks permainan saat ini ({self.current_door_index}) berada di luar batas "
                f"total urutan pintu aktual ({len(self.door_sequence)})."
            )

        return self.door_sequence[self.current_door_index]

    def rotate_key_next(self) -> None:
        """Mengubah pilihan ID kunci ke nomor berikutnya secara circular (1 -> 2

        ... 10 -> 1).
        """
        if self.current_key_id >= self.MAX_KEY_ID:
            self.current_key_id = self.MIN_KEY_ID
        else:
            self.current_key_id += 1

    def rotate_key_prev(self) -> None:
        """Mengubah pilihan ID kunci ke nomor sebelumnya secara circular (1 ->

        10 ... 2 -> 1).
        """
        if self.current_key_id <= self.MIN_KEY_ID:
            self.current_key_id = self.MAX_KEY_ID
        else:
            self.current_key_id -= 1

    def is_match(self) -> bool:
        """Memeriksa apakah kunci yang dipilih saat ini cocok dengan pintu yang

        sedang dihadapi.

        Returns:
            bool: True jika ID kunci sama dengan ID pintu aktif, sebaliknya
            False.
        """
        return self.current_key_id == self.get_current_door_id()

    def advance_to_next_door(self) -> bool:
        """Menaikkan progres permainan ke pintu berikutnya jika kunci berhasil

        dicocokkan. Menggunakan panjang aktual dari door_sequence untuk

        pemeriksaan batas akhir permainan.

        Returns:
            bool: True jika seluruh pintu berhasil dibuka (kondisi menang),
                  False jika masih ada pintu tersisa yang harus dibuka.
        """
        self.current_door_index += 1

        # Menggunakan panjang aktual dari urutan pintu (dynamic sequence check)
        if self.current_door_index >= len(self.door_sequence):
            return True
        return False

    def tick_second(self) -> bool:
        """Mengurangi sisa waktu permainan sebanyak satu detik dan mengunci nilai

        minimum waktu pada angka 0 jika habis.

        Returns:
            bool: True jika waktu masih tersedia,
                  False jika waktu telah habis (menyentuh angka 0).
        """
        if self.remaining_time <= self.TIME_EXHAUSTED:
            return False

        self.remaining_time -= 1

        if self.remaining_time == self.TIME_EXHAUSTED:
            return False
        return True

    def calculate_score(self) -> int:
        """Menghitung skor akhir permainan berdasarkan sisa waktu yang tersedia.

        Returns:
            int: Skor akhir yang setara dengan remaining_time.
        """
        return self.remaining_time