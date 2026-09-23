import aio_pika
from .events import DomainEvent

EXCHANGE_NAME = "sigtpi.events"

async def publish_event(rabbitmq_url: str, event: DomainEvent) -> None:
    connection = await aio_pika.connect_robust(rabbitmq_url)
    async with connection:
        channel = await connection.channel()
        exchange = await channel.declare_exchange(EXCHANGE_NAME, aio_pika.ExchangeType.TOPIC, durable=True)
        message = aio_pika.Message(
            body=event.model_dump_json().encode(),
            content_type="application/json",
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
            message_id=str(event.event_id),
        )
        await exchange.publish(message, routing_key=str(event.event_type))
