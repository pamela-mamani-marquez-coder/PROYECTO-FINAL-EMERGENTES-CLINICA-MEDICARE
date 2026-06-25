# 🏥 Nombre del Proyecto
**Clínica Medicare - Sistema de Gestión de Consultorios Médicos**

---

## 📋 Descripción
Describe brevemente qué hace tu sistema.

> Ejemplo: "Sistema web desarrollado en Flask para la gestión integral de consultorios médicos. Permite administrar pacientes, médicos, citas, historiales clínicos y facturación."

---

## 🚀 Tecnologías Utilizadas

- **Backend:** Python, Flask, SQLAlchemy, Flask-Login, Flask-Bcrypt
- **Frontend:** Bootstrap 5, Jinja2, Bootstrap Icons
- **Base de Datos:** SQLite
- **Despliegue:** Render

---

## 🎯 Funcionalidades Principales

- ✅ Autenticación con 4 roles: Administrador, Médico, Paciente, Recepcionista
- ✅ CRUD completo de Pacientes, Médicos, Citas, Historiales y Facturas
- ✅ Panel administrativo con estadísticas
- ✅ Diseño responsivo con Bootstrap 5

---

## 👥 Roles y Credenciales de Prueba

| Rol | Usuario | Contraseña |
|-----|---------|------------|
| Administrador | `admin` | `admin123` |
| Médico | `medico1` - `medico7` | `medico123` |
| Paciente | `paciente1` - `paciente14` | `paciente123` |
| Recepcionista | `recepcionista1` | `recep123` |

---

## 📸 Capturas de Pantalla

Incluye algunas imágenes de tu sistema para dar una vista rápida.

---

## 🌐 Enlace a la Aplicación

https://proyecto-final-emergentes-clinica-3rfc.onrender.com/

---

## ⚙️ Instalación y Ejecución en Local

```bash
# 1. Clonar el repositorio
git clone https://github.com/pamela-mamani-marquez-coder/PROYECTO-FINAL-EMERGENTES-CLINICA-MEDICARE

# 2. Crear entorno virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Crear base de datos
python seed_data.py

# 5. Ejecutar
python run.py


#ESTRUCTURA DEL PROYECTO

CLINICA/
├── app/
│   ├── admin/          # Módulo administrador
│   ├── auth/           # Autenticación
│   ├── citas/          # Gestión de citas
│   ├── core/           # Página principal
│   ├── facturacion/    # Facturación
│   ├── historial/      # Historial clínico
│   ├── medicos/        # Gestión de médicos
│   ├── modelos/        # Modelos de base de datos
│   └── pacientes/      # Gestión de pacientes
├── templates/          # Plantillas HTML
├── static/             # Archivos CSS, JS, imágenes
├── instance/           # Base de datos SQLite
├── run.py              # Punto de entrada
├── requirements.txt    # Dependencias
└── README.md           # Este archivo



#AUTORES
Cari Paco Bethy Mercedes

Mamani Marquez Pamela

Materia: Emergentes II (SIS-745)
Docente: M. Sc. Mario Torrez C.
Gestión: 2026