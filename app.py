import boto3
from botocore.client import Config
import datetime
import time
import os
from flask import Flask, request, redirect, url_for, flash, render_template
from flask_cors import CORS
from werkzeug.utils import secure_filename
from json import dumps

UPLOAD_FOLDER = 'images'
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg'])

bucket_login = 'es-workflows-login'
bucket_register = 'es-workflows-register'

app = Flask(__name__)
app.secret_key = 'some_secret'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
CORS(app)

simpleDB = boto3.client('sdb')

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

            # Connect to queue (SQS)
            sqs = boto3.resource("sqs")
            #SQS Client
            client = boto3.client('sqs')
            #Input queue
            write_to = sqs.get_queue_by_name(QueueName='filita')
            write_to_url = write_to.url
            #Output queue
            read_from = sqs.get_queue_by_name(QueueName='output_login_queue')
            read_from_url = read_from.url

            # Send message to queue
            write_to.send_message(
                QueueUrl=write_to_url,
                MessageBody=file.filename,
                DelaySeconds=0,
            )

            while (True):
                try:
                    login_result = client.receive_message(
                    QueueUrl=read_from_url,
                    MaxNumberOfMessages=1,
                    AttributeNames = ['All'],
                    MessageAttributeNames=[
                        'credit',
                        'user',
                        'itemName'
                    ]
                    )
                    receiptHandle = login_result["Messages"][0]["ReceiptHandle"]
                    body = login_result["Messages"][0]["Body"]

                    if body == "SUCCESS":
                        print "SUCCESS"
                        attributes = login_result["Messages"][0]["MessageAttributes"]
                        flash('You were successfully logged in')
                        # Delete from queue
                        delete = client.delete_message(QueueUrl=read_from_url, ReceiptHandle=receiptHandle)

                        if float(attributes["credit"]["StringValue"]) >= 5:
                            return redirect(url_for('payment', itemname = attributes["itemName"]["StringValue"], credit = float(attributes["credit"]["StringValue"]) ))
                        else:
                            return redirect(url_for('payment_manual'))
                    if body == "FAILED":
                        print "FAILED"
                        return redirect(url_for('payment_manual'))
                except Exception as e:
                    # print (e)
                    pass


            # print login_result["Messages"][0]["Body"]
            # if login_result["Messages"][0]["Body"]["status"] == 'SUCCESS':
            #     return redirect(url_for('payment'))


        except Exception as e:
            print str(e)
            pass
    return render_template("login.html")


@app.route('/payment/<itemname>/<credit>/', methods=['GET','POST'])
def payment(itemname, credit):
    # Delete from queue
    # delete = client.delete_message(QueueUrl=read_from_url, ReceiptHandle=receiptHandle)
    update_credit = float(credit)-5
    u_credit = str(update_credit)

    response = simpleDB.put_attributes(
    DomainName='ESWorkflows',
    ItemName=itemname,
    Attributes=[
        {
            'Name': 'Credit',
            'Value': u_credit,
            'Replace': True
        },
    ])

    return render_template("payment.html")

@app.route('/confirm', methods=['GET','POST'])
def confirm():
    return None

@app.route('/payment_manual', methods=['GET','POST'])
def payment_manual():
    return render_template("payment_manual.html")


@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        import uuid
        uuid = str(uuid.uuid4())

        data = request.form

        url = upload_file(request,'register',uuid)

        #do register in sdb

        simpleDB.create_domain(DomainName='ESWorkflows')

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
                    'Value' : uuid,
                    'Replace' : True
                },
            ]
        )
        return redirect(url_for('login'))

    return render_template("register.html")
