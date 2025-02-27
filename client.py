import asyncio
import websockets
import json

async def handle_status(websocket, message:dict):
    match message['status']:
        case 'connected':
            await websocket.send(json.dumps({
                'command':'set_main_led',
                'r': 255,
                'g': 0,
                'b': 255
            }))

async def main():
    uri = "ws://localhost:8765"
    async with websockets.connect(uri) as websocket:
        # while True:
        #     command = input("Enter command (find_toy, forward, backward, stop, quit): ").strip()
        #     if command == "quit":
        #         break
            
        #     await websocket.send(command)
        #     response = await websocket.recv()
        #     print(f"Server response: {response}")

        # Send initial command
        await websocket.send(json.dumps({
            'command': 'find_toy',
            'toy_name': 'D2-0CC9'
        }))

        # Process messages received on the connection.
        try:
            async for message in websocket:
                message_dict = json.loads(message)
                if 'status' in message_dict:
                    await handle_status(websocket, message_dict)

        except websockets.exceptions.ConnectionClosed:
            print("Connection closed")

if __name__ == "__main__":
    asyncio.run(main())