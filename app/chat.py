# app/chat.py
from flask import Blueprint, render_template

# Maak een nieuwe blueprint aan voor de chat
chat = Blueprint('chat', __name__)

# Voeg je chat-gerelateerde routes hier toe
@chat.route('/<klusnummer>')
def chat_view(klusnummer):
    # Haal de chatberichten voor de klus op en toon deze in de template
    return render_template('chat.html', klusnummer=klusnummer)
