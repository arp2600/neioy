import concurrent.futures
import enum
from contextlib import contextmanager

from supriya.enums import RequestName
from supriya.osc import HealthCheck, OscMessage, OscBundle, ThreadedOscProtocol

DEFAULT_GROUP = 1


class AddAction(enum.Enum):
    ADD_TO_HEAD = 0
    ADD_TO_TAIL = 1
    ADD_BEFORE = 2
    ADD_AFTER = 3
    REPLACE = 4


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
        self._server._free_node(self._uid)

    def uid(self):
        return self._uid


class Synth:
    def __init__(self, server, uid):
        self._server = server
        self._uid = uid

    def free(self):
        self._server._free_node(self._uid)

    def set(self, name, value):
        self._server.send_message(RequestName.NODE_SET, self._uid, name, value)

    def setn(self, name, *values):
        self._server.send_message(
            RequestName.NODE_SET_CONTIGUOUS, self._uid, name, len(values), *values
        )

    def uid(self):
        return self._uid


class _MessageSender:
    def __init__(self, osc_protocol):
        self._osc_protocol = osc_protocol

    def __call__(self, msg):
        self._osc_protocol.send(msg)


class _BundleMessageSender:
    def __init__(self, osc_protocol, timestamp):
        self._osc_protocol = osc_protocol
        self._timestamp = timestamp
        self._contents = []

    def __call__(self, msg):
        self._contents.append(msg)

    def send_bundle(self):
        bundle = OscBundle(timestamp=self._timestamp, contents=self._contents)
        self._osc_protocol.send(bundle)


class Server:
    def __init__(self):
        self._next_uid = 1234
        self._osc_protocol = ThreadedOscProtocol(
            name="",
            on_panic_callback=lambda: shutdown_future.set_result(
                ServerShutdownEvent.OSC_PANIC
            ),
        )

        self._send_message = _MessageSender(self._osc_protocol)

    @contextmanager
    def bundle(self, timestamp):
        old_send_message = self._send_message
        self._send_message = _BundleMessageSender(self._osc_protocol, timestamp)

        yield None

        self._send_message.send_bundle()
        self._send_message = old_send_message

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
        self._send_message(msg)

    def _free_node(self, uid):
        self.send_message(RequestName.NODE_FREE, uid)

    def _get_next_uid(self):
        result = self._next_uid
        self._next_uid += 1
        return result

    def add_group(self, add_action, target_node=DEFAULT_GROUP):
        uid = self._get_next_uid()
        self.send_message(RequestName.GROUP_NEW, uid, add_action, target_node)
        return Group(self, uid)

    def add_synth(
        self,
        synthdef_name,
        *args,
        target=DEFAULT_GROUP,
        add_action=AddAction.ADD_TO_HEAD
    ):
        if hasattr(target, "uid"):
            target = target.uid()

        uid = self._get_next_uid()
        self.send_message(
            RequestName.SYNTH_NEW, synthdef_name, uid, add_action, target, *args
        )
        return Synth(self, uid)
        # msg = OscMessage(
        #     RequestName.SYNTH_NEW, synthdef_name, synth_id, add_action, target_node, *args
        # )
        # osc_protocol.send(msg)
        # bundle = OscBundle(timestamp=t.beats2seconds(t.beats()) + LATENCY, contents=(msg,))
        # osc_protocol.send(bundle)
