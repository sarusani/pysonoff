History
=======


1.1.5 (2023-07-30)
------------------
* Fixed zeroconf behaviour
* Renamed to pysonoff

1.1.4 (2020-03-29)
------------------
* Enabled code to work if device IP address changes
* Fixed faulty CLI introduced with 1.1.3 (https://github.com/mattsaxon/pysonofflan/issues/65)
* Removed previous workaround code for earlier version of zeroconf (<=24.4)

1.1.3 (2020-02-16)
------------------
* Fixed issue of reconnection that device remains unavailable until state changes
* Fixed retry code for strip type devices

1.1.2 (deleted release)
-----------------------

1.1.1 (2020-02-01)
------------------
* Optimisations to deal with later zeroconf versions which have some different behaviour
* Improved error handling of unexpected errors

1.1.0 (2020-01-10)
------------------
* First release on PyPI.
* Forked from PySonoffLAN package (courtesy of Andrew Beveridge)
* Works on V3 Itead firmware using mDNS for service discovery and REST for service invocation
* Supports DIY mode as well as 'standard' mode (for standard mode API key is needed to be obtained, e.g. by sniffing LAN)
* Supports all known devices for switching, although no sensors added at this point
