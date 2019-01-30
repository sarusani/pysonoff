import binascii
import json
import logging
import random
import time
from typing import Dict, Union, Callable, Awaitable

import websockets
from websockets.framing import OP_CLOSE, parse_close, OP_PING, OP_PONG

_LOGGER = logging.getLogger(__name__)


class SonoffLANModeClientProtocol(websockets.WebSocketClientProtocol):
    """Customised WebSocket client protocol to ignore pong payload match."""

    async def read_data_frame(self, max_size):
        """
        Copied from websockets.WebSocketCommonProtocol to change pong handling
        """
        while True:
            frame = await self.read_frame(max_size)

            if frame.opcode == OP_CLOSE:
                self.close_code, self.close_reason = parse_close(frame.data)
                await self.write_close_frame(frame.data)
                return

            elif frame.opcode == OP_PING:
                ping_hex = binascii.hexlify(frame.data).decode() or '[empty]'
                _LOGGER.debug(
                    "%s - received ping, sending pong: %s", self.side, ping_hex
                )
                await self.pong(frame.data)

            elif frame.opcode == OP_PONG:
                # Acknowledge pings on solicited pongs, regardless of payload
                if self.pings:
                    ping_id, pong_waiter = self.pings.popitem(0)
                    ping_hex = binascii.hexlify(ping_id).decode() or '[empty]'
                    pong_waiter.set_result(None)
                    _LOGGER.debug(
                        "%s - received pong, clearing most recent ping: %s",
                        self.side,
                        ping_hex
                    )
                else:
                    _LOGGER.debug(
                        "%s - received pong, but no pings to clear",
                        self.side
                    )
            else:
                return frame


class SonoffLANModeClient:
    """
    Implementation of the Sonoff LAN Mode Protocol (as used by the eWeLink app)
    """
    DEFAULT_PORT = 8081
    DEFAULT_TIMEOUT = 5
    DEFAULT_PING_INTERVAL = 5

    """
    Initialise class with connection parameters

    :param str host: host name or ip address of the device
    :param int port: port on the device (default: 8081)
    :return:
    """

    def __init__(self, host: str,
                 event_handler: Callable[[str], Awaitable[None]],
                 port: int = DEFAULT_PORT,
                 ping_interval: int = DEFAULT_PING_INTERVAL,
                 timeout: int = DEFAULT_TIMEOUT):
        self.host = host
        self.port = port
        self.ping_interval = ping_interval
        self.timeout = timeout
        self.websocket = None
        self.keep_running = True
        self.event_handler = event_handler

    async def connect(self):
        """
        Connect to the Sonoff LAN Mode Device and set up communication channel.
        """
        websocket_address = 'ws://%s:%s/' % (self.host, self.port)
        _LOGGER.debug('Connecting to websocket address: %s', websocket_address)

        self.websocket = await websockets.connect(
            websocket_address,
            ping_interval=self.ping_interval,
            ping_timeout=self.timeout,
            subprotocols=['chat'],
            klass=SonoffLANModeClientProtocol
        )

    async def close_connection(self):
        _LOGGER.debug('Closing websocket from client close_connection')
        await self.websocket.close()

    async def receive_message_loop(self):
        try:
            while self.keep_running:
                _LOGGER.debug('Waiting for messages on websocket')
                message = await self.websocket.recv()
                await self.event_handler(message)
                _LOGGER.debug('Message passed to handler, should loop now')
        finally:
            _LOGGER.debug('receive_message_loop finally block reached: '
                          'closing websocket')
            await self.websocket.close()

    async def send_online_message(self):
        _LOGGER.debug('Sending user online message over websocket')

        json_data = json.dumps(self.get_user_online_payload())
        await self.websocket.send(json_data)

        response_message = await self.websocket.recv()
        response = json.loads(response_message)

        _LOGGER.debug('Received user online response:')
        _LOGGER.debug(response)
        # Example user online response:
        # {
        #     "error": 0,
        #     "apikey": "ab22d7b3-53de-44b9-ad26-f1ff260e8f1d",
        #     "sequence": "15483706231915703",
        #     "deviceid": "100040e943"
        # }

        # We want to pass the event to the event_handler already
        # because the hello event could arrive before the user online
        # confirmation response
        await self.event_handler(response_message)

        if ('error' in response and response['error'] == 0) \
            and 'deviceid' in response:
            _LOGGER.debug('Websocket connected and accepted online user OK')
            return True
        else:
            _LOGGER.error('Websocket connection online user failed')

    async def send(self, request: Union[str, Dict]):
        """
        Send message to an already-connected Sonoff LAN Mode Device
        and return the response.

        :param request: command to send to the device (can be dict or json)
        :return:
        """
        if isinstance(request, dict):
            request = json.dumps(request)

        _LOGGER.debug('Sending websocket message: %s', request)
        await self.websocket.send(request)

    @staticmethod
    def get_user_online_payload() -> Dict:
        return {
            'action': "userOnline",
            'userAgent': 'app',
            'version': 6,
            'nonce': ''.join([str(random.randint(0, 9)) for _ in range(15)]),
            'apkVesrion': "1.8",
            'os': 'ios',
            'at': 'at',  # No bearer token needed in LAN mode
            'apikey': 'apikey',  # No apikey needed in LAN mode
            'ts': str(int(time.time())),
            'model': 'iPhone10,6',
            'romVersion': '11.1.2',
            'sequence': str(time.time()).replace('.', '')
        }

    @staticmethod
    def get_update_payload(device_id: str, params: dict) -> Dict:
        return {
            'action': 'update',
            'userAgent': 'app',
            'params': params,
            'apikey': 'apikey',  # No apikey needed in LAN mode
            'deviceid': device_id,
            'sequence': str(time.time()).replace('.', ''),
            'controlType': 4,
            'ts': 0
        }

# Uncomment the below to test this websocket client directly on CLI

# async def print_event_handler(message: str):
#     print("CALLBACK SUCCESS! Message: %s" % message)
#
# logging.basicConfig(level=logging.DEBUG)  # Shows debug logs from websocket
# _LOGGER.setLevel(logging.DEBUG)
# handler = logging.StreamHandler(sys.stdout)
# handler.setLevel(logging.DEBUG)
# formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
# handler.setFormatter(formatter)
# _LOGGER.addHandler(handler)
# client = SonoffLANModeClient('127.0.0.1', print_event_handler)
# # client = SonoffLANModeClient('192.168.0.76', print_event_handler)
#
# asyncio.get_event_loop().run_until_complete(client.connect())
# asyncio.get_event_loop().run_forever()
