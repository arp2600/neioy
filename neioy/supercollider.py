import concurrent.futures
import enum

from supriya.enums import RequestName
from supriya.osc import HealthCheck, OscMessage, OscBundle, ThreadedOscProtocol


class ServerShutdownEvent(enum.Enum):
    QUIT = enum.auto()
    DISCONNECT = enum.auto()
    OSC_PANIC = enum.auto()
    PROCESS_PANIC = enum.auto()
    TOO_MANY_CLIENTS = enum.auto()


DEFAULT_HEALTHCHECK = HealthCheck(
    active=False,
    backoff_factor=1.5,
    max_attempts=5,
    request_pattern=["/status"],
    response_pattern=["/status.reply"],
    timeout=1.0,
)

shutdown_future: concurrent.futures.Future[ServerShutdownEvent] = (
    concurrent.futures.Future()
)


class Group:
    def __init__(self, server, uid):
        self._server = server
        self._uid = uid

    def free(self):
        self._server._free_node(self.uid)

    def uid(self):
        return self._uid


class Synth:
    def __init__(self, server, uid):
        self._server = server
        self._uid = uid

    def free(self):
        self._server._free_node(self.uid)

    def uid(self):
        return self._uid


class Server:
    def __init__(self):
        self._next_uid = 1234
        self._osc_protocol = ThreadedOscProtocol(
            name="",
            on_panic_callback=lambda: shutdown_future.set_result(
                ServerShutdownEvent.OSC_PANIC
            ),
        )

    def connect(self, ip_address="127.0.0.1", port=57110):
        print("Connecting...")
        self._osc_protocol.connect(
            ip_address=ip_address,
            port=port,
            healthcheck=DEFAULT_HEALTHCHECK,
        )

    def disconnect(self):
        self._osc_protocol.disconnect()

    def send_message(self, *args):
        msg = OscMessage(*args)
        self._osc_protocol.send(msg)

    def _free_node(self, uid):
        self.send_message(RequestName.NODE_FREE, uid)

    def _get_next_uid(self):
        result = self._next_uid
        self._next_uid += 1
        return result

    def add_group(self, add_action, target_node):
        uid = self._get_next_uid()
        self.send_message(RequestName.GROUP_NEW, uid, add_action, target_node)
        return Group(self, uid)

    def add_synth(self, synthdef_name, add_action, target, *args):
        uid = self._get_next_uid()
        self.send_message(
            RequestName.SYNTH_NEW, synthdef_name, uid, add_action, target.uid(), *args
        )
        return Synth(self, uid)
        # msg = OscMessage(
        #     RequestName.SYNTH_NEW, synthdef_name, synth_id, add_action, target_node, *args
        # )
        # osc_protocol.send(msg)
        # bundle = OscBundle(timestamp=t.beats2seconds(t.beats()) + LATENCY, contents=(msg,))
        # osc_protocol.send(bundle)
