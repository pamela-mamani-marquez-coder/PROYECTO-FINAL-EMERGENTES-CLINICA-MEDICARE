from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app.auth import bp_auth
from app import db
from app.models.usuario import Usuario
from app.models.paciente import Paciente
from app.models.medico import Medico
from datetime import datetime
import re

# ============================================
# FUNCIÓN PARA GENERAR USERNAME DE PACIENTE
# ============================================
def generar_username_paciente():
    """Genera un username automático para pacientes nuevos"""
    prefijo = 'paciente'
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
# FUNCIÓN PARA VALIDAR CONTRASEÑA
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
# REGISTRO DE USUARIOS (SOLO PACIENTES)
# ============================================
@bp_auth.route('/register', methods=['GET', 'POST'])
def register():
    """Página de registro de nuevos pacientes"""
    if current_user.is_authenticated:
        return redirect(url_for('core.landing'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        nombres = request.form.get('nombres')
        apellidos = request.form.get('apellidos')
        password = request.form.get('password')
        
        # Rol fijo: PACIENTE
        rol = 'paciente'
        
        # Validar contraseña
        valida, mensaje = validar_contraseña(password)
        if not valida:
            flash(f'❌ {mensaje}', 'danger')
            return render_template('auth/register.html')
        
        # Validar email único
        if Usuario.query.filter_by(email=email).first():
            flash('❌ El email ya está registrado.', 'danger')
            return render_template('auth/register.html')
        
        # Generar username automático
        username = generar_username_paciente()
        
        # Crear usuario
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
        
        # Crear perfil de paciente
        paciente = Paciente(
            usuario_id=usuario.id,
            ci=f"CI-{usuario.id}",
            nombres=nombres,
            apellidos=apellidos,
            email=email,
            fecha_registro=datetime.now()
        )
        db.session.add(paciente)
        db.session.commit()
        
        # Mensaje con el username generado
        flash(f'✅ ¡Cuenta creada exitosamente! Tu usuario es: <strong>{username}</strong>', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/register.html')


# ============================================
# LOGIN
# ============================================
@bp_auth.route('/login', methods=['GET', 'POST'])
def login():
    """Página de inicio de sesión"""
    if current_user.is_authenticated:
        if current_user.is_admin():
            return redirect(url_for('admin.dashboard'))
        elif current_user.is_medico():
            return redirect(url_for('medico.dashboard'))
        elif current_user.is_recepcionista():
            return redirect(url_for('recepcionista.dashboard'))
        else:
            return redirect(url_for('paciente.dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        usuario = Usuario.query.filter_by(username=username).first()
        
        if usuario and usuario.check_password(password):
            login_user(usuario)
            flash(f'¡Bienvenido, {usuario.nombres}!', 'success')
            
            if usuario.is_admin():
                return redirect(url_for('admin.dashboard'))
            elif usuario.is_medico():
                return redirect(url_for('medico.dashboard'))
            elif usuario.is_recepcionista():
                return redirect(url_for('recepcionista.dashboard'))
            else:
                return redirect(url_for('paciente.dashboard'))
        else:
            flash('❌ Usuario o contraseña incorrectos.', 'danger')
    
    return render_template('auth/login.html')


# ============================================
# LOGOUT
# ============================================
@bp_auth.route('/logout')
@login_required
def logout():
    """Cerrar sesión del usuario actual"""
    logout_user()
    flash('👋 Has cerrado sesión correctamente.', 'info')
    return redirect(url_for('core.landing'))


# ============================================
# PERFIL
# ============================================
@bp_auth.route('/perfil')
@login_required
def perfil():
    """Página de perfil del usuario actual"""
    return render_template('auth/perfil.html', usuario=current_user)


# ============================================
# EDITAR PERFIL
# ============================================
@bp_auth.route('/perfil/editar', methods=['GET', 'POST'])
@login_required
def editar_perfil():
    """Editar información del perfil del usuario"""
    if request.method == 'POST':
        nombres = request.form.get('nombres')
        apellidos = request.form.get('apellidos')
        email = request.form.get('email')
        
        # Validar email único
        if email != current_user.email:
            existe = Usuario.query.filter_by(email=email).first()
            if existe:
                flash('❌ El email ya está registrado por otro usuario.', 'danger')
                return render_template('auth/editar_perfil.html', usuario=current_user)
        
        current_user.nombres = nombres
        current_user.apellidos = apellidos
        current_user.email = email
        
        db.session.commit()
        flash('✅ Perfil actualizado exitosamente.', 'success')
        return redirect(url_for('auth.perfil'))
    
    return render_template('auth/editar_perfil.html', usuario=current_user)


# ============================================
# CAMBIAR CONTRASEÑA
# ============================================
@bp_auth.route('/cambiar_password', methods=['GET', 'POST'])
@login_required
def cambiar_password():
    """Cambiar la contraseña del usuario"""
    if request.method == 'POST':
        password_actual = request.form.get('password_actual')
        password_nuevo = request.form.get('password_nuevo')
        password_confirmar = request.form.get('password_confirmar')
        
        # Verificar contraseña actual
        if not current_user.check_password(password_actual):
            flash('❌ La contraseña actual es incorrecta.', 'danger')
            return render_template('auth/cambiar_password.html')
        
        # Verificar que las nuevas contraseñas coincidan
        if password_nuevo != password_confirmar:
            flash('❌ Las contraseñas no coinciden.', 'danger')
            return render_template('auth/cambiar_password.html')
        
        # Validar nueva contraseña
        valida, mensaje = validar_contraseña(password_nuevo)
        if not valida:
            flash(f'❌ {mensaje}', 'danger')
            return render_template('auth/cambiar_password.html')
        
        # Actualizar contraseña
        current_user.set_password(password_nuevo)
        db.session.commit()
        
        flash('✅ Contraseña actualizada exitosamente.', 'success')
        return redirect(url_for('auth.perfil'))
    
    return render_template('auth/cambiar_password.html')