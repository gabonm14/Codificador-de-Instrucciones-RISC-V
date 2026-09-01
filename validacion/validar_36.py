#!/usr/bin/env python3

from pathlib import Path
from datetime import datetime
import subprocess
import tempfile
import re
import sys


# ---------------------------------------------------------
# Rutas del proyecto
# ---------------------------------------------------------

VALIDACION_DIR = Path(__file__).resolve().parent
ROOT_DIR = VALIDACION_DIR.parent

CASOS_FILE = VALIDACION_DIR / "casos_36.txt"
RESULTADOS_FILE = VALIDACION_DIR / "resultados_36.txt"

RUN_SH = ROOT_DIR / "run.sh"

RISCV_AS = "riscv64-unknown-elf-as"
RISCV_LD = "riscv64-unknown-elf-ld"
RISCV_OBJDUMP = "riscv64-unknown-elf-objdump"


# ---------------------------------------------------------
# Ejecutar comandos externos
# ---------------------------------------------------------

def ejecutar_comando(comando, cwd=None):
    """
    Ejecuta un comando y retorna su salida estándar.

    Si el comando falla, genera una excepción mostrando
    también el error producido.
    """

    try:
        resultado = subprocess.run(
            comando,
            cwd=cwd,
            text=True,
            capture_output=True
        )

    except FileNotFoundError:
        raise RuntimeError(
            f"No se encontró el comando: {comando[0]}"
        )

    if resultado.returncode != 0:
        raise RuntimeError(
            f"Falló el comando:\n"
            f"{' '.join(str(x) for x in comando)}\n\n"
            f"{resultado.stderr}"
        )

    return resultado.stdout


# ---------------------------------------------------------
# Leer los 36 casos
# ---------------------------------------------------------

def leer_casos():
    """
    Lee casos_36.txt.

    Formato esperado:
    ID | escenario | instruccion
    """

    if not CASOS_FILE.exists():
        raise FileNotFoundError(
            f"No existe el archivo {CASOS_FILE}"
        )

    casos = []

    with open(CASOS_FILE, "r", encoding="utf-8") as archivo:

        for numero_linea, linea in enumerate(archivo, start=1):

            linea = linea.strip()

            # Ignorar líneas vacías y comentarios.
            if not linea or linea.startswith("#"):
                continue

            partes = [parte.strip() for parte in linea.split("|", 2)]

            if len(partes) != 3:
                raise ValueError(
                    f"Línea {numero_linea} inválida en casos_36.txt:\n"
                    f"{linea}"
                )

            identificador, escenario, instruccion = partes

            casos.append({
                "id": identificador,
                "escenario": escenario,
                "instruccion": instruccion
            })

    if len(casos) != 36:
        raise ValueError(
            f"Se esperaban 36 casos, pero se encontraron {len(casos)}."
        )

    return casos


# ---------------------------------------------------------
# Detectar branches
# ---------------------------------------------------------

def parsear_branch(instruccion):
    """
    Si la instrucción es beq o bne, retorna:

    (mnemonico, rs1, rs2, desplazamiento)

    Si no es un branch, retorna None.
    """

    patron = (
        r"^\s*(beq|bne)\s+"
        r"(x\d+)\s*,\s*"
        r"(x\d+)\s*,\s*"
        r"(-?\d+)\s*$"
    )

    coincidencia = re.match(
        patron,
        instruccion,
        re.IGNORECASE
    )

    if coincidencia is None:
        return None

    mnemonico = coincidencia.group(1).lower()
    rs1 = coincidencia.group(2).lower()
    rs2 = coincidencia.group(3).lower()
    desplazamiento = int(coincidencia.group(4))

    return mnemonico, rs1, rs2, desplazamiento


# ---------------------------------------------------------
# Crear ensamblador para el toolchain oficial
# ---------------------------------------------------------

def generar_asm(instruccion):
    """
    Genera el código ensamblador utilizado por GNU as.

    Retorna:
        codigo_asm
        direccion_de_la_instruccion_a_validar

    Para instrucciones B se utilizan etiquetas para garantizar
    que el desplazamiento sea exactamente el indicado.
    """

    branch = parsear_branch(instruccion)

    # -----------------------------------------------------
    # Instrucción que NO es un branch
    # -----------------------------------------------------

    if branch is None:

        codigo = f"""
.text
.option norvc
.globl _start

_start:
    {instruccion}
"""

        # La instrucción que comprobamos está en la dirección 0.
        return codigo, 0

    # -----------------------------------------------------
    # Branch
    # -----------------------------------------------------

    mnemonico, rs1, rs2, desplazamiento = branch

    # Nuestros casos utilizan múltiplos de 4 porque RV32I
    # sin la extensión C usa instrucciones de 4 bytes.
    if desplazamiento % 4 != 0:
        raise ValueError(
            f"Este script de validación requiere desplazamientos "
            f"múltiplos de 4 para los branches: {instruccion}"
        )

    branch_con_label = (
        f"{mnemonico} {rs1}, {rs2}, destino"
    )

    # -----------------------------------------------------
    # Salto positivo
    # -----------------------------------------------------

    if desplazamiento > 0:

        # Ejemplo:
        #
        # beq ... destino    <- dirección 0
        # nop                <- dirección 4
        # nop                <- dirección 8
        # nop                <- dirección 12
        # destino:           <- dirección 16
        #
        # desplazamiento = +16

        cantidad_nops = (desplazamiento // 4) - 1

        nops = "\n".join(
            "    nop"
            for _ in range(cantidad_nops)
        )

        codigo = f"""
.text
.option norvc
.globl _start

_start:
    {branch_con_label}
{nops}
destino:
    nop
"""

        return codigo, 0

    # -----------------------------------------------------
    # Salto negativo
    # -----------------------------------------------------

    elif desplazamiento < 0:

        # Ejemplo para -16:
        #
        # destino:           <- dirección 0
        # nop                <- 0
        # nop                <- 4
        # nop                <- 8
        # nop                <- 12
        # beq ... destino    <- dirección 16
        #
        # destino - PC = 0 - 16 = -16

        cantidad_nops = abs(desplazamiento) // 4

        nops = "\n".join(
            "    nop"
            for _ in range(cantidad_nops)
        )

        codigo = f"""
.text
.option norvc
.globl _start

_start:
destino:
{nops}
    {branch_con_label}
"""

        # La instrucción branch se encuentra en esta dirección.
        direccion_branch = abs(desplazamiento)

        return codigo, direccion_branch

    # -----------------------------------------------------
    # Desplazamiento cero
    # -----------------------------------------------------

    else:

        # La etiqueta y el branch están en la misma dirección.
        #
        # destino:
        #     beq ..., destino
        #
        # destino - PC = 0

        codigo = f"""
.text
.option norvc
.globl _start

_start:
destino:
    {branch_con_label}
"""

        return codigo, 0


# ---------------------------------------------------------
# Ejecutar nuestro encoder
# ---------------------------------------------------------

def obtener_hex_modelo(instruccion):
    """
    Ejecuta:

        ./run.sh "instruccion"

    y extrae la línea:

        HEX: 0xXXXXXXXX
    """

    salida = ejecutar_comando(
        [str(RUN_SH), instruccion],
        cwd=ROOT_DIR
    )

    coincidencia = re.search(
        r"^HEX:\s*(0x[0-9a-fA-F]{8})\s*$",
        salida,
        re.MULTILINE
    )

    if coincidencia is None:
        raise RuntimeError(
            f"No se encontró la línea HEX en la salida de:\n"
            f"{instruccion}\n\n"
            f"{salida}"
        )

    return coincidencia.group(1).lower()


# ---------------------------------------------------------
# Obtener hexadecimal oficial
# ---------------------------------------------------------

def obtener_hex_oficial(instruccion):
    """
    Genera un archivo .s temporal, lo ensambla y enlaza
    como RV32I y obtiene la codificación mediante objdump.
    """

    codigo_asm, direccion_instruccion = generar_asm(instruccion)

    # Usamos un directorio temporal para no llenar el
    # repositorio con .s, .o y .elf de cada prueba.
    with tempfile.TemporaryDirectory() as directorio:

        directorio = Path(directorio)

        archivo_s = directorio / "caso.s"
        archivo_o = directorio / "caso.o"
        archivo_elf = directorio / "caso.elf"

        archivo_s.write_text(
            codigo_asm,
            encoding="utf-8"
        )

        # -------------------------------------------------
        # Ensamblar como RV32I
        # -------------------------------------------------

        ejecutar_comando([
            RISCV_AS,
            "-march=rv32i",
            "-mabi=ilp32",
            "-o",
            str(archivo_o),
            str(archivo_s)
        ])

        # -------------------------------------------------
        # Enlazar
        #
        # Esto es especialmente útil para los branches:
        # garantiza que las direcciones de las etiquetas
        # queden completamente resueltas.
        # -------------------------------------------------

        ejecutar_comando([
            RISCV_LD,
            "-m",
            "elf32lriscv",
            "-Ttext=0x0",
            "-e",
            "_start",
            "-o",
            str(archivo_elf),
            str(archivo_o)
        ])

        # -------------------------------------------------
        # Desensamblar
        # -------------------------------------------------

        salida_objdump = ejecutar_comando([
            RISCV_OBJDUMP,
            "-d",
            "-M",
            "numeric,no-aliases",
            str(archivo_elf)
        ])

        # Buscar todas las instrucciones mostradas por objdump.
        patron = re.compile(
            r"^\s*([0-9a-fA-F]+):\s+"
            r"([0-9a-fA-F]{8})\s+",
            re.MULTILINE
        )

        for coincidencia in patron.finditer(salida_objdump):

            direccion = int(coincidencia.group(1), 16)

            if direccion == direccion_instruccion:

                hexadecimal = coincidencia.group(2).lower()

                return f"0x{hexadecimal}"

        raise RuntimeError(
            f"No se encontró en objdump la instrucción ubicada "
            f"en 0x{direccion_instruccion:x}.\n\n"
            f"{salida_objdump}"
        )


# ---------------------------------------------------------
# Programa principal
# ---------------------------------------------------------

def main():

    try:
        casos = leer_casos()

    except Exception as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2

    log = []

    log.append("VALIDACIÓN CODIFICADOR RISC-V")
    log.append("=" * 55)
    log.append(
        f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )
    log.append("")
    log.append(
        "Comparación: modelo propio vs. GNU RISC-V objdump"
    )
    log.append("=" * 55)
    log.append("")

    coincidencias = 0
    errores = 0

    for numero, caso in enumerate(casos, start=1):

        identificador = caso["id"]
        escenario = caso["escenario"]
        instruccion = caso["instruccion"]

        print(
            f"[{numero:02d}/36] {identificador}: "
            f"{instruccion}",
            end=" ... "
        )

        try:
            hex_modelo = obtener_hex_modelo(instruccion)
            hex_oficial = obtener_hex_oficial(instruccion)

            if hex_modelo == hex_oficial:
                resultado = "COINCIDE"
                coincidencias += 1
                print("OK")

            else:
                resultado = "NO COINCIDE"
                errores += 1
                print("ERROR")

            log.append(f"[{identificador}] {escenario}")
            log.append(f"Instrucción: {instruccion}")
            log.append(f"Modelo:      {hex_modelo}")
            log.append(f"Objdump:     {hex_oficial}")
            log.append(f"Resultado:   {resultado}")
            log.append("")

        except Exception as error:

            errores += 1

            print("ERROR")

            log.append(f"[{identificador}] {escenario}")
            log.append(f"Instrucción: {instruccion}")
            log.append("Resultado:   ERROR DE EJECUCIÓN")
            log.append(f"Detalle:     {error}")
            log.append("")

    # -----------------------------------------------------
    # Resumen
    # -----------------------------------------------------

    log.append("=" * 55)
    log.append("RESUMEN")
    log.append("=" * 55)
    log.append(f"Casos ejecutados: {len(casos)}")
    log.append(f"Coincidencias:     {coincidencias}")
    log.append(f"Errores:            {errores}")
    log.append("")

    if coincidencias == len(casos):
        log.append(
            f"RESULTADO FINAL: {coincidencias}/{len(casos)} CORRECTOS"
        )
    else:
        log.append(
            f"RESULTADO FINAL: {coincidencias}/{len(casos)} CORRECTOS"
        )

    texto_log = "\n".join(log) + "\n"

    RESULTADOS_FILE.write_text(
        texto_log,
        encoding="utf-8"
    )

    print()
    print("=" * 55)
    print(
        f"Resultado: {coincidencias}/{len(casos)} casos correctos"
    )
    print(
        f"Evidencia guardada en: "
        f"{RESULTADOS_FILE.relative_to(ROOT_DIR)}"
    )
    print("=" * 55)

    if coincidencias == len(casos):
        return 0

    return 1


if __name__ == "__main__":
    sys.exit(main())