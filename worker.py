import boto3
from botocore.client import Config

if __name__ == '__main__':
    # Connect to queue (SQS)
    sqs = boto3.resource("sqs")
    queue = sqs.get_queue_by_name(QueueName='filita')
    queue_url = queue.url

    # Connect to Data Store (S3 Bucket)
    s3client = boto3.client('s3', config=Config(signature_version='s3v4'))
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
            receiptHandle = response["Messages"][0]["ReceiptHandle"]
            messageBody = response["Messages"][0]["Body"]
            print(response)

            # Delete from queue
            delete = client.delete_message(QueueUrl=queue_url, ReceiptHandle=receiptHandle)
            print('deleted message from queue')

            # Get photo from S3
            photo = s3client.get_object(Bucket=bucket_name,Key=messageBody)["Body"].read()
            print("found photo")

        except Exception as e:
            print(e)
            pass
