Proyecto Final - Flask con Blueprints
Este proyecto es una aplicación web desarrollada con Flask, utilizando Blueprints para una arquitectura modular y escalable. Incluye plantillas HTML, archivos estáticos (CSS, JavaScript e imágenes) y una base de datos SQLite.
Descripción: [Incluya aquí una breve descripción del propósito de la aplicación, por ejemplo: "Aplicación para la gestión de tareas con autenticación de usuarios y un panel de administración."]

Requisitos Previos
Antes de comenzar, asegúrese de tener instalado lo siguiente:

Python 3.8 o superior
Git para clonar el repositorio
SQLite para la gestión de la base de datos
Opcional: Un editor de código como Visual Studio Code o PyCharm


Instalación y Ejecución
Siga los pasos a continuación para configurar y ejecutar el proyecto:
1. Clonar el Repositorio
git clone https://github.com/frank-Chavez/PROYECTO.git
cd PROYECTO

2. Crear y Activar un Entorno Virtual
En Windows:
python -m venv venv
venv\Scripts\activate

En Linux/Mac:
python3 -m venv venv
source venv/bin/activate

Nota: Al activar el entorno virtual, aparecerá (venv) en la terminal. Si no es así, verifique que el comando de activación se ejecutó correctamente.
3. Instalar Dependencias
Asegúrese de que el archivo requirements.txt esté presente en el repositorio, luego ejecute:
pip install -r requirements.txt

4. Configurar la Base de Datos
El proyecto utiliza SQLite como motor de base de datos. Tiene dos opciones para configurarla:
Opción 1: Generar la Base de Datos
Ejecute el siguiente comando para crear la estructura de la base de datos:
sqlite3 base_de_datos.db < script.sql

Opción 2: Usar la Base de Datos Incluida
El archivo base_de_datos.db está incluido en el repositorio. Puede utilizarlo directamente, aunque se recomienda generar una nueva base con el script para garantizar consistencia.
5. Ejecutar la Aplicación
Con el entorno virtual activado, inicie el servidor Flask en modo de desarrollo:
flask --app app --debug run

La aplicación estará disponible en:http://127.0.0.1:5000/

Estructura del Proyecto

app.py: Archivo principal de la aplicación Flask.
blueprints/: Directorio que contiene los módulos de Blueprints para organizar las rutas.
templates/: Plantillas HTML para la interfaz de usuario.
static/: Archivos CSS, JavaScript e imágenes.
base_de_datos.db: Base de datos SQLite (opcional).
script.sql: Script SQL para generar la base de datos.


Acerca de los Blueprints
Los Blueprints de Flask permiten estructurar la aplicación en módulos reutilizables, lo que facilita la organización, escalabilidad y mantenimiento del código. Este proyecto los utiliza para separar las rutas y la lógica de negocio en componentes independientes.

Notas Importantes

Entorno Virtual: Active siempre el entorno virtual antes de ejecutar comandos para evitar conflictos de dependencias.
Base de Datos: Si utiliza el archivo script.sql, ejecútelo antes de iniciar la aplicación.
Puerto Ocupado: Si el puerto 5000 está en uso, puede especificar otro puerto con:

flask --app app --debug run --port 5001


Solución de Problemas

Error: "No module named flask": Verifique que el entorno virtual está activado y que las dependencias se instalaron correctamente con:

pip install -r requirements.txt


Error en la base de datos: Asegúrese de que el archivo base_de_datos.db existe o ejecute nuevamente el script script.sql.
Para más información, consulte la documentación oficial de Flask o SQLite.


Recursos Adicionales

Documentación de Flask
Documentación de SQLite

