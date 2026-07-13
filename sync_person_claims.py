#!/usr/bin/env python3
"""
AquaCtrl – nastavení identity uživatelů přes Firebase Custom Claims
===================================================================
Bezpečnostní audit (TNS) požaduje, aby se o oprávněních NErozhodovalo podle
localStorage (ac_person), ale podle ověřené identity. Tenhle skript zapíše
každému uživateli do tokenu claim `person` = jeho kód osoby (z LIDE), podle
mapování v `aquactrl_login_email`. Adminovi (TŘ) přidá i `admin`.

Firebase pravidla pak porovnávají zapisovaná data s `auth.token.person`
(nejde podvrhnout z prohlížeče) – např. úkol lze založit jen se svým `zadal`,
cizí absenci smí měnit jen admin.

Použití:
    python sync_person_claims.py            # nastaví/aktualizuje claim person všem
    python sync_person_claims.py show <mail> # vypíše claims jednoho účtu

Účet musí v Firebase Auth existovat (dotyčný se aspoň jednou přihlásil).
Kdo se ještě nepřihlásil, se přeskočí – spusť skript znovu, až se přihlásí.
Claim se v tokenu projeví po dalším přihlášení / obnovení tokenu (appka to
dělá sama přes getIdTokenResult(true) při startu).
"""

import sys
import firebase_admin
from firebase_admin import credentials, auth, db

SERVICE_ACCOUNT = 'service-account-key.json'
DATABASE_URL    = 'https://moje-budky-default-rtdb.firebaseio.com'
NODE            = 'aquactrl_login_email'
ADMIN_CODES     = {'TŘ'}  # kdo dostane i admin claim (drž v souladu s ADMIN_KOD v index.html)


def _init():
    cred = credentials.Certificate(SERVICE_ACCOUNT)
    firebase_admin.initialize_app(cred, {'databaseURL': DATABASE_URL})


def main():
    _init()

    if len(sys.argv) >= 3 and sys.argv[1] == 'show':
        email = sys.argv[2].strip().lower()
        u = auth.get_user_by_email(email)
        print(f'{email} (uid={u.uid}) claims: {dict(u.custom_claims or {}) or "{}"}')
        return

    mapping = db.reference(NODE).get() or {}
    done = skip = 0
    for key, code in mapping.items():
        email = key.replace(',', '.')  # klíč = e-mail s čárkami místo teček
        try:
            u = auth.get_user_by_email(email)
        except auth.UserNotFoundError:
            print(f'  přeskočeno (bez Auth účtu): {email} -> {code}')
            skip += 1
            continue
        claims = dict(u.custom_claims or {})
        claims['person'] = code
        if code in ADMIN_CODES:
            claims['admin'] = True
        auth.set_custom_user_claims(u.uid, claims)
        print(f'  {email} -> person={code}' + (' +admin' if code in ADMIN_CODES else ''))
        done += 1

    print(f'\nHotovo: {done} nastaveno, {skip} přeskočeno (ještě se nepřihlásili).')
    print('Projeví se po dalším otevření appky (obnoví si token sama).')


if __name__ == '__main__':
    main()
