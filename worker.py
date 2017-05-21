import boto3


if __name__ == '__main__':
    # Connect to queue (SQS)
    sqs = boto3.resource("sqs")
    queue = sqs.get_queue_by_name(QueueName='filita')
    queue_url = queue.url

    # Connect to Data Store (S3 Bucket)
    s3client = boto3.client('s3')
    bucket_name = 'es-workflows-es'

    # Connect to SimpleDB
    conn_simpleDB = boto3.client('sdb')

    while (True):
        try:
            # Read message from queue
            client = boto3.client('sqs')
            response = client.receive_message(
            QueueUrl=queue_url,
            MaxNumberOfMessages=1
            )
            print(response)

            # Delete from queue
            delete = client.delete_message(QueueUrl=queue_url, ReceiptHandle=receiptHandle) #o que é se põe no receiptHandle?
            print(deleted)
        except Exception as e:
            print(e)
            pass
