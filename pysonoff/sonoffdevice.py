"""
pysonoff
Python library supporting Sonoff Smart Devices (Basic/S20/Touch) in LAN Mode.
"""
import asyncio
import json
import logging
import sys
from typing import Callable, Awaitable, Dict
import traceback
from pysonoff import SonoffLANModeClient
from pysonoff import utils


class SonoffDevice(object):
    def __init__(
        self,
        host: str,
        callback_after_update: Callable[..., Awaitable[None]] = None,
        shared_state: Dict = None,
        logger=None,
        loop=None,
        ping_interval=SonoffLANModeClient.DEFAULT_PING_INTERVAL,
        timeout=SonoffLANModeClient.DEFAULT_TIMEOUT,
        context: str = None,
        device_id: str = "",
        api_key: str = "",
        outlet: int = None,
    ) -> None:
        """
        Create a new SonoffDevice instance.

        :param str host: host name or ip address on which the device listens
        :param context: optional child ID for context in a parent device
        """
        self.callback_after_update = callback_after_update
        self.host = host
        self.context = context
        self.api_key = api_key
        self.outlet = outlet
        self.shared_state = shared_state
        self.basic_info = None
        self.params = {"switch": "unknown"}
        self.loop = loop
        self.tasks = []
        self.new_loop = False

        if logger is None:  # pragma: no cover
            self.logger = logging.getLogger(__name__)
        else:
            self.logger = logger

        # Ctrl-C (KeyboardInterrupt) does not work well on Windows
        # This module solve that issue with wakeup coroutine.
        # noqa https://stackoverflow.com/questions/24774980/why-cant-i-catch-sigint-when-asyncio-event-loop-is-running/24775107#24775107
        # noqa code lifted from https://gist.github.com/lambdalisue/05d5654bd1ec04992ad316d50924137c
        if sys.platform.startswith("win"):

            def hotfix(
                loop: asyncio.AbstractEventLoop,
            ) -> asyncio.AbstractEventLoop:
                loop.call_soon(_wakeup, loop, 1.0)
                return loop

            def _wakeup(
                loop: asyncio.AbstractEventLoop, delay: float = 1.0
            ) -> None:
                loop.call_later(delay, _wakeup, loop, delay)

        else:
            # Do Nothing on non Windows
            def hotfix(
                loop: asyncio.AbstractEventLoop,
            ) -> asyncio.AbstractEventLoop:
                return loop

        try:
            if self.loop is None:

                self.new_loop = True
                self.loop = asyncio.new_event_loop()
                asyncio.set_event_loop(self.loop)

            self.logger.debug(
                "Initializing SonoffLANModeClient class in SonoffDevice"
            )
            self.client = SonoffLANModeClient(
                host,
                self.handle_message,
                ping_interval=ping_interval,
                timeout=timeout,
                logger=self.logger,
                loop=self.loop,
                device_id=device_id,
                api_key=api_key,
                outlet=outlet,
            )

            self.message_ping_event = asyncio.Event()
            self.message_acknowledged_event = asyncio.Event()
            self.params_updated_event = asyncio.Event()

            self.client.listen()

            self.tasks.append(
                self.loop.create_task(self.send_availability_loop())
            )

            self.send_updated_params_task = self.loop.create_task(
                self.send_updated_params_loop()
            )
            self.tasks.append(self.send_updated_params_task)

            if self.new_loop:
                hotfix(self.loop)  # see Cltr-C hotfix earlier in routine
                self.loop.run_until_complete(self.send_updated_params_task)

        except asyncio.CancelledError:
            self.logger.debug("SonoffDevice loop ended, returning")

    async def send_availability_loop(self):

        self.logger.debug("enter send_availability_loop()")

        try:
            while True:

                self.logger.debug("waiting for connection")

                await self.client.connected_event.wait()
                self.client.disconnected_event.clear()

                self.logger.info(
                    "%s: Connected event, waiting for disconnect",
                    self.client.device_id,
                )

                # Don't send update when we connect, handle_message() will
                # if self.callback_after_update is not None:
                #    await self.callback_after_update(self)

                await self.client.disconnected_event.wait()
                self.client.connected_event.clear()

                # clear state so we know to send update when connection returns
                self.params = {"switch": "unknown"}
                self.client._info_cache = None

                self.logger.info(
                    "%s: Disconnected event, sending 'unavailable' update",
                    self.client.device_id,
                )

                if self.callback_after_update is not None:
                    await self.callback_after_update(self)

        finally:
            self.logger.debug("exiting send_availability_loop()")

    async def send_updated_params_loop(self):

        self.logger.debug(
            "send_updated_params_loop is active on the event loop"
        )

        retry_count = 0

        try:

            self.logger.debug(
                "Starting loop waiting for device params to change"
            )

            while True:
                self.logger.debug(
                    "send_updated_params_loop now awaiting event"
                )

                await self.params_updated_event.wait()

                await self.client.connected_event.wait()
                self.logger.debug("Connected!")

                update_message = self.client.get_update_payload(
                    self.device_id, self.params
                )

                try:
                    self.message_ping_event.clear()
                    self.message_acknowledged_event.clear()

                    await self.loop.run_in_executor(
                        None, self.client.send_switch, update_message
                    )

                    await asyncio.wait_for(
                        self.message_ping_event.wait(),
                        utils.calculate_retry(retry_count),
                    )

                    if self.message_acknowledged_event.is_set():
                        self.params_updated_event.clear()
                        self.logger.debug(
                            "Update message sent, event cleared, looping"
                        )
                        retry_count = 0
                    else:
                        self.logger.info(
                            "we didn't get a confirmed acknowledgement, "
                            "state has changed in between retry!"
                        )
                        retry_count += 1

                except asyncio.TimeoutError:
                    self.logger.warning(
                        "Device: %s. "
                        "Update message not received in timeout period, retry",
                        self.device_id,
                    )
                    retry_count += 1

                except asyncio.CancelledError:
                    self.logger.debug("send_updated_params_loop cancelled")
                    break

                except OSError as ex:
                    if retry_count == 0:
                        self.logger.warning(
                            "Connection issue for device %s: %s",
                            self.device_id,
                            format(ex),
                        )
                    else:
                        self.logger.debug(
                            "Connection issue for device %s: %s",
                            self.device_id,
                            format(ex),
                        )

                    await asyncio.sleep(utils.calculate_retry(retry_count))
                    retry_count += 1

                except Exception as ex:  # pragma: no cover
                    self.logger.error(
                        "send_updated_params_loop() [inner block] "
                        "Unexpected error for device %s: %s %s",
                        self.device_id,
                        format(ex),
                        traceback.format_exc(),
                    )
                    await asyncio.sleep(utils.calculate_retry(retry_count))
                    retry_count += 1

        except asyncio.CancelledError:
            self.logger.debug("send_updated_params_loop cancelled")

        except Exception as ex:  # pragma: no cover
            self.logger.error(
                "send_updated_params_loop() [outer block] "
                "Unexpected error for device %s: %s %s",
                self.device_id,
                format(ex),
                traceback.format_exc(),
            )

        finally:
            self.logger.debug("send_updated_params_loop finally block reached")

    def update_params(self, params):

        if self.params != params:

            self.logger.debug(
                "Scheduling params update message to device: %s" % params
            )
            self.params = params
            self.params_updated_event.set()
        else:
            self.logger.debug("unnecessary update received, ignoring")

    async def handle_message(self, message):

        self.logger.debug("enter handle_message() %s", message)

        # Null message shuts us down if we are CLI or sends update if API
        if message is None:
            if self.new_loop:
                self.shutdown_event_loop()
            else:
                await self.callback_after_update(self)
            return

        # Empty message sends update
        if message == {}:
            await self.callback_after_update(self)
            return

        """
        Receive message sent by the device and handle it, either updating
        state or storing basic device info
        """

        try:
            self.message_ping_event.set()

            response = json.loads(message.decode("utf-8"))

            if self.client.type == b"strip":

                if self.outlet is None:
                    self.outlet = 0

                switch_status = response["switches"][int(self.outlet)][
                    "switch"
                ]

            elif (
                self.client.type == b"plug"
                or self.client.type == b"diy_plug"
                or self.client.type == b"enhanced_plug"
                or self.client.type == b"th_plug"
            ):

                switch_status = response["switch"]

            else:
                self.logger.error(
                    "Unknown message received from device: " % message
                )
                raise Exception("Unknown message received from device")

            self.logger.debug(
                "Message: Received status from device, storing in instance"
            )
            self.basic_info = response
            self.basic_info["deviceid"] = self.host

            self.client.connected_event.set()
            self.logger.info(
                "%s: Connected event, sending 'available' update",
                self.client.device_id,
            )

            send_update = False

            # is there is a new message queued to be sent
            if self.params_updated_event.is_set():

                # only send client update message if the change successful
                if self.params["switch"] == switch_status:

                    self.message_acknowledged_event.set()
                    send_update = True
                    self.logger.debug(
                        "expected update received from switch: %s",
                        switch_status,
                    )

                else:
                    self.logger.info(
                        "failed update! state is: %s, expecting: %s",
                        switch_status,
                        self.params["switch"],
                    )

            else:
                # this is a status update message originating from the device
                # only send client update message if the status has changed

                self.logger.info(
                    "unsolicited update received from switch: %s",
                    switch_status,
                )

                if self.params["switch"] != switch_status:
                    self.params = {"switch": switch_status}
                    send_update = True

            if send_update and self.callback_after_update is not None:
                await self.callback_after_update(self)

        except Exception as ex:  # pragma: no cover
            self.logger.error(
                "Unexpected error in handle_message() for device %s: %s %s",
                self.device_id,
                format(ex),
                traceback.format_exc(),
            )

    def shutdown_event_loop(self):
        self.logger.debug("shutdown_event_loop called")

        try:
            # Hide Cancelled Error exceptions during shutdown
            def shutdown_exception_handler(loop, context):
                if "exception" not in context or not isinstance(
                    context["exception"], asyncio.CancelledError
                ):
                    loop.default_exception_handler(context)

            self.loop.set_exception_handler(shutdown_exception_handler)

            # Handle shutdown gracefully by waiting for all tasks
            # to be cancelled
            tasks = asyncio.all_tasks(loop=self.loop)

            for t in tasks:
                t.cancel()
        except Exception as ex:  # pragma: no cover
            self.logger.error(
                "Unexpected error in shutdown_event_loop(): %s", format(ex)
            )

    @property
    def device_id(self) -> str:
        """
        Get current device ID (immutable value based on hardware MAC address)

        :return: Device ID.
        :rtype: str
        """
        return self.client.properties[b"id"].decode("utf-8")

    async def turn_off(self) -> None:
        """
        Turns the device off.
        """
        raise NotImplementedError("Device subclass needs to implement this.")

    @property
    def is_off(self) -> bool:
        """
        Returns whether device is off.

        :return: True if device is off, False otherwise.
        :rtype: bool
        """
        return not self.is_on

    async def turn_on(self) -> None:
        """
        Turns the device on.
        """
        raise NotImplementedError(
            "Device subclass needs to implement this."
        )  # pragma: no cover

    @property
    def is_on(self) -> bool:
        """
        Returns whether the device is on.

        :return: True if the device is on, False otherwise.
        :rtype: bool
        :return:
        """
        raise NotImplementedError(
            "Device subclass needs to implement this."
        )  # pragma: no cover

    def __repr__(self):
        return "<%s at %s>" % (self.__class__.__name__, self.device_id)

    @property
    def available(self) -> bool:

        return self.client.connected_event.is_set()
