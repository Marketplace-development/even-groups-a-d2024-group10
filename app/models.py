from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from . import db

db = SQLAlchemy()

# Categorie Model
class Categorie(db.Model):
    __tablename__ = 'categorie'
    
    categorie = db.Column(db.String(50), primary_key=True)  # Toegevoegd: een limiet op de stringlengte
    created_at = db.Column(db.TIMESTAMP, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f'<Categorie {self.categorie}>'

# Persoon Model
class Persoon(db.Model):
    __tablename__ = 'persoon'
    
    IDnummer = db.Column(db.String(10), primary_key=True)
    Voornaam = db.Column(db.String(100), nullable=False)  # Toegevoegd: limiet voor voornaam
    Achternaam = db.Column(db.String(100))  # Toegevoegd: limiet voor achternaam
    Leeftijd = db.Column(db.SmallInteger)
    Adres = db.Column(db.String(255))  # Toegevoegd: limiet voor adres
    Email = db.Column(db.String(100), nullable=False, unique=True)  # Toegevoegd: limiet en unique voor email
    Tel_nr = db.Column(db.String(15))
    Voorkeur_categorie = db.Column(db.String(50), db.ForeignKey('categorie.categorie'), nullable=True)
    created_at = db.Column(db.TIMESTAMP, nullable=False, default=datetime.utcnow)

    # Relationship to Categorie
    voorkeur_categorie = db.relationship('Categorie', backref='personen', lazy=True)

    def __repr__(self):
        return f'<Persoon {self.Voornaam} {self.Achternaam}>'

# Klusaanbieder Model
class Klusaanbieder(db.Model):
    __tablename__ = 'klusaanbieder'
    
    IDnummer = db.Column(db.String(10), db.ForeignKey('persoon.IDnummer'), primary_key=True)
    Rating = db.Column(db.Numeric(3, 2))  # Beoordeling met twee decimalen
    categorie = db.Column(db.String(50), db.ForeignKey('categorie.categorie'), nullable=True)
    created_at = db.Column(db.TIMESTAMP, nullable=False, default=datetime.utcnow)

    # Relationships
    persoon = db.relationship('Persoon', backref='klusaanbieders', lazy=True)
    categorie_ref = db.relationship('Categorie', backref='klusaanbieders', lazy=True)

    def __repr__(self):
        return f'<Klusaanbieder {self.IDnummer}>'

# Kluszoeker Model
class Kluszoeker(db.Model):
    __tablename__ = 'kluszoeker'
    
    IDnummer = db.Column(db.String(10), db.ForeignKey('persoon.IDnummer'), primary_key=True)
    Rating = db.Column(db.Numeric(3, 2))  # Beoordeling met twee decimalen
    Aantal_klussen = db.Column(db.SmallInteger)
    categorie = db.Column(db.String(50), db.ForeignKey('categorie.categorie'), nullable=True)
    created_at = db.Column(db.TIMESTAMP, nullable=False, default=datetime.utcnow)

    # Relationships
    persoon = db.relationship('Persoon', backref='kluszoekers', lazy=True)
    categorie_ref = db.relationship('Categorie', backref='kluszoekers', lazy=True)

    def __repr__(self):
        return f'<Kluszoeker {self.IDnummer}>'

# Klus Model
class Klus(db.Model):
    __tablename__ = 'klus'
    
    Klusnummer = db.Column(db.String(10), primary_key=True)
    Categorie = db.Column(db.String(50), db.ForeignKey('categorie.categorie'), nullable=True)  # Toegevoegd: limiet voor string
    Plaats = db.Column(db.String(100))  # Toegevoegd: limiet voor plaats
    Tijd = db.Column(db.String(50))  # Toegevoegd: limiet voor tijd
    Beschrijving = db.Column(db.Text)
    Vergoeding = db.Column(db.Numeric(10, 2))  # Toegevoegd: vergoeding met 2 decimalen
    created_at = db.Column(db.TIMESTAMP, nullable=False, default=datetime.utcnow)

    # Relationship to Categorie
    categorie_ref = db.relationship('Categorie', backref='klussen', lazy=True)

    def __repr__(self):
        return f'<Klus {self.Klusnummer}>'
