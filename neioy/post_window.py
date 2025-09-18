import argparse
import socket

IP_ADDRESS = "127.0.0.1"
PORT = 20001


def _parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--test-message')
    return parser.parse_args()


def post(message):
    socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM).sendto(
        str(message).encode(), (IP_ADDRESS, PORT))


def _start_server(args):
    udp_socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
    udp_socket.bind((IP_ADDRESS, PORT))
    print("UDP server up and listening")

    # Listen for incoming datagrams
    while (True):
        buffer_size = 1024
        message, address = udp_socket.recvfrom(buffer_size)
        print(message.decode('utf-8'))


def _main():
    args = _parse_args()
    if args.test_message:
        post(args.test_message)
        return

    _start_server(args)


if __name__ == '__main__':
    _main()
