-- test/solo_agregado.sql
-- Prueba que movimiento_stock es de solo agregado (RN-12). Autocontenido: crea sus propios
-- datos dentro de una transaccion y termina en ROLLBACK, asi que no deja filas.
-- Uso:  psql -U <usuario> -d <base> -f test/solo_agregado.sql
-- Requiere: base migrada (0003 o 0004) y al menos un libro (ej. tras `python seed.py`).
--
-- Resultado esperado SIN trigger (migracion 0003, "rojo"): UPDATE y DELETE se ACEPTAN.
-- Resultado esperado CON trigger (migracion 0004, "verde"): UPDATE y DELETE fallan con
--   "movimiento_stock es de solo agregado: UPDATE no permitido" / "...: DELETE no permitido".
-- Cada sentencia indica su resultado esperado en 0004; en 0003 las marcadas ERROR salen OK.

\set ON_ERROR_STOP off
\echo '=== solo_agregado.sql ==='
BEGIN;

-- Datos propios de la prueba (se descartan con el ROLLBACK final).
-- Esperado: INSERT 0 1
INSERT INTO usuario (email, nombre, password_hash)
VALUES ('solo-agregado@prueba.local', 'Prueba solo agregado', 'hash-de-prueba');

-- INSERT es lo unico permitido.
-- Esperado (0003 y 0004): INSERT 0 1
INSERT INTO movimiento_stock (libro_id, usuario_id, cantidad, motivo)
SELECT (SELECT min(id) FROM libro), id, 5, 'Prueba solo agregado'
FROM usuario WHERE email = 'solo-agregado@prueba.local';

-- Esperado (0003 y 0004): 1 fila, cantidad 5
SELECT id, cantidad, motivo FROM movimiento_stock WHERE motivo = 'Prueba solo agregado';

-- UPDATE
-- Esperado 0004: ERROR:  movimiento_stock es de solo agregado: UPDATE no permitido
-- Esperado 0003 ("rojo"): UPDATE 1
SAVEPOINT antes_update;
UPDATE movimiento_stock SET cantidad = 99 WHERE motivo = 'Prueba solo agregado';
ROLLBACK TO SAVEPOINT antes_update;

-- DELETE
-- Esperado 0004: ERROR:  movimiento_stock es de solo agregado: DELETE no permitido
-- Esperado 0003 ("rojo"): DELETE 1
SAVEPOINT antes_delete;
DELETE FROM movimiento_stock WHERE motivo = 'Prueba solo agregado';
ROLLBACK TO SAVEPOINT antes_delete;

-- La fila sigue intacta tras los intentos (los SAVEPOINT revierten lo que se haya aceptado).
-- Esperado (0003 y 0004): 1 fila, cantidad 5
SELECT id, cantidad, motivo FROM movimiento_stock WHERE motivo = 'Prueba solo agregado';

ROLLBACK;

-- Sin filas residuales.
-- Esperado (0003 y 0004): 0 | 0
SELECT (SELECT count(*) FROM movimiento_stock WHERE motivo = 'Prueba solo agregado') AS movimientos_residuales,
       (SELECT count(*) FROM usuario WHERE email = 'solo-agregado@prueba.local') AS usuarios_residuales;
