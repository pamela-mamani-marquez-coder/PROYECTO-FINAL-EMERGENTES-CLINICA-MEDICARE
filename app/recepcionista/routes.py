from flask import render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from app.recepcionista import bp_recepcionista
from app import db
from app.models.cita import Cita
from app.models.paciente import Paciente
from app.models.medico import Medico
from app.models.factura import Factura
from app.models.historial import HistorialClinico
from datetime import datetime

# ============================================
# DASHBOARD DEL RECEPCIONISTA
# ============================================
@bp_recepcionista.route('/dashboard')
@login_required
def dashboard():
    """Dashboard del recepcionista"""
    if not current_user.is_recepcionista():
        flash('⛔ Acceso denegado.', 'danger')
        return redirect(url_for('core.landing'))
    
    # Estadísticas básicas
    total_pacientes = Paciente.query.count()
    total_citas_hoy = Cita.query.filter(
        db.func.date(Cita.fecha_hora) == datetime.now().date()
    ).count()
    citas_pendientes = Cita.query.filter_by(estado='pendiente').count()
    
    # Próximas citas
    proximas_citas = Cita.query.filter(
        Cita.fecha_hora >= datetime.now()
    ).order_by(Cita.fecha_hora.asc()).limit(5).all()
    
    return render_template('recepcionista/dashboard.html',
                         total_pacientes=total_pacientes,
                         total_citas_hoy=total_citas_hoy,
                         citas_pendientes=citas_pendientes,
                         proximas_citas=proximas_citas,
                         usuario=current_user)


# ============================================
# VER CITAS (REDIRIGE AL MÓDULO DE CITAS)
# ============================================
@bp_recepcionista.route('/citas')
@login_required
def citas():
    """Redirige al módulo de citas"""
    if not current_user.is_recepcionista():
        flash('⛔ Acceso denegado.', 'danger')
        return redirect(url_for('core.landing'))
    return redirect(url_for('cita.index'))


# ============================================
# VER PACIENTES (REDIRIGE AL MÓDULO DE PACIENTES)
# ============================================
@bp_recepcionista.route('/pacientes')
@login_required
def pacientes():
    """Redirige al módulo de pacientes"""
    if not current_user.is_recepcionista():
        flash('⛔ Acceso denegado.', 'danger')
        return redirect(url_for('core.landing'))
    return redirect(url_for('paciente.index'))


# ============================================
# VER FACTURACIÓN (REDIRIGE AL MÓDULO DE FACTURACIÓN)
# ============================================
@bp_recepcionista.route('/facturacion')
@login_required
def facturacion():
    """Redirige al módulo de facturación"""
    if not current_user.is_recepcionista():
        flash('⛔ Acceso denegado.', 'danger')
        return redirect(url_for('core.landing'))
    return redirect(url_for('factura.index'))