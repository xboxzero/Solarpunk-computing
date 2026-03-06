/* Solarpunk Computing - ESP32 Linker Script */

MEMORY
{
    IROM (rx)    : ORIGIN = 0x400D0000, LENGTH = 3M
    DROM (r)     : ORIGIN = 0x3F400000, LENGTH = 1M
    IRAM (rwx)   : ORIGIN = 0x40080000, LENGTH = 128K
    DRAM (rw)    : ORIGIN = 0x3FFB0000, LENGTH = 176K
    RTC  (rw)    : ORIGIN = 0x50000000, LENGTH = 8K
}

_stack_top = ORIGIN(DRAM) + LENGTH(DRAM);

SECTIONS
{
    .entry.text : {
        *(.entry.text)
    } > IRAM

    .vector.text : {
        . = ALIGN(256);
        *(.vector.text)
    } > IRAM

    .text : {
        *(.text*)
        . = ALIGN(4);
    } > IROM

    .rodata : {
        *(.rodata*)
        . = ALIGN(4);
        _data_load = .;
    } > DROM

    .data : {
        _data_start = .;
        *(.data*)
        . = ALIGN(4);
        _data_end = .;
    } > DRAM

    .bss (NOLOAD) : {
        _bss_start = .;
        *(.bss*)
        *(COMMON)
        . = ALIGN(4);
        _bss_end = .;
    } > DRAM

    _heap_start = .;
    _heap_end = _stack_top - 4096;
}
