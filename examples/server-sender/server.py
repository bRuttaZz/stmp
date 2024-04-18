from stp import STPServer
from stp.interfaces import Packet, Peer

app = STPServer()


@app.route("/test-route")
def test_route_func(packet: Packet):
    print(f"Message got from {packet.headers.user}@{packet.sender} : {packet.data}")


# bind events
@app.on_peer_list_update
def peer_list_change(new_peer: Peer, removed_peers: list[Peer]):
    print(
        f"Peer list changed : new peer -> {new_peer.user}@{new_peer.ip}"
        + f" : removed peers -> {len(removed_peers)}"
    )


if __name__ == "__main__":
    print("starting server ...")
    app.run()
