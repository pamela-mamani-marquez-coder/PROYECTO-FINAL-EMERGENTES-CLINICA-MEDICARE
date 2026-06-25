from functools import wraps
from flask import flash, redirect, url_for, abort
from flask_login import current_user

def login_required_roles(*roles):
    """Decorador para restringir acceso por roles"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Debes iniciar sesión.', 'warning')
                return redirect(url_for('auth.login'))
            
            if current_user.rol not in roles and 'admin' not in roles:
                flash('No tienes permisos.', 'danger')
                abort(403)
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def admin_required(f):
    return login_required_roles('admin')(f)

def medico_required(f):
    return login_required_roles('admin', 'medico')(f)

def recepcionista_required(f):
    return login_required_roles('admin', 'recepcionista')(f)

def paciente_required(f):
    return login_required_roles('admin', 'medico', 'paciente')(f)