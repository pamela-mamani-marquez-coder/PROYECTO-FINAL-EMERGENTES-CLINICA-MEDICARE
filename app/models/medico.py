from app.extensions import db

class Medico(db.Model):
    __tablename__ = 'medicos'
    
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), unique=True)
    especialidad_id = db.Column(db.Integer, db.ForeignKey('especialidades.id'))
    sala_id = db.Column(db.Integer, db.ForeignKey('salas.id'))  # ✅ Nueva columna
    nombre = db.Column(db.String(100), nullable=False)
    apellidos = db.Column(db.String(100), nullable=False)
    telefono = db.Column(db.String(20))
    email = db.Column(db.String(120))
    consultorio = db.Column(db.String(50))
    horario_atencion = db.Column(db.String(100))
    
    # Relaciones
    usuario = db.relationship('Usuario', back_populates='medico', uselist=False)
    especialidad = db.relationship('Especialidad', back_populates='medicos')
    sala = db.relationship('Sala', back_populates='medicos')  
    citas = db.relationship('Cita', back_populates='medico')
    historial = db.relationship('HistorialClinico', back_populates='medico')
    
    def nombre_completo(self):
        return f"Dr. {self.nombre} {self.apellidos}"
    
    def __repr__(self):
        return f'<Medico {self.nombre_completo()}>'