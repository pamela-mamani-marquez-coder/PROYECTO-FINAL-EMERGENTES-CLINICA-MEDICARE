from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.facturacion import bp_factura
from app import db
from app.models.factura import Factura
from app.models.cita import Cita
from datetime import datetime
from app.models.paciente import Paciente
from app.models.medico import Medico

# ============================================
# LISTAR FACTURAS
# ============================================
@bp_factura.route('/')
@login_required
def index():
    """Lista todas las facturas"""
    if not (current_user.is_admin() or current_user.is_recepcionista()):
        flash('⛔ No tienes permisos.', 'danger')
        return redirect(url_for('core.landing'))
    
    facturas = Factura.query.order_by(Factura.fecha_emision.desc()).all()
    return render_template('facturacion/index.html', facturas=facturas)


# ============================================
# SELECCIONAR CITA PARA FACTURAR
# ============================================
@bp_factura.route('/seleccionar')
@login_required
def seleccionar():
    """Muestra las citas completadas para seleccionar una y facturar"""
    if not (current_user.is_admin() or current_user.is_recepcionista()):
        flash('⛔ No tienes permisos.', 'danger')
        return redirect(url_for('core.landing'))
    
    # Obtener citas completadas
    citas_completadas = Cita.query.filter_by(estado='completada').all()
    
    # Filtrar las que NO tienen factura
    citas_sin_factura = []
    for cita in citas_completadas:
        if not Factura.query.filter_by(cita_id=cita.id).first():
            citas_sin_factura.append(cita)
    
    return render_template('facturacion/seleccionar.html', citas=citas_sin_factura)


# ============================================
# CREAR FACTURA DESDE CITA SELECCIONADA
# ============================================
@bp_factura.route('/crear/<int:cita_id>', methods=['GET', 'POST'])
@login_required
def crear(cita_id):
    """Generar una factura para una cita completada"""
    if not (current_user.is_admin() or current_user.is_recepcionista()):
        flash('⛔ No tienes permisos.', 'danger')
        return redirect(url_for('core.landing'))
    
    cita = Cita.query.get_or_404(cita_id)
    
    # Validar que la cita esté completada
    if cita.estado != 'completada':
        flash('⚠️ Solo se pueden facturar citas completadas.', 'warning')
        return redirect(url_for('cita.index'))
    
    # Verificar si ya existe factura
    if Factura.query.filter_by(cita_id=cita_id).first():
        flash('⚠️ Esta cita ya tiene una factura generada.', 'info')
        return redirect(url_for('factura.index'))
    
    if request.method == 'POST':
        monto_total = request.form.get('monto_total')
        metodo_pago = request.form.get('metodo_pago')
        estado_pago = request.form.get('estado_pago', 'pendiente')
        
        # Generar número de factura
        ultima_factura = Factura.query.order_by(Factura.id.desc()).first()
        if ultima_factura:
            try:
                num = int(ultima_factura.numero_factura.split('-')[1]) + 1
            except:
                num = Factura.query.count() + 1
        else:
            num = 1
        numero_factura = f'FAC-{str(num).zfill(6)}'
        
        factura = Factura(
            cita_id=cita_id,
            numero_factura=numero_factura,
            monto_total=monto_total,
            metodo_pago=metodo_pago,
            estado_pago=estado_pago,
            fecha_emision=datetime.now()
        )
        db.session.add(factura)
        db.session.commit()
        
        flash(f'✅ Factura {numero_factura} generada exitosamente.', 'success')
        return redirect(url_for('factura.index'))
    
    return render_template('facturacion/crear.html', cita=cita)


# ============================================
# PAGAR FACTURA
# ============================================
@bp_factura.route('/pagar/<int:id>', methods=['POST'])
@login_required
def pagar(id):
    """Marcar una factura como pagada"""
    if not (current_user.is_admin() or current_user.is_recepcionista()):
        flash('⛔ No tienes permisos.', 'danger')
        return redirect(url_for('core.landing'))
    
    factura = Factura.query.get_or_404(id)
    factura.estado_pago = 'pagado'
    factura.fecha_pago = datetime.now()
    db.session.commit()
    
    flash('💰 Pago registrado correctamente.', 'success')
    return redirect(url_for('factura.index'))


# ============================================
# EDITAR FACTURA
# ============================================
@bp_factura.route('/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar(id):
    """Editar una factura"""
    if not (current_user.is_admin() or current_user.is_recepcionista()):
        flash('⛔ No tienes permisos.', 'danger')
        return redirect(url_for('core.landing'))
    
    factura = Factura.query.get_or_404(id)
    
    if request.method == 'POST':
        factura.monto_total = request.form.get('monto_total')
        factura.metodo_pago = request.form.get('metodo_pago')
        factura.estado_pago = request.form.get('estado_pago')
        
        if factura.estado_pago == 'pagado' and not factura.fecha_pago:
            factura.fecha_pago = datetime.now()
        
        db.session.commit()
        flash('✅ Factura actualizada exitosamente.', 'success')
        return redirect(url_for('factura.index'))
    
    return render_template('facturacion/editar.html', factura=factura)


# ============================================
# ELIMINAR FACTURA (SOLO ADMIN)
# ============================================
@bp_factura.route('/eliminar/<int:id>', methods=['POST'])
@login_required
def eliminar(id):
    """Eliminar una factura"""
    if not current_user.is_admin():
        flash('⛔ Acceso denegado.', 'danger')
        return redirect(url_for('core.landing'))
    
    factura = Factura.query.get_or_404(id)
    numero = factura.numero_factura
    
    db.session.delete(factura)
    db.session.commit()
    
    flash(f'✅ Factura {numero} eliminada exitosamente.', 'success')
    return redirect(url_for('factura.index'))


# ============================================
# VER DETALLE DE FACTURA
# ============================================
@bp_factura.route('/<int:id>')
@login_required
def show(id):
    """Ver detalle de una factura"""
    factura = Factura.query.get_or_404(id)
    
    # ✅ PERMITIR ACCESO A:
    # - Administradores
    # - Recepcionistas
    # - Médicos (si están relacionados con la cita)
    # - Pacientes (si es su propia factura)
    
    if current_user.is_admin() or current_user.is_recepcionista():
        # Admin y recepcionistas pueden ver todas
        pass
    elif current_user.is_medico():
        # Médicos solo pueden ver facturas de sus pacientes
        medico = Medico.query.filter_by(usuario_id=current_user.id).first()
        if not medico or factura.cita.medico_id != medico.id:
            flash('⛔ No tienes permisos para ver esta factura.', 'danger')
            return redirect(url_for('core.landing'))
    elif current_user.is_paciente():
        
        # Pacientes solo pueden ver sus propias facturas
        paciente = Paciente.query.filter_by(usuario_id=current_user.id).first()
        if not paciente or factura.cita.paciente_id != paciente.id:
            flash('⛔ No tienes permisos para ver esta factura.', 'danger')
            return redirect(url_for('core.landing'))
    else:
        flash('⛔ No tienes permisos para ver esta factura.', 'danger')
        return redirect(url_for('core.landing'))
    
    return render_template('facturacion/show.html', factura=factura)

# ============================================
# IMPRIMIR FACTURA
# ============================================
@bp_factura.route('/<int:id>/imprimir')
@login_required
def imprimir(id):
    """Vista optimizada para imprimir la factura"""
    if not (current_user.is_admin() or current_user.is_recepcionista()):
        flash('⛔ No tienes permisos.', 'danger')
        return redirect(url_for('core.landing'))
    
    factura = Factura.query.get_or_404(id)
    return render_template('facturacion/imprimir.html', factura=factura)



# ============================================
# MIS FACTURAS (SOLO PARA PACIENTES)
# ============================================
@bp_factura.route('/mis-facturas')
@login_required
def mis_facturas():
    """Ver las facturas del paciente actual"""
    if not current_user.is_paciente():
        flash('⛔ Acceso denegado.', 'danger')
        return redirect(url_for('core.landing'))
    
    paciente = Paciente.query.filter_by(usuario_id=current_user.id).first()
    if not paciente:
        flash('⚠️ No tienes un perfil de paciente completo.', 'warning')
        return redirect(url_for('auth.perfil'))
    
    # Obtener todas las facturas del paciente
    facturas = Factura.query.join(Cita).filter(
        Cita.paciente_id == paciente.id
    ).order_by(Factura.fecha_emision.desc()).all()
    
    
    return render_template('facturacion/mis_facturas.html', 
                         facturas=facturas,
                         paciente=paciente)