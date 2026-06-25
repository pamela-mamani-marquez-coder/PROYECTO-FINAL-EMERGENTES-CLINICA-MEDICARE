import os
from flask import Flask
from app.config import Config
from app.extensions import db, migrate, login_manager, bcrypt
from datetime import datetime

def create_app():
    # Ruta base del proyecto
    base_dir = os.path.abspath(os.path.dirname(__file__) + '/..')
    
    app = Flask(
        __name__,
        template_folder=os.path.join(base_dir, 'templates'),
        static_folder=os.path.join(base_dir, 'static')
    )
    
    app.config.from_object(Config)
    
    # Inicializar extensiones
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    bcrypt.init_app(app)
    
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Por favor, inicia sesión.'
    login_manager.login_message_category = 'info'
    
    # User loader
    from app.models.usuario import Usuario
    
    @login_manager.user_loader
    def load_user(user_id):
        return Usuario.query.get(int(user_id))
    
    # Importar modelos
    from app.models import Usuario, Paciente, Medico, Especialidad, Sala, Cita, Factura, HistorialClinico, Receta
    
    # Registrar blueprints
    from app.core.routes import bp_core
    from app.auth.routes import bp_auth
    from app.admin.routes import bp_admin
    from app.pacientes.routes import bp_paciente
    from app.medicos.routes import bp_medico
    from app.citas.routes import bp_cita
    from app.facturacion.routes import bp_factura
    from app.historial.routes import bp_historial
    from app.recepcionista.routes import bp_recepcionista 
    
    app.register_blueprint(bp_core, url_prefix='/')
    app.register_blueprint(bp_auth, url_prefix='/auth')
    app.register_blueprint(bp_admin, url_prefix='/admin')
    app.register_blueprint(bp_paciente, url_prefix='/pacientes')
    app.register_blueprint(bp_medico, url_prefix='/medicos')
    app.register_blueprint(bp_cita, url_prefix='/citas')
    app.register_blueprint(bp_factura, url_prefix='/facturacion')
    app.register_blueprint(bp_historial, url_prefix='/historial')
    app.register_blueprint(bp_recepcionista, url_prefix='/recepcionista')
    
    # CREAR BASE DE DATOS Y DATOS DE PRUEBA
    
    with app.app_context():
        # 1. Crear todas las tablas 
        db.create_all()
        print("✅ Base de datos verificada/creada exitosamente.")
        
        
        if Usuario.query.first() is None:
            print(" Creando datos iniciales (primera vez)...")
            
            # === CREAR DATOS  ===
            
            # Especialidades
            especialidades = [
                Especialidad(nombre='Cardiología', descripcion='Especialidad del corazón'),
                Especialidad(nombre='Pediatría', descripcion='Especialidad de niños'),
                Especialidad(nombre='Ginecología', descripcion='Especialidad de la mujer'),
                Especialidad(nombre='Traumatología', descripcion='Especialidad de huesos'),
                Especialidad(nombre='Dermatología', descripcion='Especialidad de la piel'),
            ]
            db.session.add_all(especialidades)
            db.session.commit()
            print("   ✅ Especialidades creadas")
            
            # Salas
            salas = [
                Sala(numero='101', nombre='Consultorio 1', ubicacion='Planta 1', estado='disponible'),
                Sala(numero='102', nombre='Consultorio 2', ubicacion='Planta 1', estado='disponible'),
                Sala(numero='201', nombre='Consultorio 3', ubicacion='Planta 2', estado='disponible'),
            ]
            db.session.add_all(salas)
            db.session.commit()
            print("   ✅ Salas creadas")
            
            # Usuarios
            usuarios_data = [
                {'username': 'admin', 'nombres': 'Administrador', 
                'apellidos': 'Sistema', 'email': 'admin@medicare.com', 'rol': 'admin'},
                {'username': 'medico1', 'nombres': 'Carlos', 
                'apellidos': 'García', 'email': 'carlos@medicare.com', 'rol': 'medico'},
                {'username': 'medico2', 'nombres': 'María', 
                'apellidos': 'López', 'email': 'maria@medicare.com', 'rol': 'medico'},
                {'username': 'recepcionista', 'nombres': 'Ana', 
                'apellidos': 'Martínez', 'email': 'ana@medicare.com', 'rol': 'recepcionista'},
                {'username': 'paciente1', 'nombres': 'Pamela', 
                'apellidos': 'Mamani', 'email': 'pamela@medicare.com', 'rol': 'paciente'},
                {'username': 'paciente2', 'nombres': 'Juan', 
                'apellidos': 'Pérez', 'email': 'juan@medicare.com', 'rol': 'paciente'},
            ]
            
            passwords = {
                'admin': 'admin123',
                'medico1': 'medico123',
                'medico2': 'medico123',
                'recepcionista': 'recep123',
                'paciente1': 'paciente123',
                'paciente2': 'paciente123',
            }
            
            for data in usuarios_data:
                usuario = Usuario(**data)
                usuario.set_password(passwords[data['username']])
                db.session.add(usuario)
            db.session.commit()
            print("   ✅ Usuarios creados")
            
            # Pacientes
            pacientes_data = [
                {'usuario_id': 5, 'ci': '11546948', 'nombres': 'Pamela', 'apellidos': 'Mamani Marquez',
                'fecha_nacimiento': datetime(1990, 5, 15), 'genero': 'Femenino', 
                'telefono': '78945612', 'email': 'pamela@medicare.com', 'seguro_medico': 'Salud Total'},
                {'usuario_id': 6, 'ci': '12345678', 'nombres': 'Juan', 'apellidos': 'Pérez',
                'fecha_nacimiento': datetime(1985, 8, 20), 'genero': 'Masculino',
                'telefono': '78945613', 'email': 'juan@medicare.com', 'seguro_medico': 'MediSalud'},
            ]
            
            for data in pacientes_data:
                paciente = Paciente(**data)
                db.session.add(paciente)
            db.session.commit()
            print("   ✅ Pacientes creados")
            
            # Médicos
            medicos_data = [
                {'usuario_id': 2, 'especialidad_id': 1, 'nombre': 'Carlos', 'apellidos': 'García',
                'telefono': '77745612', 'email': 'carlos@medicare.com', 'consultorio': '101A',
                'horario_atencion': 'Lun-Vie 08:00-18:00'},
                {'usuario_id': 3, 'especialidad_id': 2, 'nombre': 'María', 'apellidos': 'López',
                'telefono': '77745613', 'email': 'maria@medicare.com', 'consultorio': '102B',
                'horario_atencion': 'Lun-Vie 09:00-17:00'},
            ]
            
            for data in medicos_data:
                medico = Medico(**data)
                db.session.add(medico)
            db.session.commit()
            print("   ✅ Médicos creados")
            
            # Citas
            citas_data = [
                {'paciente_id': 1, 'medico_id': 1, 'sala_id': 1, 
                'fecha_hora': datetime(2026, 6, 25, 10, 0), 
                'motivo': 'Consulta general', 'estado': 'confirmada'},
                {'paciente_id': 2, 'medico_id': 2, 'sala_id': 2,
                'fecha_hora': datetime(2026, 6, 26, 15, 30),
                'motivo': 'Dolor de cabeza', 'estado': 'pendiente'},
            ]
            
            for data in citas_data:
                cita = Cita(**data)
                db.session.add(cita)
            db.session.commit()
            print("   ✅ Citas creadas")
            
            print("=" * 50)
            print("✅ ¡DATOS INICIALES CREADOS EXITOSAMENTE!")
            print("=" * 50)
            print("📋 USUARIOS DE PRUEBA:")
            print("   👑 admin / admin123 (Administrador)")
            print("   🏥 medico1 / medico123 (Médico - Carlos García)")
            print("   🏥 medico2 / medico123 (Médico - María López)")
            print("   📋 recepcionista / recep123 (Recepcionista)")
            print("   👤 paciente1 / paciente123 (Paciente - Pamela)")
            print("   👤 paciente2 / paciente123 (Paciente - Juan)")
            print("=" * 50)
        else:
            
            print("📊 Base de datos ya contiene datos. No se eliminarán.")
            total_usuarios = Usuario.query.count()
            total_pacientes = Paciente.query.count()
            total_citas = Cita.query.count()
            print(f"   📊 Usuarios: {total_usuarios}")
            print(f"   📊 Pacientes: {total_pacientes}")
            print(f"   📊 Citas: {total_citas}")
            
    return app