import boto3
from botocore.client import Config

import datetime
import os

from flask import Flask, request, redirect, url_for, flash, render_template
from flask_cors import CORS

from werkzeug.utils import secure_filename
from json import dumps

UPLOAD_FOLDER = 'images'
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg'])

bucket_login = 'es-workflows-login'
bucket_register = 'es-workflows-register'
input_queue = 'https://sqs.eu-west-1.amazonaws.com/727565144708/filita'

app = Flask(__name__)
app.secret_key = 'some_secret'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
CORS(app)


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def upload_file(request,action):
    # check if the post request has the file part
    if 'file' not in request.files:
        print('file not in request files')
        print(request.url)
        return redirect(request.url)
    file = request.files['file']

    # if user does not select file, browser also
    # submit a empty part without filename
    if file.filename == '':
        print('No selected file')
        return redirect(request.url)

    if file and allowed_file(file.filename):
        print('File and allowed filename')
        filename = secure_filename(file.filename)

        if action == 'login':
            #send to s3
            s3client = boto3.client('s3', config=Config(signature_version='s3v4'))

            s3client.put_object(Bucket=bucket_login, Key=file.filename,Body=file)

            url = s3client.generate_presigned_url('get_object', {'Bucket': bucket_login, 'Key': file.filename},(3600 * 24) * 60)
            return url

        if action == 'register':
            #send to s3
            s3client = boto3.client('s3', config=Config(signature_version='s3v4'))

            s3client.put_object(Bucket=bucket_register, Key=file.filename,Body=file)

            url = s3client.generate_presigned_url('get_object', {'Bucket': bucket_register, 'Key': file.filename},(3600 * 24) * 60)
            return url

    resp = {"Result": "Something went wrong", "Status Code": 500}
    return dumps(resp)


@app.route('/')
def index():
    return render_template("index.html")


@app.route('/login', methods=['GET','POST'])
def login():

    if request.method == 'POST':
        try:
            url = upload_file(request,'login')
            print(url)
            file = request.files['file']

            # Connect to queue (SQS)
            sqs = boto3.resource("sqs")
            queue = sqs.get_queue_by_name(QueueName='filita')

            # Send message to queue
            queue.send_message(
                QueueUrl=input_queue,
                MessageBody=file.filename,
                DelaySeconds=5,
            )


        except Exception as e:
            print str(e)
            pass
    return render_template("login.html")


@app.route('/payment', methods=['GET','POST'])
def payment():
    return render_template("payment.html")

@app.route('/get_all_users', methods=['GET','POST'])
def getUsers():
    # Connect to SimpleDB
    conn_simpleDB = boto3.client('sdb')
    users = conn_simpleDB.select(SelectExpression="SELECT * FROM ESWorkflows")

    response = users["Items"]
    data = []
    for i in response:
        compare = rekognition.compare_faces(photo, i["Attributes"][1]["Value"])
        print compare["FaceMatches"][0]["Similarity"]

    return "GET ALL USERS"


@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':

        data = request.form

        url = upload_file(request,'register')

        #do register in sdb
        simpleDB = boto3.client('sdb')
        simpleDB.create_domain(DomainName='ESWorkflows')

        import uuid
        uuid = str(uuid.uuid4())

        resolve = simpleDB.put_attributes(
            DomainName="ESWorkflows",
            ItemName=uuid,
            Attributes=[
                {
                    'Name' : 'Name',
                    'Value' : data["name"],
                    'Replace' : True
                },
                {
                    'Name' : 'Credit',
                    'Value' : data["credit"],
                    'Replace' : True
                },
                {
                    'Name' : 'Photo',
                    'Value' : url,
                    'Replace' : True
                },
            ]
        )
        return redirect(url_for('login'))

    return render_template("register.html")
