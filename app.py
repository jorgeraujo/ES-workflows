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

app = Flask(__name__)
app.secret_key = 'some_secret'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
CORS(app)


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
def index():
    return render_template("index.html")


@app.route('/login', methods=['GET','POST'])
def login():

    if request.method == 'POST':
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
            # file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            # file.seek(0)

            #send to s3
            s3 = boto3.resource('s3', config=Config(signature_version='s3v4'))
            b = s3.Bucket('es-workflows-es')
            objects = b.objects.all()

            b.put_object(Key=file.filename,Body=file)
            print ('File saved to S3')

            # Connect to queue (SQS)
            sqs = boto3.resource("sqs")
            queue = sqs.get_queue_by_name(QueueName='filita')


            # Send message to queue
            queue.send_message(
                QueueUrl="https://sqs.eu-west-1.amazonaws.com/727565144708/filita",
                MessageBody=file.filename,
                DelaySeconds=5,
            )

            # Read message from queue
            client = boto3.client('sqs')
            response = client.receive_message(
            QueueUrl='https://sqs.eu-west-1.amazonaws.com/727565144708/filita',
            MaxNumberOfMessages=1
            )
            print(response)

            return redirect(url_for('payment'))
    return render_template("login.html")


@app.route('/payment', methods=['GET','POST'])
def payment():

    return render_template("payment.html")
