import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
VARIABLE, FUNCTION, PROCEDURE, PARAMETER, PROGRAM = 1, 2, 3, 4, 5
ATTRIBUTE_NAMES = {
    VARIABLE: 'variable', FUNCTION: 'función', PROCEDURE: 'procedimiento',
    PARAMETER: 'parámetro', PROGRAM: 'programa'
}
# Unidad léxica producida por el analizador y consumida por el parser.
class Token:
    # name: categoría del token. value: atributo (vacío si no aplica). line_number: línea de origen.
    def __init__(self, name, value, line_number):
        self.name = name
        self.value = value
        self.line_number = line_number

    # Formato de salida: <ID | symbolTable[n]>, <NAME, value> o <NAME>.
    def __str__(self):
        if self.name == 'ID':
            return f'<ID | {self.value} | line {self.line_number}>'
        elif self.value != '':
            return f'<{self.name}, {self.value}>'
        return f'<{self.name}>'


class SymbolTable:
    def __init__(self, name):
        self.table = {}
        self.name = name
        
    def declare(self, lexeme, type_, attribute, line_declared):
        if lexeme in self.table:
            return None           # redeclaración: el parser reporta el error
        entry = SymbolTableEntry(lexeme, type_, attribute, line_declared)
        self.table[lexeme] = entry
        return entry
    
    def lookup(self, lexeme):
        return self.table.get(lexeme)

    # Escribe la tabla como una grilla: una fila por entrada, en orden de declaración.
    def print_table(self, output=sys.stdout):
        header = f"{'Lexema':<15} {'Tipo':<10} {'Atributo':<12} {'Línea decl.':<12} Referencias"
        output.write(f"\n=== Ámbito: {self.name} ===\n")
        output.write(header + "\n")
        output.write("-" * len(header) + "\n")
        if not self.table:
            output.write("(sin declaraciones)\n")
        for entry in self.table.values():
            tipo = entry.type if entry.type is not None else '-'
            atributo = ATTRIBUTE_NAMES.get(entry.attribute, '?')
            refs = ', '.join(str(l) for l in entry.lines_referenced) or '-'
            output.write(f"{entry.name:<15} {tipo:<10} {atributo:<12} {entry.line_declared:<12} {refs}\n")
   

class SymbolTableEntry:
    def __init__(self, lexeme, type_, attribute, line_declared):
        self.name = lexeme
        self.type = type_
        self.attribute = attribute
        self.line_declared = line_declared
        self.lines_referenced = []
        self.params = []

# Analizador léxico para un subconjunto del lenguaje Pascal.
class LexiAnalyzer:
    # Abre el archivo fuente y carga el primer carácter, las palabras reservadas y los mensajes de error.
    def __init__(self, archivo):
        self.file = open(archivo, 'r')
        self.line_number = 1
        self.current_char = self.file.read(1)
        #self.symbol_table = SymbolTable()

        self.keywords = {
            "program": 'PROGRAM', "var": 'VAR', "integer": 'INTEGER',
            "boolean": 'BOOLEAN', "function": 'FUNCTION', "procedure": 'PROCEDURE',
            "begin": 'BEGIN', "end": 'END', "if": 'IF', "then": 'THEN',
            "else": 'ELSE', "while": 'WHILE', "do": 'DO', "read": 'READ',
            "write": 'WRITE', "true": 'TRUE', "false": 'FALSE',
            "or": 'OR', "and": 'AND', "not": 'NOT'
        }

        self.errors = {
            "COMMENT": "Comentario no cerrado. Se esperaba una llave de cierre.",
            "UNRECOGNIZED_CHAR": "Carácter no reconocido.",
            "ASIGN": "Se esperaba un '=' después de ':'.",
            "NUM_ERROR": "Número mal formado. No se permiten letras después de dígitos."
        }

    # Avanza un carácter en el archivo.
    def next_char(self):
        self.current_char = self.file.read(1)

    # Punto de entrada principal: consume caracteres hasta reconocer y retornar el siguiente token.
    def get_next_token(self) -> Token:
        while self.current_char:
            match self.current_char:
                case ' ' | '\t':
                    self.next_char()
                    continue

                case '\n':
                    self.line_number += 1
                    self.next_char()
                    continue

                case '{':
                    self.next_char()
                    self.recognize_comment()
                    continue

                case c if c.isalpha():
                    return self.recognize_id_or_keyword()

                case c if c.isdigit():
                    return self.recognize_number()

                case ':':
                    self.next_char()
                    if self.current_char != '=':
                        return Token('DOS_PUNTOS', '', self.line_number)
                    self.next_char()
                    return Token('OP_ASIG', '', self.line_number)

                case '<':
                    self.next_char()
                    if self.current_char == '>':
                        self.next_char()
                        return Token('OP_REL', 'NE', self.line_number)
                    elif self.current_char == '=':
                        self.next_char()
                        return Token('OP_REL', 'LE', self.line_number)
                    return Token('OP_REL', 'LT', self.line_number)

                case '>':
                    self.next_char()
                    if self.current_char == '=':
                        self.next_char()
                        return Token('OP_REL', 'GE', self.line_number)
                    return Token('OP_REL', 'GT', self.line_number)

                case '=':
                    self.next_char()
                    return Token('OP_REL', 'EQ', self.line_number)

                case '+':
                    self.next_char()
                    return Token('OP_ARIT', 'ADD', self.line_number)

                case '-':
                    self.next_char()
                    return Token('OP_ARIT', 'SUB', self.line_number)

                case '*':
                    self.next_char()
                    return Token('OP_ARIT', 'MUL', self.line_number)

                case '/':
                    self.next_char()
                    return Token('OP_ARIT', 'DIV', self.line_number)

                case '(':
                    self.next_char()
                    return Token('PAR_ABRE', '', self.line_number)

                case ')':
                    self.next_char()
                    return Token('PAR_CIERRA', '', self.line_number)

                case ',':
                    self.next_char()
                    return Token('COMA', '', self.line_number)

                case '.':
                    self.next_char()
                    return Token('PUNTO', '', self.line_number)

                case ';':
                    self.next_char()
                    return Token('PUNTO_COMA', '', self.line_number)

                case _:
                    self.print_error(self.errors["UNRECOGNIZED_CHAR"])
                    self.next_char()

    # Consume todos los caracteres hasta la llave de cierre '}', descartando el comentario.
    def recognize_comment(self):
        while self.current_char and self.current_char != '}':
            if self.current_char == '\n':
                self.line_number += 1
            self.next_char()

        if self.current_char:
            self.next_char()
        else:
            self.print_error(self.errors["COMMENT"])

    # Reconoce un identificador o palabra reservada; retorna el token correspondiente.
    def recognize_id_or_keyword(self) -> Token:
        lexeme = ""
        while self.current_char and self.current_char.isalnum():
            lexeme += self.current_char
            self.next_char()

        lexeme = lexeme.lower()

        name = self.keywords.get(lexeme, 'ID')
        if name == 'ID':
            return Token(name, lexeme, self.line_number)
        return Token(name, '', self.line_number)

    # Reconoce un literal entero; reporta error y retorna None si le siguen letras al número.
    def recognize_number(self) -> Token:
        lexeme = ""
        while self.current_char and self.current_char.isdigit():
            lexeme += self.current_char
            self.next_char()

        if self.current_char and self.current_char.isalpha():
            self.print_error(self.errors["NUM_ERROR"])
            while self.current_char and self.current_char.isalnum():
                self.next_char()
            return self.get_next_token()

        return Token('NUM', lexeme, self.line_number)

    # Imprime un error léxico indicando la línea donde ocurrió.
    def print_error(self, msg):
        print(f"Error Léxico en línea {self.line_number}: {msg}")

class ParserError(Exception):
    pass


# Analizador sintáctico descendente recursivo predictivo para mini-Pascal.
class Parser:
    def __init__(self, source_file):
        self.lex = LexiAnalyzer(source_file)
        self.lookahead = self.lex.get_next_token()
        self.scopeStack = []  
        self.tables = []    


    def get_table(self):
        return self.scopeStack[-1]  

    def unstack_table(self):
        if len(self.scopeStack) > 1:
            self.scopeStack.pop()


    def new_table(self, name):
        new_table = SymbolTable(name)
        self.scopeStack.append(new_table)
        self.tables.append(new_table)

    def _declare(self, tok, type_, attribute):
        entry = self.get_table().declare(tok.value, type_, attribute, tok.line_number)
        if entry is None:
            raise ParserError(f"Error semántico en línea {tok.line_number}: '{tok.value}' ya fue declarado en este ámbito")
        return entry

    def _lookup(self, tok):
        for table in reversed(self.scopeStack):
            entry = table.lookup(tok.value)
            if entry is not None:
                entry.lines_referenced.append(tok.line_number)
                return entry
        raise ParserError(f"Error semántico en línea {tok.line_number}: '{tok.value}' no fue declarado")

    # Imprime todas las tablas en el orden en que se abrieron los ámbitos.
    def print_symbol_tables(self, output=sys.stdout):
        output.write("\n===== Tablas de Símbolos =====\n")
        for table in self.tables:
            table.print_table(output)

    def _tipo_binario(self, op, izq, der, linea):
        if op in ('ADD', 'SUB', 'MUL', 'DIV'):
            esperado, resultado = 'INTEGER', 'INTEGER'
        elif op in ('AND', 'OR'):
            esperado, resultado = 'BOOLEAN', 'BOOLEAN'
        elif op in ('LT', 'LE', 'GT', 'GE'):
            esperado, resultado = 'INTEGER', 'BOOLEAN'
        else:  # EQ, NE: los dos lados del mismo tipo, cualquiera
            esperado, resultado = izq, 'BOOLEAN'
        if izq != esperado or der != esperado:
            self._error_semantico(linea, f"operador '{op}' aplicado a {izq} y {der}")
        return resultado

    def _error_semantico(self, linea, msg):
        raise ParserError(f"Error semántico en línea {linea}: {msg}")


    # Punto de entrada. Verifica el programa completo y que no queden tokens.
    def parse(self):
        self._statement()
        if self.lookahead is not None:
            self._error("Tokens inesperados después del final del programa")

    # --- Auxiliares ---

    def _peek_token(self):
        return self.lookahead

    def _peek(self):
        return self.lookahead.name if self.lookahead else None

    def _peek_value(self):
        return self.lookahead.value if self.lookahead else None


    def _line(self):
        return self.lookahead.line_number if self.lookahead else '?'

    def _match(self, expected):
        if self._peek() == expected:
            self.lookahead = self.lex.get_next_token()
        else:
            found = self._peek() or 'EOF'
            self._error(f"Se esperaba '{expected}', se encontró '{found}'")

    def _error(self, msg):
        raise ParserError(f"Error sintáctico en línea {self._line()}: {msg}")

    def _es_inicio_de_factor(self):
        return self._peek() in ('ID', 'NUM', 'TRUE', 'FALSE', 'PAR_ABRE', 'NOT')

    # --- Procedimientos de la gramática ---

    def _statement(self):
        self._match('PROGRAM')
        self.new_table("global")
        tok = self._ident()
        self._declare(tok, None, PROGRAM)
        self._match('PUNTO_COMA')
        self._bloque()
        self._match('PUNTO')

    def _bloque(self):
        p = self._peek()
        if p == 'VAR':
            self._match('VAR')
            self._sentencia_de_tipos()
            if self._peek() in ('FUNCTION', 'PROCEDURE'):
                self._lista_subprogramas()
            self._cuerpo()
        elif p in ('FUNCTION', 'PROCEDURE'):
            self._lista_subprogramas()
            self._cuerpo()
        elif p == 'BEGIN':
            self._cuerpo()
        else:
            self._error("Se esperaba 'var', 'function', 'procedure' o 'begin'")

    def _sentencia_de_tipos(self):
        self._declaracion_de_var()
        self._match('PUNTO_COMA')
        self._sentencia_de_tipos_prima()

    def _sentencia_de_tipos_prima(self):
        if self._peek() == 'ID':
            self._sentencia_de_tipos()

    def _declaracion_de_var(self):
        ids = []
        self._lista_var(ids)
        self._match('DOS_PUNTOS')
        tipo = self._tipo()
        for tok in ids:
            self._declare(tok, tipo, VARIABLE)

    def _ident(self):
        tok = self._peek_token()
        self._match('ID')
        return tok

    def _lista_var(self, toks):
        tok = self._ident()
        toks.append(tok)
        self._lista_var_prima(toks)

    def _lista_var_prima(self, toks):
        if self._peek() == 'COMA':
            self._match('COMA')
            self._lista_var(toks)

    def _tipo(self):
        p = self._peek()
        if p == 'INTEGER':
            self._match('INTEGER')
            return 'INTEGER'
        elif p == 'BOOLEAN':
            self._match('BOOLEAN')
            return 'BOOLEAN'
        else:
            self._error("Se esperaba 'integer' o 'boolean'")

    def _lista_subprogramas(self):
        self._subprograma()
        self._lista_subprogramas_prima()

    def _lista_subprogramas_prima(self):
        if self._peek() == 'PUNTO_COMA':
            self._match('PUNTO_COMA')
            # Admite el ';' final después del último subprograma (end; begin ...).
            if self._peek() in ('FUNCTION', 'PROCEDURE'):
                self._lista_subprogramas()

    def _subprograma(self):
        p = self._peek()
        if p == 'FUNCTION':
            self._funcion()
        elif p == 'PROCEDURE':
            self._procedimiento()
        else:
            self._error("Se esperaba 'function' o 'procedure'")

    def _funcion(self):
        self._match('FUNCTION')
        tok = self._ident()
        entry = self._declare(tok, None, FUNCTION)
        self.new_table(tok.value)
        self._funcion_prima(entry)
        self.unstack_table()

    def _funcion_prima(self, entry):
        p = self._peek()
        if p == 'PAR_ABRE':
            self._match('PAR_ABRE')
            self._param_formales(entry)
            self._match('PAR_CIERRA')
            self._match('DOS_PUNTOS')
            entry.type = self._tipo()
            self._match('PUNTO_COMA')
            self._bloque()
        elif p == 'DOS_PUNTOS':
            self._match('DOS_PUNTOS')
            entry.type = self._tipo()
            self._match('PUNTO_COMA')
            self._bloque()
        else:
            self._error("Error en declaración de función: se esperaba '(' o ':'")

    def _procedimiento(self):
        self._match('PROCEDURE')
        tok = self._ident()
        entry = self._declare(tok, None, PROCEDURE)
        self.new_table(tok.value)
        self._procedimiento_prima(entry)
        self.unstack_table()

    def _procedimiento_prima(self, entry):
        p = self._peek()
        if p == 'PAR_ABRE':
            self._match('PAR_ABRE')
            self._param_formales(entry)
            self._match('PAR_CIERRA')
            self._match('PUNTO_COMA')
            self._bloque()
        elif p == 'PUNTO_COMA':
            self._match('PUNTO_COMA')
            self._bloque()
        else:
            self._error("Error en declaración de procedimiento: se esperaba '(' o ';'")

    def _param_formales(self, entry):
        toks = []
        self._lista_ident(toks)
        self._match('DOS_PUNTOS')
        tipo = self._tipo()
        for tok in toks:
            self._declare(tok, tipo, PARAMETER)
            entry.params.append((tipo))
        self._param_formales_prima(entry)

    def _param_formales_prima(self, entry):
        if self._peek() == 'PUNTO_COMA':
            self._match('PUNTO_COMA')
            self._param_formales(entry)

    def _lista_ident(self, toks):
        toks.append(self._ident())
        self._lista_ident_prima(toks)

    def _lista_ident_prima(self, toks):
        if self._peek() == 'COMA':
            self._match('COMA')
            self._lista_ident(toks)

    def _cuerpo(self):
        self._match('BEGIN')
        self._lista_sentencias()
        self._match('END')

    def _lista_sentencias(self):
        self._sentencia()
        self._lista_sentencias_prima()

    def _lista_sentencias_prima(self):
        if self._peek() == 'PUNTO_COMA':
            self._match('PUNTO_COMA')
            self._lista_sentencias()

    def _sentencia(self):
        p = self._peek()
        # Sentencia vacía: admite un ';' antes de 'end'.
        if p == 'END':
            return
        if p == 'ID':
            self._lookup(self._ident())
            self._sentencia_prima()
        elif p == 'IF':
            self._alternativa()
        elif p == 'WHILE':
            self._repetitiva()
        elif p == 'BEGIN':
            self._cuerpo()
        elif p == 'READ':
            self._lectura()
        elif p == 'WRITE':
            self._escritura()
        else:
            self._error("Sentencia inválida")

    def _sentencia_prima(self):
        p = self._peek()
        if p == 'OP_ASIG':
            self._match('OP_ASIG')
            self._expresion()
        elif p == 'PAR_ABRE':
            self._match('PAR_ABRE')
            self._lista_expresion()
            self._match('PAR_CIERRA')

    def _alternativa(self):
        self._match('IF')
        self._expresion()
        self._match('THEN')
        self._sentencia()
        self._alternativa_prima()

    def _alternativa_prima(self):
        if self._peek() == 'ELSE':
            self._match('ELSE')
            self._sentencia()

    def _repetitiva(self):
        self._match('WHILE')
        self._expresion()
        self._match('DO')
        self._sentencia()

    def _lectura(self):
        self._match('READ')
        self._match('PAR_ABRE')
        self._lookup(self._ident())
        self._match('PAR_CIERRA')

    def _escritura(self):
        self._match('WRITE')
        self._match('PAR_ABRE')
        self._expresion()
        self._match('PAR_CIERRA')

    def _lista_expresion(self):
        self._expresion()
        self._lista_expresion_prima()

    def _lista_expresion_prima(self):
        if self._peek() == 'COMA':
            self._match('COMA')
            self._lista_expresion()

    def _expresion(self):
        izq = self._expresion_simple()
        return self._expresion_prima(izq)

    def _expresion_prima(self, izq):
        if self._peek() == 'OP_REL':
            op, linea = self._relacion()
            der = self._expresion_simple()
            return self._tipo_binario(op, izq, der, linea)
        return izq

    def _relacion(self):
        linea = self._line()
        if self._peek() == 'OP_REL':
            op = self._peek_value()
            self._match('OP_REL')
        else:
            self._error("Se esperaba un operador relacional")
        return op, linea

    def _expresion_simple(self):
        if self._peek() == 'OP_ARIT' and self._peek_value() in ('ADD', 'SUB'):
            op, linea = self._signo()
            tipo = self._termino()
            if tipo != 'INTEGER':
                self._error_semantico(linea, f"signo '{op}' aplicado a {tipo}")
            return self._expresion_simple_prima(tipo)
        elif self._es_inicio_de_factor():
            tipo = self._termino()
            return self._expresion_simple_prima(tipo)
        else:
            self._error("Error en expresión simple")

    def _expresion_simple_prima(self, izq):
        if self._peek() == 'OR' or (self._peek() == 'OP_ARIT' and self._peek_value() in ('ADD', 'SUB')):
            tipo = self._lista_expresion_simple(izq)
            return self._expresion_simple_prima(tipo)
        return izq

    def _lista_expresion_simple(self, izq):
        p = self._peek()
        if p == 'OR':
            linea = self._line()
            op = 'OR'
            self._match('OR')
        elif p == 'OP_ARIT' and self._peek_value() in ('ADD', 'SUB'):
            op, linea = self._signo()
        else:
            self._error("Error en operador de expresión")
        der = self._termino()
        return self._tipo_binario(op, izq, der, linea)

    def _signo(self):
        linea = self._line()
        if self._peek() == 'OP_ARIT' and self._peek_value() in ('ADD', 'SUB'):
            op = self._peek_value()
            self._match('OP_ARIT')
        else:
            self._error("Se esperaba un signo (+ o -)")
        return op, linea

    def _termino(self):
        izq = self._factor()
        return self._termino_prima(izq)

    def _termino_prima(self, izq):
        if self._peek() == 'AND' or (self._peek() == 'OP_ARIT' and self._peek_value() in ('MUL', 'DIV')):
            return self._lista_terminos(izq)
        return izq


    def _lista_terminos(self, izq):
        op, linea = self._operacion()
        der = self._factor()
        tipo = self._tipo_binario(op, izq, der, linea)
        return self._lista_terminos_prima(tipo)

    def _lista_terminos_prima(self, izq):
        if self._peek() == 'AND' or (self._peek() == 'OP_ARIT' and self._peek_value() in ('MUL', 'DIV')):
            return self._lista_terminos(izq)
        return izq

    def _operacion(self):
        linea = self._line()
        p = self._peek()
        if p == 'OP_ARIT' and self._peek_value() in ('MUL', 'DIV'):
            op = self._peek_value()
            self._match('OP_ARIT')
        elif p == 'AND':
            op = 'AND'
            self._match('AND')
        else:
            self._error("Se esperaba '*', '/' o 'and'")

        return op, linea

    def _factor(self):
        p = self._peek()
        if p == 'ID':
            tok = self._ident()
            entry = self._lookup(tok)
            self._llamada_funcion()         
            return entry.type
        elif p == 'NUM':
            self._numero()
            return 'INTEGER'
        elif p == 'TRUE':
            self._match('TRUE')
            return 'BOOLEAN'
        elif p == 'FALSE':
            self._match('FALSE')
            return 'BOOLEAN'
        elif p == 'PAR_ABRE':
            self._match('PAR_ABRE')
            tipo = self._expresion()         
            self._match('PAR_CIERRA')
            return tipo
        elif p == 'NOT':
            linea = self._line()
            self._match('NOT')
            tipo = self._factor()
            if tipo != 'BOOLEAN':
                self._error_semantico(linea, f"'not' aplicado a {tipo}")
            return 'BOOLEAN'
        else:
            self._error("Error en factor")


    def _llamada_funcion(self):
        if self._peek() == 'PAR_ABRE':
            self._match('PAR_ABRE')
            self._lista_expresion()
            self._match('PAR_CIERRA')

    

    def _numero(self):
        self._match('NUM')


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Utilizar el comando: analizador <archivo.pas>")
        sys.exit(1)

    try:
        parser = Parser(sys.argv[1])
        parser.parse()
        print("Análisis sintáctico exitoso")
        parser.print_symbol_tables()
    except ParserError as e:
        print(e)
        sys.exit(1)
