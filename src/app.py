"""
This module takes care of starting the API Server, Loading the DB and Adding the endpoints
"""
import os
from flask import Flask, request, jsonify, url_for
from flask_migrate import Migrate
from flask_swagger import swagger
from flask_cors import CORS
from utils import APIException, generate_sitemap
from admin import setup_admin
from models import db, Language, Word
#from models import Person

app = Flask(__name__)
app.url_map.strict_slashes = False

db_url = os.getenv("DATABASE_URL")
if db_url is not None:
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url.replace("postgres://", "postgresql://")
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:////tmp/test.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

MIGRATE = Migrate(app, db)
db.init_app(app)
CORS(app)
setup_admin(app)

# Handle/serialize errors like a JSON object
@app.errorhandler(APIException)
def handle_invalid_usage(error):
    return jsonify(error.to_dict()), error.status_code

# generate sitemap with all your endpoints
@app.route('/')
def sitemap():
    return generate_sitemap(app)

# Methods -> Protocolos HTTP

# Endpoint -> Punto de conexión
@app.route('/languages', methods=['GET'])
def get_languages():
    all_languages = Language.query.all()
    serialize_languages = [language.serialize() for language in all_languages]
    # Javascript Object Notation: JSON
    return jsonify(serialize_languages), 200

# Post -> Para crear
@app.route('/language', methods=['POST'])
def create_language():
    # En el metodo|Formato Json
    request_body = request.get_json()
    if request_body is None:
        # 400 BAD REQUEST
        raise APIException('Necesitas un BODY', status_code=400)
    
    if "name" not in request_body:
        raise APIException('Necesitas especificar un NOMBRE(name)', status_code=400)
    # Dictionary -> Python
    # Uppercase -> Mayuscula

    exists_language = Language.query.filter_by(name=request_body["name"].upper()).first()

    if exists_language is not None:
        raise APIException('Ya existe ese lenguaje :(', status_code=400)
    
    new_language = Language(name=request_body["name"].upper())

    db.session.add(new_language)
    db.session.commit()

    # 201 -> creado
    return jsonify(new_language.serialize()), 201


# PALABRAS
@app.route('/words', methods=['GET'])
def get_all_words():
    all_words = Word.query.all()
    serialized_words = [word.serialize() for word in all_words]
    return jsonify(serialized_words), 200

# Crear una palabra
@app.route('/word', methods=["POST"])
def create_word():
    request_body = request.get_json()

    if request_body is None:
        raise APIException('Necesitas un BODY', status_code=400)
    if "word" not in request_body:
        raise APIException('Necesitas una palabra', status_code=400)
    if "definition" not in request_body:
        raise APIException('Necesitas una definicion', status_code=400)
    if "language_id" not in request_body:
        raise APIException('Necesitas un lenguaje para tu palabra', status_code=400)
    
    # Si el lenguaje que el usuario mandó existe
    language = Language.query.get(request_body["language_id"])

    if language is None:
        raise APIException('Lenguaje no encontrado :(', status_code=404)
    
    word_exists = Word.query.filter_by(word=request_body["word"].lower(), language_id=request_body["language_id"]).first()
    
    if word_exists:
        raise APIException('Ya la palabra existe', status_code=400)
    
    new_word = Word(word=request_body["word"].lower(), definition=request_body["definition"], language_id=request_body["language_id"])
    db.session.add(new_word)
    db.session.commit()

    return jsonify(new_word.serialize()), 201

@app.route('/word/<int:id>', methods=["PUT"])
def update_word(id):
    word = Word.query.get(id)
    if word is None:
        raise APIException('La palabra no existe', status_code=404)
    
    request_body =request.get_json()

    if request_body is None:
        raise APIException('Tienes que pasar un body', status_code=404)

    if "word" in request_body:
        word.word = request_body["word"]
    if "definition" in request_body:
        word.definition = request_body["definition"]
    # Quizas funcione
    if "language_id" in request_body:
        language = Language.query.get(request_body["language_id"])
        if language is None:
            raise APIException('Lenguaje invalido', status_code=404)

        word.language_id = language.id

    db.session.commit()
    return jsonify(word.serialize()), 200

# http://localhost:3000/words/En
@app.route('/words/<string:language>', methods=["GET"])
def get_words_by_language(language):
    language_in_db = Language.query.filter_by(name=language.upper()).first()
    if language_in_db is None:
        raise APIException('Lenguaje no encontrado :(', status_code=404)
    
    words_by_language = Word.query.filter_by(language_id = language_in_db.id).all()

    serialized_words = [word.serialize() for word in words_by_language]
    return jsonify(serialized_words)

# http://localhost:3000/word/en/something
@app.route('/word/<string:language>/<string:word>', methods=["GET"])
def get_word_by_language(language, word):
    language_in_db = Language.query.filter_by(name=language.upper()).first()
    if language_in_db is None:
        raise APIException('Lenguaje no encontrado :(', status_code=404)

    word_in_db = Word.query.filter_by(word=word, language_id= language_in_db.id).first()

    if word_in_db is None:
        raise APIException('Palabra no encontrada :(', status_code=404)
    
    return jsonify(word_in_db.serialize()), 200

# Con el zen de python
# Explicito es mejor que implicito


@app.route('/word/<int:id>', methods=["DELETE"])
def delete_a_word(id):
    word = Word.query.get(id)
    if word is None:
        raise APIException('Palabra no encontrada :(', status_code=404)
    
    db.session.delete(word)
    db.session.commit()
    return jsonify({"message": "Palabra removida con exito :)"}), 200



# this only runs if `$ python src/app.py` is executed
if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=PORT, debug=False)
