import os
import time
import serial
import threading
from xmodem import XMODEM

COM_PORT = "COM1"
BAUD_RATE = 9600


class ModemTerminal:
    def __init__(self):
        self.ser = None
        self.transfer_active = threading.Event()

    # ---------------------------
    # Wysyłanie komendy AT
    # ---------------------------
    def send_cmd(self, cmd: str):
        self.ser.write((cmd + "\r\n").encode())

    # ---------------------------
    # Wątek czytający port szeregowy
    # ---------------------------
    def read_from_port(self):
        while True:
            if not self.transfer_active.is_set():
                try:
                    if self.ser.in_waiting:
                        msg = self.ser.readline().decode("utf-8", errors="ignore").strip()
                        if "CONNECT" not in msg: 
                            print(f"\rWiadomość: {msg}\n", end="") 
                        else: print("Połączono!")
                except (serial.SerialException, OSError):
                    print("\nPort został zamknięty.")
                    break
            else:
                time.sleep(0.05)

    # ---------------------------
    # Funkcje XMODEM – poprawione
    # ---------------------------
    def serial_get(self, size=1, timeout=1, *args, **kwargs):
        data = self.ser.read(size)
        return data if data else None

    def serial_put(self, data, *args, **kwargs):
        return self.ser.write(data)

    # ---------------------------
    # Wysyłanie pliku XMODEM
    # ---------------------------
    def send_file(self, filename):
        if not os.path.exists(filename):
            print(f"BŁĄD: Plik '{filename}' nie istnieje.")
            return

        print("\nWysyłanie pliku...")

        self.transfer_active.set()
        try:
            modem = XMODEM(self.serial_get, self.serial_put)
            with open(filename, "rb") as f:
                if modem.send(f):
                    print("Plik wysłany.")
                else:
                    print("Błąd transmisji.")
        finally:
            self.transfer_active.clear()

    # ---------------------------
    # Odbieranie pliku XMODEM
    # ---------------------------
    def receive_file(self, filename):
        print("\nOdbieranie pliku...")

        self.transfer_active.set()
        try:
            modem = XMODEM(self.serial_get, self.serial_put)
            with open(filename, "wb") as f:
                if modem.recv(f):
                    print(f"Plik zapisano jako {filename}.")
                else:
                    print("Błąd odbierania.")
        finally:
            self.transfer_active.clear()

    # ---------------------------
    # Tryb menu
    # ---------------------------
    def call_menu(self):
        print("\nKomendy: /send /receive /exit")

        while True:
            msg = input("> ").strip()

            if msg == "/exit":
                print("Rozłączanie...")
                self.ser.write(b"+++")
                time.sleep(1)
                self.send_cmd("ATH")
                break

            elif msg == "/send":
                plik = input("Plik do wysłania: ")
                self.send_file(plik)

            elif msg == "/receive":
                plik = input("Zapisz jako: ")
                self.receive_file(plik)

            else:
                self.send_cmd(msg)

    # ---------------------------
    # Program główny
    # ---------------------------
    def main(self):
        print("Otwieranie portu...")

        try:
            self.ser = serial.Serial(COM_PORT, BAUD_RATE, timeout=1)
        except serial.SerialException:
            print(f"Nie mogę otworzyć {COM_PORT}.")
            return

        print(f"Połączono z {COM_PORT}.")

        threading.Thread(target=self.read_from_port, daemon=True).start()

        while True:
            print("\n1. Zadzwoń\n2. Odbierz\n3. Admin\n4. GŁOŚNIK ON\n5. GŁOŚNIK OFF\n9. Wyjście")
            choice = input("Wybór: ")

            if choice == "1":
                self.send_cmd("ATDT" + input("Numer: "))
                self.call_menu()

            elif choice == "2":
                self.send_cmd("ATA")
                self.call_menu()

            elif choice == "3":
                while True:
                    cmd = input("Admin (0 = wyjście): ")
                    if cmd == "0":
                        break
                    self.send_cmd(cmd)

            elif choice == "4":
                self.send_cmd("ATM2")
                self.send_cmd("ATL2")

            elif choice == "5":
                self.send_cmd("ATM0")

            elif choice == "9":
                print("Zamykanie...")
                self.ser.close()
                break

            else:
                print("Niepoprawny wybór.")


if __name__ == "__main__":
    ModemTerminal().main()



