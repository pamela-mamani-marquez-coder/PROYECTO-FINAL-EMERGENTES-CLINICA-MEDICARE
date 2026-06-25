from flask import render_template, redirect, url_for, flash, request, session
from flask_login import login_required, current_user
from app.core import bp_core
from app import db
from app.models.usuario import Usuario

# ============================================
# PÁGINA DE INICIO (LANDING PAGE)
# ============================================
@bp_core.route('/', methods=['GET', 'POST'])
def landing():
    """
    Página principal del sistema.
    - GET: Muestra la landing page
    - POST: Redirige a login (por si alguien envía un formulario aquí)
    """
    # Si es POST, redirigir a login (evita el error 405)
    if request.method == 'POST':
        flash('Por favor, inicia sesión desde el formulario de login.', 'info')
        return redirect(url_for('auth.login'))
    
    # Si el usuario ya está autenticado, redirigir según su rol
    if current_user.is_authenticated:
        return redirect(redirect_segun_rol(current_user))
    
    return render_template('core/landing.html')


# ============================================
# DASHBOARD GENERAL (REDIRECCIONA SEGÚN ROL)
# ============================================

@bp_core.route('/dashboard')
@login_required
def dashboard():
    """Dashboard general según el rol del usuario"""
    if current_user.is_admin():
        return redirect(url_for('admin.dashboard'))
    elif current_user.is_medico():
        return redirect(url_for('medico.dashboard'))
    elif current_user.is_recepcionista():
        return redirect(url_for('recepcionista.dashboard'))  # ✅ RECEPCIONISTA A SU DASHBOARD
    else:  # paciente
        return redirect(url_for('paciente.dashboard'))

# ============================================
# PÁGINA DE ACERCA DE / QUIENES SOMOS
# ============================================
@bp_core.route('/about')
def about():
    """Página de información del sistema"""
    return render_template('core/about.html')


# ============================================
# PÁGINA DE SERVICIOS
# ============================================
@bp_core.route('/servicios')
def servicios():
    """Página de servicios ofrecidos por la clínica"""
    return render_template('core/servicios.html')


# ============================================
# PÁGINA DE CONTACTO
# ============================================
@bp_core.route('/contacto', methods=['GET', 'POST'])
def contacto():
    """
    Página de contacto con formulario
    - GET: Muestra el formulario
    - POST: Procesa el mensaje (simulado por ahora)
    """
    if request.method == 'POST':
        nombre = request.form.get('nombre')
        email = request.form.get('email')
        mensaje = request.form.get('mensaje')
        
        flash(f'✅ ¡Gracias por tu mensaje, {nombre}! Te contactaremos pronto.', 'success')
        return redirect(url_for('core.contacto'))
    
    return render_template('core/contacto.html')


# ============================================
# ERROR 404 - PÁGINA NO ENCONTRADA
# ============================================
@bp_core.app_errorhandler(404)
def page_not_found(error):
    """Página de error 404 personalizada"""
    return render_template('core/404.html'), 404


# ============================================
# ERROR 403 - ACCESO DENEGADO
# ============================================
@bp_core.app_errorhandler(403)
def forbidden(error):
    """Página de error 403 personalizada"""
    flash('⛔ No tienes permisos para acceder a esta página.', 'danger')
    return render_template('core/403.html'), 403


# ============================================
# ERROR 500 - ERROR INTERNO DEL SERVIDOR
# ============================================
@bp_core.app_errorhandler(500)
def server_error(error):
    """Página de error 500 personalizada"""
    flash('❌ Ha ocurrido un error interno en el servidor.', 'danger')
    return render_template('core/500.html'), 500


# ============================================
# FUNCIÓN AUXILIAR: Redirección por Rol
# ============================================
def redirect_segun_rol(usuario):
    """
    Redirige al usuario según su rol.
    Esta función es compartida entre auth y core.
    """
    if usuario.is_admin():
        return url_for('admin.dashboard')
    elif usuario.is_medico():
        return url_for('medico.dashboard')
    elif usuario.is_recepcionista():
        return url_for('cita.index')
    else:  # paciente
        return url_for('paciente.dashboard')