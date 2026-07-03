// AquaControl – přihlášení PINem
// Ověří PIN proti hashované hodnotě v Realtime Database (přístup jen přes
// service account, mimo dosah klientských DB pravidel) a vrátí podepsaný
// Firebase custom token, kterým se appka přihlásí přes signInWithCustomToken.
//
// Env proměnné (Vercel → Project Settings → Environment Variables):
//   FIREBASE_SERVICE_ACCOUNT – celý obsah service-account JSON (stejný, jaký
//                               je jako GitHub secret pro GitHub Actions)
//   ALLOWED_ORIGIN            – povolený CORS origin appky
//                               (výchozí https://pkobelka.github.io)

const admin = require('firebase-admin');
const bcrypt = require('bcryptjs');

const DATABASE_URL = 'https://moje-budky-default-rtdb.firebaseio.com';
const ADMIN_KOD = 'TŘ';
const MAX_POKUSU = 5;
const ZAMKNOUT_MS = 15 * 60 * 1000;

if (!admin.apps.length) {
  admin.initializeApp({
    credential: admin.credential.cert(JSON.parse(process.env.FIREBASE_SERVICE_ACCOUNT)),
    databaseURL: DATABASE_URL,
  });
}

function setCors(req, res) {
  const origin = process.env.ALLOWED_ORIGIN || 'https://pkobelka.github.io';
  res.setHeader('Access-Control-Allow-Origin', origin);
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
}

module.exports = async function handler(req, res) {
  setCors(req, res);
  if (req.method === 'OPTIONS') { res.status(204).end(); return; }
  if (req.method !== 'POST') { res.status(405).json({ error: 'method_not_allowed' }); return; }

  const body = typeof req.body === 'string' ? JSON.parse(req.body || '{}') : (req.body || {});
  const code = String(body.code || '').trim();
  const pin = String(body.pin || '').trim();

  if (!/^[A-ZÁČĎÉĚÍŇÓŘŠŤÚŮÝŽ]{2,4}$/.test(code) || !/^\d{4,6}$/.test(pin)) {
    res.status(400).json({ error: 'invalid_format' });
    return;
  }

  const db = admin.database();
  const attemptsRef = db.ref('aqua_pin_attempts/' + code);
  const now = Date.now();

  const attemptsSnap = await attemptsRef.get();
  const attempts = attemptsSnap.val() || { count: 0, lockUntil: 0 };
  if (attempts.lockUntil && attempts.lockUntil > now) {
    res.status(429).json({ error: 'locked', retryAfterMs: attempts.lockUntil - now });
    return;
  }

  const pinSnap = await db.ref('aqua_pins/' + code).get();
  const pinRec = pinSnap.val();
  const ok = pinRec && pinRec.hash && await bcrypt.compare(pin, pinRec.hash);

  if (!ok) {
    const count = (attempts.count || 0) + 1;
    const next = { count };
    if (count >= MAX_POKUSU) { next.count = 0; next.lockUntil = now + ZAMKNOUT_MS; }
    await attemptsRef.set(next);
    res.status(401).json({ error: 'invalid_credentials' });
    return;
  }

  await attemptsRef.remove();

  const token = await admin.auth().createCustomToken(code, {
    person: code,
    admin: code === ADMIN_KOD,
  });

  res.status(200).json({ token });
};
