import socket
import threading

HOST = '127.0.0.1'
PORT = 7115

clients = []
symbols = ['X', 'O']
board = [['' for _ in range(3)] for _ in range(3)]
current_turn = 0  # Index of the player whose turn it is
lock = threading.Lock()

def send_all(msg):
    for client in clients:
        try:
            client.sendall((msg + "\n").encode())
        except:
            pass

def check_winner():
    # Check rows & columns
    for i in range(3):
        if board[i][0] and board[i][0] == board[i][1] == board[i][2]:
            return True
        if board[0][i] and board[0][i] == board[1][i] == board[2][i]:
            return True

    # Check diagonal's
    if board[0][0] and board[0][0] == board[1][1] == board[2][2]:
        return True
    if board[0][2] and board[0][2] == board[1][1] == board[2][0]:
        return True

    return False

def check_draw():
    for row in board:
        for cell in row:
            if not cell:
                return False
    return True

def handle_client(conn, player_id):
    global current_turn
    symbol = symbols[player_id]
    conn.sendall((symbol + "\n").encode())

    try:
        while True:
            data = conn.recv(1024).decode().strip()
            if not data:
                break

            if data.startswith("MOVE"):
                with lock:
                    if player_id != current_turn:
                        continue

                    _, row, col = data.split()
                    row, col = int(row), int(col)

                    if board[row][col] == '':
                        board[row][col] = symbol
                        send_all(f"UPDATE {row} {col} {symbol}")

                        if check_winner():
                            send_all("WIN")
                            break
                        elif check_draw():
                            send_all("DRAW")
                            break

                        # Switch turns
                        current_turn = 1 - current_turn
                        clients[current_turn].sendall("TURN\n".encode())
    except Exception as e:
        print("Error in server: ", e)
    finally:
        conn.close()


def main():
    global clients
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen(2)
    print("Server running. Waiting for players...")

    threads = []

    while len(clients) < 2:
        conn, addr = server.accept()
        print(f"Player connected from {addr}")
        clients.append(conn)
        t = threading.Thread(target=handle_client, args=(conn, len(clients) - 1))
        t.start()
        threads.append(t)

    # Let the first player know it's their turn
    clients[0].sendall("TURN\n".encode())

    for t in threads:
        t.join()

if __name__ == "__main__":
    main()