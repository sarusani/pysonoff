import sys
import socket
import time
import threading
import subprocess
from flask import Flask, json, request, abort
from zeroconf import Zeroconf, ServiceInfo
from pysonoff import sonoffcrypto


next_port = 8082  # to stop conflicting with command line by default


class MockController:
    def __init__(self, cmd):

        self._p = subprocess.Popen(["python", "sonoff_mock.py", cmd])
        self._p.start()

    def stop_server(self):
        self._p.terminate()

    def stop_server_in(self, seconds):
        def stop(self, seconds):
            time.sleep(seconds)
            self.stop_server()

        self._p = threading.Thread(target=stop)
        self._p.start()


class SonoffLANModeDeviceMock:
    def __init__(self, name, sonoff_type, api_key, ip, port, error_mock=None):

        self._name = name
        self._sonoff_type = sonoff_type
        self._api_key = api_key
        self._ip = ip
        self._port = port
        self._error_code = 0

        if self._name is None:
            self._name = ""

        print("Device __init__ %s" % self._name)

        if self._sonoff_type is None:
            self._sonoff_type = "plug"

        if self._api_key == "None" or self._api_key is None:
            print("No Encryption")
            self._encrypt = False
        else:
            self._encrypt = True

        if self._ip is None:
            self._ip = "127.0.0.1"

        if self._port is None:
            global next_port
            self._port = next_port
            next_port += 1

        self._status = "off"

        self.register()

        self.mock_error(error_mock)

    def mock_error(self, error_mock):

        if error_mock == "Disconnect":

            def disconnect():
                self.disconnect()

            self._p = threading.Thread(target=disconnect)
            self._p.start()

        elif error_mock == "Reconnect":

            def reconnect():
                self.reconnect()

            self._p = threading.Thread(target=reconnect)
            self._p.start()

    def reconnect(self):

        try:
            print("....waiting")

            time.sleep(5)

            print("....deregister")

            self._error_code = 0
            self.deregister()

            time.sleep(5)

            print("....register")

            self.register()

        except Exception as Ex:
            print(Ex)

    def disconnect(self):

        try:
            print("....waiting")

            time.sleep(5)

            print("....deregister")

            self._error_code = 500
            self.deregister()

            time.sleep(5)

            print("....register")

            self.register()

        except Exception as Ex:
            print(Ex)

    def run_server(self):

        api = Flask(self._name)

        @api.route("/zeroconf/switch", methods=["POST"])
        @api.route("/zeroconf/switches", methods=["POST"])
        # pylint: disable=unused-variable
        def post_switch():

            try:

                print("Device %s, Received: %s" % (self._name, request.json))

                if request.json["deviceid"] == self._name:
                    self.process_request(request.json)

                    return (
                        json.dumps(
                            {"seq": 1, "sequence": "1577725767", "error": 0}
                        ),
                        200,
                    )

                else:
                    print("wrong device")
                    abort(404)

            except Exception as Ex:
                print(Ex)
                abort(500)

        @api.route("/zeroconf/signal_strength", methods=["POST"])
        # pylint: disable=unused-variable
        def post_signal():

            print("Device %s, Received: %s" % (self._name, request.json))

            if request.json["deviceid"] == self._name:

                if self._error_code != 0:
                    abort(self._error_code)

                else:

                    return (
                        json.dumps(
                            {"seq": 1, "sequence": "1577725767", "error": 0}
                        ),
                        200,
                    )

            else:
                print("wrong device")
                abort(404)

        def start():
            api.run(host=self._ip, port=self._port)

        print("starting device: %s" % self._name)
        t = threading.Thread(target=start)
        t.daemon = True
        t.start()
        print("device started: %s" % self._name)

    def register(self):

        self._properties = dict(id=self._name, type=self._sonoff_type,)

        self.set_data()
        self._zeroconf_registrar = Zeroconf(interfaces=[self._ip])
        self._zeroconf_registrar.register_service(self.get_service_info())

    def deregister(self):

        self._zeroconf_registrar.unregister_service(self.get_service_info())

    def get_service_info(self):

        type_ = "_ewelink._tcp.local."
        registration_name = "eWeLink_%s.%s" % (self._name, type_)

        service_info = ServiceInfo(
            type_,
            registration_name,
            socket.inet_aton(self._ip),
            port=self._port,
            properties=self._properties,
            server="eWeLink_" + self._name + ".local.",
        )

        return service_info

    def set_data(self):

        if self._sonoff_type == "strip":

            data = (
                '{"sledOnline":"on",'
                '"configure":['
                '{"startup":"off","outlet":0},{"startup":"off","outlet":1},'
                '{"startup":"off","outlet":2},{"startup":"off","outlet":3}],'
                '"pulses":['
                '{"pulse":"off","width":1000,"outlet":0},'
                '{"pulse":"off","width":1000,"outlet":1},'
                '{"pulse":"off","width":1000,"outlet":2},'
                '{"pulse":"off","width":1000,"outlet":3}],'
            )

            if self._status == "on":
                data += (
                    '"switches":[{"switch":"on","outlet":0},'
                    '{"switch":"off","outlet":1},{"switch":"off",'
                    '"outlet":2},{"switch":"on","outlet":3}]}'
                )

            else:
                data += (
                    '"switches":[{"switch":"off","outlet":0},'
                    '{"switch":"off","outlet":1},'
                    '{"switch":"off","outlet":2},'
                    '{"switch":"on","outlet":3}]}'
                )

        else:

            if self._status == "on":
                data = (
                    '{"switch":"on","startup":"stay","pulse":"off",'
                    '"sledOnline":"off","pulseWidth":500,"rssi":-55}'
                )
            else:
                data = (
                    '{"switch":"off","startup":"stay","pulse":"off",'
                    '"sledOnline":"off","pulseWidth":500,"rssi":-55}'
                )

        if self._encrypt:
            data = sonoffcrypto.format_encryption_txt(
                self._properties, data, self._api_key
            )

        self.split_data(data)

    def split_data(self, data):

        if len(data) <= 249:
            self._properties["data1"] = data

        else:
            self._properties["data1"] = data[0:249]
            data = data[249:]

            if len(data) <= 249:
                self._properties["data2"] = data

            else:
                self._properties["data2"] = data[0:249]
                data = data[249:]

                if len(data) <= 249:
                    self._properties["data3"] = data

                else:
                    self._properties["data3"] = data[0:249]
                    self._properties["data4"] = data[249:]

    def get_status_from_data(self, data):

        if self._sonoff_type == "strip":
            return data["switches"][0]["switch"]

        else:
            return data["switch"]

    def process_request(self, json_):

        if json_["encrypt"] is True:
            iv = json_["iv"]
            data = sonoffcrypto.decrypt(json_["data"], iv, self._api_key)
            import json

            data = json.loads(data.decode("utf-8"))

        else:
            print(json_)
            data = json_["data"]

        print(data)

        self._status = self.get_status_from_data(data)
        self.set_data()

        print("Updated Properties: %s" % self._properties)

        self._zeroconf_registrar.update_service(self.get_service_info())


def start_device(
    name=None, sonoff_type=None, api_key=None, ip=None, port=None, error=None
):

    device = SonoffLANModeDeviceMock(
        name, sonoff_type, api_key, ip, port, error
    )
    device.run_server()

    # device = MockController(name, sonoff_type, api_key, ip, port)


def stop_device():
    pass


if __name__ == "__main__":

    name = None
    sonoff_type = None
    api_key = None
    ip = None
    port = 8081  # use 8081 as default port form command line
    error = None

    try:
        name = sys.argv[1]
        sonoff_type = sys.argv[2]
        api_key = sys.argv[3]
        ip = sys.argv[4]
        port = int(sys.argv[5])
        error = sys.argv[6]
    except IndexError:
        pass

    start_device(name, sonoff_type, api_key, ip, port, error)

    try:
        input("Press enter to exit...\n\n")

    finally:
        device = None
