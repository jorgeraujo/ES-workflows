import boto3
import os
from flask import Flask
from flask import Flask, request, redirect, url_for, flash, render_template
from flask.ext.cors import CORS

app = Flask(__name__)
app.secret_key = 'some_secret'
UPLOAD_FOLDER = '/images'
CORS(app)

@app.route('/')
def index():
    return render_template("index.html")


@app.route('/login', methods=["POST"])
def login():

    # check if the post request has the file part
    if 'file' not in request.files:
        flash('No file part')
        return redirect(request.url)
    file = request.files['file']
    # if user does not select file, browser also
    # submit a empty part without filename
    if file.filename == '':
        flash('No selected file')
        return redirect(request.url)
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        return redirect(url_for('uploaded_file',
                                filename=filename))
