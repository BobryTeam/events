from queue import Queue

import threading
from threading import Thread

from kafka import KafkaConsumer, KafkaProducer

from event import *


MESSAGE_ENCODING = 'utf-8'


class KafkaEventReader:
    '''
    Класс, который считывает сообщения с кафки и сохраняет их в виде ивентов
    '''

    def __init__(self, kafka_consumer: KafkaConsumer, event_queue: Queue):
        '''
        Подготовка к считыванию сообщений
        '''
        self.consumer = kafka_consumer

        self.running = threading.Event()
        self.running.set()

        self.event_queue = event_queue

        self.reading_thread = Thread(target=self.read_events)
        self.reading_thread.start()

    def read_events(self):
        '''
        Считывание сообщений от кафки, превращение их в ивенты, сохранение в очередь ивентов
        Запущен на отдельном потоке для постоянного считывания новых сообщений
        '''
        while self.running.is_set():
            message_pack = self.consumer.poll(timeout_ms=1000)

            for _topic, messages in message_pack.items():
                for message in messages:
                    self.event_queue.put(EventFromMessage(message.value.decode(MESSAGE_ENCODING)))

    def release(self):
        '''
        Отключение от кафки
        '''
        self.running.clear()
        self.consumer.close()


class KafkaEventWriter:
    '''
    Класс, который превращает ивенты в сообщения и отправляет их в кафку
    '''

    def __init__(self, kafka_producer: KafkaProducer, topic: str):
        '''
        Инициализация класса
        '''
        self.topic = topic
        self.producer = kafka_producer

    def send_event(self, event: Event):
        '''
        Отправка ивента превращенного в сообщение
        '''
        message = str(event)
        self.producer.send(self.topic, message.encode(MESSAGE_ENCODING))

    def release(self):
        '''
        Отключение от кафки
        '''
        self.producer.close()
