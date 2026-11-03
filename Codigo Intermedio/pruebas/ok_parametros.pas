program parametros;
var total: integer;
    activo: boolean;

{ Recibe parámetros de distintos tipos }
function ajustar(valor: integer; duplicar: boolean): integer;
var aux: integer;
begin
  aux := valor + 1;
  if duplicar then
    ajustar := aux * 2
  else
    ajustar := aux
end;

procedure informar(n: integer; ok: boolean);
begin
  if ok and (n > 0) then
    write(n)
  else
    write(0)
end;

begin
  read(total);
  activo := total >= 10;
  total := ajustar(total, activo);
  informar(total, not activo or (total = 20))
end.
