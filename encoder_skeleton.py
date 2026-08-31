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
