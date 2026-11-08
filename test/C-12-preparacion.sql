-- C-12: datos de prueba de PERSONAL (provisorio hasta el seed.py de C-14, que lo reemplaza con los mismos correos).
-- Correr DESPUES de `python scripts/seed.py`, por ejemplo:
--   psql -h <host> -p <puerto> -U <usuario> -d <base> -f test/C-12-preparacion.sql
-- Idempotente: se puede correr varias veces; deja a estos cuatro usuarios en el estado inicial.
-- NUNCA hace DELETE sobre asignacion_rol: cierra con revocada_en las asignaciones abiertas y agrega las nuevas.
-- Contrasenas de mentira (solo para pruebas locales; los hashes son bcrypt de costo 12):
--   admin@example.com     clave-admin-1      ADMIN
--   admin2@example.com    clave-admin-2      ADMIN
--   vendedor@example.com  clave-vendedor-1   VENDEDOR
--   nuevo@example.com     clave-nuevo-1      VENDEDOR  (debe_cambiar_password = true)

BEGIN;

INSERT INTO usuario (email, nombre, password_hash, activo, debe_cambiar_password) VALUES
    ('admin@example.com', 'Administrador Uno', '$2b$12$TnNxoThsA4hkZPcMhJZLQuCNUfB77kFaUBEmFxPMm9MteAk9bR.kW', true, false),
    ('admin2@example.com', 'Administrador Dos', '$2b$12$VNs74oqv6FIrrPIXv//xb.AVxg.Oac8a52.JfJbDvRbFOCx7DRJMK', true, false),
    ('vendedor@example.com', 'Vendedor Uno', '$2b$12$hhxQJakxDPd1uUfCx2Dw3.OkmplrwTp1tlj/xnbSZRGHreiwFL8Tu', true, false),
    ('nuevo@example.com', 'Vendedor Nuevo', '$2b$12$7/nD/yCCJ38WdUBYwU2JT.1Qp5uLlvtXYCWkFGyCdoxB//cd8Qr0K', true, true)
ON CONFLICT (email) DO UPDATE SET
    nombre = EXCLUDED.nombre,
    password_hash = EXCLUDED.password_hash,
    activo = true,
    debe_cambiar_password = EXCLUDED.debe_cambiar_password;

-- Cierra (revocada_en) las asignaciones abiertas de estos cuatro usuarios; la fila queda como historial.
UPDATE asignacion_rol
   SET revocada_en = now()
 WHERE revocada_en IS NULL
   AND usuario_id IN (SELECT id FROM usuario
                       WHERE email IN ('admin@example.com', 'admin2@example.com',
                                       'vendedor@example.com', 'nuevo@example.com'));

-- Abre la asignacion inicial de cada uno (sin vencimiento; otorgada_por nulo = datos iniciales).
INSERT INTO asignacion_rol (usuario_id, rol)
SELECT u.id, v.rol
  FROM (VALUES
    ('admin@example.com', 'ADMIN'),
    ('admin2@example.com', 'ADMIN'),
    ('vendedor@example.com', 'VENDEDOR'),
    ('nuevo@example.com', 'VENDEDOR')
       ) AS v(email, rol)
  JOIN usuario u ON u.email = v.email;

COMMIT;
