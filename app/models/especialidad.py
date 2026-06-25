from app.extensions import db

class Especialidad(db.Model):
    __tablename__ = 'especialidades'
    
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), unique=True, nullable=False)
    descripcion = db.Column(db.Text)
    
    # Relación
    medicos = db.relationship('Medico', back_populates='especialidad')
    
    def __repr__(self):
        return f'<Especialidad {self.nombre}>'