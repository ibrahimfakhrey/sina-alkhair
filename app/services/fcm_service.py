import os
import firebase_admin
from firebase_admin import credentials, messaging

# Initialize Firebase Admin SDK
_firebase_app = None


def init_firebase():
    """Initialize Firebase Admin SDK"""
    global _firebase_app

    if _firebase_app is not None:
        return _firebase_app

    # Look for service account key in multiple locations
    possible_paths = [
        os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'firebase-service-account.json'),
        os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'serviceAccountKey.json'),
        os.getenv('FIREBASE_SERVICE_ACCOUNT_PATH', ''),
    ]

    cred_path = None
    for path in possible_paths:
        if path and os.path.exists(path):
            cred_path = path
            break

    if cred_path:
        cred = credentials.Certificate(cred_path)
        _firebase_app = firebase_admin.initialize_app(cred)
        print(f"Firebase initialized with credentials from: {cred_path}")
    else:
        # Try to initialize without credentials (for environments with default credentials)
        try:
            _firebase_app = firebase_admin.initialize_app()
            print("Firebase initialized with default credentials")
        except Exception as e:
            print(f"Warning: Could not initialize Firebase: {e}")
            print("Push notifications will not work until Firebase is configured.")
            return None

    return _firebase_app


def send_push_notification(fcm_token, title, body, data=None, platform='android'):
    """
    Send push notification to a single device

    Args:
        fcm_token: The device's FCM token
        title: Notification title
        body: Notification body/message
        data: Optional dict of additional data
        platform: 'ios' or 'android'

    Returns:
        bool: True if successful, False otherwise
    """
    if not fcm_token:
        return False

    # Initialize Firebase if not already done
    if init_firebase() is None:
        print("Firebase not initialized, skipping push notification")
        return False

    try:
        # Create the message
        message = messaging.Message(
            token=fcm_token,
            notification=messaging.Notification(
                title=title,
                body=body,
            ),
            data=data or {},
        )

        # Platform-specific configuration
        if platform == 'ios':
            message.apns = messaging.APNSConfig(
                payload=messaging.APNSPayload(
                    aps=messaging.Aps(
                        alert=messaging.ApsAlert(
                            title=title,
                            body=body,
                        ),
                        badge=1,
                        sound='default',
                    ),
                ),
            )
        else:  # android
            message.android = messaging.AndroidConfig(
                priority='high',
                notification=messaging.AndroidNotification(
                    title=title,
                    body=body,
                    icon='@mipmap/ic_launcher',
                    channel_id='high_importance_channel',
                    sound='default',
                ),
            )

        # Send the message
        response = messaging.send(message)
        print(f"Successfully sent push notification: {response}")
        return True

    except messaging.UnregisteredError:
        print(f"FCM token is no longer valid: {fcm_token[:20]}...")
        # Token is invalid, should be removed from database
        return False
    except Exception as e:
        print(f"Error sending push notification: {e}")
        return False


def send_push_to_user(user, title, body, data=None):
    """
    Send push notification to a user if they have FCM token

    Args:
        user: User model instance
        title: Notification title
        body: Notification body/message
        data: Optional dict of additional data

    Returns:
        bool: True if successful, False otherwise
    """
    if not user or not user.fcm_token:
        return False

    return send_push_notification(
        fcm_token=user.fcm_token,
        title=title,
        body=body,
        data=data,
        platform=user.fcm_platform or 'android'
    )


def send_push_to_multiple(users, title, body, data=None):
    """
    Send push notification to multiple users

    Args:
        users: List of User model instances
        title: Notification title
        body: Notification body/message
        data: Optional dict of additional data

    Returns:
        int: Number of successful sends
    """
    success_count = 0
    for user in users:
        if send_push_to_user(user, title, body, data):
            success_count += 1
    return success_count
