# AquaControl

PWA pro evidenci provozních (mimořádných) událostí na vodárenské infrastruktuře **VHOS a.s.** – „mimka" / klikací prototyp. Vše je v jednom souboru `index.html` (inline CSS+JS) + ikony, `manifest.json`, `sw.js`, FCM push.

- **Živá adresa:** https://pkobelka.github.io/aquacontrol/
- Pozn.: stále jde o **mimku** – data se reálně neukládají (kromě push tokenů). Push notifikace fungují (sdílí Firebase projekt `moje-budky`).

## První nasazení (jednorázově)

1. **GitHub Pages:** Settings → Pages → Source = *Deploy from a branch*, Branch = `main` / `/ (root)` → Save. Za chvíli naběhne https://pkobelka.github.io/aquacontrol/
2. **Push notifikace (Actions secret):** Settings → Secrets and variables → Actions → *New repository secret*
   - Name: `FIREBASE_SERVICE_ACCOUNT`
   - Value: celý obsah service-account JSON z Firebase projektu `moje-budky` (stejný, jaký je v repu `mojebudky`).
   - Bez tohoto secretu nebude fungovat workflow „Odeslat push".

Doména `pkobelka.github.io` je v Firebase už autorizovaná (stejný origin jako budky), takže **VAPID/config netřeba měnit**.

## Přihlašování (PIN) – nasazení

Appka dřív neměla žádné skutečné přihlášení (kdokoli si v konzoli mohl nastavit, kdo je). Teď se lidé přihlašují kódem + PINem; PIN se ověřuje na malé serverové funkci (`api/login.js`), appka pak dostane podepsaný Firebase token a zůstává přihlášená (dokud se sám neodhlásíš).

**Pořadí nasazení, aby nikdo nezůstal zaseknutý:**

1. **Nasaď `api/login.js` na Vercel** (free plán, žádná karta):
   - Import repa do Vercelu (New Project → vyber `pkobelka/aquacontrol`).
   - Project Settings → Environment Variables:
     - `FIREBASE_SERVICE_ACCOUNT` = stejný JSON obsah jako GitHub Actions secret výše.
     - `ALLOWED_ORIGIN` = `https://pkobelka.github.io` (nepovinné, to už je výchozí).
   - Deploy → zkopíruj přidělenou URL (např. `https://aquacontrol-xxxx.vercel.app`).
2. V `index.html` najdi `window.AC_LOGIN_URL = "https://REPLACE-ME.vercel.app/api/login";` a nahraď skutečnou URL + `/api/login`. Commitni, počkej na redeploy GitHub Pages a **bumpni `CACHE` v `sw.js`**.
3. **Vygeneruj PINy:** lokálně (kde máš `service-account-key.json`, stejně jako pro `approve_aqua.py`) spusť `pip install firebase-admin bcrypt` a pak `python set_pins_aqua.py`. Vypíše kód/jméno/PIN pro každého – rozdej to lidem soukromě (osobně/telefonem, ne mailem/Slackem) a výpis pak smaž z terminálu.
4. **Vyzkoušej přihlášení** (klikni na badge „Vyber, kdo jsi" → zadej svůj kód + PIN) – v tuhle chvíli jsou databázová pravidla ještě stará (otevřená), takže i kdyby něco nesedělo, appka dál funguje.
5. Dej lidem pár dní, ať se každý alespoň jednou přihlásí (appka si je pak pamatuje, není potřeba nic opakovat).
6. **Až se přihlásí drtivá většina:** Firebase konzole → Realtime Database → *Rules* → nahraď obsahem `rules.aquacontrol.json` z tohoto repa → *Publish*. Od teď appka bez přihlášení nefunguje – kdokoli, kdo se ještě nepřihlásil, to prostě udělá při příštím otevření appky.

`rules.aquacontrol.json` mění jen uzly `aqua_*` (a přidává zavřené `aqua_pins`/`aqua_pin_attempts`) – ostatní uzly sdíleného Firebase projektu (patří appce „mojebudky") nechává beze změny, ty je potřeba vyřešit zvlášť v jejím repu.

## Odeslání push notifikace

GitHub → Actions → **Odeslat push (AquaControl)** → *Run workflow* (titulek + text, případně Device ID jednoho příjemce). Tokeny se čtou z uzlu `aqua_push_tokens` ve sdílené Firebase DB.

## Soubory

| soubor | účel |
|---|---|
| `index.html` | celá appka (UI + data + logika + push) |
| `sw.js` | offline service worker (scope `/aquacontrol/`) |
| `firebase-messaging-sw.js` | FCM service worker pro push (scope `/aquacontrol/fcm/`) |
| `manifest.json` | PWA manifest |
| `icon-*.png`, `logo-ac-*.png` | ikony / logo (odznak „AC") |
| `send_push_aqua.py` | skript pro odeslání FCM push |
| `approve_aqua.py` | ruční schválení zařízení pro push |
| `check_terminy_aqua.py` | hlídání zmeškaných termínů úkolů (cron) |
| `set_pins_aqua.py` | vygenerování/reset přihlašovacích PINů |
| `api/login.js` | serverová funkce (Vercel) – ověří PIN, vrátí Firebase custom token |
| `rules.aquacontrol.json` | doporučená pravidla Realtime Database (nasazuje se ručně přes Firebase konzoli) |
| `.github/workflows/send-push.yml` | ruční spuštění push notifikace |
| `.github/workflows/approve-devices.yml` | ruční schválení zařízení |
| `.github/workflows/check-terminy.yml` | plánované hlídání termínů (cron) |

## Vývoj

Po každé změně dat/UI v `index.html` bumpni `CACHE` v `sw.js` (kvůli refreshi PWA na mobilech).

Logo source (`logo-ac.png`, 6 MB mockup) zůstal v repu `mojebudky` – zde je jen vyříznutý odznak (`logo-ac-512.png`) a runtime ikony.
