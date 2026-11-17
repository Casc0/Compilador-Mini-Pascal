program completo;
var n: integer;

{ Factorial recursivo }
function fact(k: integer): integer;
begin
  if k < 2 then
    fact := 1
  else
    fact := k * fact(k - 1)
end;

{ Imprime los factoriales de 1 a tope }
procedure tabla(tope: integer);
var i: integer;
begin
  i := 1;
  while i <= tope do
  begin
    write(fact(i));
    i := i + 1
  end
end;

begin
  read(n);
  tabla(n)
end.
