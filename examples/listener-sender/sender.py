from stmp import STMPServer

app = STMPServer()

if __name__ == "__main__":
    app.broadcast("/test-route", "hi dear")
    # app.send_to_peer() # work only if peers are discovered (uses TCP)
