program condicional;
var n: integer;
    positivo: boolean;
begin
  read(n);
  positivo := n > 0;
  if positivo then
    write(1)
  else
    write(0);
  if n = 0 then
    write(n)
end.
