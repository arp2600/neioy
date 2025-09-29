import argparse
import socket
import signal

IP_ADDRESS = "127.0.0.1"
PORT = 20001


def _parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--test-message')
    return parser.parse_args()


def post(message, end='\n'):
    socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM).sendto(
        (str(message) + end).encode(), (IP_ADDRESS, PORT))


def _start_server(args):
    udp_socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
    udp_socket.bind((IP_ADDRESS, PORT))
    udp_socket.settimeout(1)
    print("UDP server up and listening")

    server_active = True

    def quit_server(sig, frame):
        # The terminal probably printed a ^C in response to ctrl-c
        # being pressed. '\r' will return the cursor to the beginning
        # of the line and the message will overwrite the ^C.
        print('\rshutting down server...')
        nonlocal server_active
        server_active = False

    signal.signal(signal.SIGINT, quit_server)

    # Listen for incoming datagrams
    while server_active:
        buffer_size = 1024
        try:
            message, address = udp_socket.recvfrom(buffer_size)
            print(message.decode('utf-8'), end='')
        except TimeoutError:
            pass


def _main():
    args = _parse_args()
    if args.test_message:
        post(args.test_message)
        return

    _start_server(args)


if __name__ == '__main__':
    _main()
