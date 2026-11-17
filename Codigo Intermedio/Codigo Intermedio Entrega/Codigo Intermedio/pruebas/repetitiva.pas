program repetitiva;
var i, suma: integer;
begin
  read(i);
  suma := 0;
  while i > 0 do
  begin
    suma := suma + i;
    i := i - 1
  end;
  write(suma)
end.
