import cv2
from cvzone.HandTrackingModule import HandDetector
from time import sleep
import numpy as np
import cvzone
from pynput.keyboard import Controller, Key
import sys
import time
import pygame  # Untuk efek suara
import os
from fpdf import FPDF

try:
    # Inisialisasi pygame untuk suara
    pygame.mixer.init()
    # Cek file keypress.mp3 di folder yang sama dengan main.py
    sound_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "keypress.mp3")
    try:
        pygame.mixer.music.load(sound_file)
        sound_enabled = True
    except pygame.error:
        print(f"File {sound_file} tidak ditemukan. Efek suara akan dinonaktifkan.")
        sound_enabled = False

    def initialize_camera():
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("Error: Tidak dapat membuka webcam")
            print("Pastikan:")
            print("1. Webcam terhubung dengan benar")
            print("2. Tidak ada aplikasi lain yang menggunakan webcam")
            print("3. Anda memberikan izin untuk mengakses webcam")
            sys.exit(1)
        cap.set(3, 1280)
        cap.set(4, 720)
        return cap

    cap = initialize_camera()
    detector = HandDetector(detectionCon=0.8, maxHands=1)

    # Layout keyboard yang lebih rapi, tombol Save PDF diganti menjadi PDF
    keys = [
        ["Q", "W", "E", "R", "T", "Y", "U", "I", "O", "P"],
        ["A", "S", "D", "F", "G", "H", "J", "K", "L"],
        ["Z", "X", "C", "V", "B", "N", "M"],
        ["Space", "Del", "Enter", "PDF"],
        [".", ",", "(", ")", "-", "Theme"]  # Theme di kanan '-'
    ]

    finalText = ""
    keyboard = Controller()

    # Dictionary untuk mapping tombol khusus
    special_keys = {
        "Space": " ",
        "Del": "BACKSPACE",  # Nama tombol diganti tapi fungsinya tetap sama
        "Enter": "ENTER",
        "PDF": "SAVE_PDF"    # Nama tombol diganti tapi fungsinya tetap sama
    }

    # === Tambahkan 5 pilihan tema warna modern ===
    themes = {
        "dark": {
            "bg": (34, 40, 49),
            "button": (57, 62, 70),
            "button_active": (0, 173, 181),
            "text": (238, 238, 238),
            "output_bg": (57, 62, 70),
            "border": (0, 173, 181)
        },
        "soft_green": {
            "bg": (232, 245, 233),
            "button": (165, 214, 167),
            "button_active": (56, 142, 60),
            "text": (27, 94, 32),
            "output_bg": (200, 230, 201),
            "border": (56, 142, 60)
        },
        "blue_sky": {
            "bg": (227, 242, 253),
            "button": (144, 202, 249),
            "button_active": (25, 118, 210),
            "text": (13, 71, 161),
            "output_bg": (187, 222, 251),
            "border": (25, 118, 210)
        },
        "sunset": {
            "bg": (255, 236, 179),
            "button": (255, 183, 77),
            "button_active": (255, 111, 0),
            "text": (102, 51, 0),
            "output_bg": (255, 224, 178),
            "border": (255, 111, 0)
        },
        "purple_dream": {
            "bg": (243, 229, 245),
            "button": (186, 104, 200),
            "button_active": (123, 31, 162),
            "text": (74, 20, 140),
            "output_bg": (225, 190, 231),
            "border": (123, 31, 162)
        }
    }
    theme_names = list(themes.keys())
    current_theme_idx = 0
    current_theme = theme_names[current_theme_idx]

    def drawAll(img, buttonList):
        for button in buttonList:
            x, y = button.pos
            w, h = button.size
            # Border modern
            cv2.rectangle(img, (x-4, y-4), (x + w+4, y + h+4), themes[current_theme]["border"], cv2.FILLED)
            # Tombol utama
            cv2.rectangle(img, button.pos, (x + w, y + h), themes[current_theme]["button"], cv2.FILLED)
            # Teks tombol
            cv2.putText(img, button.text, (x + 18, y + int(h*0.7)),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.6, themes[current_theme]["text"], 3, cv2.LINE_AA)
        return img

    class Button():
        def __init__(self, pos, text, size=[85, 85]):
            self.pos = pos
            self.size = size
            self.text = text
            self.is_pressed = False

    # Pastikan tidak ada pembuatan tombol Theme di luar loop berikut!
    # Buat ulang buttonList dengan margin antar tombol, baris bawah: ['.', ',', '(', ')', '-', 'Theme']
    buttonList = []
    button_sizes = {
        "Del": [120, 85],
        "Enter": [170, 85],
        "Space": [400, 85],
        "PDF": [120, 85]
    }
    margin_x = 10
    margin_y = 15
    for i in range(len(keys)):
        # Untuk baris terakhir, hitung lebar tombol Theme secara dinamis
        if i == len(keys) - 1:
            # Baris bawah
            baris_bawah = keys[i]
            sizes_bawah = []
            for key in baris_bawah:
                if key == "Theme":
                    # Hitung lebar tombol Theme berdasarkan panjang teks dan font
                    theme_text = "Theme"
                    (text_width, _), _ = cv2.getTextSize(theme_text, cv2.FONT_HERSHEY_SIMPLEX, 1.6, 3)
                    theme_width = text_width + 40  # padding kiri-kanan
                    sizes_bawah.append([theme_width, 85])
                else:
                    sizes_bawah.append(button_sizes.get(key, [85, 85]))
            total_width = sum(size[0] for size in sizes_bawah) + (len(baris_bawah) - 1) * margin_x
            x_offset = (1280 - total_width) // 2
            for j, key in enumerate(baris_bawah):
                size = sizes_bawah[j]
                buttonList.append(Button([x_offset, 180 + i * (size[1] + margin_y)], key, size))
                x_offset += size[0] + margin_x
        else:
            total_width = sum(button_sizes.get(key, [85, 85])[0] for key in keys[i]) + (len(keys[i]) - 1) * margin_x
            x_offset = (1280 - total_width) // 2
            for j, key in enumerate(keys[i]):
                size = button_sizes.get(key, [85, 85])
                buttonList.append(Button([x_offset, 180 + i * (size[1] + margin_y)], key, size))
                x_offset += size[0] + margin_x
    # Hapus seluruh kode pembuatan tombol Theme di luar loop ini!

    # Variabel untuk debouncing
    last_click_time = 0
    click_delay = 0.1

    # Tambahkan variabel alpha di awal
    alpha = 0.7  # 0.0 = transparan penuh, 1.0 = tidak transparan

    # Tambahkan variabel untuk mendeteksi klik pada tombol Theme
    theme_button_pressed = False
    
    # Pastikan area output dan keyboard tidak keluar dari 1280x720
    output_left, output_top = 60, 20
    output_right, output_bottom = 1220, 170  # 60px margin kanan

    # Tambahkan grid checker (border tipis) di sekeliling area keyboard
    keyboard_top = 180 - margin_y
    keyboard_bottom = buttonList[-1].pos[1] + buttonList[-1].size[1] + margin_y
    keyboard_left = min(b.pos[0] for b in buttonList) - margin_x
    keyboard_right = max(b.pos[0] + b.size[0] for b in buttonList) + margin_x

    while True:
        try:
            success, img = cap.read()
            if not success:
                print("Error: Tidak dapat membaca frame dari webcam")
                break
            img = cv2.flip(img, 1)
            hands, img = detector.findHands(img, flipType=False)

            # Keyboard transparan
            keyboard_layer = img.copy()
            keyboard_layer = drawAll(keyboard_layer, buttonList)
            # Tambahkan grid checker (border tipis) di sekeliling keyboard
            cv2.rectangle(keyboard_layer, (keyboard_left, keyboard_top), (keyboard_right, keyboard_bottom), (0, 255, 0), 2)
            img = cv2.addWeighted(keyboard_layer, alpha, img, 1 - alpha, 0)

            # Area output lebih besar dan bisa multi-baris, tidak keluar batas
            cv2.rectangle(img, (output_left, output_top), (output_right, output_bottom), themes[current_theme]["output_bg"], cv2.FILLED)
            lines = (finalText + "|").split("\n")
            for idx, line in enumerate(lines):
                cv2.putText(img, line, (output_left + 10, output_top + 40 + idx * 35),
                            cv2.FONT_HERSHEY_SIMPLEX, 1.4, themes[current_theme]["text"], 3, cv2.LINE_AA)

            # Deteksi klik pada tombol Theme secara khusus
            if hands:
                hand = hands[0]
                lmList = hand["lmList"]
                for button in buttonList:
                    x, y = button.pos
                    w, h = button.size
                    if x < lmList[8][0] < x + w and y < lmList[8][1] < y + h:
                        cv2.rectangle(img, (x - 5, y - 5), (x + w + 5, y + h + 5), themes[current_theme]["button_active"], cv2.FILLED)
                        cv2.putText(img, button.text, (x + 18, y + int(h*0.7)),
                                    cv2.FONT_HERSHEY_SIMPLEX, 1.6, themes[current_theme]["text"], 3, cv2.LINE_AA)
                        p1 = (lmList[4][0], lmList[4][1])
                        p2 = (lmList[8][0], lmList[8][1])
                        l = detector.findDistance(p1, p2)[0]
                        current_time = time.time()
                        if l < 35 and (current_time - last_click_time) > 0.3 and not button.is_pressed:
                            button.is_pressed = True
                            cv2.rectangle(img, button.pos, (x + w, y + h), themes[current_theme]["button_active"], cv2.FILLED)
                            cv2.putText(img, button.text, (x + 18, y + int(h*0.7)),
                                        cv2.FONT_HERSHEY_SIMPLEX, 1.6, themes[current_theme]["text"], 3, cv2.LINE_AA)
                            if button.text == "Theme":
                                # Ganti tema hanya saat tombol Theme benar-benar ditekan
                                current_theme_idx = (current_theme_idx + 1) % len(theme_names)
                                current_theme = theme_names[current_theme_idx]
                                theme_button_pressed = True
                            else:
                                theme_button_pressed = False
                            # Putar efek suara ketikan
                            if sound_enabled and button.text != "Theme":
                                pygame.mixer.music.play()
                            # Fungsi tombol khusus
                            if button.text in special_keys and button.text != "Theme":
                                if button.text == "Del":
                                    if len(finalText) > 0:
                                        finalText = finalText[:-1]
                                elif button.text == "Enter":
                                    finalText += "\n"
                                elif button.text == "Space":
                                    finalText += " "
                                elif button.text == "PDF":
                                    pdf = FPDF()
                                    pdf.add_page()
                                    pdf.set_font("Arial", size=16)
                                    for line in finalText.split("\n"):
                                        pdf.cell(0, 10, line, ln=1)
                                    pdf.output("output_keyboard.pdf")
                            elif button.text != "Theme":
                                finalText += button.text
                            last_click_time = current_time
                            sleep(0.3)
                            button.is_pressed = False
                        cv2.line(img, p1, p2, (0, 255, 0), 2)
                    else:
                        button.is_pressed = False

            cv2.imshow("Virtual Keyboard", img)
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('+') or key == ord('='):
                alpha = max(0.2, alpha - 0.1)
            elif key == ord('-') or key == ord('_'):
                alpha = min(1.0, alpha + 0.1)

        except Exception as e:
            print(f"Terjadi error: {str(e)}")
            continue

    cap.release()
    cv2.destroyAllWindows()

except Exception as e:
    print(f"Terjadi error fatal: {str(e)}")
    input("Tekan Enter untuk keluar...")