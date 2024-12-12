from datetime import datetime
from . import db  # Verwijzen naar extensiemodule
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
    __tablename__ = 'persoon'

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
    

    def gemiddelde_score_zoeker(self):
        ratings = Rating.query.filter(Rating.kluszoeker_id == self.idnummer).all()
        if not ratings:
            return 0.0  # Geen beoordelingen

    # Bereken het gemiddelde voor elke beoordeling en het algemene gemiddelde
        scores = []
        for r in ratings:
            totaal = sum([
                r.vriendelijkheid_zoeker or 0,
                r.tijdigheid or 0,
                r.kwaliteit or 0,
                r.communicatie_zoeker or 0,
                r.algemene_ervaring_zoeker or 0
            ])
            scores.append(totaal / 5)  # Gemiddelde per beoordelingscriterium
        return round(sum(scores) / len(scores), 2) if scores else 0

    def gemiddelde_score_aanbieder(self):
        ratings = Rating.query.filter(Rating.klusaanbieder_id == self.idnummer).all()
        if not ratings:
            return 0.0  # Geen beoordelingen

        scores = []
        for r in ratings:
            totaal = sum([
                r.vriendelijkheid_aanbieder or 0,
                r.gastvrijheid or 0,
                r.betrouwbaarheid or 0,
                r.communicatie_aanbieder or 0,
                r.algemene_ervaring_aanbieder or 0
            ])
            scores.append(totaal / 5)  # Gemiddelde per beoordelingscriterium
        return round(sum(scores) / len(scores), 2) if scores else 0



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

class Klus(db.Model):
    __tablename__ = 'klus'

    klusnummer = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    naam = db.Column(db.String(100), nullable=False)
    beschrijving = db.Column(db.Text, nullable=False)
    categorie = db.Column(db.String(50), db.ForeignKey('categorie.categorie'), nullable=False)  # ForeignKey toegevoegd
    locatie = db.Column(db.String(100), nullable=False)
    tijd = db.Column(db.Time, nullable=False)  # Tijd als TIME
    vergoeding = db.Column(db.Numeric(10, 2), nullable=False)  # Decimal voor geld
    datum = db.Column(db.Date, nullable=False)  # Datum als DATE
    verwachte_duur = db.Column(db.Integer, nullable=False)  # Integer voor uren
    created_at = db.Column(db.TIMESTAMP, default=datetime.utcnow, nullable=False)
    status = db.Column(db.String(20), default='beschikbaar', nullable=False)  # Status
    idnummer = db.Column(db.String(10), db.ForeignKey('persoon.idnummer'), nullable=False)
    voltooid_op = db.Column(db.DateTime, nullable=True)

    persoon_aanbieder = db.relationship('Persoon', backref=db.backref('klussen', lazy=True))
    
    # Relatie met klussenzoekers (via de tussen tabel)
    klussen_zoekers = db.relationship(
        'Persoon', 
        secondary=klus_zoeker, 
        backref=db.backref('geinteresseerd_in_klussen', lazy='dynamic')
    )

    # Relatie naar Categorie (via ForeignKey 'categorie')
    categorie_ref = db.relationship('Categorie', backref='klussen', lazy=True)

    def is_gewaardeerd_door_aanbieder(self):
        return any(r.vriendelijkheid_zoeker is not None for r in self.ratings)

    def is_gewaardeerd_door_zoeker(self):
        return any(r.vriendelijkheid_aanbieder is not None for r in self.ratings)
    
    def __repr__(self):
        return f'<Klus {self.klusnummer} voor {self.locatie}>'
    
class Categorie(db.Model):
    __tablename__ = 'categorie'  # Correcte naamgeving

    categorie = db.Column(db.String(50), primary_key=True)  # Unieke identificatie
    naam = db.Column(db.String(100), nullable=False)

    def __repr__(self):
        return f'<Categorie {self.categorie}>'

class Rating(db.Model):
    __tablename__ = 'rating'

    id = db.Column(db.Integer, primary_key=True)
    klusnummer = db.Column(db.String(36), db.ForeignKey('klus.klusnummer'), nullable=False)
    
    # Velden voor rate_zoeker (beoordeling door klusaanbieder)
    kluszoeker_id = db.Column(db.String(10), db.ForeignKey('persoon.idnummer'), nullable=True)
    vriendelijkheid_zoeker = db.Column(db.Integer, nullable=True)  # Score van 1-10
    tijdigheid = db.Column(db.Integer, nullable=True)  # Score van 1-10
    kwaliteit = db.Column(db.Integer, nullable=True)  # Score van 1-10
    communicatie_zoeker = db.Column(db.Integer, nullable=True)  # Score van 1-10
    algemene_ervaring_zoeker = db.Column(db.Integer, nullable=True)  # Score van 1-10

    # Velden voor rate_aanbieder (beoordeling door kluszoeker)
    klusaanbieder_id = db.Column(db.String(10), db.ForeignKey('persoon.idnummer'), nullable=True)
    vriendelijkheid_aanbieder = db.Column(db.Integer, nullable=True)  # Score van 1-10
    gastvrijheid = db.Column(db.Integer, nullable=True)  # Score van 1-10
    betrouwbaarheid = db.Column(db.Integer, nullable=True)  # Score van 1-10
    communicatie_aanbieder = db.Column(db.Integer, nullable=True)  # Score van 1-10
    algemene_ervaring_aanbieder = db.Column(db.Integer, nullable=True)  # Score van 1-10

    # Algemene velden
    comment = db.Column(db.String(500), nullable=True)  # Optionele commentaar
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    # Relaties
    klus = db.relationship('Klus', backref=db.backref('ratings', lazy=True))
    kluszoeker = db.relationship('Persoon', foreign_keys=[kluszoeker_id], backref='zoeker_ratings')
    klusaanbieder = db.relationship('Persoon', foreign_keys=[klusaanbieder_id], backref='aanbieder_ratings')

    def __repr__(self):
        return f'<Rating {self.id} - Klusnummer {self.klusnummer}>'




class CategorieStatistiek(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    idnummer = db.Column(db.String(10), db.ForeignKey('persoon.idnummer', ondelete='CASCADE'), nullable=False)
    categorie = db.Column(db.String(50), db.ForeignKey('categorie.categorie'), nullable=False)
    aantal_accepteerd = db.Column(db.Integer, default=0)

    persoon = db.relationship('Persoon', backref='categorie_statistieken', lazy=True)
    categorie_ref = db.relationship('Categorie', backref='gebruikers_statistieken', lazy=True)











class Bericht(db.Model):
    __tablename__ = 'bericht'

    id = db.Column(db.Integer, primary_key=True)
    afzender_id = db.Column(db.String(10), db.ForeignKey('persoon.idnummer'), nullable=False)
    ontvanger_id = db.Column(db.String(10), db.ForeignKey('persoon.idnummer'), nullable=False)
    klusnummer = db.Column(db.String(36), db.ForeignKey('klus.klusnummer'), nullable=True)
    inhoud = db.Column(db.Text, nullable=False)
    verzonden_op = db.Column(db.TIMESTAMP, nullable=False, default=datetime.utcnow)

    # Relaties
    afzender = db.relationship('Persoon', foreign_keys=[afzender_id], backref='verzonden_berichten')
    ontvanger = db.relationship('Persoon', foreign_keys=[ontvanger_id], backref='ontvangen_berichten')
    klus = db.relationship('Klus', backref=db.backref('berichten', lazy=True))

    def __repr__(self):
        return f'<Bericht {self.id} van {self.afzender_id} naar {self.ontvanger_id}>'
