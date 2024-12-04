from datetime import datetime
from . import db  # Gebruik de geïmporteerde instantie van SQLAlchemy
import uuid
from flask_login import current_user
from sqlalchemy import CheckConstraint


# Functie om een ID-nummer te genereren
def generate_id_number():
    return str(uuid.uuid4().int)[:10]  # 10 cijfers van een UUID

# Tussenliggende tabel voor de veel-op-veel-relatie tussen Klus en Persoon (Kluszoeker)
klus_zoeker = db.Table('klus_zoeker',
    db.Column('klusnummer', db.String(36), db.ForeignKey('klus.klusnummer'), primary_key=True),
    db.Column('idnummer', db.String(10), db.ForeignKey('persoon.idnummer'), primary_key=True)
)

# Persoon Model
class Persoon(db.Model):
    _tablename_ = 'persoon'
    
    idnummer = db.Column(db.String(10), primary_key=True, default=generate_id_number)
    voornaam = db.Column(db.String(100), nullable=False)
    achternaam = db.Column(db.String(100))
    leeftijd = db.Column(db.SmallInteger)
    geslacht = db.Column(db.String(10))
    adres = db.Column(db.String(255))
    email = db.Column(db.String(100), nullable=False, unique=True, index=True)
    telefoonnummer = db.Column(db.String(15))
    username = db.Column(db.String(20), nullable=False, unique=True, index=True)
    
    voorkeur_categorie = db.Column(db.String(50), db.ForeignKey('categorie.categorie'), nullable=True)
    created_at = db.Column(db.TIMESTAMP, nullable=False, default=datetime.utcnow)

    voorkeur_categorie_rel = db.relationship('Categorie', backref='personen', lazy=True)

    klusaanbieders = db.relationship('Klusaanbieder', backref='persoon_aanbieder', lazy='joined')
    kluszoekers = db.relationship('Kluszoeker', backref='persoon_zoeker', lazy='joined')

    def __repr__(self):
        return f'<Persoon {self.voornaam} {self.achternaam}>'

# Klusaanbieder Model
class Klusaanbieder(db.Model):
    _tablename_ = 'klusaanbieder'
    
    idnummer = db.Column(db.String(10), db.ForeignKey('persoon.idnummer'), primary_key=True)
    rating = db.Column(db.Numeric(3, 2))
    categorie = db.Column(db.String(50))
    beschikbaarheid = db.Column(db.String(100))
    
    persoon = db.relationship('Persoon', backref='klusaanbieders_rel')

    def __repr__(self):
        return f'<Klusaanbieder {self.idnummer}>'

# Kluszoeker Model
class Kluszoeker(db.Model):
    _tablename_ = 'kluszoeker'
    
    idnummer = db.Column(db.String(10), db.ForeignKey('persoon.idnummer'), primary_key=True)
    rating = db.Column(db.Numeric(3, 2))
    aantal_klussen = db.Column(db.Integer)
    categorie = db.Column(db.String(50))
    
    persoon = db.relationship('Persoon', backref='kluszoekers_rel')

    def __repr__(self):
        return f'<Kluszoeker {self.idnummer}>'

# Klus Model
class Klus(db.Model):
    _tablename_ = 'klus'
    
    klusnummer = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    naam = db.Column(db.String(100), nullable=False)
    categorie = db.Column(db.String(50), db.ForeignKey('categorie.categorie', ondelete="SET NULL"), nullable=True)
    locatie = db.Column(db.String(100))
    tijd = db.Column(db.Time, nullable=False)
    beschrijving = db.Column(db.Text)
    vergoeding = db.Column(db.Numeric(10, 2))
    datum = db.Column(db.Date, nullable=False)
    verwachte_duur = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.TIMESTAMP, nullable=False, default=datetime.utcnow)
    status = db.Column(db.String(20), default='beschikbaar')  # Status: beschikbaar, geaccepteerd, completed
    idnummer = db.Column(db.String(10), db.ForeignKey('persoon.idnummer'), nullable=False)

    persoon_aanbieder = db.relationship('Persoon', backref=db.backref('klussen', lazy=True))
    klussen_zoekers = db.relationship(
        'Persoon', 
        secondary=klus_zoeker, 
        backref=db.backref('geinteresseerd_in_klussen', lazy='dynamic'))
    categorie_ref = db.relationship('Categorie', backref='klussen', lazy=True)

    def __repr__(self):
        return f'<Klus {self.klusnummer} voor {self.locatie}>'


# Categorie Model
class Categorie(db.Model):
    _tablename_ = 'categorie'
    
    categorie = db.Column(db.String(50), primary_key=True)
    naam = db.Column(db.String(100), nullable=False)

    def __repr__(self):
        return f'<Categorie {self.categorie}>'
    

class Rating(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    klusnummer = db.Column(db.String(36), db.ForeignKey('klus.klusnummer'), nullable=False)
    kluszoeker_id = db.Column(db.String(10), db.ForeignKey('persoon.idnummer'), nullable=False)
    klusaanbieder_id = db.Column(db.String(10), db.ForeignKey('persoon.idnummer'), nullable=False)
    rating_zoeker = db.Column(db.Integer, nullable=False)  # Rating voor de kluszoeker
    rating_aanbieder = db.Column(db.Integer, nullable=False)  # Rating voor de klusaanbieder
    comment_zoeker = db.Column(db.String(500), nullable=True)  # Commentaar voor de kluszoeker
    comment_aanbieder = db.Column(db.String(500), nullable=True)  # Commentaar voor de klusaanbieder
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    klus = db.relationship('Klus', backref=db.backref('ratings', lazy=True))
    kluszoeker = db.relationship('Persoon', foreign_keys=[kluszoeker_id])
    klusaanbieder = db.relationship('Persoon', foreign_keys=[klusaanbieder_id])

    def __repr__(self):
        return f'<Rating {self.id}>'
