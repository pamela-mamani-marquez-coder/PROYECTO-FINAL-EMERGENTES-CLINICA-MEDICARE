from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app.medicos import bp_medico
from app import db
from app.models.medico import Medico
from app.models.sala import Sala
from app.models.especialidad import Especialidad
from app.models.usuario import Usuario
from app.models.cita import Cita
from app.models.paciente import Paciente
from datetime import datetime, timedelta
from sqlalchemy import func

# ============================================
# LISTAR MÉDICOS CON BUSCADOR
# ============================================
@bp_medico.route('/')
@login_required
def index():
    """Lista todos los médicos con búsqueda"""
    search = request.args.get('search', '').strip()
    
    query = Medico.query
    
    # BÚSQUEDA SIMPLE Y COMPATIBLE
    if search:
        search_term = f'%{search}%'
        query = query.filter(
            db.or_(
                Medico.nombre.ilike(search_term),
                Medico.apellidos.ilike(search_term),
                Medico.especialidad.has(Especialidad.nombre.ilike(search_term)),
                Medico.telefono.ilike(search_term),
                Medico.email.ilike(search_term)
            )
        )
    
    # Ordenar por ID descendente (más reciente primero)
    medicos = query.order_by(Medico.id.desc()).all()
    
    return render_template('medicos/index.html', medicos=medicos, search=search)

# ============================================
# DASHBOARD DEL MÉDICO
# ============================================
@bp_medico.route('/dashboard')
@login_required
def dashboard():
    """Dashboard del médico con estadísticas completas"""
    if not current_user.is_medico():
        flash('⛔ Acceso denegado.', 'danger')
        return redirect(url_for('core.landing'))
    
    medico = Medico.query.filter_by(usuario_id=current_user.id).first()
    if not medico:
        flash('⚠️ No tienes un perfil de médico completo.', 'warning')
        return redirect(url_for('auth.perfil'))
    
    # Fechas para cálculos
    hoy = datetime.now().date()
    inicio_semana = hoy - timedelta(days=hoy.weekday())  # Lunes de esta semana
    fin_semana = inicio_semana + timedelta(days=6)       # Domingo de esta semana
    proximos_7_dias = hoy + timedelta(days=7)
    
    # ============================================
    # 1. CITAS DE HOY
    # ============================================
    citas_hoy = Cita.query.filter(
        Cita.medico_id == medico.id,
        func.date(Cita.fecha_hora) == hoy
    ).order_by(Cita.fecha_hora.asc()).all()
    
    # ============================================
    # 2. CITAS PENDIENTES (TODAS)
    # ============================================
    citas_pendientes = Cita.query.filter(
        Cita.medico_id == medico.id,
        Cita.estado == 'pendiente'
    ).count()
    
    # ============================================
    # 3. CITAS DE LA SEMANA (Lunes a Domingo)
    # ============================================
    citas_semana = Cita.query.filter(
        Cita.medico_id == medico.id,
        func.date(Cita.fecha_hora) >= inicio_semana,
        func.date(Cita.fecha_hora) <= fin_semana
    ).count()
    
    # ============================================
    # 4. TOTAL DE PACIENTES ÚNICOS
    # ============================================
    total_pacientes = db.session.query(func.count(Cita.paciente_id.distinct())).filter(
        Cita.medico_id == medico.id
    ).scalar() or 0
    
    # ============================================
    # 5. ESTADÍSTICAS ADICIONALES
    # ============================================
    citas_completadas = Cita.query.filter_by(medico_id=medico.id, estado='completada').count()
    citas_canceladas = Cita.query.filter_by(medico_id=medico.id, estado='cancelada').count()
    
    # ============================================
    # 6. PRÓXIMAS CITAS (próximos 7 días, excluyendo hoy)
    # ============================================
    citas_proximas = Cita.query.filter(
        Cita.medico_id == medico.id,
        func.date(Cita.fecha_hora) > hoy,
        func.date(Cita.fecha_hora) <= proximos_7_dias,
        Cita.estado.in_(['pendiente', 'confirmada'])
    ).order_by(Cita.fecha_hora.asc()).all()
    
    # ============================================
    # 7. ÚLTIMOS PACIENTES ATENDIDOS
    # ============================================
    ultimos_pacientes = db.session.query(
        Paciente, Cita
    ).join(
        Cita, Cita.paciente_id == Paciente.id
    ).filter(
        Cita.medico_id == medico.id,
        Cita.estado == 'completada'
    ).order_by(
        Cita.fecha_hora.desc()
    ).limit(5).all()
    
    # ============================================
    # 8. PACIENTES FRECUENTES (más citas)
    # ============================================
    pacientes_frecuentes = db.session.query(
        Paciente,
        func.count(Cita.id).label('total_citas')
    ).join(
        Cita, Cita.paciente_id == Paciente.id
    ).filter(
        Cita.medico_id == medico.id
    ).group_by(
        Paciente.id
    ).order_by(
        func.count(Cita.id).desc()
    ).limit(5).all()
    
    return render_template(
        'medicos/dashboard.html',
        medico=medico,
        citas_hoy=citas_hoy,
        citas_pendientes=citas_pendientes,
        citas_semana=citas_semana,
        total_pacientes=total_pacientes,
        citas_completadas=citas_completadas,
        citas_canceladas=citas_canceladas,
        citas_proximas=citas_proximas,
        ultimos_pacientes=ultimos_pacientes,
        pacientes_frecuentes=pacientes_frecuentes,
        hoy=hoy,
        inicio_semana=inicio_semana,
        fin_semana=fin_semana
    )


# ============================================
# CREAR MÉDICO (SOLO ADMIN)
# ============================================
@bp_medico.route('/crear', methods=['GET', 'POST'])
@login_required
def crear():
    """Crear un nuevo médico"""
    if not current_user.is_admin():
        flash('⛔ Acceso denegado. Solo administradores.', 'danger')
        return redirect(url_for('core.landing'))
    
    if request.method == 'POST':
        usuario_id = request.form.get('usuario_id')
        especialidad_id = request.form.get('especialidad_id')
        nombre = request.form.get('nombre')
        apellidos = request.form.get('apellidos')
        telefono = request.form.get('telefono')
        email = request.form.get('email')
        sala_id = request.form.get('sala_id')
        horario_atencion = request.form.get('horario_atencion')
        
        usuario = Usuario.query.get(usuario_id)
        if not usuario or usuario.rol != 'medico':
            flash('❌ El usuario seleccionado no es un médico.', 'danger')
            return render_template('medicos/crear.html', 
                                 usuarios=Usuario.query.filter_by(rol='medico').all(),
                                 especialidades=Especialidad.query.all(),
                                 salas=Sala.query.filter_by(estado='disponible').all())
        
        if Medico.query.filter_by(usuario_id=usuario_id).first():
            flash('❌ Este usuario ya tiene un perfil de médico.', 'danger')
            return render_template('medicos/crear.html',
                                 usuarios=Usuario.query.filter_by(rol='medico').all(),
                                 especialidades=Especialidad.query.all(),
                                 salas=Sala.query.filter_by(estado='disponible').all())
        
        # Obtener el número de consultorio desde la sala seleccionada
        sala = Sala.query.get(sala_id)
        consultorio = sala.numero if sala else None
        
        medico = Medico(
            usuario_id=usuario_id,
            especialidad_id=especialidad_id,
            nombre=nombre,
            apellidos=apellidos,
            telefono=telefono,
            email=email,
            consultorio=consultorio,
            horario_atencion=horario_atencion,
            sala_id=sala_id
        )
        db.session.add(medico)
        db.session.commit()
        
        flash(f'✅ Médico {nombre} {apellidos} creado exitosamente.', 'success')
        return redirect(url_for('medico.index'))
    
    # GET - Mostrar formulario
    usuarios = Usuario.query.filter_by(rol='medico').all()
    especialidades = Especialidad.query.all()
    salas = Sala.query.filter_by(estado='disponible').all()
    
    return render_template('medicos/crear.html', 
                         usuarios=usuarios, 
                         especialidades=especialidades,
                         salas=salas)


# ============================================
# API: OBTENER DATOS DE USUARIO (AJAX)
# ============================================
@bp_medico.route('/api/usuario/<int:usuario_id>')
@login_required
def api_get_usuario(usuario_id):
    """API para obtener datos de un usuario por ID (para autocompletar)"""
    usuario = Usuario.query.get_or_404(usuario_id)
    
    # Verificar que el usuario tenga rol médico
    if usuario.rol != 'medico':
        return jsonify({'error': 'El usuario no es un médico'}), 400
    
    return jsonify({
        'nombres': usuario.nombres or '',
        'apellidos': usuario.apellidos or '',
        'telefono': usuario.telefono or '',
        'email': usuario.email or ''
    })


# ============================================
# VER DETALLE DE MÉDICO
# ============================================
@bp_medico.route('/<int:id>')
@login_required
def show(id):
    """Ver detalle de un médico"""
    medico = Medico.query.get_or_404(id)
    return render_template('medicos/show.html', medico=medico)


# ============================================
# EDITAR MÉDICO (SOLO ADMIN)
# ============================================
@bp_medico.route('/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar(id):
    """Editar un médico"""
    if not current_user.is_admin():
        flash('⛔ Acceso denegado. Solo administradores.', 'danger')
        return redirect(url_for('core.landing'))
    
    medico = Medico.query.get_or_404(id)
    
    if request.method == 'POST':
        medico.especialidad_id = request.form.get('especialidad_id')
        medico.nombre = request.form.get('nombre')
        medico.apellidos = request.form.get('apellidos')
        medico.telefono = request.form.get('telefono')
        medico.email = request.form.get('email')
        medico.consultorio = request.form.get('consultorio')
        medico.horario_atencion = request.form.get('horario_atencion')
        
        db.session.commit()
        flash(f'✅ Médico {medico.nombre} actualizado exitosamente.', 'success')
        return redirect(url_for('medico.index'))
    
    especialidades = Especialidad.query.all()
    return render_template('medicos/editar.html', medico=medico, especialidades=especialidades)


# ============================================
# ELIMINAR MÉDICO (SOLO ADMIN)
# ============================================
@bp_medico.route('/eliminar/<int:id>', methods=['POST'])
@login_required
def eliminar(id):
    """Eliminar un médico"""
    if not current_user.is_admin():
        flash('⛔ Acceso denegado.', 'danger')
        return redirect(url_for('core.landing'))
    
    medico = Medico.query.get_or_404(id)
    nombre = medico.nombre
    
    db.session.delete(medico)
    db.session.commit()
    
    flash(f'✅ Médico {nombre} eliminado exitosamente.', 'success')
    return redirect(url_for('medico.index'))