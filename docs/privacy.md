# NotifyIQ — Privacy & Security Architecture

## 1. Privacy Principles

NotifyIQ is built on the principle of **radical data minimization and local user sovereignty**.

1. **Local-First Processing**: All ML vectorization, classification, deadline parsing, and priority calculations run offline on your machine.
2. **Zero Third-Party Cloud AI**: Notification bodies are **never** transmitted to OpenAI, Anthropic, Google Gemini API, or any external LLM service.
3. **No Unsolicited Network Transmission**: The application does not require an active internet connection.
4. **No Raw Notification Text in Logs**: Application logs strictly log event IDs, status codes, and timings. Notification titles, bodies, and personal metadata are never written to application logs.
5. **No Autonomous Actions**: NotifyIQ is a decision-support tool. It does not automatically dismiss notifications, send replies, or conduct transactions on the user's behalf.

## 2. Android Permission & Capture Lifecycle

- **Explicit Access Required**: Android notification capture relies on Android's `NotificationListenerService`. The OS strictly prevents apps from accessing notifications without the user manually navigating to system settings and granting access.
- **Package Allowlist & Pause**: Users can pause capture at any time using a single switch, or exclude sensitive applications (e.g., banking or personal messengers) from capture.
- **Notification Removal Handling**: When Android reports a notification was dismissed in the system shade (`onNotificationRemoved`), NotifyIQ does not automatically delete the local historical record without user consent.

## 3. Sensitive Data Redaction

NotifyIQ includes an automated rule-based redaction engine (`backend/ai/preprocess.py`) that masks common sensitive patterns:
- **Email addresses** $\rightarrow$ `[EMAIL]`
- **Telephone numbers** $\rightarrow$ `[PHONE]`
- **Credit card & 13–19 digit account sequences** $\rightarrow$ `[ACCOUNT]`
- **URLs and web links** $\rightarrow$ `[URL]`
- **One-time passwords (OTP) and verification codes** $\rightarrow$ `[CODE]`

> **Privacy Notice**: Redaction is rule-based pattern matching and is not guaranteed to catch every personal identifier. Users retain the choice to exclude apps from capture entirely.

## 4. Retention & Complete Data Purge

- **Retention Expiry**: Notifications can have automated retention limits.
- **One-Click Purge**: Users can permanently wipe all captured notifications, actions, and feedback at any time via the Settings & Privacy page in the Streamlit dashboard or via the API endpoint `POST /privacy/purge`.
- **Database Storage**: SQLite database is stored locally at `data/notifyiq.db` and is ignored from git tracking.
