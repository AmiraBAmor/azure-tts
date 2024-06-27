from http.server import HTTPServer, BaseHTTPRequestHandler
import json
from app import CallBotServicer  # Import your existing bot logic
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

bot = CallBotServicer()

class BotHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        data = json.loads(post_data.decode('utf-8'))
        
        message = data['message']
        response = bot.SendMessage(bot_pb2.MessageRequest(message=message), None)
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({'response': response.response}).encode('utf-8'))

def run(server_class=HTTPServer, handler_class=BotHandler, port=8000):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print(f"Starting server on port {port}...")
    httpd.serve_forever()

if __name__ == '__main__':
    run()