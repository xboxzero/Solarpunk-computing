// Solarpunk Computing - ESP32 Boot
// Xtensa LX6 startup assembly

#include "xtensa/config/specreg.h"

    .section .entry.text, "ax"
    .global _start
    .type _start, @function
    .align 4

_start:
    // Disable interrupts
    rsil a0, 15

    // Set stack pointer
    movi a1, _stack_top

    // Clear .bss section
    movi a2, _bss_start
    movi a3, _bss_end
    movi a4, 0
_bss_loop:
    bge a2, a3, _bss_done
    s32i a4, a2, 0
    addi a2, a2, 4
    j _bss_loop
_bss_done:

    // Copy .data from flash to RAM
    movi a2, _data_start
    movi a3, _data_end
    movi a4, _data_load
_data_loop:
    bge a2, a3, _data_done
    l32i a5, a4, 0
    s32i a5, a2, 0
    addi a2, a2, 4
    addi a4, a4, 4
    j _data_loop
_data_done:

    // Configure CPU clock (240 MHz)
    call0 _clock_init_esp32

    // Initialize interrupt vectors
    movi a2, _vector_table
    wsr a2, vecbase

    // Enable interrupts
    rsil a0, 0

    // Jump to kernel
    call0 kernel_main

    // Should not return
_halt:
    waiti 0
    j _halt

// Clock init for ESP32 (PLL to 240 MHz)
    .type _clock_init_esp32, @function
_clock_init_esp32:
    entry a1, 16

    // RTC_CNTL_CLK_CONF_REG
    movi a2, 0x3FF48070
    l32i a3, a2, 0

    // Select PLL_CLK (CPU_CLK_SEL = 1)
    movi a4, 0x3
    slli a4, a4, 27
    or a3, a3, a4       // Not quite right but placeholder
    s32i a3, a2, 0

    // DPORT_CPU_PER_CONF_REG - set CPU freq to 240MHz
    movi a2, 0x3FF0003C
    movi a3, 2           // CPUPERIOD_SEL = 2 (240 MHz)
    s32i a3, a2, 0

    retw

// Vector table
    .section .vector.text, "ax"
    .global _vector_table
    .align 256
_vector_table:
    // Exception vectors (Xtensa window ABI)
    .org 0x00
    j _kernel_exception
    .org 0x180
    j _level2_int
    .org 0x1C0
    j _level3_int
    .org 0x200
    j _level4_int
    .org 0x240
    j _level5_int
    .org 0x280
    j _nmi_handler_esp32
    .org 0x300
    j _kernel_exception
    .org 0x340
    j _kernel_exception

_kernel_exception:
    // Save state and call C handler
    entry a1, 64
    mov a6, a1
    call4 fault_handler
    retw

_level2_int:
_level3_int:
_level4_int:
_level5_int:
    entry a1, 16
    call4 systick_handler
    retw

_nmi_handler_esp32:
    entry a1, 16
    retw
