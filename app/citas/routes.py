from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app.citas import bp_cita
from app import db
from app.models.cita import Cita
from app.models.paciente import Paciente
from app.models.medico import Medico
from app.models.sala import Sala
from datetime import datetime, timedelta

# ============================================
# LISTAR CITAS (CON BUSCADOR MEJORADO)
# ============================================
@bp_cita.route('/')
@login_required
def index():
    """Lista citas según el rol del usuario con búsqueda mejorada y filtro por estado"""
    search = request.args.get('search', '').strip()
    estado = request.args.get('estado', '').strip()  
    
    # Construir consulta base según rol
    if current_user.is_admin():
        query = Cita.query
    elif current_user.is_medico():
        medico = Medico.query.filter_by(usuario_id=current_user.id).first()
        query = Cita.query.filter_by(medico_id=medico.id) if medico else Cita.query.filter_by(medico_id=-1)
    elif current_user.is_paciente():
        paciente = Paciente.query.filter_by(usuario_id=current_user.id).first()
        query = Cita.query.filter_by(paciente_id=paciente.id) if paciente else Cita.query.filter_by(paciente_id=-1)
    elif current_user.is_recepcionista():
        query = Cita.query
    else:
        flash('⛔ No tienes permisos.', 'danger')
        return redirect(url_for('core.landing'))
    
    # FILTRO POR ESTADO (se aplica ANTES de la búsqueda)
    if estado:
        query = query.filter(Cita.estado == estado)
    
    # BÚSQUEDA 
    if search:
        conditions = []
        search_terms = search.split()
        
        # ============================================
        # 1. SI ES NÚMERO: BUSCAR POR ID EXACTO
        # ============================================
        if search.isdigit():
            # Buscar EXACTAMENTE el número
            conditions.append(Cita.id == int(search))
        else:
            # ============================================
            # 2. SI NO ES NÚMERO: BUSCAR POR TEXTO
            # ============================================
            # Buscar por nombre completo (concatenado)
            conditions.append(
                db.func.concat(Paciente.nombres, ' ', Paciente.apellidos).ilike(f'%{search}%')
            )
            
            # Buscar por nombre o apellido individual
            for term in search_terms:
                conditions.append(Cita.paciente.has(Paciente.nombres.ilike(f'%{term}%')))
                conditions.append(Cita.paciente.has(Paciente.apellidos.ilike(f'%{term}%')))
            
            # Buscar por CI del paciente
            conditions.append(Cita.paciente.has(Paciente.ci.ilike(f'%{search}%')))
            
            # Buscar por médico
            for term in search_terms:
                conditions.append(Cita.medico.has(Medico.nombre.ilike(f'%{term}%')))
                conditions.append(Cita.medico.has(Medico.apellidos.ilike(f'%{term}%')))
            
            # Buscar por motivo y estado
            conditions.append(Cita.motivo.ilike(f'%{search}%'))
            conditions.append(Cita.estado.ilike(f'%{search}%'))
        
        # Aplicar todas las condiciones con OR
        if conditions:
            query = query.filter(db.or_(*conditions))
    
    # Ordenar por ID DESCENDENTE (más reciente primero)
    citas = query.order_by(Cita.id.desc()).all()
    
    
    return render_template('citas/index.html', citas=citas, search=search, estado=estado)

# ============================================
# OBTENER HORARIOS DISPONIBLES (AJAX)
# ============================================
@bp_cita.route('/horarios_disponibles')
@login_required
def horarios_disponibles():
    """Devuelve los horarios disponibles de un médico para una fecha"""
    medico_id = request.args.get('medico_id', type=int)
    fecha_str = request.args.get('fecha')
    
    if not medico_id or not fecha_str:
        return jsonify({'error': 'Faltan parámetros'}), 400
    
    try:
        fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'error': 'Fecha inválida'}), 400
    
    medico = Medico.query.get_or_404(medico_id)
    
    # DEFINIR HORARIO DE ATENCIÓN
    hora_inicio = 8   # 8:00 AM
    hora_fin = 18     # 6:00 PM
    intervalo = 30    # 30 minutos
    
    # GENERAR TODOS LOS HORARIOS POSIBLES
    horarios_posibles = []
    hora_actual = datetime.combine(fecha, datetime.min.time()) + timedelta(hours=hora_inicio)
    hora_limite = datetime.combine(fecha, datetime.min.time()) + timedelta(hours=hora_fin)
    
    while hora_actual < hora_limite:
        horarios_posibles.append(hora_actual)
        hora_actual += timedelta(minutes=intervalo)
    
    # OBTENER CITAS OCUPADAS (TODOS LOS ESTADOS EXCEPTO CANCELADA Y COMPLETADA)
    inicio_dia = datetime.combine(fecha, datetime.min.time())
    fin_dia = datetime.combine(fecha, datetime.max.time())
    
    citas_ocupadas = Cita.query.filter(
        Cita.medico_id == medico_id,
        Cita.fecha_hora >= inicio_dia,
        Cita.fecha_hora <= fin_dia,
        Cita.estado.in_(['pendiente', 'confirmada'])  # ✅ SOLO pendientes y confirmadas
    ).all()
    
    # CREAR SET DE HORARIOS OCUPADOS
    horarios_ocupados = set()
    for cita in citas_ocupadas:
        # Usar el formato exacto de hora (HH:MM)
        hora_str = cita.fecha_hora.strftime('%H:%M')
        horarios_ocupados.add(hora_str)
        print(f"🔴 Horario ocupado: {hora_str} - Cita #{cita.id} - Estado: {cita.estado}")
    
    # FILTRAR HORARIOS DISPONIBLES
    horarios_disponibles = []
    for hora in horarios_posibles:
        hora_str = hora.strftime('%H:%M')
        if hora_str not in horarios_ocupados:
            horarios_disponibles.append({
                'hora': hora_str,
                'timestamp': hora.isoformat()
            })
    
    # LOG DE DEPURACIÓN
    print(f"📅 Médico: {medico.nombre_completo()}")
    print(f"📅 Fecha: {fecha_str}")
    print(f"📊 Horarios disponibles: {len(horarios_disponibles)}")
    
    return jsonify({
        'medico': medico.nombre_completo(),
        'fecha': fecha_str,
        'horarios': horarios_disponibles
    })

# ============================================
# CREAR CITA 
# ============================================
@bp_cita.route('/crear', methods=['GET', 'POST'])
@login_required
def crear():
    """Crear una nueva cita con selección de horario disponible"""
    # Verificar permisos
    if not (current_user.is_admin() or current_user.is_recepcionista() or current_user.is_medico() or current_user.is_paciente()):
        flash('⛔ No tienes permisos para crear citas.', 'danger')
        return redirect(url_for('core.landing'))
    
    # Obtener paciente actual si es paciente
    paciente_actual = None
    if current_user.is_paciente():
        paciente_actual = Paciente.query.filter_by(usuario_id=current_user.id).first()
        if not paciente_actual:
            flash('⚠️ No tienes un perfil de paciente completo.', 'warning')
            return redirect(url_for('auth.perfil'))
    
    # Procesar formulario POST
    if request.method == 'POST':
        # Obtener datos del formulario
        if current_user.is_paciente():
            paciente_id = paciente_actual.id
        else:
            paciente_id = request.form.get('paciente_id')
        
        medico_id = request.form.get('medico_id')
        sala_id = request.form.get('sala_id')
        fecha_hora_str = request.form.get('fecha_hora')
        motivo = request.form.get('motivo')
        estado = request.form.get('estado', 'pendiente')
        
        # Validar que se haya seleccionado un horario
        if not fecha_hora_str:
            flash('⚠️ Por favor, selecciona un horario disponible.', 'warning')
            return redirect(url_for('cita.crear'))
        
        # Intentar diferentes formatos de fecha
        formatos = ['%Y-%m-%dT%H:%M:%S', '%Y-%m-%dT%H:%M', '%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M']
        fecha_hora = None
        
        for formato in formatos:
            try:
                fecha_hora = datetime.strptime(fecha_hora_str, formato)
                break
            except ValueError:
                continue
        
        if not fecha_hora:
            flash('❌ Formato de fecha inválido. Por favor, selecciona un horario.', 'danger')
            return redirect(url_for('cita.crear'))
        
        # Validar que la fecha no sea en el pasado
        if fecha_hora < datetime.now():
            flash('⚠️ No puedes agendar citas en fechas pasadas.', 'warning')
            return redirect(url_for('cita.crear'))
        
        # Validar disponibilidad de sala
        sala_ocupada = Cita.query.filter_by(
            sala_id=sala_id,
            fecha_hora=fecha_hora
        ).first()
        
        if sala_ocupada:
            flash('⚠️ La sala ya está ocupada en ese horario.', 'warning')
            return redirect(url_for('cita.crear'))
        
        # Validar disponibilidad del médico
        medico_ocupado = Cita.query.filter_by(
            medico_id=medico_id,
            fecha_hora=fecha_hora
        ).first()
        
        if medico_ocupado:
            flash('⚠️ El médico ya tiene una cita en ese horario.', 'warning')
            return redirect(url_for('cita.crear'))
        
        # Crear la cita
        cita = Cita(
            paciente_id=paciente_id,
            medico_id=medico_id,
            sala_id=sala_id,
            fecha_hora=fecha_hora,
            motivo=motivo,
            estado=estado
        )
        db.session.add(cita)
        db.session.commit()
        
        flash('✅ Cita agendada exitosamente.', 'success')
        
        # Redirigir según rol
        if current_user.is_paciente():
            return redirect(url_for('paciente.dashboard'))
        else:
            return redirect(url_for('cita.index'))
    
    # GET - Mostrar formulario
    pacientes = Paciente.query.all() if not current_user.is_paciente() else []
    medicos = Medico.query.all()
    salas = Sala.query.filter_by(estado='disponible').all()
    
    return render_template('citas/crear.html', 
                         pacientes=pacientes, 
                         medicos=medicos, 
                         salas=salas,
                         paciente=paciente_actual if current_user.is_paciente() else None,
                         datetime=datetime)


# ============================================
# EDITAR CITA
# ============================================
@bp_cita.route('/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar(id):
    """Editar una cita existente"""
    cita = Cita.query.get_or_404(id)
    
    if not (current_user.is_admin() or current_user.is_recepcionista()):
        flash('⛔ No tienes permisos.', 'danger')
        return redirect(url_for('core.landing'))
    
    if request.method == 'POST':
        paciente_id = request.form.get('paciente_id')
        medico_id = request.form.get('medico_id')
        sala_id = request.form.get('sala_id')
        fecha_hora_str = request.form.get('fecha_hora')
        motivo = request.form.get('motivo')
        estado = request.form.get('estado')
        
        # Intentar diferentes formatos de fecha
        formatos = ['%Y-%m-%dT%H:%M:%S', '%Y-%m-%dT%H:%M', '%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M']
        fecha_hora = None
        
        for formato in formatos:
            try:
                fecha_hora = datetime.strptime(fecha_hora_str, formato)
                break
            except ValueError:
                continue
        
        if not fecha_hora:
            flash('❌ Formato de fecha inválido.', 'danger')
            return redirect(url_for('cita.editar', id=id))
        
        # Validar disponibilidad de sala (excepto la misma cita)
        sala_ocupada = Cita.query.filter(
            Cita.sala_id == sala_id,
            Cita.fecha_hora == fecha_hora,
            Cita.id != id
        ).first()
        
        if sala_ocupada:
            flash('⚠️ La sala ya está ocupada en ese horario.', 'warning')
            return redirect(url_for('cita.editar', id=id))
        
        cita.paciente_id = paciente_id
        cita.medico_id = medico_id
        cita.sala_id = sala_id
        cita.fecha_hora = fecha_hora
        cita.motivo = motivo
        cita.estado = estado
        
        db.session.commit()
        flash('✅ Cita actualizada exitosamente.', 'success')
        return redirect(url_for('cita.index'))
    
    pacientes = Paciente.query.all()
    medicos = Medico.query.all()
    salas = Sala.query.all()
    return render_template('citas/editar.html', 
                         cita=cita, 
                         pacientes=pacientes, 
                         medicos=medicos, 
                         salas=salas,
                         datetime=datetime)


# ============================================
# COMPLETAR CITA
# ============================================
@bp_cita.route('/completar/<int:id>', methods=['POST'])
@login_required
def completar(id):
    """Marcar una cita como completada"""
    cita = Cita.query.get_or_404(id)
    
    if not (current_user.is_admin() or current_user.is_medico()):
        flash('⛔ No tienes permisos.', 'danger')
        return redirect(url_for('core.landing'))
    
    if cita.estado == 'cancelada':
        flash('⚠️ No se puede completar una cita cancelada.', 'warning')
        return redirect(url_for('cita.index'))
    
    cita.estado = 'completada'
    db.session.commit()
    
    flash('✅ Cita marcada como completada.', 'success')
    return redirect(url_for('cita.index'))


# ============================================
# CANCELAR CITA
# ============================================
@bp_cita.route('/cancelar/<int:id>')
@login_required
def cancelar(id):
    """Cancelar una cita"""
    cita = Cita.query.get_or_404(id)
    
    if cita.estado == 'completada':
        flash('⚠️ No se puede cancelar una cita ya completada.', 'warning')
        return redirect(url_for('cita.index'))
    
    if current_user.is_paciente():
        paciente = Paciente.query.filter_by(usuario_id=current_user.id).first()
        if cita.paciente_id != paciente.id:
            flash('⛔ No puedes cancelar esta cita.', 'danger')
            return redirect(url_for('cita.index'))
    elif not (current_user.is_admin() or current_user.is_recepcionista() or current_user.is_medico()):
        flash('⛔ No tienes permisos.', 'danger')
        return redirect(url_for('core.landing'))
    
    cita.estado = 'cancelada'
    db.session.commit()
    
    flash('🗑️ Cita cancelada correctamente.', 'info')
    return redirect(url_for('cita.index'))


# ============================================
# VER DETALLE DE CITA
# ============================================
@bp_cita.route('/<int:id>')
@login_required
def show(id):
    """Ver detalle de una cita"""
    cita = Cita.query.get_or_404(id)
    return render_template('citas/show.html', cita=cita)