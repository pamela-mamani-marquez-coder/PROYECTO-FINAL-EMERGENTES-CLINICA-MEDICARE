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
    
    
    
@bp_core.route('/ver-db')
@login_required
def ver_db():
    """Ver el contenido de la base de datos (solo admin)"""
    if not current_user.is_admin():
        flash('⛔ Acceso denegado.', 'danger')
        return redirect(url_for('core.landing'))
    
    import sqlite3
    import os
    
    # Buscar la base de datos en diferentes ubicaciones posibles
    posibles_rutas = [
        'instance/medicare.db',
        os.path.join(os.path.dirname(os.path.dirname(__file__)), 'instance', 'medicare.db'),
        '/opt/render/project/src/instance/medicare.db'
    ]
    
    db_path = None
    for ruta in posibles_rutas:
        if os.path.exists(ruta):
            db_path = ruta
            break
    
    if not db_path:
        return "❌ Base de datos no encontrada en ninguna ubicación"
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Obtener todas las tablas
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [row[0] for row in cursor.fetchall() if not row[0].startswith('sqlite_')]
    
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Base de Datos</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
            .container { max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            h1 { color: #0d1b3e; }
            h2 { color: #2563eb; margin-top: 30px; border-bottom: 2px solid #e5e7eb; padding-bottom: 10px; }
            table { width: 100%; border-collapse: collapse; margin: 10px 0; }
            th { background: #0d1b3e; color: white; padding: 8px; text-align: left; }
            td { padding: 8px; border-bottom: 1px solid #e5e7eb; }
            tr:hover { background: #f0f4ff; }
            .badge { display: inline-block; background: #2563eb; color: white; padding: 2px 10px; border-radius: 20px; font-size: 14px; }
            .ruta { background: #e5e7eb; padding: 10px; border-radius: 5px; font-family: monospace; }
            .info { background: #dbeafe; padding: 10px; border-radius: 5px; margin: 10px 0; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📊 Base de Datos</h1>
            <div class="info">
                <strong>📍 Ruta:</strong> <span class="ruta">{db_path}</span>
            </div>
            <div class="info">
                <strong>📦 Tamaño:</strong> {tamano:.2f} KB
            </div>
    """
    
    html = html.format(db_path=db_path, tamano=os.path.getsize(db_path) / 1024)
    
    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        html += f'<h2>📋 {table} <span class="badge">{count} registros</span></h2>'
        
        cursor.execute(f"SELECT * FROM {table} LIMIT 20")
        columns = [description[0] for description in cursor.description]
        rows = cursor.fetchall()
        
        if rows:
            html += "<table>"
            html += "<tr>" + "".join(f"<th>{col}</th>" for col in columns) + "</tr>"
            for row in rows:
                html += "<tr>" + "".join(f"<td>{cell if cell is not None else ''}</td>" for cell in row) + "</tr>"
            html += "</table>"
        else:
            html += "<p><em>Tabla vacía</em></p>"
    
    html += """
        </div>
    </body>
    </html>
    """
    
    conn.close()
    return html