#!/usr/bin/env python3
"""
Esqueleto del Codificador Educativo de Instrucciones RISC-V.
CE4301 Arquitectura de Computadores I — Proyecto Individual — 2026-II

Este esqueleto ya implementa el contrato de línea de comandos y de salida
requerido por la especificación. Usted debe completar las dos funciones
marcadas con TODO; puede modificar el resto del archivo si lo necesita,
siempre que se preserve el contrato de invocación y la línea "HEX: 0x...".

No es obligatorio usar este esqueleto ni Python: puede implementar su
propia herramienta desde cero, en el lenguaje que prefiera, siempre que
respete el mismo contrato (ver especificación, sección "Modo de operación").
"""
import sys

SOPORTADAS = ["add", "sub", "and", "or", "addi", "andi",
              "lw", "lb", "sw", "sb", "beq", "bne"]


INSTRUCCIONES = {
    "add": {
        "formato": "R",
        "opcode": 0b0110011,
        "funct3": 0b000,
        "funct7": 0b0000000
    },

    "sub": {
        "formato": "R",
        "opcode": 0b0110011,
        "funct3": 0b000,
        "funct7": 0b0100000
    },

    "and": {
        "formato": "R",
        "opcode": 0b0110011,
        "funct3": 0b111,
        "funct7": 0b0000000
    },

    "or": {
        "formato": "R",
        "opcode": 0b0110011,
        "funct3": 0b110,
        "funct7": 0b0000000
    },

    "addi": {
        "formato": "I",
        "tipo": "aritmetica",
        "opcode": 0b0010011,
        "funct3": 0b000
    },

    "andi": {
        "formato": "I",
        "tipo": "aritmetica",
        "opcode": 0b0010011,
        "funct3": 0b111
    },

    "lw": {
        "formato": "I",
        "tipo": "carga",
        "opcode": 0b0000011,
        "funct3": 0b010
    },

    "lb": {
        "formato": "I",
        "tipo": "carga",
        "opcode": 0b0000011,
        "funct3": 0b000
    },

    "sw": {
        "formato": "S",
        "opcode": 0b0100011,
        "funct3": 0b010
    },

    "sb": {
        "formato": "S",
        "opcode": 0b0100011,
        "funct3": 0b000
    },

    "beq": {
        "formato": "B",
        "opcode": 0b1100011,
        "funct3": 0b000
    },

    "bne": {
        "formato": "B",
        "opcode": 0b1100011,
        "funct3": 0b001
    }
    
 
}

def parse_register(registro: str) -> int:
    """
    Convierte un registro escrito como 'x5' en el número 5.
    Solo acepta registros desde x0 hasta x31.
    """

    registro = registro.strip().lower()

    if not registro.startswith("x"):
        raise ValueError(f"Registro inválido: {registro}")

    try:
        numero = int(registro[1:])
    except ValueError:
        raise ValueError(f"Registro inválido: {registro}")

    if numero < 0 or numero > 31:
        raise ValueError(f"Registro fuera de rango: {registro}")

    return numero

def parse_memory_operand(operand: str):
    """
    Convierte un operando como '8(x6)' en:
    offset = 8
    base = x6
    """

    operand = operand.replace(" ", "")

    if "(" not in operand or not operand.endswith(")"):
        raise ValueError(
            f"Operando de memoria inválido: {operand}"
        )

    offset_text, registro_text = operand.split("(", 1)

    registro_text = registro_text[:-1]

    try:
        offset = int(offset_text)
    except ValueError:
        raise ValueError(
            f"Desplazamiento inválido: {offset_text}"
        )

    registro = parse_register(registro_text)

    return offset, registro


def encode_immediate(value: int, bits: int) -> int:
    """
    Verifica que un inmediato con signo pueda representarse
    con la cantidad indicada de bits y retorna su representación
    binaria como entero positivo.
    """

    minimo = -(1 << (bits - 1))
    maximo = (1 << (bits - 1)) - 1

    if value < minimo or value > maximo:
        raise ValueError(
            f"Inmediato fuera de rango para {bits} bits: {value}"
        )

    return value & ((1 << bits) - 1)

def encode_branch_immediate(value: int) -> int:
    """
    Valida y codifica el desplazamiento de una instrucción tipo B.

    El desplazamiento debe ser par porque el bit 0 del inmediato
    no se almacena en la instrucción.
    """

    if value % 2 != 0:
        raise ValueError(
            f"El desplazamiento de un branch debe ser múltiplo de 2: {value}"
        )

    return encode_immediate(value, 13)



def encode_instruction(instruction: str) -> int:
    """
    Recibe una instrucción RISC-V como texto y retorna
    su codificación de 32 bits como entero.
    """

    partes = instruction.replace(",", " ").split()

    if len(partes) == 0:
        raise ValueError("La instrucción está vacía")

    # La primera palabra es el mnemónico.
    mnemonico = partes[0].lower()

    if mnemonico not in SOPORTADAS:
        raise ValueError(f"Instrucción no soportada: {mnemonico}")


    if mnemonico not in INSTRUCCIONES:
        raise NotImplementedError(
            f"La instrucción {mnemonico} todavía no ha sido implementada"
        )

    info = INSTRUCCIONES[mnemonico]

    if info["formato"] == "R":

        if len(partes) != 4:
            raise ValueError(
                f"Formato inválido para {mnemonico}. "
                f"Use: {mnemonico} rd, rs1, rs2"
            )

        rd = parse_register(partes[1])
        rs1 = parse_register(partes[2])
        rs2 = parse_register(partes[3])

        opcode = info["opcode"]
        funct3 = info["funct3"]
        funct7 = info["funct7"]

        word = (
            (funct7 << 25)
            | (rs2 << 20)
            | (rs1 << 15)
            | (funct3 << 12)
            | (rd << 7)
            | opcode
        )

        return word

    if info["formato"] == "I":

            opcode = info["opcode"]
            funct3 = info["funct3"]

            # I aritmético: addi rd, rs1, imm
            if info["tipo"] == "aritmetica":

                if len(partes) != 4:
                    raise ValueError(
                        f"Formato inválido para {mnemonico}. "
                        f"Use: {mnemonico} rd, rs1, imm"
                    )

                rd = parse_register(partes[1])
                rs1 = parse_register(partes[2])

                try:
                    imm = int(partes[3])
                except ValueError:
                    raise ValueError(
                        f"Inmediato inválido: {partes[3]}"
                    )

            # I de carga: lw rd, offset(rs1)
            elif info["tipo"] == "carga":

                if len(partes) < 3:
                    raise ValueError(
                        f"Formato inválido para {mnemonico}. "
                        f"Use: {mnemonico} rd, offset(rs1)"
                    )

                rd = parse_register(partes[1])

                # Esto permite incluso escribir:
                # lw x5, 8( x6 )
                operando_memoria = "".join(partes[2:])

                imm, rs1 = parse_memory_operand(operando_memoria)

            imm_bits = encode_immediate(imm, 12)

            word = (
                (imm_bits << 20)
                | (rs1 << 15)
                | (funct3 << 12)
                | (rd << 7)
                | opcode
            )

            return word

    if info["formato"] == "S":

        if len(partes) < 3:
            raise ValueError(
                f"Formato inválido para {mnemonico}. "
                f"Use: {mnemonico} rs2, offset(rs1)"
            )

        # En un store, el primer registro es rs2.
        rs2 = parse_register(partes[1])

        # Permite formatos como:
        # sw x8, -4(x2)
        # sw x8, -4( x2 )
        operando_memoria = "".join(partes[2:])

        imm, rs1 = parse_memory_operand(operando_memoria)

        opcode = info["opcode"]
        funct3 = info["funct3"]

        # Representación del inmediato en complemento a 2 de 12 bits.
        imm_bits = encode_immediate(imm, 12)

        # Separar los 12 bits del inmediato.
        imm_4_0 = imm_bits & 0b11111
        imm_11_5 = (imm_bits >> 5) & 0b1111111

        word = (
            (imm_11_5 << 25)
            | (rs2 << 20)
            | (rs1 << 15)
            | (funct3 << 12)
            | (imm_4_0 << 7)
            | opcode
        )

        return word

    if info["formato"] == "B":

        if len(partes) != 4:
            raise ValueError(
                f"Formato inválido para {mnemonico}. "
                f"Use: {mnemonico} rs1, rs2, offset"
            )

        rs1 = parse_register(partes[1])
        rs2 = parse_register(partes[2])

        try:
            imm = int(partes[3])
        except ValueError:
            raise ValueError(
                f"Desplazamiento inválido: {partes[3]}"
            )

        opcode = info["opcode"]
        funct3 = info["funct3"]

        imm_bits = encode_branch_immediate(imm)

        # Extraer los diferentes pedazos del inmediato.
        imm_12 = (imm_bits >> 12) & 0b1
        imm_10_5 = (imm_bits >> 5) & 0b111111
        imm_4_1 = (imm_bits >> 1) & 0b1111
        imm_11 = (imm_bits >> 11) & 0b1

        word = (
            (imm_12 << 31)
            | (imm_10_5 << 25)
            | (rs2 << 20)
            | (rs1 << 15)
            | (funct3 << 12)
            | (imm_4_1 << 8)
            | (imm_11 << 7)
            | opcode
        )

        return word

    
    raise NotImplementedError(
        f"Formato {info['formato']} todavía no implementado"
    )

def explain_instruction(instruction: str, word: int) -> str:
    """
    Muestra los campos de la instrucción de forma visual.
    """

    partes = instruction.replace(",", " ").split()
    mnemonico = partes[0].lower()

    info = INSTRUCCIONES.get(mnemonico)

    if info is None:
        raise NotImplementedError(
            f"Explicación no implementada para {mnemonico}"
        )

    if info["formato"] == "R":

        rd = parse_register(partes[1])
        rs1 = parse_register(partes[2])
        rs2 = parse_register(partes[3])

        funct3 = info["funct3"]
        funct7 = info["funct7"]
        opcode = info["opcode"]

        binario_completo = f"{word:032b}"

        explicacion = f"""

        
Instrucción: {instruction}
Formato: R

Bits:
31      25 24   20 19   15 14 12 11    7 6       0
{funct7:07b}   {rs2:05b}   {rs1:05b}   {funct3:03b}   {rd:05b}   {opcode:07b}
funct7    rs2     rs1    funct3    rd     opcode

Campos:
funct7 [31:25] = {funct7:07b}
rs2    [24:20] = x{rs2} = {rs2:05b}
rs1    [19:15] = x{rs1} = {rs1:05b}
funct3 [14:12] = {funct3:03b}
rd     [11:7]  = x{rd} = {rd:05b}
opcode [6:0]   = {opcode:07b}

Binario completo:
{binario_completo}
"""

        explicacion += f"""

Rol de los campos:
funct7: complementa a funct3 para identificar la operación exacta.
rs2:    segundo registro fuente (x{rs2}).
rs1:    primer registro fuente (x{rs1}).
funct3: identifica la operación dentro del opcode.
rd:     registro destino donde se guarda el resultado (x{rd}).
opcode: identifica la categoría principal de la instrucción.
"""

        return explicacion.strip()


    if info["formato"] == "I":

            opcode = info["opcode"]
            funct3 = info["funct3"]

            if info["tipo"] == "aritmetica":

                rd = parse_register(partes[1])
                rs1 = parse_register(partes[2])
                imm = int(partes[3])

                significado_imm = (
                    f"constante con signo utilizada por {mnemonico}"
                )

            elif info["tipo"] == "carga":

                rd = parse_register(partes[1])

                operando_memoria = "".join(partes[2:])
                imm, rs1 = parse_memory_operand(operando_memoria)

                significado_imm = (
                    f"desplazamiento respecto al registro base x{rs1}"
                )

            imm_bits = encode_immediate(imm, 12)

            binario_completo = f"{word:032b}"

            explicacion = f"""
    Instrucción: {instruction}
    Formato: I

    Bits:
    31             20 19   15 14 12 11    7 6       0
    {imm_bits:012b}   {rs1:05b}   {funct3:03b}   {rd:05b}   {opcode:07b}
    imm[11:0]       rs1    funct3    rd     opcode

    Campos:
    imm    [31:20] = {imm_bits:012b} = {imm}
    rs1    [19:15] = x{rs1} = {rs1:05b}
    funct3 [14:12] = {funct3:03b}
    rd     [11:7]  = x{rd} = {rd:05b}
    opcode [6:0]   = {opcode:07b}

    Rol de los campos:
    imm:    {significado_imm}.
    rs1:    registro fuente o registro base (x{rs1}).
    funct3: identifica la operación específica dentro del opcode.
    rd:     registro destino donde se almacena el resultado (x{rd}).
    opcode: identifica la categoría principal de la instrucción.

    Binario completo:
    {binario_completo}
    """

            return explicacion.strip()

    if info["formato"] == "S":

        rs2 = parse_register(partes[1])

        operando_memoria = "".join(partes[2:])
        imm, rs1 = parse_memory_operand(operando_memoria)

        opcode = info["opcode"]
        funct3 = info["funct3"]

        imm_bits = encode_immediate(imm, 12)

        imm_4_0 = imm_bits & 0b11111
        imm_11_5 = (imm_bits >> 5) & 0b1111111

        binario_completo = f"{word:032b}"

        explicacion = f"""
Instrucción: {instruction}
Formato: S

Bits:
31      25 24   20 19   15 14 12 11    7 6       0
{imm_11_5:07b}   {rs2:05b}   {rs1:05b}   {funct3:03b}   {imm_4_0:05b}   {opcode:07b}
imm[11:5]  rs2     rs1    funct3 imm[4:0] opcode

Campos:
imm[11:5] [31:25] = {imm_11_5:07b}
rs2       [24:20] = x{rs2} = {rs2:05b}
rs1       [19:15] = x{rs1} = {rs1:05b}
funct3    [14:12] = {funct3:03b}
imm[4:0]  [11:7]  = {imm_4_0:05b}
opcode    [6:0]   = {opcode:07b}

Inmediato completo:
{imm_bits:012b} = {imm}

Rol de los campos:
imm:    desplazamiento con signo respecto al registro base x{rs1}.
rs2:    registro fuente que contiene el dato que se almacena en memoria (x{rs2}).
rs1:    registro base utilizado para calcular la dirección de memoria (x{rs1}).
funct3: indica el tamaño del dato que se almacena.
opcode: identifica la instrucción como una operación de almacenamiento.

Dirección efectiva:
Regs[x{rs1}] + ({imm})

Binario completo:
{binario_completo}
"""

        return explicacion.strip()

    if info["formato"] == "B":

        rs1 = parse_register(partes[1])
        rs2 = parse_register(partes[2])

        try:
            imm = int(partes[3])
        except ValueError:
            raise ValueError(
                f"Desplazamiento inválido: {partes[3]}"
            )

        opcode = info["opcode"]
        funct3 = info["funct3"]

        imm_bits = encode_branch_immediate(imm)

        imm_12 = (imm_bits >> 12) & 0b1
        imm_10_5 = (imm_bits >> 5) & 0b111111
        imm_4_1 = (imm_bits >> 1) & 0b1111
        imm_11 = (imm_bits >> 11) & 0b1

        binario_completo = f"{word:032b}"

        if mnemonico == "beq":
            condicion = f"Regs[x{rs1}] == Regs[x{rs2}]"
        else:
            condicion = f"Regs[x{rs1}] != Regs[x{rs2}]"

        explicacion = f"""
Instrucción: {instruction}
Formato: B

Bits:
31 30    25 24   20 19   15 14 12 11   8 7 6       0
{imm_12:01b}  {imm_10_5:06b}   {rs2:05b}   {rs1:05b}   {funct3:03b}   {imm_4_1:04b}  {imm_11:01b} {opcode:07b}
12  10:5      rs2     rs1    funct3 4:1   11 opcode

Campos:
imm[12]   [31]    = {imm_12:b}
imm[10:5] [30:25] = {imm_10_5:06b}
rs2       [24:20] = x{rs2} = {rs2:05b}
rs1       [19:15] = x{rs1} = {rs1:05b}
funct3    [14:12] = {funct3:03b}
imm[4:1]  [11:8]  = {imm_4_1:04b}
imm[11]   [7]     = {imm_11:b}
opcode    [6:0]   = {opcode:07b}

Inmediato:
{imm_bits:013b} = {imm}

Rol de los campos:
rs1:    primer registro utilizado en la comparación (x{rs1}).
rs2:    segundo registro utilizado en la comparación (x{rs2}).
funct3: identifica la condición específica del branch.
imm:    desplazamiento con signo relativo al PC.
opcode: identifica la instrucción como un branch condicional.

Condición:
{condicion}

Si la condición se cumple:
PC = PC + ({imm})

El bit imm[0] no se almacena porque el desplazamiento es múltiplo de 2.

Binario completo:
{binario_completo}
"""

        return explicacion.strip()


    raise NotImplementedError(
        f"Explicación del formato {info['formato']} todavía no implementada"
    )








def main():
    if len(sys.argv) != 2:
        print(f'Uso: {sys.argv[0]} "<instruccion>"', file=sys.stderr)
        print(f'Ejemplo: {sys.argv[0]} "add x5, x6, x7"', file=sys.stderr)
        sys.exit(2)

    instruction = sys.argv[1]
    word = encode_instruction(instruction) & 0xFFFFFFFF

    print(explain_instruction(instruction, word))

    # No modificar el formato de la siguiente línea: la especificación la
    # requiere, literal, para permitir la validación automática.
    print(f"HEX: 0x{word:08x}")


if __name__ == "__main__":
    main()


