DEFAULT_CONFIG = {
    'detectors': {
        'posture': {
            'enabled': True,
            'min_detection_confidence': 0.5,
            'min_tracking_confidence': 0.5,
            'leg_angle_threshold': 307,
            'neck_angle_threshold': 45,
            'alert_duration': 5  # segundos
        },
        'hands': {
            'enabled': True,
            'min_detection_confidence': 0.5,
            'min_tracking_confidence': 0.5,
            'max_shoulder_distance': 0.5,
            'max_elbow_distance': 0.3
        }
    },
    'notifications': {
        'enabled': True,
        'notification_cooldown': 30,  # segundos
        'log_file': 'posture_logs.txt'
    },
    'video': {
        'source': 0,  # 0 para webcam, o ruta a archivo
        'width': 1280,
        'height': 720
    }
}