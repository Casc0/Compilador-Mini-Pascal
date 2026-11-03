program parametros;
var r: integer;

{ Función con dos parámetros por valor }
function maximo(a: integer; b: integer): integer;
begin
  if a > b then
    maximo := a
  else
    maximo := b
end;

begin
  r := maximo(3, 8) + 1;
  write(r)
end.
