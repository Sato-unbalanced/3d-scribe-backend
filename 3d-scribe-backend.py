from flask import Flask , jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from dotenv import load_dotenv
from botocore.exceptions import ClientError
from sqlalchemy import text
import boto3
import os
import requests


app = Flask(__name__)    
CORS(app, origins=[os.getenv("WEBSITE_URL")])
DATABASE_URL = os.getenv('DATABASE_URL')
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
app.config['SQLALCHEMY_DATABASE_URI']= DATABASE_URL

db = SQLAlchemy(app)
session = boto3.Session(
    aws_access_key_id = os.getenv('ACCESS_KEY'),
    aws_secret_access_key = os.getenv('SECRET_KEY'),
    region_name= os.getenv('REGION_NAME')
    )
s3 = session.client('s3')

class Model3D(db.Model):
    __tablename__ = 'model'
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(100))
    key = db.Column(db.String(100))

class Model_Tag(db.Model):
    __tablename__ = 'model_tag'
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(100))

class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.String(50), primary_key = True)

class Project(db.Model):
    __tablename__ = 'project'
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(50))
    model_id = db.Column(db.Integer)

class Project_To_Tag(db.Model):
    __tablename__ = 'project_to_tag'
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), primary_key=True)  # Correct capitalization
    tag_id = db.Column(db.Integer, db.ForeignKey('model_tag.id'), primary_key=True)   # Correct capitalization

class User_To_Project(db.Model):
    __tablename__ = 'user_to_project'
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), primary_key = True)
    user_id = db.Column(db.String(50), db.ForeignKey('user.id'), primary_key = True)
    auth = db.Column(db.Boolean)

class Annotation(db.Model):
    __tablename__ = 'annotation'
    anotation_id = db.Column(db.Integer, primary_key = True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), primary_key = True)
    text = db.Column(db.String(500))
    location = db.Column(db.String(15))


with app.app_context():
    db.create_all()

@app.route("/")
def hello_world():
    return "<p>Hello world</p>"

@app.route("/buckets", methods=['GET'])
def get_buckets():
    bucket_list = [{"s": "33"}]
    response = s3.list_buckets()
    for bucket in response['Buckets']:
        print(bucket['Name'])
    presigned_url = s3.generate_presigned_url(
        ClientMethod = 'get_object',
        Params = {'Bucket': "3d-scribe-models", "Key": "airboat.obj"},
        ExpiresIn=3600
    )
    return jsonify(bucket_list)

@app.route("/models/<string:model_uri>")
def get_model(model_uri):
    uri_array = model_uri.split('/')
    model_uri = "/".join(uri_array[len(uri_array)-2:len(uri_array)])
    try:
        response = s3.generate_presigned_url(
            ClinetMethod = 'get_object',
            Params = {'Bucket': "3d-scribe-models", "Key": model_uri},
            ExpiresIn = 3600
        )
    except ClientError as e:
        print(e)
        return None
    return  jsonify( [{"uri": response }] )

@app.route("/url/<int:project_id>")
def get_presigned_url(project_id):
    query = text('''
    SELECT model.key
    FROM model
    WHERE model.id = (
    SELECT project.model_id
    FROM project 
    WHERE project.id = :project_id)          
    ''')
    results = db.session.execute(query, {'project_id': project_id}).fetchall()
    try:
        response = s3.generate_presigned_url(
            ClientMethod = 'get_object',
            Params = {'Bucket': "3d-scribe-models", "Key" : results[0].key},
            ExpiresIn = 3600
        )
    except ClientError as e:
        print(e)
        return None
    return jsonify([{"url": response}])

@app.route("/project/names", methods=['GET'])
def get_models():
    query = text('''
    SELECT project.name AS name, project.id AS id
    FROM project
    ''')
    results = db.session.execute(query).fetchall()
    response = [{'project_name': row[0], 'project_id': row[1]} for row in results]
    return jsonify(response)
   

@app.route("/model/names/<string:user_id>", methods=['GET'])
def get_model_names(user_id):
    query = text('''
    SELECT model.name AS name, project.id AS id
    FROM "user"
    JOIN user_to_project ON user_to_project.user_id = :user_id
    JOIN project ON user_to_project.project_id = project.id
    JOIN model ON project.model_id = model.id
    ''')
    results = db.session.execute(query, {'user_id': user_id}).fetchall()

    response = [{'model_name': row[0], 'project_id': row[1]} for row in results]

    return jsonify(response)
    
@app.errorhandler(404)
def page_not_found(error):
    return jsonify({'error':'Resource not Found'}), 404
