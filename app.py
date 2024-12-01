import random
import threading
import time
from flask import Flask, request, render_template, redirect, url_for, session, flash, jsonify
import os
import datetime
from threading import Lock
import logging


app = Flask(__name__)
app.secret_key = 'supersecretkey'

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Dane globalne
ustawienia_aukcji = {}  # Globalna zmienna przechowująca dane aukcji
uzytkownicy = ["Pomarańcza", "Magenta", "Lila", "Zieleniak", "Administrator"]
zalogowani_uzytkownicy = []
produkty = {
    "Blok czekoladowy A": 10,
    "Blok czekoladowy B": 10,
    "Blok czekoladowy C": 10,
    "Blok czekoladowy D": 10,
    "Blok czekoladowy E": 10,
    "Blok czekoladowy F": 10,
    "Bombonierka 800": 10
}
licytacje = {produkt: [] for produkt in produkty}
propozycje = {produkt: {} for produkt in produkty}
wszystkie_oferty = {produkt: [] for produkt in produkty}
aukcja_aktywny = False
czas_rundy = 60
czas_pozostaly = czas_rundy
round_number = 0  # Initialize round_number
lock = Lock()

# Funkcje pomocnicze
def zapisz_wyniki_do_pliku():
    data = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    sciezka = os.path.join(os.getcwd(), f"wyniki_aukcji_{data}.txt")
    with open(sciezka, "w", encoding="utf-8") as plik:
        plik.write("Wyniki aukcji:\n")
        for produkt, zwyciezcy in licytacje.items():
            plik.write(f"{produkt}: {', '.join(zwyciezcy) if zwyciezcy else 'Brak zwycięzcy'}\n")
    logging.info(f"Auction results saved to {sciezka}")
    return sciezka

def uruchom_runde_aukcji():
    global aukcja_aktywny, czas_pozostaly
    aukcja_aktywny = True
    with lock:
        czas_pozostaly = czas_rundy
    while czas_pozostaly > 0:
        time.sleep(1)
        with lock:
            czas_pozostaly -= 1
    aukcja_aktywny = False
    logging.info("Auction round ended")

# Endpointy
@app.route('/')
def index():
    if 'user' not in session:
        return redirect(url_for('choose_user'))
    user = session['user']
    if user == "Administrator":
        return redirect(url_for('auction_settings'))
    user_bids = [product for product, bidders in licytacje.items() if user in bidders]
    return render_template('index.html', produkty=produkty, user=user, user_bids=user_bids,
                           aukcja_aktywny=aukcja_aktywny, czas_pozostaly=czas_pozostaly, round_number=round_number)

@app.route('/choose_user', methods=['GET', 'POST'])
def choose_user():
    if request.method == 'POST':
        user = request.form.get('user')
        if user in uzytkownicy and user not in zalogowani_uzytkownicy:
            session['user'] = user
            zalogowani_uzytkownicy.append(user)
            logging.info(f"User {user} logged in.")
            flash("Zalogowano pomyślnie.")
            return redirect(url_for('index'))
        else:
            flash("Użytkownik jest już zalogowany lub nie istnieje.")
            logging.warning(f"Failed login attempt for user {user}.")
            return redirect(url_for('choose_user'))
    return render_template('choose_user.html', uzytkownicy=uzytkownicy, zalogowani_uzytkownicy=zalogowani_uzytkownicy)

@app.route('/auction_settings', methods=['GET'])
def auction_settings():
    produkty_list = list(enumerate(produkty.items()))
    return render_template('admin.html', produkty_list=produkty_list, licytacje=licytacje, zalogowani_uzytkownicy=zalogowani_uzytkownicy, round_number=round_number)

@app.route('/update_auction_settings', methods=['POST'])
def update_auction_settings():
    global produkty
    for idx, product in enumerate(produkty.keys()):
        new_price = request.form.get(f'starting_price_{idx}', type=int)
        produkty[product] = max(1, new_price)
        logging.info(f"Updated starting price for {product} to {new_price}.")
    flash("Ustawienia aukcji zostały zaktualizowane.")
    return redirect(url_for('auction_settings'))

@app.route('/reset', methods=['POST'])
def reset():
    global licytacje, propozycje, wszystkie_oferty, produkty, round_number
    licytacje = {produkt: [] for produkt in produkty}
    propozycje = {produkt: {} for produkt in produkty}
    wszystkie_oferty = {produkt: [] for produkt in produkty}
    produkty = {
        "Blok czekoladowy A": 10,
        "Blok czekoladowy B": 10,
        "Blok czekoladowy C": 10,
        "Blok czekoladowy D": 10,
        "Blok czekoladowy E": 10,
        "Blok czekoladowy F": 10,
        "Bombonierka 800": 10
    }
    round_number = 1  # Reset round_number to 1
    logging.info("Auction has been reset.")
    flash("Aukcja została zrestartowana.")
    return redirect(url_for('auction_settings'))

@app.route('/start_auction', methods=['POST'])
def start_auction():
    global ustawienia_aukcji
    # Przechowaj bieżące ustawienia aukcji
    ustawienia_aukcji = {product: {"starting_price": price, "bid_increment": 5}
                         for product, price in produkty.items()}
    threading.Thread(target=uruchom_runde_aukcji).start()
    flash("Runda aukcji została uruchomiona. Ustawienia przesłane do użytkowników.")
    return redirect(url_for('auction_settings'))

@app.route('/get_auction_settings', methods=['GET'])
def get_auction_settings():
    # Endpoint dla użytkowników pobierający dane o aukcji
    return jsonify(ustawienia_aukcji)

@app.route('/end_round', methods=['POST'])
def end_round():
    global czas_pozostaly
    with lock:
        czas_pozostaly = 0
    logging.info("Auction round ended.")
    flash("Runda została zakończona.")
    return redirect(url_for('auction_settings'))

@app.route('/next_round', methods=['POST'])
def next_round():
    global propozycje, round_number
    propozycje.clear()
    round_number += 1  # Increment round_number
    logging.info(f"Prepared next auction round. Current round number is {round_number}.")
    flash("Przygotowano następną rundę.")
    return redirect(url_for('auction_settings'))

@app.route('/end_auction', methods=['POST'])
def end_auction():
    sciezka = zapisz_wyniki_do_pliku()
    logging.info(f"Auction ended. Results saved to file: {sciezka}")
    flash(f"Aukcja została zakończona. Wyniki zapisano w pliku: {sciezka}")
    return redirect(url_for('auction_settings'))

@app.route('/logout')
def logout():
    user = session.pop('user', None)
    if user in zalogowani_uzytkownicy:
        zalogowani_uzytkownicy.remove(user)
    logging.info(f"User {user} logged out.")
    flash("Zostałeś wylogowany.")
    return redirect(url_for('choose_user'))

if __name__ == '__main__':
    app.run(debug=True)
