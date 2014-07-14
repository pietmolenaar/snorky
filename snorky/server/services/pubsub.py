from snorky.server.services.base import RPCService, RPCError, rpc_command
from miau.common.types import MultiDict


class PubSubService(RPCService):
    def __init__(self, name):
        super(PubSubService, self).__init__(name)
        self.subscriptions = MultiDict() # channel : str -> set<Client>

    def do_publish(self, channel, message):
        for client in self.subscriptions.get_set(channel):
            self.send_message_to(client, {
                "type": "message",
                "channel": channel,
                "message": message
            })

    @rpc_command
    def publish(self, req, channel, message):
        if self.can_publish(req.client, channel):
            self.do_publish(channel, message)
        else:
            raise RPCError("Not authorized")

    @rpc_command
    def subscribe(self, req, channel):
        if self.subscriptions.in_set(channel, req.client):
            raise RPCError("Already subscribed")
        self.subscriptions.add(channel, req.client)

    @rpc_command
    def unsubscribe(self, req, channel):
        try:
            self.subscriptions.remove(channel, req.client)
        except KeyError:
            raise RPCError("Not subscribed")

    def can_publish(self, client, channel):
        return True


class PubSubBackend(RPCService):
    def __init__(self, name, frontend):
        super(PubSubBackend, self).__init__(name)
        self.frontend = frontend

    @rpc_command
    def publish(self, req, channel, message):
        self.frontend.do_publish(channel, message)
