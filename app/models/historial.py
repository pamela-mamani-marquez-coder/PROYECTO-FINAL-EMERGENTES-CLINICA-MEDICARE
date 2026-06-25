from app.extensions import db
from datetime import datetime

class HistorialClinico(db.Model):
    __tablename__ = 'historiales'
    
    id = db.Column(db.Integer, primary_key=True)
    paciente_id = db.Column(db.Integer, db.ForeignKey('pacientes.id'))
    medico_id = db.Column(db.Integer, db.ForeignKey('medicos.id'))
    cita_id = db.Column(db.Integer, db.ForeignKey('citas.id'))
    fecha = db.Column(db.DateTime, default=datetime.utcnow)
    diagnostico = db.Column(db.Text)
    sintomas = db.Column(db.Text)
    tratamiento = db.Column(db.Text)
    observaciones = db.Column(db.Text)
    
    # Relaciones 
    paciente = db.relationship('Paciente', back_populates='historial')
    medico = db.relationship('Medico', back_populates='historial')
    cita = db.relationship('Cita', back_populates='historial')  
    recetas = db.relationship('Receta', back_populates='historial')