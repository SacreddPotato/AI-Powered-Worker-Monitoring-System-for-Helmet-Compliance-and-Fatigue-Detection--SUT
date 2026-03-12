import json
from channels.generic.websocket import WebsocketConsumer
from asgiref.sync import async_to_sync

class AlertConsumer(WebsocketConsumer):
    def connect(self):
        async_to_sync(self.channel_layer.group_add)('alerts', self.channel_name)
        self.accept()

    def disconnect(self, close_code):
        async_to_sync(self.channel_layer.group_discard)('alerts', self.channel_name)

    def alert_new(self, event):
        self.send(text_data=json.dumps({
            'type': 'alert.new',
            'alert': event['alert'],
        }))

    def alert_acknowledged(self, event):
        self.send(text_data=json.dumps({
            'type': 'alert.acknowledged',
            'alert_id': event['alert_id'],
        }))
