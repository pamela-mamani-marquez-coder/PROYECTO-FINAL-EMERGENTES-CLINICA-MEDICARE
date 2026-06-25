from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.historial import bp_historial
from app import db
from app.models.historial import HistorialClinico
from app.models.receta import Receta
from app.models.cita import Cita
from app.models.paciente import Paciente
from app.models.medico import Medico
from datetime import datetime

# ============================================
# LISTAR HISTORIAL CON BUSCADOR
# ============================================
@bp_historial.route('/')
@login_required
def index():
    """Lista historiales según el rol del usuario con búsqueda"""
    search = request.args.get('search', '').strip()
    
    # Construir consulta base según rol
    if current_user.is_admin():
        query = HistorialClinico.query
    elif current_user.is_medico():
        medico = Medico.query.filter_by(usuario_id=current_user.id).first()
        if medico:
            query = HistorialClinico.query.filter_by(medico_id=medico.id)
        else:
            query = HistorialClinico.query.filter_by(medico_id=-1)
    elif current_user.is_paciente():
        paciente = Paciente.query.filter_by(usuario_id=current_user.id).first()
        if paciente:
            query = HistorialClinico.query.filter_by(paciente_id=paciente.id)
        else:
            query = HistorialClinico.query.filter_by(paciente_id=-1)
    elif current_user.is_recepcionista():
        query = HistorialClinico.query
    else:
        flash('⛔ No tienes permisos.', 'danger')
        return redirect(url_for('core.landing'))
    
    # Aplicar búsqueda
    if search:
        search_terms = search.split()
        conditions = []
        
        if search.isdigit():
            conditions.append(HistorialClinico.id == int(search))
        
        for term in search_terms:
            conditions.append(HistorialClinico.paciente.has(Paciente.nombres.ilike(f'%{term}%')))
            conditions.append(HistorialClinico.paciente.has(Paciente.apellidos.ilike(f'%{term}%')))
            conditions.append(HistorialClinico.paciente.has(Paciente.ci.ilike(f'%{term}%')))
            conditions.append(HistorialClinico.medico.has(Medico.nombre.ilike(f'%{term}%')))
            conditions.append(HistorialClinico.medico.has(Medico.apellidos.ilike(f'%{term}%')))
        
        conditions.append(HistorialClinico.diagnostico.ilike(f'%{search}%'))
        conditions.append(HistorialClinico.sintomas.ilike(f'%{search}%'))
        conditions.append(HistorialClinico.tratamiento.ilike(f'%{search}%'))
        conditions.append(HistorialClinico.observaciones.ilike(f'%{search}%'))
        
        if conditions:
            query = query.filter(db.or_(*conditions))
    
    historiales = query.order_by(HistorialClinico.fecha.desc()).all()
    
    return render_template('historial/index.html', historiales=historiales, search=search)


# ============================================
# CREAR HISTORIAL DESDE CITA COMPLETADA
# ============================================
@bp_historial.route('/crear/<int:cita_id>', methods=['GET', 'POST'])
@login_required
def crear(cita_id):
    """Crear historial clínico a partir de una cita completada"""
    if not (current_user.is_admin() or current_user.is_medico()):
        flash('⛔ No tienes permisos.', 'danger')
        return redirect(url_for('core.landing'))
    
    cita = Cita.query.get_or_404(cita_id)
    
    if cita.estado != 'completada':
        flash('⚠️ Solo se puede crear historial de citas completadas.', 'warning')
        return redirect(url_for('cita.index'))
    
    if HistorialClinico.query.filter_by(cita_id=cita_id).first():
        flash('⚠️ Esta cita ya tiene un historial registrado.', 'info')
        return redirect(url_for('cita.index'))
    
    if request.method == 'POST':
        diagnostico = request.form.get('diagnostico')
        sintomas = request.form.get('sintomas')
        tratamiento = request.form.get('tratamiento')
        observaciones = request.form.get('observaciones')
        
        historial = HistorialClinico(
            paciente_id=cita.paciente_id,
            medico_id=cita.medico_id,
            cita_id=cita.id,
            fecha=datetime.now(),
            diagnostico=diagnostico,
            sintomas=sintomas,
            tratamiento=tratamiento,
            observaciones=observaciones
        )
        db.session.add(historial)
        db.session.commit()
        
        # Procesar recetas
        medicamentos = request.form.getlist('medicamento[]')
        dosis_list = request.form.getlist('dosis[]')
        duracion_list = request.form.getlist('duracion[]')
        indicaciones_list = request.form.getlist('indicaciones[]')
        
        for i in range(len(medicamentos)):
            if medicamentos[i].strip():
                receta = Receta(
                    historial_id=historial.id,
                    medicamento=medicamentos[i],
                    dosis=dosis_list[i] if i < len(dosis_list) else '',
                    duracion=duracion_list[i] if i < len(duracion_list) else '',
                    indicaciones=indicaciones_list[i] if i < len(indicaciones_list) else '',
                    fecha_emision=datetime.now()
                )
                db.session.add(receta)
        db.session.commit()
        
        flash('✅ Historial clínico creado exitosamente.', 'success')
        return redirect(url_for('historial.show', id=historial.id))
    
    return render_template('historial/crear.html', cita=cita)


# ============================================
# VER DETALLE DE HISTORIAL
# ============================================
@bp_historial.route('/<int:id>')
@login_required
def show(id):
    """Ver detalle de un historial clínico"""
    historial = HistorialClinico.query.get_or_404(id)
    
    if current_user.is_paciente():
        paciente = Paciente.query.filter_by(usuario_id=current_user.id).first()
        if not paciente or historial.paciente_id != paciente.id:
            flash('⛔ No tienes permisos para ver este historial.', 'danger')
            return redirect(url_for('core.landing'))
    
    return render_template('historial/show.html', historial=historial)


# ============================================
# VER RECETAS DE UN HISTORIAL
# ============================================
@bp_historial.route('/<int:id>/recetas')
@login_required
def recetas(id):
    """Ver todas las recetas de un historial clínico"""
    historial = HistorialClinico.query.get_or_404(id)
    
    if current_user.is_paciente():
        paciente = Paciente.query.filter_by(usuario_id=current_user.id).first()
        if not paciente or historial.paciente_id != paciente.id:
            flash('⛔ No tienes permisos para ver estas recetas.', 'danger')
            return redirect(url_for('core.landing'))
    
    recetas = Receta.query.filter_by(historial_id=historial.id).all()
    
    return render_template('historial/recetas.html', 
                         historial=historial, 
                         recetas=recetas)


# ============================================
# EDITAR HISTORIAL
# ============================================
@bp_historial.route('/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar(id):
    """Editar un historial clínico"""
    if not (current_user.is_admin() or current_user.is_medico()):
        flash('⛔ No tienes permisos.', 'danger')
        return redirect(url_for('core.landing'))
    
    historial = HistorialClinico.query.get_or_404(id)
    
    if request.method == 'POST':
        historial.diagnostico = request.form.get('diagnostico')
        historial.sintomas = request.form.get('sintomas')
        historial.tratamiento = request.form.get('tratamiento')
        historial.observaciones = request.form.get('observaciones')
        
        db.session.commit()
        flash('✅ Historial actualizado exitosamente.', 'success')
        return redirect(url_for('historial.show', id=historial.id))
    
    return render_template('historial/editar.html', historial=historial)


# ============================================
# ELIMINAR HISTORIAL (SOLO ADMIN)
# ============================================
@bp_historial.route('/eliminar/<int:id>', methods=['POST'])
@login_required
def eliminar(id):
    """Eliminar un historial clínico (Solo Admin)"""
    if not current_user.is_admin():
        flash('⛔ Acceso denegado.', 'danger')
        return redirect(url_for('core.landing'))
    
    historial = HistorialClinico.query.get_or_404(id)
    
    # Verificar si tiene recetas asociadas
    if historial.recetas:
        for receta in historial.recetas:
            db.session.delete(receta)
    
    db.session.delete(historial)
    db.session.commit()
    
    flash('✅ Historial eliminado exitosamente.', 'success')
    return redirect(url_for('historial.index'))