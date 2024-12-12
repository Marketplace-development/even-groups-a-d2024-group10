# app/chat.py
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from app.models import Klus, Persoon, Bericht
from app import db
from flask import Blueprint, jsonify, request, session
from app.models import Klus, Bericht, db
chat = Blueprint('chat', __name__, url_prefix='/chat')
    
@chat.route('/<klusnummer>', methods=['GET', 'POST'])
def chat_page(klusnummer):
    print(f"Ontvangen klusnummer: {klusnummer}")  # Debug-log
    # Controleer of de gebruiker is ingelogd
    user_id = session.get('user_id')
    if not user_id:
        flash("Je moet ingelogd zijn om deze pagina te bekijken.", "danger")
        return redirect(url_for('main.login'))

    # Haal de klus en berichten op
    klus = Klus.query.get_or_404(klusnummer)
    berichten = Bericht.query.filter_by(klusnummer=klusnummer).order_by(Bericht.verzonden_op).all()

    # Controleer of de gebruiker deel uitmaakt van de klus
    if user_id != klus.idnummer and user_id not in [zoeker.idnummer for zoeker in klus.klussen_zoekers]:
        flash("Je hebt geen toegang tot deze chat.", "danger")
        return redirect(url_for('main.dashboard'))

    # Ontvanger bepalen
    if klus.idnummer == user_id:  # De ingelogde gebruiker is de klusaanbieder
        ontvanger = klus.klussen_zoekers[0] if klus.klussen_zoekers else None
    else:  # De ingelogde gebruiker is een kluszoeker
        ontvanger = klus.persoon_aanbieder

    if ontvanger is None:  # Controleer of er een ontvanger is
        flash("Geen ontvanger gevonden voor deze klus.", "danger")
        return redirect(url_for('main.dashboard'))

    # Verwerk POST (nieuw bericht)
    if request.method == 'POST':
        inhoud = request.form.get('inhoud')
        if inhoud:
            nieuw_bericht = Bericht(
                afzender_id=user_id,
                ontvanger_id=ontvanger.idnummer,
                klusnummer=klusnummer,
                inhoud=inhoud
            )
            db.session.add(nieuw_bericht)
            db.session.commit()
            flash("Bericht verzonden!", "success")
            return redirect(url_for('chat.chat_page', klusnummer=klusnummer))

    # Render de chatpagina
    return render_template('chat.html', klus=klus, berichten=berichten, ontvanger=ontvanger)

@chat.route('/mijn_chats', methods=['GET'])
def mijn_chats():
    user_id = session.get('user_id')
    if not user_id:
        flash('Je moet ingelogd zijn om deze pagina te bekijken.', 'danger')
        return redirect(url_for('main.login'))

    # Haal de klussen op waar de gebruiker bij betrokken is
    klussen = Klus.query.filter_by(idnummer=user_id).all()
    klussen_info = []
    for klus in klussen:
        berichten = Bericht.query.filter_by(klusnummer=klus.klusnummer).order_by(Bericht.verzonden_op).all()
        klussen_info.append({
            'klusnummer': klus.klusnummer,
            'naam': klus.naam,
            'status': klus.status,
            'berichten': berichten,
        })

    return render_template('mijn_chats.html', klussen=klussen_info)




