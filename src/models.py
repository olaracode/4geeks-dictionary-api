from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# 

# En la programacion se suelen llamar las cosas en ingles
class Language(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    # EN | ES | JP | FR
    name = db.Column(db.String(10), unique=True, nullable=False)
    
    # Plural
    words = db.relationship('Word', backref="language")
    
    def serialize(self):
        return {
            "id": self.id,
            "name": self.name
        }

# Uno -> Muchos
# Un lenguaje puede tener muchas palabras

class Word(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    word = db.Column(db.String(120), unique=True, nullable=False)
    definition = db.Column(db.String(120), unique=False, nullable=False)

    # Si o si tiene que pertenecer a un lenguaje
    language_id = db.Column(db.Integer, db.ForeignKey('language.id'), nullable=False)


    def serialize(self):
        return {
            "id": self.id,
            "word": self.word,
            "definition": self.definition
        }
