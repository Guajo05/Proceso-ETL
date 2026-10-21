/* =====================================================================
   Sistema de Análisis de Opiniones de Clientes
   Creación de la base de datos y sus tablas (SQL Server)
   ===================================================================== */

CREATE DATABASE OpinionesClientesDB;
GO

USE OpinionesClientesDB;
GO

/* 1. Categoria */
CREATE TABLE dbo.Categoria (
    IdCategoria  INT IDENTITY(1,1) NOT NULL,
    Nombre       NVARCHAR(50)      NOT NULL,
    CONSTRAINT PK_Categoria        PRIMARY KEY (IdCategoria),
    CONSTRAINT UQ_Categoria_Nombre UNIQUE (Nombre)
);
GO

/* 2. Producto */
CREATE TABLE dbo.Producto (
    IdProducto   INT           NOT NULL,
    Nombre       NVARCHAR(100) NOT NULL,
    IdCategoria  INT           NOT NULL,
    CONSTRAINT PK_Producto           PRIMARY KEY (IdProducto),
    CONSTRAINT FK_Producto_Categoria FOREIGN KEY (IdCategoria)
        REFERENCES dbo.Categoria (IdCategoria)
);
GO

/* 3. Cliente */
CREATE TABLE dbo.Cliente (
    IdCliente  INT           NOT NULL,
    Nombre     NVARCHAR(100) NOT NULL,
    Email      NVARCHAR(150) NOT NULL,
    CONSTRAINT PK_Cliente       PRIMARY KEY (IdCliente),
    CONSTRAINT UQ_Cliente_Email UNIQUE (Email)
);
GO

/* 4. Clasificacion (Positiva, Negativa, Neutra) */
CREATE TABLE dbo.Clasificacion (
    IdClasificacion  INT IDENTITY(1,1) NOT NULL,
    Tipo             NVARCHAR(20)      NOT NULL,
    CONSTRAINT PK_Clasificacion      PRIMARY KEY (IdClasificacion),
    CONSTRAINT UQ_Clasificacion_Tipo UNIQUE (Tipo),
    CONSTRAINT CK_Clasificacion_Tipo CHECK (Tipo IN (N'Positiva', N'Negativa', N'Neutra'))
);
GO

/* 5. Fuente_Datos (cada fila representa una carga) */
CREATE TABLE dbo.Fuente_Datos (
    IdFuente    VARCHAR(4)   NOT NULL,
    TipoFuente  NVARCHAR(20) NOT NULL,
    FechaCarga  DATE         NOT NULL,
    CONSTRAINT PK_Fuente_Datos      PRIMARY KEY (IdFuente),
    CONSTRAINT CK_Fuente_TipoFuente CHECK (TipoFuente IN (N'CSV', N'Web', N'Red Social'))
);
GO

/* 6. Opinion (tabla central) */
CREATE TABLE dbo.Opinion (
    IdOpinion        INT IDENTITY(1,1) NOT NULL,
    IdOrigen         VARCHAR(20)       NOT NULL,
    Canal            NVARCHAR(30)      NOT NULL,
    Fecha            DATE              NOT NULL,
    Comentario       NVARCHAR(500)     NOT NULL,
    Puntaje          TINYINT           NULL,
    IdCliente        INT               NULL,
    IdProducto       INT               NOT NULL,
    IdClasificacion  INT               NOT NULL,
    IdFuente         VARCHAR(4)        NOT NULL,
    CONSTRAINT PK_Opinion               PRIMARY KEY (IdOpinion),
    CONSTRAINT UQ_Opinion_Origen_Canal  UNIQUE (IdOrigen, Canal),
    CONSTRAINT CK_Opinion_Puntaje       CHECK (Puntaje IS NULL OR Puntaje BETWEEN 1 AND 5),
    CONSTRAINT FK_Opinion_Cliente       FOREIGN KEY (IdCliente)
        REFERENCES dbo.Cliente (IdCliente),
    CONSTRAINT FK_Opinion_Producto      FOREIGN KEY (IdProducto)
        REFERENCES dbo.Producto (IdProducto),
    CONSTRAINT FK_Opinion_Clasificacion FOREIGN KEY (IdClasificacion)
        REFERENCES dbo.Clasificacion (IdClasificacion),
    CONSTRAINT FK_Opinion_Fuente        FOREIGN KEY (IdFuente)
        REFERENCES dbo.Fuente_Datos (IdFuente)
);
GO

/* 7. VISTAS (Requerido por la tarea) */
GO
CREATE VIEW dbo.vw_Opiniones_Completas AS
SELECT 
    o.IdOpinion,
    o.IdOrigen,
    c.Nombre AS NombreCliente,
    p.Nombre AS NombreProducto,
    cat.Nombre AS Categoria,
    cl.Tipo AS Clasificacion,
    f.TipoFuente AS Fuente,
    o.Fecha,
    o.Comentario,
    o.Puntaje
FROM dbo.Opinion o
LEFT JOIN dbo.Cliente c ON o.IdCliente = c.IdCliente
INNER JOIN dbo.Producto p ON o.IdProducto = p.IdProducto
INNER JOIN dbo.Categoria cat ON p.IdCategoria = cat.IdCategoria
INNER JOIN dbo.Clasificacion cl ON o.IdClasificacion = cl.IdClasificacion
INNER JOIN dbo.Fuente_Datos f ON o.IdFuente = f.IdFuente;
GO

/* 8. PROCEDIMIENTOS ALMACENADOS (Requerido por la tarea) */
-- Procedimiento para insertar una opinión
CREATE PROCEDURE dbo.sp_InsertarOpinion
    @IdOrigen VARCHAR(20),
    @Canal NVARCHAR(30),
    @Fecha DATE,
    @Comentario NVARCHAR(500),
    @Puntaje TINYINT = NULL,
    @IdCliente INT = NULL,
    @IdProducto INT,
    @IdClasificacion INT,
    @IdFuente VARCHAR(4)
AS
BEGIN
    SET NOCOUNT ON;
    BEGIN TRY
        INSERT INTO dbo.Opinion (IdOrigen, Canal, Fecha, Comentario, Puntaje, IdCliente, IdProducto, IdClasificacion, IdFuente)
        VALUES (@IdOrigen, @Canal, @Fecha, @Comentario, @Puntaje, @IdCliente, @IdProducto, @IdClasificacion, @IdFuente);
        
        RETURN SCOPE_IDENTITY(); -- Retorna el ID insertado
    END TRY
    BEGIN CATCH
         -- Manejo de errores
        THROW;
    END CATCH
END;
GO