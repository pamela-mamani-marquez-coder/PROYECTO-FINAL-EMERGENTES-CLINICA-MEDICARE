from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.pacientes import bp_paciente
from app import db
from app.models.paciente import Paciente
from app.models.usuario import Usuario
from datetime import datetime

# ============================================
# LISTAR PACIENTES CON BUSCADOR
# ============================================
@bp_paciente.route('/')
@login_required
def index():
    """Lista todos los pacientes con búsqueda"""
    search = request.args.get('search', '').strip()
    
    # Construir consulta base según rol
    if current_user.is_admin() or current_user.is_recepcionista() or current_user.is_medico():
        query = Paciente.query
    elif current_user.is_paciente():
        query = Paciente.query.filter_by(usuario_id=current_user.id)
    else:
        flash('⛔ No tienes permisos.', 'danger')
        return redirect(url_for('core.landing'))
    
    # APLICAR BÚSQUEDA si hay término
    if search:
        search_terms = search.split()
        conditions = []
        
        # Buscar por ID
        if search.isdigit():
            conditions.append(Paciente.id == int(search))
        
        # Buscar por CI
        conditions.append(Paciente.ci.ilike(f'%{search}%'))
        
        # Buscar por nombre completo o parcial
        for term in search_terms:
            conditions.append(Paciente.nombres.ilike(f'%{term}%'))
            conditions.append(Paciente.apellidos.ilike(f'%{term}%'))
        
        # Buscar por nombre completo (concatenado)
        conditions.append(db.func.concat(Paciente.nombres, ' ', Paciente.apellidos).ilike(f'%{search}%'))
        conditions.append(db.func.concat(Paciente.nombres, Paciente.apellidos).ilike(f'%{search}%'))
        
        # Buscar por teléfono
        conditions.append(Paciente.telefono.ilike(f'%{search}%'))
        
        # Buscar por email
        conditions.append(Paciente.email.ilike(f'%{search}%'))
        
        # Buscar por seguro médico
        conditions.append(Paciente.seguro_medico.ilike(f'%{search}%'))
        
        # Aplicar todas las condiciones con OR
        query = query.filter(db.or_(*conditions))
    
    # Ordenar por ID descendente (más reciente primero)
    pacientes = query.order_by(Paciente.id.desc()).all()
    
    return render_template('pacientes/index.html', pacientes=pacientes, search=search)


# ============================================
# CREAR PACIENTE
# ============================================
@bp_paciente.route('/crear', methods=['GET', 'POST'])
@login_required
def crear():
    """Crear un nuevo paciente"""
    if not (current_user.is_admin() or current_user.is_recepcionista()):
        flash('⛔ Acceso denegado.', 'danger')
        return redirect(url_for('core.landing'))
    
    if request.method == 'POST':
        usuario_id = request.form.get('usuario_id')
        ci = request.form.get('ci')
        nombres = request.form.get('nombres')
        apellidos = request.form.get('apellidos')
        fecha_nacimiento_str = request.form.get('fecha_nacimiento')
        genero = request.form.get('genero')
        telefono = request.form.get('telefono')
        direccion = request.form.get('direccion')
        email = request.form.get('email')
        seguro_medico = request.form.get('seguro_medico')
        alergias = request.form.get('alergias')
        
        # Validar CI único
        if Paciente.query.filter_by(ci=ci).first():
            flash('❌ El CI ya está registrado.', 'danger')
            return render_template('pacientes/crear.html',
                                 usuarios=Usuario.query.filter_by(rol='paciente').all())
        
        # Convertir fecha
        fecha_nacimiento = None
        if fecha_nacimiento_str:
            try:
                fecha_nacimiento = datetime.strptime(fecha_nacimiento_str, '%Y-%m-%d').date()
            except ValueError:
                pass
        
        paciente = Paciente(
            usuario_id=usuario_id,
            ci=ci,
            nombres=nombres,
            apellidos=apellidos,
            fecha_nacimiento=fecha_nacimiento,
            genero=genero,
            telefono=telefono,
            direccion=direccion,
            email=email,
            seguro_medico=seguro_medico,
            alergias=alergias
        )
        db.session.add(paciente)
        db.session.commit()
        
        flash(f'✅ Paciente {nombres} {apellidos} creado exitosamente.', 'success')
        return redirect(url_for('paciente.index'))
    
    usuarios = Usuario.query.filter_by(rol='paciente').all()
    return render_template('pacientes/crear.html', usuarios=usuarios)


# ============================================
# VER DETALLE DE PACIENTE
# ============================================
@bp_paciente.route('/<int:id>')
@login_required
def show(id):
    """Ver detalle de un paciente"""
    paciente = Paciente.query.get_or_404(id)
    
    if current_user.is_paciente() and paciente.usuario_id != current_user.id:
        flash('⛔ No tienes permisos para ver este perfil.', 'danger')
        return redirect(url_for('core.landing'))
    
    return render_template('pacientes/show.html', paciente=paciente)


# ============================================
# EDITAR PACIENTE
# ============================================
@bp_paciente.route('/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar(id):
    """Editar un paciente"""
    if not (current_user.is_admin() or current_user.is_recepcionista()):
        flash('⛔ Acceso denegado.', 'danger')
        return redirect(url_for('core.landing'))
    
    paciente = Paciente.query.get_or_404(id)
    
    if request.method == 'POST':
        ci = request.form.get('ci')
        nombres = request.form.get('nombres')
        apellidos = request.form.get('apellidos')
        fecha_nacimiento_str = request.form.get('fecha_nacimiento')
        genero = request.form.get('genero')
        telefono = request.form.get('telefono')
        direccion = request.form.get('direccion')
        email = request.form.get('email')
        seguro_medico = request.form.get('seguro_medico')
        alergias = request.form.get('alergias')
        
        # Validar CI único (excepto el mismo paciente)
        if ci != paciente.ci and Paciente.query.filter_by(ci=ci).first():
            flash('❌ El CI ya está registrado por otro paciente.', 'danger')
            return render_template('pacientes/editar.html', paciente=paciente)
        
        # Convertir fecha
        fecha_nacimiento = None
        if fecha_nacimiento_str:
            try:
                fecha_nacimiento = datetime.strptime(fecha_nacimiento_str, '%Y-%m-%d').date()
            except ValueError:
                pass
        
        paciente.ci = ci
        paciente.nombres = nombres
        paciente.apellidos = apellidos
        paciente.fecha_nacimiento = fecha_nacimiento
        paciente.genero = genero
        paciente.telefono = telefono
        paciente.direccion = direccion
        paciente.email = email
        paciente.seguro_medico = seguro_medico
        paciente.alergias = alergias
        
        db.session.commit()
        flash(f'✅ Paciente {nombres} {apellidos} actualizado exitosamente.', 'success')
        return redirect(url_for('paciente.index'))
    
    return render_template('pacientes/editar.html', paciente=paciente)


# ============================================
# ELIMINAR PACIENTE (SOLO ADMIN)
# ============================================
@bp_paciente.route('/eliminar/<int:id>', methods=['POST'])
@login_required
def eliminar(id):
    """Eliminar un paciente"""
    if not current_user.is_admin():
        flash('⛔ Acceso denegado.', 'danger')
        return redirect(url_for('core.landing'))
    
    paciente = Paciente.query.get_or_404(id)
    nombre = paciente.nombre_completo()
    
    db.session.delete(paciente)
    db.session.commit()
    
    flash(f'✅ Paciente {nombre} eliminado exitosamente.', 'success')
    return redirect(url_for('paciente.index'))

# ============================================
# DASHBOARD DEL PACIENTE
# ============================================
@bp_paciente.route('/dashboard')
@login_required
def dashboard():
    """Dashboard del paciente con sus citas y actividad"""
    if not current_user.is_paciente():
        flash('⛔ Acceso denegado.', 'danger')
        return redirect(url_for('core.landing'))
    
    paciente = Paciente.query.filter_by(usuario_id=current_user.id).first()
    if not paciente:
        flash('⚠️ No tienes un perfil de paciente completo.', 'warning')
        return redirect(url_for('auth.perfil'))
    
    from app.models.cita import Cita
    from app.models.factura import Factura
    from datetime import datetime
    
    ahora = datetime.now()
    
    # Próximas citas
    proximas_citas = Cita.query.filter(
        Cita.paciente_id == paciente.id,
        Cita.fecha_hora >= ahora,
        Cita.estado.in_(['pendiente', 'confirmada'])
    ).order_by(Cita.fecha_hora.asc()).limit(3).all()
    
    # Citas pasadas (historial)
    citas_pasadas = Cita.query.filter(
        Cita.paciente_id == paciente.id,
        Cita.fecha_hora < ahora
    ).order_by(Cita.fecha_hora.desc()).limit(3).all()
    
    # Facturas recientes
    facturas_recientes = Factura.query.join(Cita).filter(
        Cita.paciente_id == paciente.id
    ).order_by(Factura.fecha_emision.desc()).limit(3).all()
    
    return render_template('pacientes/dashboard.html',
                         paciente=paciente,
                         proximas_citas=proximas_citas,
                         citas_pasadas=citas_pasadas,
                         facturas_recientes=facturas_recientes)