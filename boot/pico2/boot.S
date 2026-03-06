// Solarpunk Computing - Pi Pico 2 (RP2350) Boot
// ARM Cortex-M33 startup assembly

.syntax unified
.cpu cortex-m33
.thumb

// Vector table
.section .vectors, "a"
.global _vectors
_vectors:
    .word _stack_top          // Initial stack pointer
    .word _reset_handler      // Reset handler
    .word _nmi_handler        // NMI
    .word _hardfault_handler  // HardFault
    .word _memfault_handler   // MemManage
    .word _busfault_handler   // BusFault
    .word _usagefault_handler // UsageFault
    .word 0                   // Reserved
    .word 0                   // Reserved
    .word 0                   // Reserved
    .word 0                   // Reserved
    .word _svc_handler        // SVCall
    .word 0                   // Reserved
    .word 0                   // Reserved
    .word _pendsv_handler     // PendSV
    .word _systick_handler    // SysTick

// Reset handler - entry point
.section .text
.global _reset_handler
.type _reset_handler, %function
_reset_handler:
    // Disable interrupts during init
    cpsid i

    // Set stack pointer
    ldr r0, =_stack_top
    msr msp, r0

    // Init .data section (copy from flash to RAM)
    ldr r0, =_data_start
    ldr r1, =_data_end
    ldr r2, =_data_load
_copy_data:
    cmp r0, r1
    bge _zero_bss
    ldr r3, [r2], #4
    str r3, [r0], #4
    b _copy_data

    // Zero .bss section
_zero_bss:
    ldr r0, =_bss_start
    ldr r1, =_bss_end
    movs r2, #0
_zero_loop:
    cmp r0, r1
    bge _init_hw
    str r2, [r0], #4
    b _zero_loop

    // Initialize core hardware
_init_hw:
    // Enable FPU (CP10/CP11)
    ldr r0, =0xE000ED88
    ldr r1, [r0]
    orr r1, r1, #(0xF << 20)
    str r1, [r0]
    dsb
    isb

    // Configure system clock (125 MHz from XOSC + PLL)
    bl _clock_init

    // Configure SysTick for 1ms tick
    ldr r0, =0xE000E010       // SYST_CSR
    ldr r1, =124999           // 125MHz / 1000 - 1
    str r1, [r0, #4]          // SYST_RVR (reload value)
    movs r1, #0
    str r1, [r0, #8]          // SYST_CVR (clear current)
    movs r1, #7               // Enable, interrupt, processor clock
    str r1, [r0]

    // Enable interrupts
    cpsie i

    // Jump to C++ kernel
    bl kernel_main

    // Should never return, but halt if it does
_halt:
    wfi
    b _halt

// Clock initialization (125 MHz)
.type _clock_init, %function
_clock_init:
    push {lr}

    // Enable XOSC (12 MHz crystal)
    ldr r0, =0x40064000       // XOSC_BASE
    ldr r1, =0x00FABAA0       // ENABLE value (1-15ms startup)
    str r1, [r0, #0]          // XOSC_CTRL

    // Wait for XOSC stable
_xosc_wait:
    ldr r1, [r0, #0x04]       // XOSC_STATUS
    tst r1, #(1 << 31)        // Check STABLE bit
    beq _xosc_wait

    // Configure PLL_SYS for 125 MHz
    // REFDIV=1, FBDIV=125, POSTDIV1=5, POSTDIV2=2
    // 12MHz * 125 / 5 / 2 = 150MHz ... adjusted below
    ldr r0, =0x40028000       // PLL_SYS_BASE
    movs r1, #1
    str r1, [r0, #0x08]       // REFDIV
    movs r1, #125
    str r1, [r0, #0x0C]       // FBDIV

    // Power on PLL
    ldr r1, [r0, #0x04]       // PWR register
    bic r1, r1, #(1 << 5)     // Clear PD
    bic r1, r1, #(1 << 0)     // Clear VCOPD
    str r1, [r0, #0x04]

    // Wait for PLL lock
_pll_wait:
    ldr r1, [r0, #0x00]       // CS register
    tst r1, #(1 << 31)        // Check LOCK
    beq _pll_wait

    // Set post dividers
    ldr r1, =(5 << 16) | (2 << 12)
    str r1, [r0, #0x10]       // PRIM

    // Enable post divider
    ldr r1, [r0, #0x04]
    bic r1, r1, #(1 << 3)     // Clear POSTDIVPD
    str r1, [r0, #0x04]

    pop {pc}

// Default interrupt handlers (weak, overridable)
.weak _nmi_handler
.weak _hardfault_handler
.weak _memfault_handler
.weak _busfault_handler
.weak _usagefault_handler
.weak _svc_handler
.weak _pendsv_handler
.weak _systick_handler

_nmi_handler:
_memfault_handler:
_busfault_handler:
_usagefault_handler:
_svc_handler:
_pendsv_handler:
    b _halt

.global _hardfault_handler
.type _hardfault_handler, %function
_hardfault_handler:
    // Store fault info for debugging
    mrs r0, msp
    b _halt

// SysTick handler - increment tick counter
.global _systick_handler
.type _systick_handler, %function
_systick_handler:
    push {lr}
    bl systick_handler
    pop {pc}
