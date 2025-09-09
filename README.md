# Proyecto Final - Flask con Blueprints

Este proyecto está desarrollado con **Flask** utilizando el método de *Blueprints*.  
Incluye un sistema modular con plantillas, archivos estáticos y conexión a base de datos.

---

## 🚀 Instalación y Ejecución

### 1. Clonar el repositorio
```bash
git clone https://github.com/frank-Chavez/PROYECTO.git
cd PROYECTO

### 2. Crear entorno virtual

En Windows

python -m venv venv
venv\Scripts\activate

En Linux/Mac

python3 -m venv venv
source venv/bin/activate


### 3. Instalar dependencias

pip install -r requirements.txt


## Base de Datos
Este proyecto utiliza SQLite como motor de base de datos.
Tienes dos opciones para configurar la BD:

1- Generar tu propia base de datos desde el script
Ejecuta el archivo script.sql para crear la estructura:

sqlite3 base_de_datos.db < script.sql


2-Usar la base de datos incluida
También puedes utilizar directamente el archivo base de datos.db ya disponible en el repositorio.


### Ejecutar el proyecto
Ejecuta el siguiente comando para iniciar el servidor:
pero antes dedeves de estar en el entorno virtual.

flask --app app --debug run

La aplicación estará disponible en:
👉 http://127.0.0.1:5000/


Notas

Usa siempre el entorno virtual (venv) para evitar conflictos de dependencias.

Si decides usar el archivo script.sql, asegúrate de ejecutarlo antes de correr la aplicación.

El archivo base de datos.db está incluido solo como referencia, lo recomendable es generarlo desde script.sql.

---
