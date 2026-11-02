program ambitos;
var n, resultado: integer;
    par: boolean;

{ Función recursiva y una variable local que oculta a la global }
function factorial(k: integer): integer;
var n: integer;
begin
  n := k;
  if n <= 1 then
    factorial := 1
  else
    factorial := n * factorial(n - 1)
end;

function espar(x: integer): boolean;
begin
  espar := (x / 2) * 2 = x
end;

begin
  read(n);
  resultado := factorial(n);
  par := espar(resultado);
  while not par do
  begin
    resultado := resultado + 1;
    par := espar(resultado)
  end;
  write(resultado)
end.
