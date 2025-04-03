from app import db

class VideoSource(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    video_url = db.Column(db.String(500), nullable=False)
    is_active = db.Column(db.Boolean, default=False)
    
    def __repr__(self):
        return f'<VideoSource {self.name}>'