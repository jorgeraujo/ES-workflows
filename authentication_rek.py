import boto3
bucket_login = 'es-workflows-login'
bucket_register = 'es-workflows-register'

# Connect to SimpleDB
conn_simpleDB = boto3.client('sdb')

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

    for i in response:
        targetImage = i["Attributes"][1]["Value"] + ".png"
        print i["Attributes"]
        source_face, matches = compare_faces(bucket_login, messageBody, bucket_register, targetImage)
        for match in matches:
            print "Target Face ({Confidence}%)".format(**match['Face'])
            print "  Similarity : {}%".format(match['Similarity'])

            if match["Similarity" ] > 90.0:
                print("<<<<<<<<<<<<<<<<<<FOUND MATCH>>>>>>>>>>>>>>>>")
                return {"account" : i["Attributes"][1]["Value"], "ammount" : i["Attributes"][0]["Value"] }
    return {"account" : 0}

def lambda_handler(event, context):

    print(event)

    users = conn_simpleDB.select(SelectExpression="SELECT * FROM ESWorkflows")

    response = users["Items"]
    filename =  event["filename"]

    auth_result = rekognition_loop(response, filename)

    return auth_result
