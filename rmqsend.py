import pika
import os


def send(msg):
	connection = pika.BlockingConnection(pika.ConnectionParameters(host = os.environ["HS_RMQ_PORT_25672_TCP_ADDR"]))
	channel = connection.channel()
	channel.queue_declare(queue = 'hello')
	channel.basic_publish(exchange = '', routing_key = 'hello', body = msg)  # TODO проверить на валидность msg
