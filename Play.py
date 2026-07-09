"""
Entry point tunggal buat jalanin seluruh aplikasi dari awal.

Jangan run login.py, menuutama.py, atau main.py langsung satu-satu.
run file ini aja buat mulai dari layar Login.

Alur:
    play.py -> login.py (Login/Register) -> menuutama.py (Main Menu)
    -> main.py (gameplay, punya temen) -> balik lagi ke menuutama.py
"""

import os
import sys
import pygame

import login


if getattr(sys, "frozen", False):
    BASE_DIR = sys._MEIPASS
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

BGM_FOLDER = os.path.join(BASE_DIR, "bgm")
BGM_FILE = "theme.mp3"  


def play_background_music():
    bgm_path = os.path.join(BGM_FOLDER, BGM_FILE)

    if not os.path.exists(bgm_path):
        print(f"BGM tidak ditemukan, dilewati: {bgm_path}")
        return

    try:
        pygame.mixer.init()
        pygame.mixer.music.load(bgm_path)
        pygame.mixer.music.set_volume(0.5) 
        pygame.mixer.music.play(-1)  
    except pygame.error as e:
        print(f"Gagal memutar BGM: {e}")


if __name__ == "__main__":
    play_background_music()
    login.show_login_window()