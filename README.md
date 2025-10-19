# Google Drive Music Streamer

This is a single-page web application designed to stream audio files (acting as a personal "CD repository") directly from your Google Drive using the Google Drive API. It features a secure local setup via environment variable injection to protect your **Client ID**.

---

## 🗃️ Prerequisites

1.  **Google Cloud Project:** You must have a Google Cloud Project with the **Google Drive API** enabled.

2.  **OAuth 2.0 Client ID:** A **Web application** OAuth 2.0 Client ID must be created.

3.  **Local Server Setup:** The application requires **Python 3** and the `python-dotenv` library to run the local server securely.

    ```bash
    pip install python-dotenv
    ```

---

## 🛠️ Local Setup Guide

Follow these steps to get the music player running locally on `http://localhost:8000`.

### 1. Configure Google Cloud Console

You **must** authorize the local server address for the OAuth flow to work.

* Go to your **Google Cloud Console > Credentials**.

* Edit your Web application Client ID.

* Add the following two entries. This prevents the common `redirect_uri_mismatch` error:
    * **Authorized JavaScript origins:** `http://localhost:8000`
    * **Authorized Redirect URIs:** `http://localhost:8000/`

### 2. Create the `.env` File

This file stores your secret **Client ID** securely. Create a file named **`.env`** in the same directory as `gdmp.html` and `serve.py`.

```text
# Replace the value below with your actual Google OAuth 2.0 Client ID
GOOGLE_CLIENT_ID="YOUR_REAL_CLIENT_ID.apps.googleusercontent.com"