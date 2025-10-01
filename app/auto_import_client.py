import asyncio
import websockets
import json

async def auto_import_client():
    uri = "ws://localhost:8000/ws/auto-import"  # Adjust the URL as needed

    async with websockets.connect(uri) as websocket:
        print("Connected to WebSocket")

        # Start the auto-import process
        await websocket.send("start_auto_import")
        print("Sent start command")

        try:
            while True:
                response = await websocket.recv()
                print(f"Received: {response}")

                # If the response indicates completion, you can stop or continue
                if "completed" in response.lower():
                    print("Import cycle completed")
                    # Optionally break or continue

        except websockets.exceptions.ConnectionClosed:
            print("Connection closed")

if __name__ == "__main__":
    asyncio.run(auto_import_client())
