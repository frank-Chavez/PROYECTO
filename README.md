# Proyecto Final - Flask con Blueprints

Este proyecto es una aplicación web desarrollada con **Flask**, utilizando **Blueprints** para una arquitectura modular y escalable.  
Incluye plantillas HTML, archivos estáticos (CSS, JavaScript e imágenes) y una base de datos **SQLite**.

👉 **Descripción:** Aplicación web desarrollada como proyecto final, con un enfoque modular para aprender y aplicar buenas prácticas en Flask.  
*(Puedes personalizar esta descripción según el propósito real de tu app, por ejemplo: “Aplicación para gestión de tareas con autenticación de usuarios y un panel de administración”).*

---

## 📋 Requisitos Previos

Antes de comenzar, asegúrate de tener instalado lo siguiente:

- Python **3.8 o superior**  
- Git para clonar el repositorio  
- SQLite para la gestión de la base de datos  
- Opcional: un editor de código como **Visual Studio Code** o **PyCharm**  

---

## ⚙️ Instalación y Ejecución

### 1. Clonar el repositorio
```bash
git clone https://github.com/frank-Chavez/PROYECTO.git
cd PROYECTO
```

### 2. Crear y activar un entorno virtual
En **Windows**:
```bash
python -m venv venv
venv\Scripts\activate
```

En **Linux/Mac**:
```bash
python3 -m venv venv
source venv/bin/activate
```

> 📌 Nota: Al activar el entorno virtual aparecerá `(venv)` en la terminal. Si no es así, verifica que el comando se ejecutó correctamente.

### 3. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 4. Configurar la base de datos
Este proyecto utiliza **SQLite** como motor de base de datos. Tienes dos opciones:

#### Opción 1: Generar tu propia base de datos
```bash
sqlite3 base_de_datos.db < script.sql
```

#### Opción 2: Usar la base de datos incluida
Ya se incluye un archivo `base_de_datos.db` en el repositorio. Puedes usarlo directamente, aunque se recomienda generar uno nuevo desde `script.sql`.

### 5. Ejecutar la aplicación
Con el entorno virtual activado, inicia el servidor Flask:
```bash
flask --app app --debug run
```

La aplicación estará disponible en:  
👉 [http://127.0.0.1:5000/](http://127.0.0.1:5000/)

---

## 📂 Estructura del Proyecto

```
PROYECTO/
│── app.py              # Archivo principal de la aplicación Flask
│── base_de_datos.db    # Base de datos SQLite (opcional)
│── script.sql          # Script SQL para generar la base de datos
│── requirements.txt    # Dependencias del proyecto
│
├── blueprints/         # Directorio con los módulos de Blueprints
├── templates/          # Plantillas HTML
└── static/             # Archivos estáticos (CSS, JS, imágenes)
```

---

## 🔹 Acerca de los Blueprints

Los **Blueprints** de Flask permiten estructurar la aplicación en módulos reutilizables, facilitando la organización, escalabilidad y mantenimiento del código.  
Este proyecto los utiliza para separar las rutas y la lógica de negocio en componentes independientes.

---

## ⚠️ Notas Importantes

- Activa siempre el **entorno virtual** antes de ejecutar comandos.  
- Si usas `script.sql`, ejecútalo antes de iniciar la aplicación.  
- Si el puerto **5000** está en uso, puedes iniciar en otro puerto:  
  ```bash
  flask --app app --debug run --port 5001
  ```

---

## 🛠️ Solución de Problemas

**Error:** `No module named flask`  
👉 Verifica que el entorno virtual está activado e instala dependencias con:
```bash
pip install -r requirements.txt
```

**Error en la base de datos**  
👉 Comprueba que `base_de_datos.db` existe o vuelve a ejecutar:
```bash
sqlite3 base_de_datos.db < script.sql
```

---

## 📚 Recursos Adicionales

- [Documentación oficial de Flask](https://flask.palletsprojects.com/)  
- [Documentación de SQLite](https://www.sqlite.org/docs.html)  
- [Guía sobre entornos virtuales en Python](https://docs.python.org/3/library/venv.html)  

---

## 🤝 Contribuciones

Las contribuciones son bienvenidas.  
Para colaborar, por favor crea un **pull request** o abre un **issue** en el repositorio.

---

## 📜 Licencia

Este proyecto fue desarrollado como **proyecto final académico**.  
Puedes adaptarlo o reutilizarlo según tus necesidades.
