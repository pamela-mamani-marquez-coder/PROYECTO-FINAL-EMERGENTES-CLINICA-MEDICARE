from app.extensions import db

class Sala(db.Model):
    __tablename__ = 'salas'
    
    id = db.Column(db.Integer, primary_key=True)
    numero = db.Column(db.String(10), unique=True, nullable=False)
    nombre = db.Column(db.String(100))
    ubicacion = db.Column(db.String(100))
    capacidad = db.Column(db.Integer, default=1)
    estado = db.Column(db.String(20), default='disponible')
    
    # Relaciones
    citas = db.relationship('Cita', back_populates='sala')
    medicos = db.relationship('Medico', back_populates='sala')  
    
    def __repr__(self):
        return f'<Sala {self.numero}>'