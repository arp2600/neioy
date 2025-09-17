import argparse
import socket


def _parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--test-message')
    return parser.parse_args()


def post(message):
    bytesToSend         = str(message).encode()
    serverAddressPort   = ("127.0.0.1", 20001)
    bufferSize          = 1024
    
    UDPClientSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
    UDPClientSocket.sendto(bytesToSend, serverAddressPort)
    


def _start_server(args):
    localIP     = "127.0.0.1"
    localPort   = 20001
    bufferSize  = 1024

    UDPServerSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
    UDPServerSocket.bind((localIP, localPort))
    
    print("UDP server up and listening")
    # Listen for incoming datagrams
    while(True):
        bytesAddressPair = UDPServerSocket.recvfrom(bufferSize)
        message = bytesAddressPair[0]
        print(message.decode('utf-8'))
    

def _main():
    args = _parse_args()
    if args.test_message:
        post(args.test_message)
        return

    _start_server(args)


if __name__ == '__main__':
    _main()
