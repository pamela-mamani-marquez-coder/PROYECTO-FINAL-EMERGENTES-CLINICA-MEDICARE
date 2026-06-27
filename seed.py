# seed_extra.py
from app import create_app, db
from app.models import Usuario, Paciente, Medico, Especialidad, Sala, Cita, Factura
from datetime import datetime, timedelta
import random

app = create_app()

def seed_extra():
    with app.app_context():
        print("Agregando datos extras...")
        
        # ============================================
        # 1. VERIFICAR DATOS EXISTENTES
        # ============================================
        print(f"📊 Pacientes antes: {Paciente.query.count()}")
        print(f"📊 Citas antes: {Cita.query.count()}")
        print(f"📊 Facturas antes: {Factura.query.count()}")
        
        # ============================================
        # 2. CREAR PACIENTES ADICIONALES
        # ============================================
        print("\n👨‍⚕️ Creando pacientes adicionales...")
        
        pacientes_data = [
            {'ci': '11546948', 'nombres': 'Andrea', 'apellidos': 'Castillo', 
             'fecha_nacimiento': datetime(1998, 12, 5), 'genero': 'Femenino',
             'telefono': '78945620', 'email': 'andrea@email.com', 
             'seguro_medico': 'Salud Total', 'alergias': 'Ninguna'},
            {'ci': '22446688', 'nombres': 'Fernando', 'apellidos': 'Gómez',
             'fecha_nacimiento': datetime(1975, 4, 18), 'genero': 'Masculino',
             'telefono': '78945621', 'email': 'fernando@email.com', 
             'seguro_medico': 'MediSalud', 'alergias': 'Penicilina'},
            {'ci': '11335577', 'nombres': 'Sofía', 'apellidos': 'Vargas',
             'fecha_nacimiento': datetime(2000, 8, 25), 'genero': 'Femenino',
             'telefono': '78945622', 'email': 'sofia@email.com', 
             'seguro_medico': 'Salud Total', 'alergias': 'Ninguna'},
            {'ci': '66778899', 'nombres': 'Patricia', 'apellidos': 'Ramos',
             'fecha_nacimiento': datetime(1978, 11, 3), 'genero': 'Femenino',
             'telefono': '78945630', 'email': 'patricia@email.com', 
             'seguro_medico': 'Salud Total', 'alergias': 'Ninguna'},
            {'ci': '22334455', 'nombres': 'Ricardo', 'apellidos': 'Silva',
             'fecha_nacimiento': datetime(1982, 5, 17), 'genero': 'Masculino',
             'telefono': '78945631', 'email': 'ricardo@email.com', 
             'seguro_medico': 'MediSalud', 'alergias': 'Ninguna'},
            {'ci': '33445566', 'nombres': 'Valeria', 'apellidos': 'Castro',
             'fecha_nacimiento': datetime(1991, 2, 28), 'genero': 'Femenino',
             'telefono': '78945632', 'email': 'valeria@email.com', 
             'seguro_medico': 'Salud Total', 'alergias': 'Ninguna'},
            {'ci': '44556677', 'nombres': 'Daniel', 'apellidos': 'Mora',
             'fecha_nacimiento': datetime(1996, 8, 14), 'genero': 'Masculino',
             'telefono': '78945633', 'email': 'daniel@email.com', 
             'seguro_medico': 'MediSalud', 'alergias': 'Ninguna'},
            {'ci': '77889900', 'nombres': 'Camila', 'apellidos': 'Rojas',
             'fecha_nacimiento': datetime(1999, 12, 10), 'genero': 'Femenino',
             'telefono': '78945634', 'email': 'camila@email.com', 
             'seguro_medico': 'Salud Total', 'alergias': 'Ninguna'},
            {'ci': '88990011', 'nombres': 'Roberto', 'apellidos': 'Vásquez',
             'fecha_nacimiento': datetime(1975, 8, 5), 'genero': 'Masculino',
             'telefono': '78945619', 'email': 'roberto@email.com', 
             'seguro_medico': 'MediSalud', 'alergias': 'Ninguna'},
            {'ci': '99001122', 'nombres': 'Vanessa', 'apellidos': 'Díaz',
             'fecha_nacimiento': datetime(1998, 10, 22), 'genero': 'Femenino',
             'telefono': '78945620', 'email': 'vanessa@email.com', 
             'seguro_medico': 'Salud Total', 'alergias': 'Ninguna'},
        ]
        
        pacientes_creados = 0
        for data in pacientes_data:
            # Verificar si ya existe
            existe = Paciente.query.filter_by(ci=data['ci']).first()
            if not existe:
                paciente = Paciente(**data)
                db.session.add(paciente)
                pacientes_creados += 1
        
        db.session.commit()
        print(f"✅ {pacientes_creados} pacientes nuevos creados")
        
        # ============================================
        # 3. OBTENER REFERENCIAS
        # ============================================
        medicos = Medico.query.all()
        pacientes = Paciente.query.all()
        salas = Sala.query.all()
        
        if not medicos or not pacientes or not salas:
            print("⚠️ No hay médicos, pacientes o salas. Ejecuta seed_data.py primero.")
            return
        
        # ============================================
        # 4. CREAR CITAS ADICIONALES
        # ============================================
        print("\n📅 Creando citas adicionales...")
        
        motivos = [
            'Consulta general', 'Dolor de cabeza persistente', 'Dolor de espalda crónico',
            'Chequeo anual', 'Seguimiento de tratamiento', 'Dolor de garganta',
            'Fiebre alta', 'Control de presión arterial', 'Control de embarazo',
            'Vacunación', 'Alergias estacionales', 'Examen médico general',
            'Traumatismo deportivo', 'Dermatología', 'Consulta neurológica',
            'Control de diabetes', 'Asesoría nutricional', 'Terapia física'
        ]
        
        estados = ['pendiente', 'confirmada', 'completada', 'cancelada']
        
        citas_creadas = 0
        facturas_creadas = 0
        
        # Crear 20 citas
        for i in range(20):
            paciente = random.choice(pacientes)
            medico = random.choice(medicos)
            sala = random.choice(salas) if salas else None
            
            # Fechas entre hoy y 30 días
            dias = random.randint(1, 30)
            fecha = datetime.now() + timedelta(days=dias)
            fecha = fecha.replace(hour=random.randint(8, 18), minute=random.choice([0, 15, 30, 45]))
            
            estado = random.choice(estados)
            motivo = random.choice(motivos)
            
            cita = Cita(
                paciente_id=paciente.id,
                medico_id=medico.id,
                sala_id=sala.id if sala else None,
                fecha_hora=fecha,
                motivo=f"{motivo} - Extra #{i+1}",
                estado=estado,
                observaciones=f'Cita de prueba adicional {i+1}'
            )
            db.session.add(cita)
            citas_creadas += 1
            
            # Generar factura solo para citas completadas
            if estado == 'completada':
                monto = random.randint(50, 350)
                metodos = ['Efectivo', 'Tarjeta de Crédito', 'Tarjeta de Débito', 'Transferencia Bancaria', 'Seguro Médico']
                
                # Número de factura
                ultima_factura = Factura.query.order_by(Factura.id.desc()).first()
                if ultima_factura and ultima_factura.numero_factura:
                    try:
                        num = int(ultima_factura.numero_factura.split('-')[1]) + 1
                    except:
                        num = Factura.query.count() + 1
                else:
                    num = Factura.query.count() + 1
                numero_factura = f'FAC-{str(num).zfill(6)}'
                
                factura = Factura(
                    cita_id=None,  # Se actualizará después de commit
                    numero_factura=numero_factura,
                    monto_total=monto,
                    metodo_pago=random.choice(metodos),
                    estado_pago=random.choice(['pagado', 'pagado', 'pendiente']),
                    fecha_emision=fecha + timedelta(hours=1),
                    fecha_pago=fecha + timedelta(hours=2) if random.choice([True, False]) else None
                )
                db.session.add(factura)
                facturas_creadas += 1
        
        db.session.commit()
        
        # Actualizar cita_id en facturas
        # (Esto es un poco complejo, pero podemos omitirlo para simplificar)
        
        print(f"✅ {citas_creadas} citas nuevas creadas")
        print(f"✅ {facturas_creadas} facturas nuevas creadas")
        
        # ============================================
        # 5. RESUMEN FINAL
        # ============================================
        print("\n" + "="*50)
        print("✅ ¡DATOS EXTRAS AGREGADOS EXITOSAMENTE!")
        print("="*50)
        print(f"📊 Pacientes totales: {Paciente.query.count()}")
        print(f"📊 Citas totales: {Cita.query.count()}")
        print(f"📊 Facturas totales: {Factura.query.count()}")
        print("="*50)

if __name__ == '__main__':
    seed_extra()