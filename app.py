import threading
import time
import logging
import grpc
import bot_pb2
import bot_pb2_grpc
import concurrent.futures
import os
from dotenv import load_dotenv
from azure_tts import initialize_speech_synthesizer, synthesize_text_to_speech
from azure_stt import speak_to_microphone
from groq import Groq

# Load environment variables
load_dotenv()

logging.basicConfig(filename='latency_log.txt', level=logging.INFO)

# gRPC server address
SERVER_ADDRESS = 'localhost:50051'

class CallBot:
    def __init__(self):
        self.stop_flag = threading.Event()

        # Initialize Azure Speech Synthesizer
        self.speech_synthesizer = initialize_speech_synthesizer()

        # Initialize gRPC client
        self.channel = grpc.insecure_channel(SERVER_ADDRESS)
        self.stub = bot_pb2_grpc.CallBotStub(self.channel)

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
        print(f"Vous : {recognized_text}")
        if recognized_text.lower() == "au revoir":
            self.stop_flag.set()
            farewell_message = "Au revoir !"
            print(f"Bot : {farewell_message}")
            self.speak(farewell_message)
            self.shutdown()
        else:
            self.groq_response(recognized_text)
        end_time = time.time()
        self.log_time_taken("Reconnaissance vocale", start_time, end_time)

    def shutdown(self):
        self.channel.close()
        os._exit(0)

    def bot_conversation(self):
        start_time = time.time()
        initial_message = "Comment puis-je vous aider aujourd'hui ?"
        print(f"Bot : {initial_message}")
        self.speak(initial_message)
        while not self.stop_flag.is_set():
            self.recognize_speech()
        end_time = time.time()
        self.log_time_taken("Conversation du bot", start_time, end_time)

    def groq_response(self, user_input):
        if self.stop_flag.is_set():
            return
        start_time = time.time()

        request = bot_pb2.MessageRequest(message=user_input)
        response = self.stub.SendMessage(request)
        bot_response = response.response

        print(f"Bot : {bot_response}")
        self.speak(bot_response)

        end_time = time.time()
        self.log_time_taken("Appel API Groq", start_time, end_time)

    def start_conversation(self):
        self.stop_flag.clear()
        self.bot_conversation()

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

def listen_for_enter(stop_flag):
    input("Press Enter to quit...")
    stop_flag.set()

if __name__ == "__main__":
    server_thread = threading.Thread(target=serve)
    server_thread.daemon = True
    server_thread.start()
    
    bot = CallBot()

    enter_listener_thread = threading.Thread(target=listen_for_enter, args=(bot.stop_flag,))
    enter_listener_thread.daemon = True
    enter_listener_thread.start()

    bot.start_conversation()