# Dark Star Awards

## Local Development

To run this project locally, you need to serve it over HTTP (not file://) because Firebase modules require it.

### Option 1: Python Server
```bash
python server.py
```
Then open http://localhost:8000

### Option 2: Node.js http-server
```bash
npx http-server -p 8000
```

### Option 3: VS Code Live Server
Install the "Live Server" extension and click "Go Live"

## Firebase Setup

1. Make sure Authentication is enabled in Firebase Console
2. Enable Email/Password provider in Authentication settings
3. Create a Firestore database in production mode
4. Upload the `firestore.rules` file to Firestore Rules
5. Upload the `storage.rules` file to Storage Rules

## Features

- User authentication (Sign Up / Sign In)
- Entry submission form
- Player card display with scoring
- Real-time entry loading from Firestore

