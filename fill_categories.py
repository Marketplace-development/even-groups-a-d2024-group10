from app import create_app, db
from app.models import Categorie

# Maak de app aan
app = create_app()

# Voeg de categorieën toe in een applicatiecontext
with app.app_context():
    categorieën = ['buitenshuis', 'binnenshuis', 'tuin', 'techniek']

    for cat in categorieën:
        if not Categorie.query.filter_by(categorie=cat).first():
            nieuwe_categorie = Categorie(categorie=cat, naam=cat.capitalize())
            db.session.add(nieuwe_categorie)

    db.session.commit()

print("Categorieën succesvol toegevoegd!")
