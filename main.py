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

    def send_cmd(self, cmd: str):
        self.ser.write((cmd + "\r\n").encode())

    def read_from_port(self):
        while True:
            if not self.transfer_active.is_set():
                try:
                    if self.ser.in_waiting:
                        msg = self.ser.readline().decode("utf-8", errors="ignore").strip()
                        if msg:
                            print(f"\rWiadomość: {msg}\n", end="")
                except (serial.SerialException, OSError):
                    print("\nPort został zamknięty.")
                    break
            else:
                time.sleep(0.1)

    def serial_get(self, size, timeout=1):
        return self.ser.read(size) or None

    def serial_put(self, data, timeout=1):
        return self.ser.write(data)

    def send_file(self, filename):
        if not os.path.exists(filename):
            print(f"BŁĄD: Plik '{filename}' nie istnieje.")
            return

        self.transfer_active.set()
        print("\nWysyłanie pliku...")

        try:
            modem = XMODEM(self.serial_get, self.serial_put)
            with open(filename, "rb") as f:
                if modem.send(f):
                    print("Plik wysłany.")
                else:
                    print("Błąd transmisji.")
        finally:
            self.transfer_active.clear()

    def receive_file(self, filename):
        self.transfer_active.set()
        print("\nOdbieranie pliku...")

        try:
            modem = XMODEM(self.serial_get, self.serial_put)
            with open(filename, "wb") as f:
                if modem.recv(f):
                    print(f"Plik zapisano jako {filename}.")
                else:
                    print("Błąd odbierania.")
        finally:
            self.transfer_active.clear()

    def call_menu(self):
        print("\nPołączono. Komendy: /send /receive /exit")

        while True:
            msg = input("> ").strip()

            if msg == "/exit":
                print("Rozłączanie...")
                self.ser.write(b"+++")
                time.sleep(1)
                self.send_cmd("ATH")
                break

            elif msg == "/send":
                self.send_file(input("Plik do wysłania: "))

            elif msg == "/receive":
                self.receive_file(input("Zapisz jako: "))

            else:
                self.send_cmd(msg)

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
