import concurrent.futures
import enum
import time

from supriya.enums import RequestName
from supriya.osc import HealthCheck, OscMessage, ThreadedOscProtocol


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

osc_protocol = ThreadedOscProtocol(
    name="",
    on_panic_callback=lambda: shutdown_future.set_result(ServerShutdownEvent.OSC_PANIC),
)


class Group:
    def __init__(self, osc_protocol, group_id):
        self.osc_protocol = osc_protocol
        self.group_id = group_id

    def free(self):
        msg = OscMessage(RequestName.NODE_FREE, self.group_id)
        self.osc_protocol.send(msg)

    def id(self):
        return self.group_id


def add_group(osc_protocol, group_id, add_action, target_node):
    msg = OscMessage(RequestName.GROUP_NEW, group_id, add_action, target_node)
    osc_protocol.send(msg)
    return Group(osc_protocol, group_id)


def add_synth(osc_protocol, synthdef_name, synth_id, add_action, target_node):
    msg = OscMessage(
        RequestName.SYNTH_NEW, synthdef_name, synth_id, add_action, target_node
    )
    osc_protocol.send(msg)


print("Connecting...")
osc_protocol.connect(
    ip_address="127.0.0.1",
    port=57110,
    healthcheck=DEFAULT_HEALTHCHECK,
)

time.sleep(3)

print("Creating group...")
g = add_group(osc_protocol, 34, 1, 1)

time.sleep(1)

print("Adding a synth...")
add_synth(osc_protocol, "default", 57, 1, g.id())

time.sleep(5)

print("Freeing synth...")
msg = OscMessage(RequestName.NODE_FREE, 57)
osc_protocol.send(msg)

time.sleep(1)

print("Freeing group...")
g.free()

time.sleep(1)

print("Disconnecting...")
osc_protocol.disconnect()
