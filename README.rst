=============
pysonoff
=============

Control Sonoff devices running original firmware, in LAN mode.
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To control Sonoff switches running the V3+ Itead firmware (tested on 3.0, 3.0.1, 3.1.0, 3.3.0, 3.4.0, 3.5.0), locally (LAN mode).

Unfortunately @AlexxIT has not (yet) made his component callable outside of Home Assistant, but since I'm not using this component, I will not be maintaining it. Sorry.

**This will only work for Sonoff devices running V3+ of the stock (Itead / eWeLink) firmware. For users of V1.8.0 - V2.6.1, please use**  `pysonoff <https://pypi.org/project/pysonoff/>`_


This module provides a way to interface with Sonoff smart home devices,
such as smart switches (e.g. Sonoff Basic), plugs (e.g. Sonoff S20),
and wall switches (e.g. Sonoff Touch), when these devices are in LAN Mode.

LAN Mode is a feature introduced by manufacturer Itead, to allow operation
locally when their servers are unavailable.
Further details can be found in the `eWeLink LAN Mode guide`__.

__ https://help.ewelink.cc/hc/en-us/articles/360007134171-LAN-Mode-Tutorial

Since mid 2018, the firmware Itead have shipped with most Sonoff devices
has provided this feature, allowing devices to be controlled directly
on the local network using a WebSocket connection on port 8081.

Features
--------

* Discover all devices on local network
* Read device state
* Switch device ON/OFF
* Listen for state changes announced by the device (e.g. by physical switch)
* Activate inching/momentary device, with variable ON time (e.g. 1s)

Install
------------------
::

    $ pip install pysonoff@git+https://github.com/sarusani/pysonoff

Command-Line Usage
------------------
::

    Usage: pysonoff [OPTIONS] COMMAND [ARGS]...

      A cli tool for controlling Sonoff Smart Switches/Plugs in LAN Mode.

    Options:
      --host TEXT          IP address or hostname of the device to connect to.
      --device_id TEXT     Device ID of the device to connect to.
      --inching TEXT       Number of seconds of "on" time if this is an
                           Inching/Momentary switch.
      -l, --level LVL  Either CRITICAL, ERROR, WARNING, INFO or DEBUG
      --help               Show this message and exit.
      --api_key KEY        Needed for devices not in DIY mode. See https://pysonoff.readthedocs.io/encryption.html
      
    Commands:
      discover  Discover devices in the network
      listen    Connect to device, print state and repeat
      off       Turn the device off.
      on        Turn the device on.
      state     Connect to device and print current state.

Usage Example
=======================
::

    $ pysonoff discover
    2019-01-31 00:45:32,074 - info: Attempting to discover Sonoff LAN Mode devices on the local network, please wait...
    2019-01-31 00:46:24,007 - info: Found Sonoff LAN Mode device at IP 192.168.0.77

    $ pysonoff --host 192.168.0.77 state
    2019-01-31 00:41:34,931 - info: Initialising SonoffSwitch with host 192.168.0.77
    2019-01-31 00:41:35,016 - info: == Device: 10006866e9 (192.168.0.77) ==
    2019-01-31 00:41:35,016 - info: State: OFF

    $ pysonoff --host 192.168.0.77 on
    2019-01-31 00:49:40,334 - info: Initialising SonoffSwitch with host 192.168.0.77
    2019-01-31 00:49:40,508 - info:
    2019-01-31 00:49:40,508 - info: Initial state:
    2019-01-31 00:49:40,508 - info: == Device: 10006866e9 (192.168.0.77) ==
    2019-01-31 00:49:40,508 - info: State: OFF
    2019-01-31 00:49:40,508 - info:
    2019-01-31 00:49:40,508 - info: New state:
    2019-01-31 00:49:40,508 - info: == Device: 10006866e9 (192.168.0.77) ==
    2019-01-31 00:49:40,508 - info: State: ON

Library Usage
------------------

All common, shared functionality is available through :code:`SonoffSwitch` class::

    x = SonoffSwitch("192.168.1.50")

Upon instantiating the SonoffSwitch class, a connection is
initiated and device state is populated, but no further action is taken.

For most use cases, you'll want to make use of the :code:`callback_after_update`
parameter to do something with the device after a connection has been
initialised, for example::

    async def print_state_callback(device):
        if device.basic_info is not None:
            print("ON" if device.is_on else "OFF")
            device.shutdown_event_loop()

    SonoffSwitch(
        host="192.168.1.50",
        callback_after_update=print_state_callback
    )

This example simply connects to the device, prints whether it is currently
"ON" or "OFF", then closes the connection. Note, the callback must be
asynchronous.

Module-specific errors are raised as Exceptions, and are expected
to be handled by the user of the library.

License
-------

* Free software: MIT license

Credits
-------

This package was created with Cookiecutter_ and the `audreyr/cookiecutter-pypackage`_ project template.

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`audreyr/cookiecutter-pypackage`: https://github.com/audreyr/cookiecutter-pypackage

[ ~ Dependencies scanned by PyUp.io ~ ]
