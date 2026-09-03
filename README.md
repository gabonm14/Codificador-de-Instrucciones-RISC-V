# Codificador Educativo de Instrucciones RISC-V

Proyecto Individual — CE-4301 Arquitectura de Computadores I  
Instituto Tecnológico de Costa Rica  
II Semestre 2026

---

# Instalación y preparación

## Requisitos de la herramienta

La implementación requiere:

- Linux o un entorno compatible con Bash;
- Python 3;
- Bash.

En Ubuntu se puede instalar Python mediante:

```bash
sudo apt update
sudo apt install python3
```

No se utilizan librerías externas de Python.

El script `run.sh` debe tener permiso de ejecución:

```bash
chmod +x run.sh
```

---

## Ejecución

La herramienta debe ejecutarse siempre mediante:

```bash
./run.sh "<instruccion>"
```

Ejemplos:

```bash
./run.sh "add x5, x6, x7"
./run.sh "addi x10, x1, -12"
./run.sh "lw x5, 8(x6)"
./run.sh "sw x8, -4(x2)"
./run.sh "beq x1, x2, 8"
```

No se requiere compilación previa.

La salida incluye una explicación visual de los campos de la instrucción y una línea con la codificación hexadecimal en el formato:

```text
HEX: 0xXXXXXXXX
```

Ejemplo:

```bash
./run.sh "add x7, x20, x6"
```

La salida final esperada incluye:

```text
HEX: 0x006a03b3
```

## Instrucciones soportadas

La herramienta soporta las siguientes 12 instrucciones de RV32I:

```text
add
sub
and
or
addi
andi
lw
lb
sw
sb
beq
bne
```


---

# Toolchain RISC-V utilizado

Para verificar las codificaciones se utilizó el toolchain GNU RISC-V
`riscv64-unknown-elf`.

En Ubuntu se instaló mediante:

```bash
sudo apt update
sudo apt install gcc-riscv64-unknown-elf binutils-riscv64-unknown-elf
```

Aunque el nombre del toolchain contiene `riscv64`, las pruebas se ensamblaron
específicamente para RV32I utilizando:

```bash
riscv64-unknown-elf-as -march=rv32i -mabi=ilp32
```

La codificación producida oficialmente se obtuvo mediante:

```bash
riscv64-unknown-elf-objdump -d -M numeric,no-aliases
```

---

Para información sobre la implementación, formatos utilizados y proceso de validación, consulte:

```text
documentacion.md
```

