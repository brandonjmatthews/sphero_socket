import json
import time
import signal
import threading
import asyncio
import websockets.sync.server

from spherov2 import scanner
from spherov2.sphero_edu import SpheroEduAPI
from spherov2.types import Color
from spherov2.toy.r2d2 import R2D2

# Event to handle server shutdown
shutdown_event = threading.Event()

def handle_client(websocket):
    """Handles WebSocket messages synchronously within a persistent 'with' context."""
    print("Client connected")
    toy = None

    try:
        for message in websocket:
            if shutdown_event.is_set():  # Stop if shutdown is requested
                print("Shutting find_toy listener loop.")
                break
        
            message_dict = json.loads(message)
            print(f"Received command: {message}")
            
            if 'command' in message_dict and message_dict['command'] == 'find_toy':
                if 'toy_name' in message_dict:
                    toy = scanner.find_toy(toy_name=message_dict['toy_name'])
                else:
                    toy = scanner.find_toy()

                if toy is not None:
                    response = {"status": "connected"}
                    websocket.send(json.dumps(response))

                    try:
                        # Once connected, keep the robot context open
                        with SpheroEduAPI(toy) as robot:
                            listen_for_commands(websocket, robot)
                    except:
                        print ("Failed to connect to robot")
                else:
                    response = {"status": "not_found"}
                    websocket.send(json.dumps(response))

    except websockets.exceptions.ConnectionClosed:
        print("Client disconnected")


def listen_for_commands(websocket, robot):
    """Continuously listens for WebSocket messages and processes commands within the robot context."""
    try:
        while not shutdown_event.is_set():
            try:
                # Wait for a message with a timeout, so we can check shutdown_event
                message = websocket.recv(timeout=0.5)
                message_dict = json.loads(message)
                handle_command(message_dict, robot, websocket)

            except asyncio.TimeoutError:
                # No message received, continue looping to check shutdown_event
                continue

            except websockets.exceptions.ConnectionClosed:
                print("Client disconnected")
                break

            except KeyboardInterrupt:
                print("KeyboardInterrupt detected in listen_for_commands")
                break

            except Exception as e:
                print(f"Unexpected error in listen_for_commands: {e}")
                break

    except Exception as e:
        print(f"Critical error in listen_for_commands: {e}")


def handle_command(message: dict, robot, websocket):
    """Processes robot commands."""
    match message.get('command'):
        case 'set_main_led':
            r = message['r']
            g = message['g']
            b = message['b']
            robot.set_main_led(Color(r, g, b))
        case 'play_r2_sound':
            sound = message['sound']
            robot.play_sound(R2D2.Audio(sound))
        case _:
            print(f"Command {message.get('command')} is unhandled")


def start_server():
    """Starts the synchronous WebSocket server."""
    server = websockets.sync.server.serve(handle_client, "localhost", 8765)
    server.serve_forever()

def stop_server(signal_received, frame):
    """Handles SIGINT (Ctrl+C) to gracefully stop the server."""
    print("Shutting down server...")
    shutdown_event.set()  # Set the event so loops break\      
    print("Allowing time for SpheroAPI to shutdown...")  
    time.sleep(2)

if __name__ == "__main__":
    # Capture SIGINT to stop the server gracefully
    signal.signal(signal.SIGINT, stop_server)

    print("Starting WebSocket server on ws://localhost:8765")
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()

    # Keep the main thread alive, but allow stopping with Ctrl+C
    try:
        while not shutdown_event.is_set():
            pass
    except KeyboardInterrupt:
        stop_server(None, None)

