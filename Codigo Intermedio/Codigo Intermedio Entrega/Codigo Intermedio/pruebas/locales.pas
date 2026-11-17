program locales;
var x: integer;

{ El procedimiento tiene sus propias variables locales a y b }
procedure intercambiar;
var a, b: integer;
begin
  a := x;
  b := a * 2;
  x := b - a + 1;
  write(a);
  write(b)
end;

begin
  x := 4;
  intercambiar;
  write(x)
end.
