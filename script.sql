CREATE TABLE Rol (
    rol_id INTEGER PRIMARY KEY AUTOINCREMENT,
    estado_rol INTEGER NOT NULL, 
    tipo_rol TEXT NOT NULL
);
CREATE TABLE sqlite_sequence(name,seq);
CREATE TABLE Usuario (
    id_usuario INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre_u TEXT NOT NULL,
    contraseña_u TEXT NOT NULL,
    rol_id INTEGER,
    FOREIGN KEY (rol_id) REFERENCES Rol(rol_id)
);
CREATE TABLE Familiares (
    id_familiar INTEGER PRIMARY KEY AUTOINCREMENT,
    f_nombre TEXT NOT NULL,
    f_apellido TEXT NOT NULL,
    f_parentesco TEXT NOT NULL,
    f_telefono TEXT,
    f_correo TEXT,
    f_estado INTEGER NOT NULL,
    fechaRegistro DATE,
    usuario_id INTEGER,
    FOREIGN KEY (usuario_id) REFERENCES Usuario(id_usuario)
);
CREATE TABLE Fallecidos (
    id_fallecido INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre_f TEXT NOT NULL,
    fecha_defuncion DATE NOT NULL,
    estado_f INTEGER, 
    edad_f INTEGER,
    familiar_id INTEGER,
    fechaRegistro_f DATE,
    fechaActualizacion_f DATE,
    FOREIGN KEY (familiar_id) REFERENCES Familiares(id_familiar)
);
CREATE TABLE Planes (
    id_plan INTEGER PRIMARY KEY AUTOINCREMENT,
    tipo_plan TEXT NOT NULL,
    precio_plan REAL NOT NULL,
    duracion_plan TEXT,
    categoria_plan TEXT,
    condiciones_plan TEXT,
    estado_plan INTEGER NOT NULL
);
CREATE TABLE Servicios (
    id_servicio INTEGER PRIMARY KEY AUTOINCREMENT,
    tipo_serv TEXT NOT NULL,
    descripcion_serv TEXT,
    categoria_serv TEXT,
    precio_serv REAL,
    proveedor_id INTEGER,
    estado_serv INTEGER NOT NULL,
    FOREIGN KEY (proveedor_id) REFERENCES Proveedores(id_proveedor)
);
CREATE TABLE Proveedores (
    id_proveedor INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre_p TEXT NOT NULL,
    telefono_p TEXT,
    correo_p TEXT,
    servicio_p TEXT,
    estado_p INTEGER NOT NULL,
    fechaRegistro_p DATE
);
CREATE TABLE Cotizacion (
    id_cotizacion INTEGER PRIMARY KEY AUTOINCREMENT,
    numero_cot TEXT NOT NULL,
    fecha_cot DATE NOT NULL,
    monto_cot REAL NOT NULL,
    estado_cot INTEGER NOT NULL,
    validacion_cot TEXT
);
CREATE TABLE cotizacion_detalles (
    id_detalle INTEGER PRIMARY KEY AUTOINCREMENT,
    id_cotizacion INTEGER,
    id_plan INTEGER,
    id_servicio INTEGER, 
    id_familiar INTEGER, 
    cantidad INTEGER DEFAULT 1,
    FOREIGN KEY (id_cotizacion) REFERENCES Cotizacion(id_cotizacion),
    FOREIGN KEY (id_plan) REFERENCES Planes(id_plan),
    FOREIGN KEY (id_servicio) REFERENCES Servicios(id_servicio)
);
CREATE TABLE servicio_planes (
    id_servicio INTEGER,
    id_plan INTEGER,
    PRIMARY KEY (id_servicio, id_plan),
    FOREIGN KEY (id_servicio) REFERENCES Servicios(id_servicio),
    FOREIGN KEY (id_plan) REFERENCES Planes(id_plan)
);
CREATE TABLE proveedor_servicio (
    id_proveedores INTEGER,
    id_servicios INTEGER,
    PRIMARY KEY (id_proveedores, id_servicios),
    FOREIGN KEY (id_proveedores) REFERENCES Proveedores(id_proveedor),
    FOREIGN KEY (id_servicios) REFERENCES Servicios(id_servicio)
);