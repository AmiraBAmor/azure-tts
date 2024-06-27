import argparse
import grpc
import bot_pb2
import bot_pb2_grpc

def run(remote, remote_port):
    channel = grpc.insecure_channel(f'{remote}:{remote_port}')
    stub = bot_pb2_grpc.CallBotStub(channel)
    
    while True:
        message = input("Enter your message (or 'quit' to exit): ")
        if message.lower() == 'quit':
            break
        
        request = bot_pb2.MessageRequest(message=message)
        response = stub.SendMessage(request)
        print(f"Bot: {response.response}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--remote', required=True, help='ngrok remote address')
    parser.add_argument('--remote_port', required=True, type=int, help='ngrok remote port')
    args = parser.parse_args()

    run(args.remote, args.remote_port)