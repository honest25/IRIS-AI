# IRIS AI - Android Mobile Client

This directory contains the Flutter Android application for IRIS AI.

## Setup Instructions

Since Flutter requires local SDK installation, follow these steps to initialize the project:

1. Install [Flutter SDK](https://docs.flutter.dev/get-started/install).
2. Run the following command in this directory:
   ```bash
   flutter create . --platforms android
   ```
3. Add the required dependencies to your `pubspec.yaml`:
   ```yaml
   dependencies:
     flutter:
       sdk: flutter
     web_socket_channel: ^2.4.0
     speech_to_text: ^6.1.1
     flutter_tts: ^3.8.3
     porcupine_flutter: ^3.0.0 # For Wake Word Detection
     permission_handler: ^11.0.1
     shared_preferences: ^2.2.2
     http: ^1.1.0
   ```
4. Update `android/app/src/main/AndroidManifest.xml` with permissions:
   ```xml
   <uses-permission android:name="android.permission.INTERNET" />
   <uses-permission android:name="android.permission.RECORD_AUDIO" />
   <uses-permission android:name="android.permission.READ_SMS" />
   <uses-permission android:name="android.permission.SEND_SMS" />
   <uses-permission android:name="android.permission.READ_CONTACTS" />
   ```
5. Run the app:
   ```bash
   flutter run
   ```

## Architecture
- **WebSockets**: Real-time communication with the FastAPI central server for commands and LLM responses.
- **Background Services**: (To be implemented using `flutter_background_service`) for continuous wake-word listening and notification reading.
