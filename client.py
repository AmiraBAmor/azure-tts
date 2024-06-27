import requests
import argparse

def run(url):
    while True:
        message = input("Enter your message (or 'quit' to exit): ")
        if message.lower() == 'quit':
            break
        
        response = requests.post(f'{url}/send_message', json={'message': message})
        if response.status_code == 200:
            print(f"Bot: {response.json()['response']}")
        else:
            print(f"Error: {response.status_code} - {response.text}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--url', required=True, help='ngrok URL')
    args = parser.parse_args()

    run(args.url)