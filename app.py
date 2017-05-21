import boto3
import datetime
import os
from flask import Flask
from flask import Flask, request, redirect, url_for, flash, render_template
from werkzeug.utils import secure_filename
from flask.ext.cors import CORS



UPLOAD_FOLDER = 'images'
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg'])

app = Flask(__name__)
app.secret_key = 'some_secret'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
CORS(app)

@app.route('/')
def index():
    return render_template("index.html")


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


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
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            print ('File saved')
            return redirect(url_for('payment'))
    return render_template("login.html")

    #s3: es-workflows-photos



@app.route('/payment', methods=['GET','POST'])
def payment():
    # Connect to queue (SQS)
    sqs = boto3.resource("sqs")
    queue = sqs.get_queue_by_name(QueueName='filita')


    # Send message to queue
    queue.send_message(
        QueueUrl="https://sqs.eu-west-1.amazonaws.com/727565144708/filita",
        MessageBody="dsdf",
        DelaySeconds=5,
    )
    client = boto3.client('sqs')
    response = client.receive_message(
    QueueUrl='https://sqs.eu-west-1.amazonaws.com/727565144708/filita',
    MaxNumberOfMessages=1
)



    print response
    return "ss"
