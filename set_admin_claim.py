#!/usr/bin/env python3
"""
AquaCtrl – nastavení admin oprávnění přes Firebase Custom Claims
================================================================
Bezpečnostní report (TNS, 2026-Q3) žádal, aby se o admin právech
NErozhodovalo podle localStorage (to lze v prohlížeči podvrhnout), ale
podle ověřené identity na serveru. Tenhle skript nastaví (nebo odebere)
Custom Claim `admin: true` na přihlašovacím účtu v Firebase Auth.

Appka (index.html) pak čte claim přes user.getIdTokenResult() a Firebase
pravidla (viz SECURITY.md) vynucují `auth.token.admin === true` u citlivých
uzlů (např. aquactrl_login_email = správa přístupu).

Použití:
    python set_admin_claim.py set    <e-mail>   # udělí admina
    python set_admin_claim.py remove <e-mail>   # odebere admina
    python set_admin_claim.py show   <e-mail>   # vypíše aktuální claims

Účet musí v Firebase Auth existovat = daný člověk se už aspoň jednou
přihlásil e-mailovým odkazem. Po změně se claim projeví až po dalším
přihlášení (nebo obnovení ID tokenu) – appka dělá force refresh sama.
"""

import sys
import firebase_admin
from firebase_admin import credentials, auth

SERVICE_ACCOUNT = 'service-account-key.json'
DATABASE_URL    = 'https://moje-budky-default-rtdb.firebaseio.com'


def _init():
    cred = credentials.Certificate(SERVICE_ACCOUNT)
    firebase_admin.initialize_app(cred, {'databaseURL': DATABASE_URL})


def main():
    if len(sys.argv) < 3 or sys.argv[1] not in ('set', 'remove', 'show'):
        print(__doc__)
        sys.exit(1)

    akce, email = sys.argv[1], sys.argv[2].strip().lower()
    _init()

    try:
        user = auth.get_user_by_email(email)
    except auth.UserNotFoundError:
        print(f'CHYBA: účet {email} v Firebase Auth neexistuje.')
        print('       Musí se nejdřív aspoň jednou přihlásit do appky e-mailovým odkazem.')
        sys.exit(2)

    claims = dict(user.custom_claims or {})

    if akce == 'show':
        print(f'{email} (uid={user.uid}) claims: {claims or "{}"}')
        return

    if akce == 'set':
        claims['admin'] = True
        auth.set_custom_user_claims(user.uid, claims)
        print(f'OK: {email} má nyní admin = True. Projeví se po dalším přihlášení.')
    else:  # remove
        claims.pop('admin', None)
        auth.set_custom_user_claims(user.uid, claims or None)
        print(f'OK: {email} už NENÍ admin. Projeví se po dalším přihlášení.')


if __name__ == '__main__':
    main()
