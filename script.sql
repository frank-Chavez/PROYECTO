-- Tabla de Roles
CREATE TABLE Rol (
    rol_id INTEGER PRIMARY KEY AUTOINCREMENT,
    estado_rol TEXT NOT NULL,
    tipo_rol TEXT NOT NULL
);

-- Tabla de Usuarios
CREATE TABLE Usuario (
    id_usuario INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre_u TEXT NOT NULL,
    contraseña_u TEXT NOT NULL,
    rol_id INTEGER,
    FOREIGN KEY (rol_id) REFERENCES Rol(rol_id)
);

-- Tabla de Familiares
CREATE TABLE Familiares (
    id_familiar INTEGER PRIMARY KEY AUTOINCREMENT,
    f_nombre TEXT NOT NULL,
    f_apellido TEXT NOT NULL,
    f_parentesco TEXT NOT NULL,
    f_telefono TEXT,
    f_correo TEXT,
    f_estado TEXT,
    fechaRegistro DATE,
    usuario_id INTEGER,
    FOREIGN KEY (usuario_id) REFERENCES Usuario(id_usuario)
);

-- Tabla de Fallecidos
CREATE TABLE Fallecidos (
    id_fallecido INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre_f TEXT NOT NULL,
    fecha_defuncion DATE NOT NULL,
    estado_f TEXT,
    edad_f INTEGER,
    familiar_id INTEGER,
    FOREIGN KEY (familiar_id) REFERENCES Familiares(id_familiar)
);

-- Tabla de Planes
CREATE TABLE Planes (
    id_plan INTEGER PRIMARY KEY AUTOINCREMENT,
    tipo_plan TEXT NOT NULL,
    precio_plan REAL NOT NULL,
    duracion_plan TEXT,
    categoria_plan TEXT,
    condiciones_plan TEXT,
    estado_plan TEXT
);

-- Tabla de Servicios
CREATE TABLE Servicios (
    id_servicio INTEGER PRIMARY KEY AUTOINCREMENT,
    tipo_serv TEXT NOT NULL,
    descripcion_serv TEXT,
    categoria_serv TEXT,
    precio_serv REAL,
    proveedor_id INTEGER,
    estado_serv TEXT,
    FOREIGN KEY (proveedor_id) REFERENCES Proveedores(id_proveedor)
);

-- Tabla de Cotizaciones
CREATE TABLE Cotizacion (
    id_cotizacion INTEGER PRIMARY KEY AUTOINCREMENT,
    numero_cot TEXT NOT NULL,
    fecha_cot DATE NOT NULL,
    monto_cot REAL NOT NULL,
    estado_cot TEXT,
    validacion_cot TEXT
);

-- Tabla de Cotización Detalles
CREATE TABLE cotizacion_detalles (
    id_detalle INTEGER PRIMARY KEY AUTOINCREMENT,
    id_cotizacion INTEGER,
    id_plan INTEGER,
    id_servicio INTEGER,
    FOREIGN KEY (id_cotizacion) REFERENCES Cotizacion(id_cotizacion),
    FOREIGN KEY (id_plan) REFERENCES Planes(id_plan),
    FOREIGN KEY (id_servicio) REFERENCES Servicios(id_servicio)
);

-- Tabla intermedia Servicio-Planes
CREATE TABLE servicio_planes (
    id_servicio INTEGER,
    id_plan INTEGER,
    PRIMARY KEY (id_servicio, id_plan),
    FOREIGN KEY (id_servicio) REFERENCES Servicios(id_servicio),
    FOREIGN KEY (id_plan) REFERENCES Planes(id_plan)
);

-- Tabla de Proveedores
CREATE TABLE Proveedores (
    id_proveedor INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre_p TEXT NOT NULL,
    telefono_p TEXT,
    correo_p TEXT,
    servicio_p TEXT,
    estado_p TEXT,
    fechaRegistro_p DATE
);

-- Tabla intermedia Proveedor-Servicio
CREATE TABLE proveedor_servicio (
    id_proveedores INTEGER,
    id_servicios INTEGER,
    PRIMARY KEY (id_proveedores, id_servicios),
    FOREIGN KEY (id_proveedores) REFERENCES Proveedores(id_proveedor),
    FOREIGN KEY (id_servicios) REFERENCES Servicios(id_servicio)
);
