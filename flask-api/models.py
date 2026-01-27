#from werkzeug.security import generate_password_hash
from .extensions import db

class Story(db.Model):
    __tablename__ = 'story'
    story_id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), unique=True, nullable=False, index=True)
    description = db.column(db.Text, nullable=False)