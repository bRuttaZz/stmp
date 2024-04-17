# STP : Sitty Talky Protocol
⚠️ **Work In Progress**
⚠️ Beware of the buzzword Spanig Tree Protocol. The STP described over here is much more stupid..
Sitty Talky Protocol : A primitive protocol purely written in python for tinkering with your office mates over LAN!


STP uses udp for peer finding and broadcasting (actually it's multicasting (reducing trafic (being a good citizon)))
and TCP for peer to peer connection (usual things)

### Requirements
- **Python version >= 3.11** (As it currently uses `loop.sock_recvfrom` in `asyncio`, Otherwise should go with the `loop.run_in_executor`, which I am not interested on)

- **The system is tested only on Unix (GNU/Linux to be specific)**

### Usage
**A simple use case is demonstated bellow**

starting the server
```py
from src import STPServer
from src.interfaces import Packet, Peer

app = STPServer()

@app.route("/test-route")
def test_route_func(packet:Packet):
    print(f"Message got from {packet.headers.user}@{packet.sender} : {packet.data}")

# bind events
@app.on_peer_list_update
def peer_list_change(new_peer:Peer, removed_peers:list[Peer]):
    print(f"Peer list changed : new peer -> {new_peer.user}@{new_peer.ip}" +
                f" : removed peers -> {len(removed_peers)}")
    
if __name__=="__main__":
    print(f"starting server ...")
    app.run()
```

sending messages to the client over a LAN network
```py
from src import STPServer

app = STPServer()
    
if __name__=="__main__":
    app.broadcast("/test-route", "hi dear")
    # app.send_to_peer() # work only if peers are discovered (uses TCP)
```

### The module architecture

<img src="./.assets/stp.excalidraw.svg">


