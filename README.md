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
| `.github/workflows/send-push.yml` | ruční spuštění push notifikace |

## Vývoj

Po každé změně dat/UI v `index.html` bumpni `CACHE` v `sw.js` (kvůli refreshi PWA na mobilech).

Logo source (`logo-ac.png`, 6 MB mockup) zůstal v repu `mojebudky` – zde je jen vyříznutý odznak (`logo-ac-512.png`) a runtime ikony.
