# Project-games-base-on-Tkinter-Kelompok-4

"Key Matching"

game ini adalah game 2d matching game dimana player harus menyocokan kunci untuk membuka pintu berulang hingga mencapai objektif terakhir yang dimana pada saat matching player akan diberi waktu untuk menyelesaikanya jika waktu habis sebelum player bisa menyelesaikannya player akan di anggap kalah
(Clue bisa dilihat dari bentuk yang ada di pintu untuk dicocokan dengan kunci yang ada)

Library yang perlu di install:
pip install pygame 
pip install mysqlconnnector

SQL yang dipakai di project ini:
CREATE TABLE users(
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    score INT DEFAULT 0
);

RUN GAMENYA DARI FILE "PLAY" !

Alur run di applikasinya
play.py -> login.py (Login/Register) -> menuutama.py (Main Menu)
    -> main.py (gameplay) -> balik lagi ke menuutama.py

