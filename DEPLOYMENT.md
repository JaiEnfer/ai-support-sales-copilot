# Deployment Guide

This project is set up to deploy with:

- frontend on Vercel
- backend on Render
- persistent backend storage mounted to the API service

That setup keeps the widget easy to embed on client sites while letting you manage all tenants centrally.

## Backend On Render

This repo includes `render.yaml`, so you can create the API service from the Render blueprint instead of entering settings by hand.

### Render setup

1. Create a new Blueprint instance from this repository.
2. Confirm the generated web service uses:
   - build command: `pip install -r backend/requirements.txt`
   - start command: `uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT`
   - health check path: `/api/health/live`
3. Keep the persistent disk mounted at `/var/data/ai-support-sales-copilot`.
4. Set the secret environment variables:
   - `GROQ_API_KEY`
   - `ADMIN_API_KEY`
   - `CHAT_API_KEY`
   - `COMPANY_ADMIN_TOKEN_SECRET`
5. Set host and CORS values for your real domains:
   - `TRUSTED_HOSTS=["your-backend-domain.onrender.com"]`
   - `ALLOWED_ORIGINS=["https://your-frontend-domain.vercel.app"]`

The backend supports a `DATA_DIR` setting, so Render can persist uploads, document metadata, and Chroma state on its mounted disk instead of the ephemeral container filesystem.

## Frontend On Vercel

This repo includes `frontend/vercel.json` for a straightforward Next.js deployment.

### Vercel setup

1. Import the repository.
2. Set the project root directory to `frontend`.
3. Add these environment variables:

```env
NEXT_PUBLIC_API_BASE_URL=https://your-backend-domain.onrender.com
NEXT_PUBLIC_DEFAULT_COMPANY_ID=startup-demo-001
NEXT_PUBLIC_CHAT_API_KEY=your-chat-key
NEXT_PUBLIC_SHOW_ADMIN_LINK=false
```

4. Deploy the project.

Set `NEXT_PUBLIC_SHOW_ADMIN_LINK=true` only for internal demo or operator environments where you want the home page to expose `/admin`. Leave it `false` for client-facing production so the public chat experience stays clean.

Once deployed, your public widget script will be available at:

```text
https://your-frontend-domain.vercel.app/widget.js
```

## Connect The Services

After both services are live:

1. Update Render `ALLOWED_ORIGINS` with the final Vercel URL.
2. Update Render `TRUSTED_HOSTS` with the final Render backend hostname.
3. Confirm `NEXT_PUBLIC_API_BASE_URL` points at the deployed backend.
4. Open:
   - `https://your-frontend-domain.vercel.app/`
   - `https://your-frontend-domain.vercel.app/admin`
   - `https://your-backend-domain.onrender.com/api/health`

## Provision Company Access

Use the master admin key once per client to create their company portal access:

```bash
curl -X PUT https://your-backend-domain.onrender.com/api/company-access \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-admin-key" \
  -d '{
    "company_id": "acme-dental",
    "company_access_key": "choose-a-long-random-company-key",
    "display_name": "Acme Dental",
    "answer_mode": "support",
    "chatbot_title": "Acme Dental Assistant",
    "chatbot_subtitle": "Ask us about services, bookings, pricing, or insurance."
  }'
```

Or use the helper script from your repo checkout:

```bash
.venv\Scripts\python.exe backend/scripts/provision_company_access.py ^
  --api-base-url https://your-backend-domain.onrender.com ^
  --admin-api-key your-admin-key ^
  --company-id acme-dental ^
  --display-name "Acme Dental" ^
  --answer-mode support ^
  --chatbot-title "Acme Dental Assistant" ^
  --chatbot-subtitle "Ask us about services, bookings, pricing, or insurance."
```

If you do not pass `--company-access-key`, the helper generates one and prints it so you can share it with the client.

Then the client can sign into:

- `https://your-frontend-domain.vercel.app/admin`

with:

- company ID: `acme-dental`
- access key: the `company_access_key` you set for that company

## Client Website Embed

Once the frontend is public, give the client this snippet:

```html
<script
  src="https://your-frontend-domain.vercel.app/widget.js"
  data-company="acme-dental"
  data-title="Acme Dental Assistant"
  data-subtitle="Ask us about services, bookings, pricing, or insurance."
  data-api-key="your-chat-key"
  data-button-label="Chat with Acme Dental"
></script>
```

The client only needs script-tag access to their website. This works well on WordPress, Shopify, Webflow, Wix custom code blocks, and most custom websites.

## Production Checklist

- Use a unique `company_id` for each client.
- Use a long random company access key for each client and rotate it if it is shared too broadly.
- Clear old tenant data before reusing a demo workspace.
- Keep `ADMIN_API_KEY`, `CHAT_API_KEY`, and `COMPANY_ADMIN_TOKEN_SECRET` set only on the backend.
- Rotate any API key that was ever committed or shared.
- Re-scrape or re-upload client content after major retrieval changes.
- Plan to replace shared chat keys with signed widget tokens or gateway auth as the next security upgrade.
