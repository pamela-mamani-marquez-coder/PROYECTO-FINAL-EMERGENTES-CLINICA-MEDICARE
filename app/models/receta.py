from app.extensions import db
from datetime import datetime

class Receta(db.Model):
    __tablename__ = 'recetas'
    
    id = db.Column(db.Integer, primary_key=True)
    historial_id = db.Column(db.Integer, db.ForeignKey('historiales.id'))
    medicamento = db.Column(db.String(100))
    dosis = db.Column(db.String(50))
    duracion = db.Column(db.String(50))
    indicaciones = db.Column(db.Text)
    fecha_emision = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relación
    historial = db.relationship('HistorialClinico', back_populates='recetas')