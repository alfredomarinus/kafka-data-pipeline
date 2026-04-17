import json
import time
from datetime import datetime, timezone
from kafka import KafkaProducer
from kafka.errors import KafkaError
import random

def create_producer(bootstrap_servers='kafka:9092'):
    return KafkaProducer(
        bootstrap_servers=bootstrap_servers,
        value_serializer=lambda v: json.dumps(v).encode('utf-8'),
        acks=1,  # Only wait for leader acknowledgment
        retries=3,
        max_in_flight_requests_per_connection=5,  # Pipeline multiple requests
        batch_size=16384,  # Batch messages (16KB)
        linger_ms=10,  # Wait 10ms to batch messages
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
    Generate more realistic sample events with better randomization.
    
    Args:
        event_id (int): Unique event identifier
        
    Returns:
        dict: Sample event data
    """
    return {
        "event_id": event_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "user_id": f"user_{random.randint(1, 500)}",  # 500 unique users instead of 100
        "action": random.choice(["login", "logout", "purchase", "view", "click"]),
        "amount": round(random.uniform(10, 500), 2),  # Random amounts 10-500
        "region": random.choice(["US", "EU", "APAC", "LATAM"])
    }

def produce_events(topic='events', num_events=10, interval=0):
    """
    Produce sample events to a Kafka topic.
    
    Args:
        topic (str): Target Kafka topic
        num_events (int): Number of events to produce
        interval (float): Interval between events in seconds (default 0)
    """
    producer = create_producer()
    
    try:
        for i in range(num_events):
            event = generate_sample_event(i)
            
            # Send with proper callbacks
            future = producer.send(topic, event)
            future.add_callback(delivery_report)
            future.add_errback(lambda err: delivery_report(None, err))
            
            print(f"Event {i}: Sent to {topic}")
            
            if interval > 0:
                time.sleep(interval)
    
    except KeyboardInterrupt:
        print("\nProducer interrupted")
    finally:
        producer.flush(timeout=30)
        producer.close()
        print("Producer closed")

if __name__ == '__main__':
    # Example: Produce 500 events with 0 second interval (as fast as possible)
    produce_events(
        topic='prototype-events',
        num_events=500,
        interval=0  # Remove the 1-second delay!
    )