import sys
import socket
import threading
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QGridLayout, QMessageBox, QLabel, QVBoxLayout, \
    QHBoxLayout
from PyQt5.QtCore import pyqtSignal, QObject

HOST = '127.0.0.1'
PORT = 7115

class SignalHandler(QObject):
    update_tile = pyqtSignal(int, int, str)
    enable_turn = pyqtSignal(bool)

class TicTacToeClient(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Multiplayer Tic Tac Toe")
        self.setFixedSize(500, 500)

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.socket.connect((HOST, PORT))
        except Exception as e:
            QMessageBox.critical(self, "Connection Failed", str(e))
            sys.exit()

        self.symbol = None
        self.my_turn = False
        self.board = [['' for _ in range(3)] for _ in range(3)]
        self.buttons = [[None for _ in range(3)] for _ in range(3)]

        self.signals = SignalHandler()
        self.signals.update_tile.connect(self.update_tile)
        self.signals.enable_turn.connect(self.set_turn)

        self.title = QLabel("Waiting...")
        self.subtitle = QLabel("")
        self.init_ui()

        threading.Thread(target=self.listen_to_server, daemon=True).start()

    def init_ui(self):
        layout = QGridLayout()

        vertLayout = QVBoxLayout()
        vertLayout.addStretch()
        vertLayout.addWidget(self.title)
        vertLayout.addStretch()
        vertLayout.addLayout(layout)
        vertLayout.addStretch()
        vertLayout.addWidget(self.subtitle)
        vertLayout.addStretch()

        horiLayout = QHBoxLayout()
        horiLayout.addStretch()
        horiLayout.addLayout(vertLayout)
        horiLayout.addStretch()

        self.setLayout(horiLayout)

        for row in range(3):
            for col in range(3):
                btn = QPushButton("")
                btn.setFixedSize(80, 80)
                btn.setStyleSheet("font-size: 24px")
                btn.clicked.connect(lambda _, r=row, c=col: self.handle_click(r, c))
                layout.addWidget(btn, row, col)
                self.buttons[row][col] = btn

    def handle_click(self, row, col):
        if not self.my_turn:
            return
        if self.board[row][col] != '':
            return
        self.socket.sendall(f"MOVE {row} {col}".encode())

    def update_tile(self, row, col, symbol):
        self.board[row][col] = symbol
        self.buttons[row][col].setText(symbol)

    def set_turn(self, value):
        self.my_turn = value

    def listen_to_server(self):
        try:
            while True:
                data = self.socket.recv(1024).decode()
                if not data:
                    break

                lines = data.strip().split("\n")
                for line in lines:
                    if line in ['X', 'O']:
                        self.symbol = line
                        self.title.setText(f"You are {self.symbol}")
                    elif line == "TURN":
                        self.subtitle.setText(f"Your Turn!")
                        self.signals.enable_turn.emit(True)
                    elif line.startswith("UPDATE"):
                        _, row, col, sym = line.split()
                        self.signals.update_tile.emit(int(row), int(col), sym)
                        if sym == self.symbol:
                            self.subtitle.setText(f"Opponent Turn!")
                            self.signals.enable_turn.emit(False)
                    elif line in ["WIN", "DRAW"]:
                        if line == "WIN" and self.my_turn:
                            self.subtitle.setText("Game Over, you WIN!")
                        elif line == "WIN" and not self.my_turn:
                            self.subtitle.setText("Game Over, you lose.")
                        else:
                            self.subtitle.setText("Game Over, DRAW.")
                        break
        except Exception as e:
            print("Error in listener: ", e)
        finally:
            self.socket.close()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TicTacToeClient()
    window.show()
    sys.exit(app.exec_())
