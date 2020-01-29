import websockets
import asyncio


async def main_service_loop(websocket, path):
    print('Received user.')
    await websocket.send('hello')
    print('Hello send!')
    while True:
        try:
            output_str = await websocket.recv()
            print(output_str)
            input_str = input('Please input your command:')
            await websocket.send(input_str)

        except Exception as err:
            print(err)
    print('Connection closed.')

start_server = websockets.serve(
    main_service_loop, '0.0.0.0', 6666, read_limit=2**25, max_size=2**25)
print('start service...')
asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
