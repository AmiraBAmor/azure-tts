import tkinter as tk
from tkinter import ttk
import threading
import time
import logging
import grpc
import bot_pb2
import bot_pb2_grpc
import concurrent.futures  # Import futures for ThreadPoolExecutor
import os  # Import os for environment variables
from dotenv import load_dotenv
from azure_tts import initialize_speech_synthesizer, synthesize_text_to_speech
from azure_stt import speak_to_microphone
from groq import Groq  # Assuming Groq is in the same directory

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(filename='latency_log.txt', level=logging.INFO)

# gRPC server address
SERVER_ADDRESS = 'localhost:50051'

class CallBotGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Bot d'appel")
        self.stop_flag = False

        # Initialize Azure Speech Synthesizer
        self.speech_synthesizer = initialize_speech_synthesizer()

        # Initialize gRPC client
        self.channel = grpc.insecure_channel(SERVER_ADDRESS)
        self.stub = bot_pb2_grpc.CallBotStub(self.channel)

        self.create_widgets()

    def create_widgets(self):
        self.dialogue_frame = ttk.Frame(self.root, padding="20")
        self.dialogue_frame.grid(row=0, column=0, sticky="nsew")

        self.dialogue_label = ttk.Label(self.dialogue_frame, text="Dialogue :")
        self.dialogue_label.grid(row=0, column=0, sticky="w")

        self.dialogue_text = tk.Text(self.dialogue_frame, width=50, height=10)
        self.dialogue_text.grid(row=1, column=0, padx=5, pady=5)

        self.start_button = ttk.Button(self.root, text="Commencer la conversation", command=self.start_conversation)
        self.start_button.grid(row=1, column=0, sticky="e")

    def log_time_taken(self, task_name, start_time, end_time):
        elapsed_time = end_time - start_time
        logging.info(f"{task_name} a pris {elapsed_time:.2f} secondes")
        print(f"{task_name} a pris {elapsed_time:.2f} secondes")

    def speak(self, text):
        start_time = time.time()
        synthesize_text_to_speech(text, self.speech_synthesizer)
        end_time = time.time()
        self.log_time_taken("Texte-à-parole (Azure TTS)", start_time, end_time)

    def recognize_speech(self):
        start_time = time.time()
        recognized_text = speak_to_microphone(os.getenv("api_key"), os.getenv("region"))
        self.dialogue_text.insert(tk.END, f"Vous : {recognized_text}\n")
        if recognized_text.lower() == "au revoir":
            self.stop_flag = True
            farewell_message = "Au revoir !"
            self.dialogue_text.insert(tk.END, f"Bot : {farewell_message}\n")
            self.speak(farewell_message)
        else:
            self.groq_response(recognized_text)
        end_time = time.time()
        self.log_time_taken("Reconnaissance vocale", start_time, end_time)

    def bot_conversation(self):
        start_time = time.time()
        initial_message = "Comment puis-je vous aider aujourd'hui ?"
        self.dialogue_text.insert(tk.END, f"Bot : {initial_message}\n")
        self.speak(initial_message)
        while not self.stop_flag:
            self.recognize_speech()
        end_time = time.time()
        self.log_time_taken("Conversation du bot", start_time, end_time)

    def groq_response(self, user_input):
        start_time = time.time()

        # Call gRPC server
        request = bot_pb2.MessageRequest(message=user_input)
        response = self.stub.SendMessage(request)
        bot_response = response.response

        self.dialogue_text.insert(tk.END, f"Bot : {bot_response}\n")
        self.speak(bot_response)

        end_time = time.time()
        self.log_time_taken("Appel API Groq", start_time, end_time)

    def start_conversation(self):
        self.stop_flag = False
        thread = threading.Thread(target=self.bot_conversation)
        thread.daemon = True
        thread.start()

def serve():
    server = grpc.server(thread_pool=concurrent.futures.ThreadPoolExecutor(max_workers=10))
    bot_pb2_grpc.add_CallBotServicer_to_server(CallBotServicer(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    server.wait_for_termination()

class CallBotServicer(bot_pb2_grpc.CallBotServicer):
    def __init__(self):
        self.client = Groq(api_key=os.getenv("groq_api"))
    def SendMessage(self, request, context):
        start_time = time.time()
        
        user_input = request.message
        chat_completion = self.client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": user_input,
                    "name": "FrenchUser",
                }
            ],
            model="Llama3-8b-8192",
        )
        
        response = chat_completion.choices[0].message.content
        
        end_time = time.time()
        logging.info(f"Appel API Groq a pris {end_time - start_time:.2f} secondes")
        return bot_pb2.MessageResponse(response=response)

if __name__ == "__main__":
    root = tk.Tk()
    app = CallBotGUI(root)
    
    # Start gRPC server in a separate thread
    server_thread = threading.Thread(target=serve)
    server_thread.daemon = True
    server_thread.start()
    
    root.mainloop()