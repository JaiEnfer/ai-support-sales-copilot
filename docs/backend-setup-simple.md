# Backend Setup Guide

This file explains what to change in `backend/.env`.

Keep it simple:

- The backend is the "brain"
- The `.env` file is where you add the settings
- You do not need to change everything

## Open This File

Open:

- `backend/.env`

## Change These 4 Things

### 1. `GROQ_API_KEY`

What it is:

- This helps the chatbot give better AI answers

What to do:

- If you already have a Groq key, keep it
- If you do not have one, you can leave it empty

Example:

```env
GROQ_API_KEY=your-groq-key-here
```

Or:

```env
GROQ_API_KEY=
```

### 2. `DEFAULT_COMPANY_ID`

What it is:

- This is the company name/id used for testing

What to do:

- Keep this for now unless you want a different company name

Example:

```env
DEFAULT_COMPANY_ID=startup-demo-001
```

### 3. `ADMIN_API_KEY`

What it is:

- This is the master admin key
- It is used only for admin/provisioning work

What to do:

- Change it from the default value to something private

Example:

```env
ADMIN_API_KEY=my-secret-admin-key-123
```

### 4. `COMPANY_ADMIN_TOKEN_SECRET`

What it is:

- This is used for admin login sessions

What to do:

- Change it from the default value to any long secret text

Example:

```env
COMPANY_ADMIN_TOKEN_SECRET=my-long-random-secret-text
```

## You Can Leave These As They Are

You usually do not need to change these for local testing:

- `APP_ENV=development`
- `ENABLE_API_DOCS=true`
- `CHAT_API_KEY=`
- `REQUIRE_COMPANY_ID=true`
- `ALLOWED_ORIGINS=["http://localhost:3000","http://127.0.0.1:3000"]`

## Simple Ready Version

Your `backend/.env` can look like this:

```env
APP_ENV=development
APP_VERSION=1.0.0
ENABLE_API_DOCS=true
GROQ_API_KEY=your-groq-key-here
GROQ_MODEL=llama-3.1-8b-instant
DEFAULT_COMPANY_ID=startup-demo-001
ADMIN_API_KEY=my-secret-admin-key-123
COMPANY_ADMIN_TOKEN_SECRET=my-long-random-secret-text
CHAT_API_KEY=
REQUIRE_COMPANY_ID=true
MAX_CHAT_HISTORY_MESSAGES=12
MAX_CHAT_MESSAGE_LENGTH=4000
MAX_UPLOAD_SIZE_BYTES=10485760
WEBSITE_SCRAPE_MAX_PAGES=6
WEBSITE_SCRAPE_TIMEOUT_SECONDS=10
WEBSITE_SCRAPE_USER_AGENT=AI-Support-Sales-Copilot/1.0
TRUSTED_HOSTS=["localhost","127.0.0.1","testserver"]
ALLOWED_ORIGINS=["http://localhost:3000","http://127.0.0.1:3000"]
```

## After This

Start the backend server.

If it runs without errors, your backend setup is done.
