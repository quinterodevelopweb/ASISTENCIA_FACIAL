PRAGMA foreign_keys = ON;

-- ==========================================
-- TABLA: tipo_usuario
-- ==========================================
CREATE TABLE tipo_usuario (
    idTipoUsuario INTEGER PRIMARY KEY AUTOINCREMENT,
    nombreTipoUsuario TEXT NOT NULL UNIQUE,
    estado INTEGER NOT NULL DEFAULT 1
);

-- ==========================================
-- TABLA: usuarios
-- ==========================================
CREATE TABLE usuarios (
    idUsuario INTEGER PRIMARY KEY AUTOINCREMENT,
    tipoUsuario INTEGER NOT NULL,

    noCuenta TEXT UNIQUE,
    nombre TEXT NOT NULL,
    apPaterno TEXT NOT NULL,
    apMaterno TEXT,

    email TEXT,
    telefono TEXT,

    -- Contraseña de acceso al panel de Profesor (junto con noCuenta). Solo se
    -- usa cuando tipoUsuario es 'Profesor'.
    password TEXT,

    estado INTEGER NOT NULL DEFAULT 1,

    fechaHoraRegistro DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fechaHoraActualizacion DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY(tipoUsuario)
        REFERENCES tipo_usuario(idTipoUsuario)
        ON UPDATE CASCADE
        ON DELETE RESTRICT
);

-- ==========================================
-- TABLA: clases
-- ==========================================
CREATE TABLE clases (
    idClase INTEGER PRIMARY KEY AUTOINCREMENT,
    nombreClase TEXT NOT NULL,
    periodoClase TEXT NOT NULL,
    estado INTEGER NOT NULL DEFAULT 1,

    fechaHoraRegistro DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fechaHoraActualizacion DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ==========================================
-- TABLA: usuario_clase (inscripciones, muchos a muchos)
-- ==========================================
CREATE TABLE usuario_clase (
    idUsuarioClase INTEGER PRIMARY KEY AUTOINCREMENT,

    idUsuario INTEGER NOT NULL,
    idClase INTEGER NOT NULL,

    estado INTEGER NOT NULL DEFAULT 1,

    fechaHoraRegistro DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY(idUsuario)
        REFERENCES usuarios(idUsuario)
        ON DELETE CASCADE,

    FOREIGN KEY(idClase)
        REFERENCES clases(idClase)
        ON DELETE CASCADE,

    UNIQUE(idUsuario, idClase)
);

-- ==========================================
-- TABLA: encoding
-- ==========================================
CREATE TABLE encoding (
    idEncoding INTEGER PRIMARY KEY AUTOINCREMENT,

    idUsuario INTEGER NOT NULL,

    vector BLOB NOT NULL,

    modelo TEXT NOT NULL,
    modeloVersion TEXT,

    dimension INTEGER NOT NULL,

    estado INTEGER NOT NULL DEFAULT 1,

    fechaHoraRegistro DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fechaHoraActualizacion DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY(idUsuario)
        REFERENCES usuarios(idUsuario)
        ON DELETE CASCADE
);

-- ==========================================
-- TABLA: asistencia
-- ==========================================
CREATE TABLE asistencia (
    idAsistencia INTEGER PRIMARY KEY AUTOINCREMENT,

    idUsuario INTEGER NOT NULL,
    idClase INTEGER NOT NULL,

    -- Copia del nombre del usuario y de la clase al momento del registro, para
    -- que el registro sea legible directamente en la base de datos (sin JOIN).
    nombreUsuario TEXT NOT NULL DEFAULT '',
    nombreClase TEXT NOT NULL DEFAULT '',

    fechaHora DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    confianza REAL CHECK(confianza >= 0 AND confianza <= 1),

    tipoRegistro TEXT NOT NULL DEFAULT 'ENTRADA' CHECK(tipoRegistro IN ('ENTRADA', 'SALIDA')),

    FOREIGN KEY(idUsuario)
        REFERENCES usuarios(idUsuario)
        ON DELETE CASCADE,

    FOREIGN KEY(idClase)
        REFERENCES clases(idClase)
        ON DELETE CASCADE
);

-- Usuarios
CREATE INDEX idx_usuario_cuenta
ON usuarios(noCuenta);

CREATE INDEX idx_usuario_nombre
ON usuarios(apPaterno, apMaterno, nombre);

CREATE INDEX idx_usuario_tipo
ON usuarios(tipoUsuario);

-- Usuario_clase
CREATE INDEX idx_usuario_clase_usuario
ON usuario_clase(idUsuario);

CREATE INDEX idx_usuario_clase_clase
ON usuario_clase(idClase);

-- Encoding
CREATE INDEX idx_encoding_usuario
ON encoding(idUsuario);

CREATE INDEX idx_encoding_estado
ON encoding(estado);

-- Asistencia
CREATE INDEX idx_asistencia_usuario
ON asistencia(idUsuario);

CREATE INDEX idx_asistencia_clase
ON asistencia(idClase);

CREATE INDEX idx_asistencia_fecha
ON asistencia(fechaHora);

CREATE INDEX idx_asistencia_usuario_fecha
ON asistencia(idUsuario, fechaHora);

-- Triggers: mantener fechaHoraActualizacion al día
CREATE TRIGGER trg_usuario_update
AFTER UPDATE ON usuarios
FOR EACH ROW
BEGIN
    UPDATE usuarios
    SET fechaHoraActualizacion = CURRENT_TIMESTAMP
    WHERE idUsuario = NEW.idUsuario;
END;

CREATE TRIGGER trg_clase_update
AFTER UPDATE ON clases
FOR EACH ROW
BEGIN
    UPDATE clases
    SET fechaHoraActualizacion = CURRENT_TIMESTAMP
    WHERE idClase = NEW.idClase;
END;

CREATE TRIGGER trg_encoding_update
AFTER UPDATE ON encoding
FOR EACH ROW
BEGIN
    UPDATE encoding
    SET fechaHoraActualizacion = CURRENT_TIMESTAMP
    WHERE idEncoding = NEW.idEncoding;
END;

-- Catálogo inicial de tipos de usuario
INSERT INTO tipo_usuario(nombreTipoUsuario)
VALUES
('Alumno'),
('Profesor'),
('Administrador');
