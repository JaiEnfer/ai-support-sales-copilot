# Client Side Guide

This file explains what to add on the client side.

Keep it simple:

- The frontend is what you see in the browser
- It needs to know where the backend is running

## Open This File

Open:

- `frontend/.env.local`

## Add These 3 Lines

Put this inside `frontend/.env.local`:

```env
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000
NEXT_PUBLIC_DEFAULT_COMPANY_ID=startup-demo-001
NEXT_PUBLIC_SHOW_ADMIN_LINK=true
```

## What These Mean

### `NEXT_PUBLIC_API_BASE_URL`

- Tells the frontend where the backend is running

### `NEXT_PUBLIC_DEFAULT_COMPANY_ID`

- Tells the frontend which company to use for testing

### `NEXT_PUBLIC_SHOW_ADMIN_LINK`

- Shows the Admin page link in the browser

## You Do Not Need This

You do not need to keep this in the frontend for normal local testing:

```env
NEXT_PUBLIC_ADMIN_API_KEY=
```

The admin page now uses:

- company ID
- company access key

## How To Test In Browser

### Step 1

Start the backend on port `8000`

### Step 2

Start the frontend on port `3000`

### Step 3

Open:

- `http://localhost:3000`

This is the main client chat page.

### Step 4

Open:

- `http://localhost:3000/admin`

This is the admin page.

Use it to:

- upload PDF files
- scrape a website
- test document search

### Step 5

Go back to:

- `http://localhost:3000`

Ask questions in the chat box.

## Important

If chat is empty or gives weak answers, it usually means:

- no document was uploaded yet

So before testing the main chat, do one of these:

- upload a PDF in the admin page
- scrape a website in the admin page

## Very Short Version

Backend running on `8000` + frontend running on `3000` + at least one uploaded document = local testing works.
