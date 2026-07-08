# Project-games-base-on-Tkinter-Kelompok-4

"Key Matching"

game ini adalah game 2d matching game dimana player harus menyocokan kunci untuk membuka pintu berulang hingga mencapai objektif terakhir yang dimana pada saat matching player akan diberi waktu untuk menyelesaikanya jika waktu habis sebelum player bisa menyelesaikannya player akan di anggap kalah

SQL yang dipakai di project ini:
CREATE TABLE users(
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    score INT DEFAULT 0
);