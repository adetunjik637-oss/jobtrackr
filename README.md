# JobTrackr

AI cover-letter generator + job-application tracker. Built with Django, PostgreSQL
(SQLite for local dev), OpenAI, and Paystack subscriptions.

A user uploads a resume, pastes a job link or description, and gets a tailored
cover letter in seconds — then tracks every application in one dashboard. Free
users get 3 letters a month; Pro (₦1,500 / $5 a month) unlocks unlimited letters.

---

## What's inside

```
jobtrackr/
├── jobtrackr/          # project settings, root urls, wsgi
├── accounts/           # Profile, subscription state, free-tier counter, auth
├── core/               # resumes, job applications, cover letters, OpenAI + parsing
│   └── services/       # openai_service.py, resume_parser.py
├── billing/            # Paystack client, subscribe / callback / webhook
├── templates/          # all pages (base, auth, dashboard, tracker, pricing…)
├── static/app.css      # styling
├── requirements.txt
└── .env.example
```

### Key features
- **Auth** — signup / login / logout (Django auth). A `Profile` is created automatically.
- **Resumes** — upload PDF / DOCX / TXT; text is extracted and stored for tailoring.
- **Cover letters** — OpenAI generates a letter from the resume + job; editable in-app; download as `.txt`.
- **Free-tier gate** — non-subscribers are capped at `FREE_MONTHLY_LETTERS` per month (resets monthly).
- **Tracker** — add jobs, set status (Saved / Applied / Interviewing / Offer / Rejected), follow-up dates, filter by status.
- **Billing** — Paystack Plans drive recurring subscriptions; a signed webhook keeps subscription state in sync.

---

## Run it locally (5 minutes)

You need **Python 3.11+**.

```bash
# 1. From the project folder
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
#   Open .env and set at least SECRET_KEY. Leave DATABASE_URL empty to use SQLite.
#   Add OPENAI_API_KEY to generate letters, and Paystack keys to take payments.

# 4. Create the database tables
python manage.py makemigrations
python manage.py migrate

# 5. (Optional) create an admin user for /admin
python manage.py createsuperuser

# 6. Run
python manage.py runserver
```

Open **http://127.0.0.1:8000** and sign up.

> The app runs without any API keys — you just can't generate letters (needs
> `OPENAI_API_KEY`) or take payments (needs Paystack keys) until those are set.

---

## Getting the API keys

### OpenAI
1. Create a key at <https://platform.openai.com/api-keys>.
2. Put it in `.env` as `OPENAI_API_KEY`. `OPENAI_MODEL` defaults to `gpt-4o-mini`
   (cheap — well under ₦5 per letter). Switch to `gpt-4o` for higher quality.

### Paystack (recurring subscriptions)
1. Sign up at <https://dashboard.paystack.com> and grab your **test** keys from
   *Settings → API Keys & Webhooks*. Put them in `.env`
   (`PAYSTACK_SECRET_KEY`, `PAYSTACK_PUBLIC_KEY`).
2. Create two **Plans** (*Dashboard → Plans*): one NGN plan at ₦1,500/monthly and
   one USD plan at $5/monthly. Copy each plan code into `.env`
   (`PAYSTACK_PLAN_CODE_NGN`, `PAYSTACK_PLAN_CODE_USD`).
3. Set your **webhook URL** to `https://YOUR_DOMAIN/billing/webhook/`. The webhook
   is signature-verified and is the source of truth for renewals and cancellations.
4. Test with Paystack's test card: `4084 0840 8408 4081`, any future expiry, CVV `408`.

---

## How the subscription flow works

1. On **/billing/pricing/** the user picks a currency and clicks *Subscribe*.
2. `billing/views.subscribe` creates a pending `Payment` and calls Paystack
   `transaction/initialize` with the plan code, then redirects to Paystack.
3. After payment, Paystack redirects back to `/billing/callback/`, which verifies
   the transaction and activates the subscription (31 days).
4. On each renewal, Paystack posts `charge.success` / `invoice.payment_succeeded`
   to `/billing/webhook/`, which extends `subscription_expiry`. A
   `subscription.disable` event marks the profile cancelled.

`Profile.is_subscribed` (active status + unexpired) is what unlocks unlimited
letters throughout the app.

---

## Deploying to production

Works on Render, Railway, Fly.io, or any host that runs Django + Postgres.

1. Provision a **PostgreSQL** database and set `DATABASE_URL` (the app switches to
   Postgres automatically when this is set).
2. Set env vars: `SECRET_KEY`, `DEBUG=False`, `ALLOWED_HOSTS=yourdomain.com`,
   `CSRF_TRUSTED_ORIGINS=https://yourdomain.com`, plus the OpenAI and Paystack keys.
3. Build steps:
   ```bash
   pip install -r requirements.txt
   python manage.py collectstatic --noinput
   python manage.py migrate
   ```
4. Start command:
   ```bash
   gunicorn jobtrackr.wsgi
   ```
   WhiteNoise serves static files, so no separate static host is needed.
5. Point your Paystack webhook at `https://yourdomain.com/billing/webhook/`.

---

## Notes & next steps

- **Verification status:** every Python file compiles cleanly. Migrations and a
  live boot were not run in the build sandbox (no PyPI access there) — run
  `makemigrations && migrate` once locally and you're live.
- The paid-only extras from the business plan (CSV export, follow-up reminders,
  multiple-resume limits, tone-gating) are easy to add on top of the
  `Profile.is_subscribed` check — the hooks are already in place.
- Cover letters download as `.txt` today; add PDF/DOCX export with the same
  libraries already in `requirements.txt` (`python-docx`, and a PDF writer).
