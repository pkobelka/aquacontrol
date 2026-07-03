#!/usr/bin/env python3
"""
AquaControl – vygenerování/reset přihlašovacích PINů
=====================================================
Vygeneruje náhodný 5místný PIN, uloží jeho bcrypt hash do uzlu `aqua_pins`
(RTDB, čteno jen přes service account, klienti tam nesmí) a vypíše čitelný
seznam kód -> jméno -> PIN pro rozdání lidem. Výstup nikam needituj/needivej
– PINy si po rozdání smaž z terminálu/historie.

Použití:
    python set_pins_aqua.py                # vygeneruje PIN jen těm, co ho ještě nemají
    python set_pins_aqua.py TŘ PŘ           # vygeneruje/resetuje PIN jen vyjmenovaným
    python set_pins_aqua.py --all --force   # resetuje úplně všem (i těm, co PIN už mají)

Vyžaduje: pip install firebase-admin bcrypt
"""

import sys
import time
import secrets
import bcrypt
import firebase_admin
from firebase_admin import credentials, db

from approve_aqua import LIDE  # kód osoby -> celé jméno, jeden zdroj pravdy

SERVICE_ACCOUNT = 'service-account-key.json'
DATABASE_URL    = 'https://moje-budky-default-rtdb.firebaseio.com'
NODE            = 'aqua_pins'
PIN_DELKA       = 5


def novy_pin():
    return str(secrets.randbelow(10 ** PIN_DELKA)).zfill(PIN_DELKA)


def main():
    args = sys.argv[1:]
    force = '--force' in args
    all_ = '--all' in args
    kody = [a for a in args if not a.startswith('--')]

    cred = credentials.Certificate(SERVICE_ACCOUNT)
    firebase_admin.initialize_app(cred, {'databaseURL': DATABASE_URL})

    if kody:
        cile = kody
    elif all_:
        cile = list(LIDE.keys())
    else:
        cile = list(LIDE.keys())

    vysledky = []
    for kod in cile:
        if kod not in LIDE:
            print(f'Přeskočeno – neznámý kód "{kod}" (není v LIDE).')
            continue
        ref = db.reference(f'{NODE}/{kod}')
        if ref.get() and not force and not kody:
            continue  # bez --force/explicitního kódu neresetuj existující PIN

        pin = novy_pin()
        hash_ = bcrypt.hashpw(pin.encode(), bcrypt.gensalt()).decode()
        ref.set({'hash': hash_, 'ts': int(time.time() * 1000)})
        db.reference(f'aqua_pin_attempts/{kod}').delete()
        vysledky.append((kod, LIDE[kod], pin))

    if not vysledky:
        print('Nic ke generování – všichni už PIN mají (použij --force pro reset).')
        return

    print(f'\nVygenerováno {len(vysledky)} PINů – rozdej lidem soukromě, pak výstup smaž:\n')
    for kod, jmeno, pin in vysledky:
        print(f'  {jmeno:<22} ({kod})  PIN: {pin}')


if __name__ == '__main__':
    main()
