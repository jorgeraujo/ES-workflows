import boto3
from botocore.client import Config
import sys

reload(sys)
sys.setdefaultencoding('utf8')

bucket_login = 'es-workflows-login'
bucket_register = 'es-workflows-register'

def compare_faces(bucket, key, bucket_target, key_target, threshold=80, region="eu-west-1"):
	#rekognition
    rekognition = boto3.client('rekognition', region)

    response = rekognition.compare_faces(
	    SourceImage={
			"S3Object": {
				"Bucket": bucket,
				"Name": key,
			}
		},
		TargetImage={
			"S3Object": {
				"Bucket": bucket_target,
				"Name": key_target,
			}
		},
	    SimilarityThreshold=threshold,
	)
    print(response['SourceImageFace'])
    print(response['FaceMatches'])
    return response['SourceImageFace'], response['FaceMatches']


def rekognition_loop(response, messageBody):
    try:
        for i in response:
            targetImage = i["Attributes"][1]["Value"] + ".png"
            print i["Attributes"]
            source_face, matches = compare_faces(bucket_login, messageBody, bucket_register, targetImage)
            for match in matches:
                print "Target Face ({Confidence}%)".format(**match['Face'])
                print "  Similarity : {}%".format(match['Similarity'])
                print(match["Similarity" ])
                if match["Similarity" ] > 90.0:
                    writing = client.send_message(
                        QueueUrl=queue_output_url,
                        MessageBody= 'SUCCESS',
                        MessageAttributes={
                            'user': {
                                'StringValue': i["Attributes"][2]["Value"],
                                'DataType': 'String',
                            },
                            'credit': {
                                'StringValue': i["Attributes"][0]["Value"],
                                'DataType': 'Number',
                            },
                            'itemName': {
                                'StringValue': i["Attributes"][1]["Value"],
                                'DataType': 'String',
                            },
                        },
                        DelaySeconds=0,
                    )
                    print("<<<<<<<<<<<<<<<<<<FOUND MATCH>>>>>>>>>>>>>>>>")
                    return None

        print("<<<<<<<<<<<<<<<<<<NOT FOUND MATCH>>>>>>>>>>>>>>>>")
        writing = client.send_message(
            QueueUrl=queue_output_url,
            MessageBody= 'FAILED',
            MessageAttributes={
                'user': {
                    'StringValue': "doe",
                    'DataType': 'String',
                },
                'credit': {
                    'StringValue': "doe",
                    'DataType': 'Number',
                },
                'itemName': {
                    'StringValue': "0",
                    'DataType': 'String',
                },
            },
            DelaySeconds=0,
        )
        return None
    except Exception as e:
        print(e)



if __name__ == '__main__':
    # Connect to queue (SQS)
    sqs = boto3.resource("sqs")

    #Input queue
    queue_input = sqs.get_queue_by_name(QueueName='filita')
    queue_input_url = queue_input.url

    #Output queue
    queue_output = sqs.get_queue_by_name(QueueName="output_login_queue")
    queue_output_url = queue_output.url

    print("URL:"+queue_output_url)

    # Connect to Data Store (S3 Bucket)
    s3client = boto3.client('s3', config=Config(signature_version='s3v4'))

    # Connect to SimpleDB
    conn_simpleDB = boto3.client('sdb')

    #region
    region="eu-west-1"

    while (True):
        try:
            # Read message from queue
            client = boto3.client('sqs')
            response = client.receive_message(
            QueueUrl=queue_input_url,
            MaxNumberOfMessages=1
            )
            receiptHandle = response["Messages"][0]["ReceiptHandle"]
            messageBody = response["Messages"][0]["Body"]
            # print(response)

            # Delete from queue
            delete = client.delete_message(QueueUrl=queue_input_url, ReceiptHandle=receiptHandle)

            # Get photo from S3
            sourceImage = s3client.get_object(Bucket=bucket_login,Key=messageBody)["Body"].read()

            users = conn_simpleDB.select(SelectExpression="SELECT * FROM ESWorkflows")

            response = users["Items"]

            rekognition_loop(response, messageBody)

        except Exception as e:
            # print(e)
            pass
