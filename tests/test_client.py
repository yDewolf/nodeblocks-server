import asyncio
import websockets
import json

scene_data = json.loads(
"""
{
    "node_types_id": "MyCoolTypes",
    "node_types_version": 0,
    "nodes": {
        "node_2": {
            "type": "SumNode",
            "data": {}
        },
        "node_3": {
            "type": "MulNode",
            "data": {}
        },
        "node_0": {
            "type": "InputNode",
            "data": {"value": 39}
        },
        "node_1": {
            "type": "InputNode",
            "data": {"value": 28}
        },
        "node_4": {
            "type": "InputNode",
            "data": {"value": 0.1}
        }
    },
    "connections": {
        "c1": {
            "from": "nodes:node_0:slots:out_0",
            "to": "nodes:node_2:slots:in_0"
        },
        "c4": {
            "from": "nodes:node_4:slots:out_0",
            "to": "nodes:node_3:slots:in_0"
        },
        "c2": {
            "from": "nodes:node_1:slots:out_0",
            "to": "nodes:node_2:slots:in_1"
        },
        "c3": {
            "from": "nodes:node_2:slots:out_0",
            "to": "nodes:node_3:slots:in_0"
        }
    }
} 
"""
)
async def async_input(prompt: str) -> str:
    return await asyncio.get_event_loop().run_in_executor(
        None, input, prompt
    )

async def listen_to_messages(websocket):
    print("listening to node outputs")
    while True:
        response = await websocket.recv()
        data = json.loads(response)
        print(f"Node Output: {data}")

async def test_node_server():
    uri = "ws://localhost:3001/instance/test_user"
    async with websockets.connect(uri) as websocket:
        greeting = await websocket.recv()
        print(f"Server says: {greeting}")


        await websocket.send(json.dumps({"type": "LOAD_SCENE", "payload": scene_data}))
        await websocket.send(json.dumps({"type": "SET_LOOP_STATE", "payload": {"state": 1}}))
        await websocket.send(json.dumps({"type": "RUN"}))

        asyncio.create_task(listen_to_messages(websocket))
        try:
            while True:
                command = await async_input("\nWaiting for command: \n>> ")
                if command.upper() == "NODE" or command.upper() == "CONNECTION":
                    payload = await async_input("Payload: \n>>")
                    await websocket.send(json.dumps({"type": command, "payload": json.loads(payload)}))
                    continue
                
                match command.upper():
                    case "SET_STATE":
                        new_state = int(await async_input("New State: \n>> "))
                        await websocket.send(json.dumps({"type": command, "payload": {"state": new_state}}))
                        continue

                    case "SET_LOOP_STATE":
                        new_state = int(await async_input("New State: \n>> "))
                        await websocket.send(json.dumps({"type": command, "payload": {"state": new_state}}))
                        continue

                    case _:
                        if command == "":
                            continue

                        await websocket.send(json.dumps({"type": command.upper()}))
                

        except websockets.ConnectionClosed:
            print("Connection closed by server")

if __name__ == "__main__":
    asyncio.run(test_node_server())