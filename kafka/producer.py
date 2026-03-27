"""
Sample Kafka Producer

This producer demonstrates how to send messages to a Kafka topic.
It generates sample event data and streams it to the configured Kafka broker.

Usage:
    python producer.py
"""

import json
import time
from datetime import datetime
from kafka import KafkaProducer
from kafka.errors import KafkaError


def create_producer(bootstrap_servers='localhost:9092'):
    """
    Create and configure a Kafka producer.
    
    Args:
        bootstrap_servers (str): Comma-separated list of Kafka brokers
        
    Returns:
        KafkaProducer: Configured producer instance
    """
    return KafkaProducer(
        bootstrap_servers=bootstrap_servers,
        value_serializer=lambda v: json.dumps(v).encode('utf-8'),
        acks='all',
        retries=3,
        max_in_flight_requests_per_connection=1
    )


def delivery_report(record_metadata, error):
    """
    Callback for handling delivery reports.
    
    Args:
        record_metadata: Successfully delivered message metadata
        error: Delivery error
    """
    if error is not None:
        print(f"Message delivery failed: {error}")
    else:
        print(
            f"Message delivered to topic: {record_metadata.topic()} "
            f"[partition: {record_metadata.partition()}, offset: {record_metadata.offset()}]"
        )


def generate_sample_event(event_id):
    """
    Generate a sample event for streaming.
    
    Args:
        event_id (int): Unique event identifier
        
    Returns:
        dict: Sample event data
    """
    return {
        "event_id": event_id,
        "timestamp": datetime.utcnow().isoformat(),
        "user_id": f"user_{event_id % 100}",
        "action": ["login", "logout", "purchase", "view", "click"][event_id % 5],
        "amount": round((event_id % 1000) * 0.5, 2),
        "region": ["US", "EU", "APAC", "LATAM"][event_id % 4]
    }


def produce_events(topic='events', num_events=10, interval=1):
    """
    Produce sample events to a Kafka topic.
    
    Args:
        topic (str): Target Kafka topic
        num_events (int): Number of events to produce
        interval (float): Interval between events in seconds
    """
    producer = create_producer()
    
    try:
        for i in range(num_events):
            event = generate_sample_event(i)
            
            # Send message
            future = producer.send(topic, event)
            
            # Get result
            try:
                record_metadata = future.get(timeout=10)
                print(f"Event {i}: Sent to {topic}")
            except KafkaError as err:
                print(f"Event {i}: Failed to send - {err}")
            
            time.sleep(interval)
    
    except KeyboardInterrupt:
        print("\nProducer interrupted")
    finally:
        producer.flush()
        producer.close()
        print("Producer closed")


if __name__ == '__main__':
    # Example: Produce 100 events with 1 second interval
    produce_events(
        topic='events',
        num_events=100,
        interval=1
    )
