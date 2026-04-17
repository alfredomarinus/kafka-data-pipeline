from datetime import datetime, timedelta
import json
import logging
from typing import Dict, List, Any

from airflow.sdk import dag, task
from airflow.providers.postgres.hooks.postgres import PostgresHook
from kafka import KafkaConsumer
from kafka.errors import KafkaError

# Configure logging
logger = logging.getLogger(__name__)

@dag(
    dag_id='kafka_consumer_pipeline',
    description='Consume from Kafka and store in PostgreSQL',
    schedule=None,
    start_date=datetime(2024, 1, 1),
    catchup=False,
    default_args={
        'owner': 'airflow',
        'retries': 2,
        'retry_delay': timedelta(minutes=1),
    },
    tags=['kafka', 'pipeline'],
)
def kafka_consumer_pipeline():
    """
    TaskFlow DAG that orchestrates Kafka consumption and PostgreSQL storage.
    """

    @task(task_id='consume_kafka')
    def consume_from_kafka(topic: str = 'my_stream_topic', num_messages: int = 10) -> Dict[str, Any]:
        logger.info(f"Starting to consume from topic: {topic}")

        # Generate unique consumer group for this run
        unique_group_id = f'airflow-consumer-group-{datetime.now().timestamp()}'
        
        consumer = KafkaConsumer(
            topic,
            bootstrap_servers=['kafka:9092'],
            auto_offset_reset='earliest',
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            group_id=unique_group_id,
            session_timeout_ms=30000,
            consumer_timeout_ms=5000,
        )

        messages = []
        msg_count = 0

        try:
            for message in consumer:
                if message is None:
                    logger.info(f"Consumer timeout reached after {msg_count} messages")
                    break
                
                messages.append(message.value)
                msg_count += 1
                logger.info(f"Consumed message {msg_count}: {message.value}")

                if msg_count >= num_messages:
                    break
        except KafkaError as e:
            logger.error(f"Kafka error: {e}")
        finally:
            consumer.close()

        logger.info(f"Consumed {msg_count} messages from {topic}")

        return {
            'messages_consumed': msg_count,
            'topic': topic,
            'messages': messages,
        }

    @task(task_id='process_messages')
    def process_kafka_messages(consume_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process messages from Kafka.

        Args:
            consume_result: Result from consume_from_kafka task containing messages

        Returns:
            Dictionary with processed messages and metadata
        """
        messages = consume_result.get('messages', [])

        if not messages:
            logger.warning("No messages to process")
            return {'processed_count': 0, 'messages': []}

        logger.info(f"Processing {len(messages)} messages")

        processed = []
        for msg in messages:
            # Example processing: enrich with processing timestamp
            processed.append({
                'event_id': msg.get('event_id'),
                'user_id': msg.get('user_id'),
                'action': msg.get('action'),
                'amount': msg.get('amount'),
                'region': msg.get('region'),
                'timestamp': msg.get('timestamp'),
                'processed_at': datetime.utcnow().isoformat(),
            })

        logger.info(f"Processed {len(processed)} messages")

        return {'processed_count': len(processed), 'messages': processed}

    @task(task_id='store_postgres')
    def store_in_postgres(process_result: Dict[str, Any]) -> Dict[str, int]:
        """
        Store processed messages in PostgreSQL.

        Args:
            process_result: Result from process_kafka_messages task

        Returns:
            Dictionary with number of stored records
        """
        messages = process_result.get('messages', [])

        if not messages:
            logger.warning("No processed messages to store")
            return {'stored_count': 0}

        # Connect to PostgreSQL
        postgres_hook = PostgresHook(postgres_conn_id='postgres_default')

        # Create table if not exists
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS kafka_events (
            id SERIAL PRIMARY KEY,
            event_id INTEGER,
            user_id VARCHAR(255),
            action VARCHAR(50),
            amount FLOAT,
            region VARCHAR(50),
            timestamp VARCHAR(255),
            processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """

        postgres_hook.run(create_table_sql)
        logger.info("Table kafka_events created/verified")

        # Insert messages
        insert_sql = """
        INSERT INTO kafka_events (event_id, user_id, action, amount, region, timestamp, processed_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s);
        """

        rows = [
            (
                msg['event_id'],
                msg['user_id'],
                msg['action'],
                msg['amount'],
                msg['region'],
                msg['timestamp'],
                datetime.utcnow(),
            )
            for msg in messages
        ]

        postgres_hook.insert_rows(
            table='kafka_events',
            rows=rows,
            target_fields=['event_id', 'user_id', 'action', 'amount', 'region', 'timestamp', 'processed_at'],
        )

        logger.info(f"Stored {len(rows)} messages in PostgreSQL")

        return {'stored_count': len(rows)}

    @task(task_id='summarize_pipeline')
    def summarize_pipeline(consume_result: Dict, process_result: Dict, store_result: Dict) -> Dict[str, int]:
        """
        Summarize the pipeline execution.

        Args:
            consume_result: Result from consume_kafka task
            process_result: Result from process_messages task
            store_result: Result from store_postgres task

        Returns:
            Summary dictionary with counts from each stage
        """
        summary = {
            'consumed': consume_result.get('messages_consumed', 0),
            'processed': process_result.get('processed_count', 0),
            'stored': store_result.get('stored_count', 0),
        }

        logger.info(f"Pipeline Summary: {summary}")

        return summary

    # Task orchestration using TaskFlow API
    # Dependencies are implicit through function parameters
    consume_result = consume_from_kafka(topic='prototype-events', num_messages=500)
    process_result = process_kafka_messages(consume_result)
    store_result = store_in_postgres(process_result)
    summarize_pipeline(consume_result, process_result, store_result)

# Instantiate the DAG
kafka_pipeline_dag = kafka_consumer_pipeline()