# Codificador Educativo de Instrucciones RISC-V

Proyecto Individual — CE-4301 Arquitectura de Computadores I  
Instituto Tecnológico de Costa Rica  
II Semestre 2026

## 1. Descripción

Este proyecto implementa un codificador educativo para un subconjunto de
instrucciones de la arquitectura RISC-V RV32I.

La herramienta recibe una única instrucción escrita en lenguaje ensamblador,
identifica su formato y genera su codificación de 32 bits.

Además de obtener la representación hexadecimal, la herramienta muestra
visualmente los campos que componen la instrucción y explica el significado
de cada uno.

El programa soporta los formatos:

- R
- I
- S
- B

El punto de entrada del programa es:

```bash
./run.sh "<instruccion>"
```

Por ejemplo:

```bash
./run.sh "add x5, x6, x7"
```

La salida siempre contiene una línea con el formato:

```text
HEX: 0xXXXXXXXX
```

que permite validar automáticamente la codificación.

---

# 2. Instrucciones soportadas

La herramienta implementa las siguientes 12 instrucciones del subconjunto
RV32I:

| Categoría | Formato | Instrucciones |
|---|---|---|
| Aritmética registro-registro | R | `add`, `sub`, `and`, `or` |
| Aritmética con inmediato | I | `addi`, `andi` |
| Carga desde memoria | I | `lw`, `lb` |
| Almacenamiento en memoria | S | `sw`, `sb` |
| Saltos condicionales | B | `beq`, `bne` |

---

# 3. Campos de codificación

Los valores de `opcode`, `funct3` y `funct7` se obtuvieron de la
especificación oficial de la ISA RISC-V.

| Instrucción | Formato | opcode | funct3 | funct7 |
|---|---|---|---|---|
| `add` | R | `0110011` | `000` | `0000000` |
| `sub` | R | `0110011` | `000` | `0100000` |
| `and` | R | `0110011` | `111` | `0000000` |
| `or` | R | `0110011` | `110` | `0000000` |
| `addi` | I | `0010011` | `000` | — |
| `andi` | I | `0010011` | `111` | — |
| `lw` | I | `0000011` | `010` | — |
| `lb` | I | `0000011` | `000` | — |
| `sw` | S | `0100011` | `010` | — |
| `sb` | S | `0100011` | `000` | — |
| `beq` | B | `1100011` | `000` | — |
| `bne` | B | `1100011` | `001` | — |

Fuente consultada:

> Waterman, Andrew y Krste Asanović. *The RISC-V Instruction Set Manual,
> Volume I: User-Level ISA*, Document Version 20191213.
> RISC-V Foundation, 2019.

---

# 4. Formatos implementados

## 4.1. Formato R

Las instrucciones tipo R realizan operaciones entre registros.

Su estructura es:

```text
31       25 24    20 19    15 14    12 11     7 6       0
┌──────────┬────────┬────────┬─────────┬────────┬─────────┐
│ funct7   │  rs2   │  rs1   │ funct3  │   rd   │ opcode  │
└──────────┴────────┴────────┴─────────┴────────┴─────────┘
```

Los campos `rs1` y `rs2` representan los registros fuente y `rd` representa
el registro destino.

---

## 4.2. Formato I

El formato I utiliza un inmediato de 12 bits con signo.

```text
31                 20 19    15 14    12 11     7 6       0
┌────────────────────┬────────┬─────────┬────────┬─────────┐
│     imm[11:0]      │  rs1   │ funct3  │   rd   │ opcode  │
└────────────────────┴────────┴─────────┴────────┴─────────┘
```

Se utiliza tanto para operaciones aritméticas con constantes (`addi`,
`andi`) como para cargas desde memoria (`lw`, `lb`).

El rango del inmediato es:

```text
-2048 <= imm <= 2047
```

Para instrucciones de carga se utiliza la sintaxis:

```text
lw rd, offset(rs1)
```

La dirección efectiva corresponde a:

```text
Regs[rs1] + offset
```

---

## 4.3. Formato S

El formato S se utiliza para almacenar información en memoria.

```text
31       25 24    20 19    15 14    12 11       7 6       0
┌──────────┬────────┬────────┬─────────┬───────────┬─────────┐
│imm[11:5] │  rs2   │  rs1   │ funct3  │ imm[4:0]  │ opcode  │
└──────────┴────────┴────────┴─────────┴───────────┴─────────┘
```

A diferencia del formato I, el inmediato de 12 bits se divide en dos partes:

```text
imm[11:5]
imm[4:0]
```

`rs2` contiene el dato que se desea almacenar y `rs1` funciona como registro
base para calcular la dirección de memoria.

---

## 4.4. Formato B

El formato B se utiliza para saltos condicionales.

```text
31 30       25 24   20 19   15 14 12 11    8 7 6       0
┌──┬──────────┬───────┬───────┬──────┬────────┬──┬─────────┐
│12│ imm[10:5]│  rs2  │  rs1  │funct3│imm[4:1]│11│ opcode  │
└──┴──────────┴───────┴───────┴──────┴────────┴──┴─────────┘
```

El desplazamiento se distribuye de la siguiente manera:

```text
imm[12]   -> bit 31
imm[10:5] -> bits 30:25
imm[4:1]  -> bits 11:8
imm[11]   -> bit 7
```

El bit `imm[0]` no se almacena porque los destinos de branch tienen
desplazamientos múltiplos de 2.

Las instrucciones implementadas son:

```text
beq rs1, rs2, offset
bne rs1, rs2, offset
```

El destino del salto corresponde a:

```text
PC + offset
```

---

# 5. Arquitectura de la implementación

La implementación principal se encuentra en `encoder_skeleton.py`.

El programa está dividido en funciones pequeñas para separar las diferentes
responsabilidades del codificador.

## `parse_register()`

Convierte registros escritos como:

```text
x0
x5
x31
```

a sus valores numéricos y verifica que se encuentren dentro del rango válido
de registros RISC-V:

```text
0 <= registro <= 31
```

Como existen 32 registros, cada campo de registro se representa utilizando
5 bits.

---

## `encode_immediate()`

Valida y convierte valores inmediatos con signo a su representación binaria
de una cantidad determinada de bits.

Esta función permite manejar correctamente inmediatos negativos mediante
complemento a 2.

Por ejemplo, para los formatos I y S se utilizan inmediatos de 12 bits.

---

## `parse_memory_operand()`

Procesa operandos de memoria como:

```text
8(x6)
-20(x8)
```

separándolos en:

```text
offset
registro base
```

Esta función se utiliza para instrucciones `lw`, `lb`, `sw` y `sb`.

---

## `encode_branch_immediate()`

Valida los desplazamientos utilizados por las instrucciones tipo B.

Además de comprobar el rango del inmediato, verifica que el desplazamiento
sea múltiplo de 2.

---

## `encode_instruction()`

Es la función principal de codificación.

Primero identifica el mnemónico y su formato y posteriormente obtiene los
operandos correspondientes.

Los diferentes campos se colocan dentro de la palabra de 32 bits utilizando
operaciones de desplazamiento (`<<`) y OR bit a bit (`|`).

Por ejemplo, para una instrucción tipo R:

```python
word = (
    (funct7 << 25)
    | (rs2 << 20)
    | (rs1 << 15)
    | (funct3 << 12)
    | (rd << 7)
    | opcode
)
```

Este procedimiento coloca cada campo directamente en las posiciones
establecidas por el formato RISC-V.

---

## `explain_instruction()`

Genera la salida educativa del programa.

Para cada instrucción muestra:

- formato identificado;
- rango de bits de cada campo;
- representación binaria de cada campo;
- registros utilizados;
- valor del inmediato cuando corresponda;
- significado de los campos;
- palabra binaria completa;
- codificación hexadecimal.

---

# 6. Ejemplos de ejecución

A continuación se presenta un ejemplo de cada formato implementado.

## 6.1. Formato R

Comando:

```bash
./run.sh "add x7, x20, x6"
```

Campos principales:

```text
Formato: R

funct7 [31:25] = 0000000
rs2    [24:20] = x6  = 00110
rs1    [19:15] = x20 = 10100
funct3 [14:12] = 000
rd     [11:7]  = x7  = 00111
opcode [6:0]   = 0110011

Binario completo:
00000000011010100000001110110011

HEX: 0x006a03b3
```

---

## 6.2. Formato I

Comando:

```bash
./run.sh "addi x5, x25, 2035"
```

Campos principales:

```text
Formato: I

imm    [31:20] = 011111110011 = 2035
rs1    [19:15] = x25 = 11001
funct3 [14:12] = 000
rd     [11:7]  = x5 = 00101
opcode [6:0]   = 0010011

Binario completo:
01111111001111001000001010010011

HEX: 0x7f3c8293
```

---

## 6.3. Formato S

Comando:

```bash
./run.sh "sw x31, -411(x23)"
```

Campos principales:

```text
Formato: S

imm[11:5] [31:25] = 1110011
rs2       [24:20] = x31 = 11111
rs1       [19:15] = x23 = 10111
funct3    [14:12] = 010
imm[4:0]  [11:7]  = 00101
opcode    [6:0]    = 0100011

Binario completo:
11100111111110111010001010100011

HEX: 0xe7fba2a3
```

---

## 6.4. Formato B

Comando:

```bash
./run.sh "beq x31, x23, 16"
```

Campos principales:

```text
Formato: B

imm[12]   [31]    = 0
imm[10:5] [30:25] = 000000
rs2       [24:20] = x23 = 10111
rs1       [19:15] = x31 = 11111
funct3    [14:12] = 000
imm[4:1]  [11:8]  = 1000
imm[11]   [7]     = 0
opcode    [6:0]    = 1100011

Binario completo:
00000001011111111000100001100011

HEX: 0x017f8863
```

# 7. Validación

Se construyeron 36 casos de prueba:

```text
12 instrucciones x 3 escenarios = 36 casos
```

Los casos se encuentran definidos en:

```text
validacion/casos_36.txt
```

Para cada instrucción se utilizaron escenarios distintos según el tipo de
operación.

| Tipo | Escenarios utilizados |
|---|---|
| R | caso normal, registro `x0`, registro `x31` |
| I aritmético | inmediato positivo, negativo y límite |
| Load | desplazamiento positivo, negativo y límite |
| Store | desplazamiento positivo, negativo y límite |
| Branch | desplazamiento positivo, negativo y cero |

La validación se automatizó mediante:

```text
validacion/validar_36.py
```

El script realiza dos codificaciones independientes para cada caso:

1. ejecuta la herramienta desarrollada mediante `./run.sh`;
2. ensambla la instrucción utilizando el toolchain GNU RISC-V;
3. obtiene la codificación oficial mediante `objdump`;
4. compara ambas representaciones hexadecimales.

La validación puede repetirse mediante:

```bash
python3 validacion/validar_36.py
```

Resultado obtenido:

```text
Casos ejecutados: 36
Coincidencias:     36
Errores:            0

RESULTADO FINAL: 36/36 CORRECTOS
```

El log completo con la instrucción, salida del modelo, salida de `objdump` y
resultado de cada comparación se encuentra en:

[validacion/resultados_36.txt](validacion/resultados_36.txt)

---

# 8. Estructura del repositorio

```text
.
├── encoder_skeleton.py
├── run.sh
├── vectores_ejemplo.txt
├── README.md
├── Documentacion.md
└── validacion/
    ├── casos_36.txt
    ├── validar_36.py
    └── resultados_36.txt
```

### `encoder_skeleton.py`

Implementación del codificador y de la salida educativa.

### `run.sh`

Punto de entrada requerido para ejecutar la herramienta.

### `vectores_ejemplo.txt`

Vectores de ejemplo proporcionados con el kit del proyecto.

### `validacion/casos_36.txt`

Casos propios utilizados para la validación contra el toolchain oficial.

### `validacion/validar_36.py`

Script que automatiza la comparación de los 36 casos.

### `validacion/resultados_36.txt`

Log con la evidencia completa de la validación.

---

# 9. Resultado

La herramienta implementa correctamente las 12 instrucciones solicitadas y
los cuatro formatos RISC-V requeridos.

La validación de los 36 casos contra el toolchain GNU RISC-V produjo una
coincidencia de:

```text
36 / 36 casos
```

incluyendo registros extremos, inmediatos positivos y negativos, valores
límite y desplazamientos de branch positivos, negativos y cero.