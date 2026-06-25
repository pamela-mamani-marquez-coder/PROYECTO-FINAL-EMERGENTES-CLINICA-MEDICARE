from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app.admin import bp_admin
from app import db
from app.models.usuario import Usuario
from app.models.paciente import Paciente
from app.models.medico import Medico
from app.models.especialidad import Especialidad
from app.models.cita import Cita
from app.models.sala import Sala 
from app.models.historial import HistorialClinico  
from app.models.receta import Receta      
from app.models.factura import Factura
from datetime import datetime, timedelta
import re

# ============================================
# FUNCIÓN PARA GENERAR USERNAME AUTOMÁTICO
# ============================================
def generar_username(rol):
    """Genera un username automático según el rol"""
    prefijos = {
        'admin': 'admin',
        'medico': 'medico',
        'recepcionista': 'recepcionista',
        'paciente': 'paciente'
    }
    
    prefijo = prefijos.get(rol, 'usuario')
    
    # Buscar el último número usado para ese rol
    usuarios = Usuario.query.filter(Usuario.username.startswith(prefijo)).all()
    
    if usuarios:
        numeros = []
        for u in usuarios:
            try:
                num = int(u.username.replace(prefijo, ''))
                numeros.append(num)
            except ValueError:
                continue
        if numeros:
            siguiente = max(numeros) + 1
        else:
            siguiente = 1
    else:
        siguiente = 1
    
    return f"{prefijo}{siguiente}"


# ============================================
# FUNCIÓN PARA VALIDAR CONTRASEÑA SEGURA
# ============================================
def validar_contraseña(password):
    """Valida que la contraseña sea segura"""
    if len(password) < 8:
        return False, "La contraseña debe tener al menos 8 caracteres."
    if not re.search(r'[A-Z]', password):
        return False, "La contraseña debe tener al menos una mayúscula."
    if not re.search(r'[a-z]', password):
        return False, "La contraseña debe tener al menos una minúscula."
    if not re.search(r'[0-9]', password):
        return False, "La contraseña debe tener al menos un número."
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False, "La contraseña debe tener al menos un carácter especial (!@#$%^&*)."
    return True, "Contraseña válida."


# ============================================
# OBTENER SIGUIENTE USERNAME (AJAX)
# ============================================
@bp_admin.route('/next_username')
@login_required
def next_username():
    """Devuelve el siguiente username disponible para un rol"""
    if not current_user.is_admin():
        return jsonify({'error': 'No autorizado'}), 403
    
    rol = request.args.get('rol', 'paciente')
    username = generar_username(rol)
    
    return jsonify({'username': username})


# ============================================
# DASHBOARD - Panel Principal del Administrador
# ============================================
@bp_admin.route('/')
@login_required
def dashboard():
    """Panel principal del administrador con estadísticas completas"""
    if not current_user.is_admin():
        flash('⛔ Acceso denegado. Solo administradores.', 'danger')
        return redirect(url_for('core.landing'))
    
    total_usuarios = Usuario.query.count()
    total_medicos = Medico.query.count()
    total_pacientes = Paciente.query.count()
    total_citas = Cita.query.count()
    total_facturas = Factura.query.count()
    
    return render_template('admin/dashboard.html',
                         total_usuarios=total_usuarios,
                         total_medicos=total_medicos,
                         total_pacientes=total_pacientes,
                         total_citas=total_citas,
                         total_facturas=total_facturas,
                         usuario=current_user)


# ============================================
# LISTAR USUARIOS - Gestión de Usuarios
# ============================================
@bp_admin.route('/usuarios')
@login_required
def usuarios():
    """Lista todos los usuarios del sistema con búsqueda"""
    if not current_user.is_admin():
        flash('⛔ Acceso denegado.', 'danger')
        return redirect(url_for('core.landing'))
    
    # Obtener término de búsqueda
    search = request.args.get('search', '').strip()
    
    # Construir consulta base
    query = Usuario.query
    
    # Aplicar búsqueda si hay término
    if search:
        search_terms = search.split()
        conditions = []
        
        # Buscar por ID
        if search.isdigit():
            conditions.append(Usuario.id == int(search))
        
        # Buscar por nombre completo o parcial
        for term in search_terms:
            conditions.append(Usuario.nombres.ilike(f'%{term}%'))
            conditions.append(Usuario.apellidos.ilike(f'%{term}%'))
        
        # Buscar por nombre completo (concatenado)
        conditions.append(db.func.concat(Usuario.nombres, ' ', Usuario.apellidos).ilike(f'%{search}%'))
        conditions.append(db.func.concat(Usuario.nombres, Usuario.apellidos).ilike(f'%{search}%'))
        
        # Buscar por username
        conditions.append(Usuario.username.ilike(f'%{search}%'))
        
        # Buscar por email
        conditions.append(Usuario.email.ilike(f'%{search}%'))
        
        # Buscar por rol
        conditions.append(Usuario.rol.ilike(f'%{search}%'))
        
        # Aplicar todas las condiciones con OR
        query = query.filter(db.or_(*conditions))
    
    # Ordenar por fecha de registro (más reciente primero)
    usuarios = query.order_by(Usuario.fecha_registro.desc()).all()
    
    return render_template('admin/usuarios.html', usuarios=usuarios, search=search)


# ============================================
# CREAR USUARIO - Desde el Panel Admin
# ============================================
@bp_admin.route('/usuarios/crear', methods=['GET', 'POST'])
@login_required
def crear_usuario():
    """Crear un nuevo usuario desde el panel de administración"""
    if not current_user.is_admin():
        flash('⛔ Acceso denegado.', 'danger')
        return redirect(url_for('core.landing'))
    
    if request.method == 'POST':
        nombres = request.form.get('nombres')
        apellidos = request.form.get('apellidos')
        email = request.form.get('email')
        rol = request.form.get('rol')
        password = request.form.get('password')
        
        # Validar contraseña segura
        valida, mensaje = validar_contraseña(password)
        if not valida:
            flash(f'❌ {mensaje}', 'danger')
            username_sugerido = generar_username(rol)
            return render_template('admin/crear_usuario.html', username_sugerido=username_sugerido)
        
        username = generar_username(rol)
        
        # Validar email único
        if Usuario.query.filter_by(email=email).first():
            flash('❌ El email ya está registrado.', 'danger')
            username_sugerido = generar_username(rol)
            return render_template('admin/crear_usuario.html', username_sugerido=username_sugerido)
        
        # Crear nuevo usuario
        usuario = Usuario(
            username=username,
            email=email,
            nombres=nombres,
            apellidos=apellidos,
            rol=rol
        )
        usuario.set_password(password)
        
        db.session.add(usuario)
        db.session.commit()
        
        # Si el rol es PACIENTE, crear perfil automáticamente
        if rol == 'paciente':
            paciente = Paciente(
                usuario_id=usuario.id,
                ci=f"CI-{usuario.id}",  
                nombres=nombres,
                apellidos=apellidos,
                email=email,
                telefono='',
                direccion='',
                seguro_medico='',
                alergias=''
            )
            db.session.add(paciente)
            db.session.commit()
            flash(f'✅ Usuario {username} y su perfil de paciente creados exitosamente.', 'success')
        else:
            flash(f'✅ Usuario {username} creado exitosamente.', 'success')
        
        return redirect(url_for('admin.usuarios'))
    
    username_sugerido = generar_username('paciente')
    return render_template('admin/crear_usuario.html', username_sugerido=username_sugerido)


# ============================================
# EDITAR USUARIO - Modificar datos de usuario
# ============================================
@bp_admin.route('/usuarios/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_usuario(id):
    """Editar un usuario existente"""
    if not current_user.is_admin():
        flash('⛔ Acceso denegado.', 'danger')
        return redirect(url_for('core.landing'))
    
    usuario = Usuario.query.get_or_404(id)
    
    if usuario.id == current_user.id:
        flash('⚠️ No puedes editar tu propio usuario desde aquí.', 'warning')
        return redirect(url_for('admin.usuarios'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        nombres = request.form.get('nombres')
        apellidos = request.form.get('apellidos')
        rol = request.form.get('rol')
        nueva_password = request.form.get('password')
        
        # Validar username único
        if username != usuario.username:
            existe = Usuario.query.filter_by(username=username).first()
            if existe:
                flash('❌ El nombre de usuario ya está registrado.', 'danger')
                return render_template('admin/editar_usuario.html', usuario=usuario)
        
        # Validar email único
        if email != usuario.email:
            existe = Usuario.query.filter_by(email=email).first()
            if existe:
                flash('❌ El email ya está registrado.', 'danger')
                return render_template('admin/editar_usuario.html', usuario=usuario)
        
        # Si se proporcionó nueva contraseña, validarla
        if nueva_password:
            valida, mensaje = validar_contraseña(nueva_password)
            if not valida:
                flash(f'❌ {mensaje}', 'danger')
                return render_template('admin/editar_usuario.html', usuario=usuario)
            usuario.set_password(nueva_password)
        
        usuario.username = username
        usuario.email = email
        usuario.nombres = nombres
        usuario.apellidos = apellidos
        usuario.rol = rol
        
        db.session.commit()
        flash(f'✅ Usuario {username} actualizado exitosamente.', 'success')
        return redirect(url_for('admin.usuarios'))
    
    return render_template('admin/editar_usuario.html', usuario=usuario)


# ============================================
# VER PERFIL DE USUARIO
# ============================================
@bp_admin.route('/usuarios/perfil/<int:id>')
@login_required
def perfil_usuario(id):
    """Ver perfil de un usuario específico"""
    if not current_user.is_admin():
        flash('⛔ Acceso denegado.', 'danger')
        return redirect(url_for('core.landing'))
    
    usuario = Usuario.query.get_or_404(id)
    return render_template('admin/perfil_usuario.html', usuario=usuario)


# ============================================
# ELIMINAR USUARIO - Eliminar usuario del sistema
# ============================================
@bp_admin.route('/usuarios/eliminar/<int:id>', methods=['POST'])
@login_required
def eliminar_usuario(id):
    """Eliminar un usuario del sistema"""
    if not current_user.is_admin():
        flash('⛔ Acceso denegado.', 'danger')
        return redirect(url_for('core.landing'))
    
    usuario = Usuario.query.get_or_404(id)
    
    if usuario.id == current_user.id:
        flash('⚠️ No puedes eliminar tu propio usuario.', 'warning')
        return redirect(url_for('admin.usuarios'))
    
    db.session.delete(usuario)
    db.session.commit()
    
    flash(f'✅ Usuario {usuario.username} eliminado exitosamente.', 'success')
    return redirect(url_for('admin.usuarios'))


# ============================================
# CAMBIAR ESTADO DE USUARIO - Activar/Desactivar
# ============================================
@bp_admin.route('/usuarios/toggle/<int:id>')
@login_required
def toggle_usuario(id):
    """Activar o desactivar un usuario"""
    if not current_user.is_admin():
        flash('⛔ Acceso denegado.', 'danger')
        return redirect(url_for('core.landing'))
    
    usuario = Usuario.query.get_or_404(id)
    
    if usuario.id == current_user.id:
        flash('⚠️ No puedes desactivar tu propio usuario.', 'warning')
        return redirect(url_for('admin.usuarios'))
    
    usuario.activo = not usuario.activo
    db.session.commit()
    
    estado = "activado" if usuario.activo else "desactivado"
    flash(f'✅ Usuario {usuario.username} {estado} correctamente.', 'success')
    return redirect(url_for('admin.usuarios'))


# ============================================
# ESTADÍSTICAS AVANZADAS
# ============================================
@bp_admin.route('/estadisticas')
@login_required
def estadisticas():
    """Página de estadísticas detalladas (Solo Admin)"""
    if not current_user.is_admin():
        flash('⛔ Acceso denegado.', 'danger')
        return redirect(url_for('core.landing'))
    
    # ========== ESTADÍSTICAS GENERALES ==========
    total_pacientes = Paciente.query.count()
    total_medicos = Medico.query.count()
    total_citas = Cita.query.count()
    total_facturas = Factura.query.count()
    
    total_ingresos = db.session.query(
        db.func.sum(Factura.monto_total)
    ).filter(Factura.estado_pago == 'pagado').scalar() or 0
    
    # ========== CITAS POR ESTADO ==========
    citas_pendientes = Cita.query.filter_by(estado='pendiente').count()
    citas_confirmadas = Cita.query.filter_by(estado='confirmada').count()
    citas_completadas = Cita.query.filter_by(estado='completada').count()
    citas_canceladas = Cita.query.filter_by(estado='cancelada').count()
    
    # ========== CITAS POR MES ==========
    hoy = datetime.now()
    meses = []
    citas_por_mes = []
    
    for i in range(5, -1, -1):
        mes_actual = hoy - timedelta(days=30 * i)
        nombre_mes = mes_actual.strftime('%B')
        año = mes_actual.strftime('%Y')
        meses.append(f"{nombre_mes[:3]} {año}")
        
        inicio_mes = mes_actual.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        if mes_actual.month == 12:
            fin_mes = mes_actual.replace(year=mes_actual.year + 1, month=1, day=1)
        else:
            fin_mes = mes_actual.replace(month=mes_actual.month + 1, day=1)
        
        count = Cita.query.filter(
            Cita.fecha_hora >= inicio_mes,
            Cita.fecha_hora < fin_mes
        ).count()
        
        citas_por_mes.append(count)
    
    # ========== INGRESOS POR MES ==========
    ingresos_por_mes = []
    
    for i in range(5, -1, -1):
        mes_actual = hoy - timedelta(days=30 * i)
        
        inicio_mes = mes_actual.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        if mes_actual.month == 12:
            fin_mes = mes_actual.replace(year=mes_actual.year + 1, month=1, day=1)
        else:
            fin_mes = mes_actual.replace(month=mes_actual.month + 1, day=1)
        
        total = db.session.query(
            db.func.sum(Factura.monto_total)
        ).filter(
            Factura.fecha_emision >= inicio_mes,
            Factura.fecha_emision < fin_mes,
            Factura.estado_pago == 'pagado'
        ).scalar() or 0
        
        ingresos_por_mes.append(float(total))
    
    # ========== MÉDICOS MÁS SOLICITADOS ==========
    medicos_top = (
        db.session.query(
            Medico.id,
            Medico.nombre,
            Medico.apellidos,
            db.func.count(Cita.id).label('total_citas')
        )
        .join(Cita, Cita.medico_id == Medico.id)
        .group_by(Medico.id)
        .order_by(db.func.count(Cita.id).desc())
        .limit(5)
        .all()
    )
    
    # ========== ESPECIALIDADES MÁS DEMANDADAS ==========
    especialidades_top = (
        db.session.query(
            Especialidad.id,
            Especialidad.nombre,
            db.func.count(Cita.id).label('total_citas')
        )
        .join(Medico, Medico.especialidad_id == Especialidad.id)
        .join(Cita, Cita.medico_id == Medico.id)
        .group_by(Especialidad.id)
        .order_by(db.func.count(Cita.id).desc())
        .limit(5)
        .all()
    )
    
    # ========== PACIENTES RECIENTES ==========
    pacientes_recientes = Paciente.query.order_by(Paciente.id.desc()).limit(10).all()
    
    # ========== CITAS DE HOY ==========
    hoy_inicio = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    hoy_fin = datetime.now().replace(hour=23, minute=59, second=59, microsecond=999999)
    
    citas_hoy = Cita.query.filter(
        Cita.fecha_hora >= hoy_inicio,
        Cita.fecha_hora <= hoy_fin
    ).count()
    
    return render_template('admin/estadisticas.html',
                         total_pacientes=total_pacientes,
                         total_medicos=total_medicos,
                         total_citas=total_citas,
                         total_facturas=total_facturas,
                         total_ingresos=total_ingresos,
                         citas_pendientes=citas_pendientes,
                         citas_confirmadas=citas_confirmadas,
                         citas_completadas=citas_completadas,
                         citas_canceladas=citas_canceladas,
                         citas_por_mes=citas_por_mes,
                         meses=meses,
                         ingresos_por_mes=ingresos_por_mes,
                         medicos_top=medicos_top,
                         especialidades_top=especialidades_top,
                         pacientes_recientes=pacientes_recientes,
                         citas_hoy=citas_hoy,
                         usuario=current_user)
    
# ============================================
# GESTIÓN DE SALAS
# ============================================

@bp_admin.route('/salas')
@login_required
def salas():
    """Lista todas las salas con búsqueda"""
    if not current_user.is_admin():
        flash('⛔ Acceso denegado.', 'danger')
        return redirect(url_for('core.landing'))
    
    search = request.args.get('search', '').strip()
    query = Sala.query
    
    if search:
        search_terms = search.split()
        conditions = []
        
        if search.isdigit():
            conditions.append(Sala.id == int(search))
        
        for term in search_terms:
            conditions.append(Sala.numero.ilike(f'%{term}%'))
            conditions.append(Sala.nombre.ilike(f'%{term}%'))
            conditions.append(Sala.ubicacion.ilike(f'%{term}%'))
            conditions.append(Sala.estado.ilike(f'%{term}%'))
        
        if conditions:
            query = query.filter(db.or_(*conditions))
    
    salas = query.order_by(Sala.id.asc()).all()
    return render_template('admin/salas.html', salas=salas, search=search)


@bp_admin.route('/salas/crear', methods=['GET', 'POST'])
@login_required
def crear_sala():
    """Crear una nueva sala"""
    if not current_user.is_admin():
        flash('⛔ Acceso denegado.', 'danger')
        return redirect(url_for('core.landing'))
    
    if request.method == 'POST':
        numero = request.form.get('numero')
        nombre = request.form.get('nombre')
        ubicacion = request.form.get('ubicacion')
        capacidad = request.form.get('capacidad', 1)
        estado = request.form.get('estado', 'disponible')
        
        if Sala.query.filter_by(numero=numero).first():
            flash('❌ El número de sala ya está registrado.', 'danger')
            return render_template('admin/crear_sala.html')
        
        sala = Sala(
            numero=numero,
            nombre=nombre,
            ubicacion=ubicacion,
            capacidad=capacidad,
            estado=estado
        )
        db.session.add(sala)
        db.session.commit()
        
        flash(f'✅ Sala {numero} creada exitosamente.', 'success')
        return redirect(url_for('admin.salas'))
    
    return render_template('admin/crear_sala.html')


@bp_admin.route('/salas/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_sala(id):
    """Editar una sala"""
    if not current_user.is_admin():
        flash('⛔ Acceso denegado.', 'danger')
        return redirect(url_for('core.landing'))
    
    sala = Sala.query.get_or_404(id)
    
    if request.method == 'POST':
        numero = request.form.get('numero')
        nombre = request.form.get('nombre')
        ubicacion = request.form.get('ubicacion')
        capacidad = request.form.get('capacidad', 1)
        estado = request.form.get('estado', 'disponible')
        
        if numero != sala.numero and Sala.query.filter_by(numero=numero).first():
            flash('❌ El número de sala ya está registrado.', 'danger')
            return render_template('admin/editar_sala.html', sala=sala)
        
        sala.numero = numero
        sala.nombre = nombre
        sala.ubicacion = ubicacion
        sala.capacidad = capacidad
        sala.estado = estado
        
        db.session.commit()
        flash(f'✅ Sala {numero} actualizada exitosamente.', 'success')
        return redirect(url_for('admin.salas'))
    
    return render_template('admin/editar_sala.html', sala=sala)


@bp_admin.route('/salas/eliminar/<int:id>', methods=['POST'])
@login_required
def eliminar_sala(id):
    """Eliminar una sala"""
    if not current_user.is_admin():
        flash('⛔ Acceso denegado.', 'danger')
        return redirect(url_for('core.landing'))
    
    sala = Sala.query.get_or_404(id)
    
    if sala.citas:
        flash('⚠️ No se puede eliminar la sala porque tiene citas asociadas.', 'warning')
        return redirect(url_for('admin.salas'))
    
    numero = sala.numero
    db.session.delete(sala)
    db.session.commit()
    
    flash(f'✅ Sala {numero} eliminada exitosamente.', 'success')
    return redirect(url_for('admin.salas'))



# ============================================
# GESTIÓN DE RECETAS
# ============================================

@bp_admin.route('/recetas')
@login_required
def recetas():
    """Lista todas las recetas"""
    if not current_user.is_admin():
        flash('⛔ Acceso denegado.', 'danger')
        return redirect(url_for('core.landing'))
    
    search = request.args.get('search', '').strip()
    query = Receta.query
    
    if search:
        conditions = []
        search_terms = search.split()
        
        if search.isdigit():
            conditions.append(Receta.id == int(search))
        
        for term in search_terms:
            conditions.append(Receta.medicamento.ilike(f'%{term}%'))
            conditions.append(Receta.historial.has(HistorialClinico.paciente.has(Paciente.nombres.ilike(f'%{term}%'))))
            conditions.append(Receta.historial.has(HistorialClinico.paciente.has(Paciente.apellidos.ilike(f'%{term}%'))))
        
        if conditions:
            query = query.filter(db.or_(*conditions))
    
    recetas = query.order_by(Receta.fecha_emision.desc()).all()
    return render_template('admin/recetas.html', recetas=recetas, search=search)


@bp_admin.route('/recetas/ver/<int:id>')
@login_required
def ver_receta(id):
    """Ver detalle de una receta"""
    if not current_user.is_admin():
        flash('⛔ Acceso denegado.', 'danger')
        return redirect(url_for('core.landing'))
    
    receta = Receta.query.get_or_404(id)
    return render_template('admin/ver_receta.html', receta=receta)


@bp_admin.route('/recetas/eliminar/<int:id>', methods=['POST'])
@login_required
def eliminar_receta(id):
    """Eliminar una receta"""
    if not current_user.is_admin():
        flash('⛔ Acceso denegado.', 'danger')
        return redirect(url_for('core.landing'))
    
    receta = Receta.query.get_or_404(id)
    medicamento = receta.medicamento
    
    db.session.delete(receta)
    db.session.commit()
    
    flash(f'✅ Receta de {medicamento} eliminada exitosamente.', 'success')
    return redirect(url_for('admin.recetas'))