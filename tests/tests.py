"""Test SQS responses."""
import boto3
import botocore.endpoint
import os
import unittest


def get_url():
    """Return the url for the SQS server."""
    host = os.environ.get('SQS_IP', '127.0.0.1')
    port = os.environ.get('SQS_PORT', '8080')
    return 'http://{}:{}'.format(host, port)


class SQSTestCase(unittest.TestCase):
    """Testcase for sqs docker container."""

    def setUp(self):
        """Setup testcase."""
        class MockEndpoint(botocore.endpoint.Endpoint):
            def __init__(self, host, *args, **kwargs):
                url = get_url()
                super().__init__(url, *args, **kwargs)

        botocore.endpoint.Endpoint = MockEndpoint
        super().setUp()

    def get_queue(self):
        """Return a SQS Queue."""
        queue_name = 'foobar'
        sqs = boto3.resource('sqs')
        sqs.create_queue(QueueName=queue_name)
        queue = sqs.get_queue_by_name(QueueName=queue_name)
        # Cleanup messages
        for message in queue.receive_messages(MaxNumberOfMessages=100):
            message.delete()
        return queue

    def test_create_queue(self):
        """Create a queue."""
        queue = self.get_queue()
        self.assertIsNotNone(queue)
        self.assertEqual(queue.__class__.__name__, 'sqs.Queue')

    def test_handle_message(self):
        """Write and read message."""
        from datetime import datetime
        import json
        body = {'hello': 'world'}
        queue = self.get_queue()
        resp = queue.send_message(
            MessageBody=json.dumps(body),
            MessageAttributes={
                'Origin': {'StringValue': 'testcase', 'DataType': 'String'},
                'Author': {'StringValue': 'RideLink', 'DataType': 'String'},
                'CreationDate': {'StringValue': str(datetime.now()), 'DataType': 'String'}
            }
        )
        self.assertIsNotNone(resp)
        message_id = resp.get('MessageId').strip()
        self.assertIsNotNone(message_id)
        messages = queue.receive_messages(MaxNumberOfMessages=100)

        self.assertIsInstance(messages, list)
        self.assertEqual(len(messages), 1)

        message = messages[0]
        self.assertEqual(json.loads(message.body), body)
