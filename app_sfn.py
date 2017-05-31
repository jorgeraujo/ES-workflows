import boto3
from botocore.client import Config
import datetime
import time
import os
from flask import Flask, request, redirect, url_for, flash, render_template
from flask_cors import CORS
from werkzeug.utils import secure_filename
from json import dumps
import ast

UPLOAD_FOLDER = 'images'
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg'])

bucket_login = 'es-workflows-login'
bucket_register = 'es-workflows-register'

app = Flask(__name__)
app.secret_key = 'some_secret'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
CORS(app)

simpleDB = boto3.client('sdb')
sfn = boto3.client('stepfunctions')

machine_arn = 'arn:aws:states:eu-west-1:727565144708:stateMachine:ChoiceState'

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def upload_file(request,action,uuid):
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
            print("File "+file.filename +" is in S3")

            url = s3client.generate_presigned_url('get_object', {'Bucket': bucket_login, 'Key': file.filename},(3600 * 24) * 60)

            return url

        if action == 'register':
            #send to s3
            s3client = boto3.client('s3', config=Config(signature_version='s3v4'))

            s3client.put_object(Bucket=bucket_register, Key=uuid+'.png',Body=file)
            print("File "+uuid +".png is in S3")
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
            url = upload_file(request,'login', None)
            print(url)
            file = request.files['file']
            filename = file.filename
            time_name = str(time.time())
            startExecution = sfn.start_execution(
                stateMachineArn=machine_arn,
                name=time_name,
                input='{"filename" : "' + filename + '"}'
            )

            while(True):
                time.sleep(2)
                result = sfn.describe_execution(
            	    executionArn=startExecution['executionArn']
            	)
                if result['status'] == 'RUNNING':
                    pass
                else:
                    response = ast.literal_eval(result["output"])
                    credit = float(response["credit"])

                    if credit >= 5:
                        return redirect(url_for('payment'))
                    else:
                        return redirect(url_for('payment_manual'))

        except Exception as e:
            print str(e)
            pass
    return render_template("login.html")


@app.route('/payment', methods=['GET','POST'])
def payment():
    return render_template("payment.html")

@app.route('/payment_manual', methods=['GET','POST'])
def payment_manual():
    return render_template("payment_manual.html")
