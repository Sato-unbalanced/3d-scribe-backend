from flask import Flask , jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from dotenv import load_dotenv
from botocore.exceptions import ClientError
from sqlalchemy import text
import boto3
import os
#import requests


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
    model_id = db.Column(db.Integer,autoincrement=True)

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
    anotation_id = db.Column(db.Integer,autoincrement=True, primary_key = True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'))
    name = db.Column(db.String(50))
    text = db.Column(db.String(500))
    size = db.Column(db.String(50))
    color = db.Column(db.String(50))

    object_anchor_x = db.Column(db.Float, nullable=False)
    object_anchor_y = db.Column(db.Float, nullable=False)
    object_anchor_z = db.Column(db.Float, nullable=False)

    div_anchor_x = db.Column(db.Float, nullable=False)
    div_anchor_y = db.Column(db.Float, nullable=False)
    div_anchor_z = db.Column(db.Float, nullable=False)



with app.app_context():
    db.create_all()

@app.route("/")
def hello_world():
    return "<p>Hello world</p>"

@app.route("/create/user/<string:user_id>", methods=['POST'])
def create_user(user_id):
    result = User.query.filter(User.id == user_id).first()
    if result == None:
        user = User(id = user_id)
        db.session.add(user)
        db.session.commit() 
    return jsonify([{'result':"200"}])
@app.route("/retrive/annotations/<int:project_id>/<string:user_id>", methods=['GET'])
def return_annotations(project_id,user_id):
    result = Annotation.query.filter(Annotation.project_id == project_id).all()
    return_item = [{"id":item.anotation_id, 'name': item.name}for item in result]
    return jsonify(return_item)

@app.route("/retrive/annotation/<int:project_id>/<string:user_id>/<int:annotation_id>", methods=['GET'])
def return_annotation(project_id, user_id, annotation_id):
    result = Annotation.query.filter(Annotation.anotation_id == annotation_id).first()
    return_item = [{"id":result.anotation_id, 'name': result.name, 'text': result.text,'size': result.size, 'color': result.color, 'object_anchor_x': result.object_anchor_x, 'object_anchor_y' : result.object_anchor_y,'object_anchor_z' : result.object_anchor_z,'div_anchor_x' : result.div_anchor_x,'div_anchor_y' : result.div_anchor_y,'div_anchor_z' : result.div_anchor_z}]
    return jsonify(return_item)

@app.route("/update/annotation/<int:annotation_id><string:user_id>/<string:name_v>/<string:text_v>/<string:size_v>/<string:color_v>/<string:object_x>/<string:object_y>/<string:object_z>/<string:x_anchor>/<string:y_anchor>/<string:z_anchor>", methods=['POST'])
def update_annotation(annotation_id,name_v, text_v, size_v, color_v, object_x, object_y, object_z, x_anchor, y_anchor, z_anchor):
    result = Annotation.query.filter(Annotation.anotation_id == annotation_id).first()
    if result != None:
        result.name = name_v
        result.text = text_v
        result.size = size_v
        result.color = color_v
        result.div_anchor_x = float(object_x)
        result.div_anchor_y =  float(object_y)
        result.div_anchor_z = float(object_z)
        result.object_anchor_x = float(x_anchor) 
        result.object_anchor_y = float(y_anchor)
        result.object_anchor_z = float(z_anchor)
        db.session.commit()
        return jsonify([{'result': 200}])
    else:
        return jsonify([{'result': 400}])

@app.route("/create/annotation/<int:project_id_v>/<string:user_id>/<string:name_v>/<string:text_v>/<string:size_v>/<string:color_v>/<string:object_x>/<string:object_y>/<string:object_z>/<string:x_anchor>/<string:y_anchor>/<string:z_anchor>", methods=['POST'])
def create_annotation(project_id_v, user_id, name_v, text_v, size_v, color_v, object_x, object_y, object_z, x_anchor, y_anchor, z_anchor):
    print("preresult")
    result = Annotation.query.filter(Annotation.name == name_v).first()
    print("this is result: ",result)
    if result is None:
        annotation = Annotation(project_id = project_id_v, name = name_v, text = text_v,
                                 size = size_v, color = color_v, div_anchor_x =float(object_x),
                                 div_anchor_y =  float(object_y), div_anchor_z = float(object_z), 
                                 object_anchor_x = float(x_anchor), object_anchor_y = float(y_anchor), object_anchor_z = float(z_anchor))
        db.session.add(annotation)
        db.session.commit()
        return jsonify([{'id':annotation.anotation_id}])
    else:
        print("project name already taken")
        return jsonify([{'id':"-400"}])

@app.route("/create/project/<string:project_name>/<string:user_id>", methods=['POST'])
def create_projects(project_name, user_id):
    result = Project.query.filter(Project.name == project_name).first()
    file = request.files['file']
    print(result)
    print(file)
    print(project_name)
    print(user_id)
    print(file.filename)
    
    if result == None:
        
        try:
            response = s3.upload_fileobj(file, "3d-scribe-models", "models/"+project_name)

            model = Model3D( name = project_name, key = "models/"+project_name)
            db.session.add(model)
            db.session.commit()

            project = Project(name = project_name, model_id = model.id)
            db.session.add(project)
            db.session.commit()

            user = User_To_Project(user_id = user_id, project_id = project.id)
            db.session.add(user)
            db.session.commit()
        except ClientError as e:
            print(e)

        return jsonify([{'result':"200"}])
    else:
        print("project name already taken")
        return jsonify([{'result':"400"}])


@app.route("/models/<string:model_uri>",methods=['GET'])
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

@app.route("/url/<int:project_id>", methods=['GET'])
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
    SELECT project.name AS name, project.id AS id
    FROM user_to_project
    LEFT JOIN "user" ON "user".id = user_to_project.user_id
    LEFT JOIN project ON user_to_project.project_id = project.id
    LEFT JOIN model ON project.model_id = model.id
    WHERE "user".id = :user_id;
    ''')
    results = db.session.execute(query, {'user_id': user_id}).fetchall()
    if len(results) == 0:
        return jsonify([{"project_name": "No Projects", "project_id": ""}])
    
    response = [{'project_name': row[0], 'project_id': row[1]} for row in results]

    return jsonify(response)
    
@app.errorhandler(404)
def page_not_found(error):
    return jsonify({'error':'Resource not Found'}), 404
