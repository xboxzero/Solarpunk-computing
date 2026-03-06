/* Solarpunk Computing - Pi Pico 2 (RP2350) Linker Script */

MEMORY
{
    FLASH (rx)  : ORIGIN = 0x10000000, LENGTH = 4M
    RAM   (rwx) : ORIGIN = 0x20000000, LENGTH = 520K
}

_stack_top = ORIGIN(RAM) + LENGTH(RAM);

SECTIONS
{
    .vectors : {
        KEEP(*(.vectors))
    } > FLASH

    .text : {
        *(.text*)
        *(.rodata*)
        . = ALIGN(4);
        _data_load = LOADADDR(.data);
    } > FLASH

    .data : AT(_data_load) {
        _data_start = .;
        *(.data*)
        . = ALIGN(4);
        _data_end = .;
    } > RAM

    .bss (NOLOAD) : {
        _bss_start = .;
        *(.bss*)
        *(COMMON)
        . = ALIGN(4);
        _bss_end = .;
    } > RAM

    _heap_start = .;
    _heap_end = _stack_top - 4096;  /* Reserve 4K for main stack */
}
