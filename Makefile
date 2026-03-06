# Solarpunk Computing OS - Build System
# Usage:
#   make TARGET=pico2    - Build for Pi Pico 2
#   make TARGET=esp32    - Build for ESP32
#   make test            - Build and run host tests

TARGET ?= host

# Source files
KERNEL_SRC = kernel/kernel.cpp kernel/scheduler.cpp kernel/memory.cpp
DRIVER_SRC = drivers/uart.cpp drivers/gpio.cpp
NET_SRC    = net/net.cpp
WEB3_SRC   = web3/web3.cpp
CONT_SRC   = container/container.cpp
TERM_SRC   = terminal/terminal.cpp

ALL_CPP = $(KERNEL_SRC) $(DRIVER_SRC) $(NET_SRC) $(WEB3_SRC) $(CONT_SRC) $(TERM_SRC)

# Common flags
COMMON_FLAGS = -Wall -Wextra -Os -fno-exceptions -fno-rtti -ffreestanding -nostdlib
COMMON_FLAGS += -ffunction-sections -fdata-sections -std=c++17

ifeq ($(TARGET),pico2)
    # Pi Pico 2 (RP2350 - ARM Cortex-M33)
    CROSS = arm-none-eabi-
    CC = $(CROSS)gcc
    CXX = $(CROSS)g++
    AS = $(CROSS)as
    LD = $(CROSS)ld
    OBJCOPY = $(CROSS)objcopy
    SIZE = $(CROSS)size

    CXXFLAGS = $(COMMON_FLAGS) -mcpu=cortex-m33 -mthumb -mfloat-abi=soft
    ASFLAGS = -mcpu=cortex-m33 -mthumb
    LDFLAGS = -T linker/pico2.ld -nostdlib --gc-sections
    BOOT_SRC = boot/pico2/boot.S

    OUTPUT = solarpunk-pico2

else ifeq ($(TARGET),esp32)
    # ESP32 (Xtensa LX6)
    CROSS = xtensa-esp32-elf-
    CC = $(CROSS)gcc
    CXX = $(CROSS)g++
    AS = $(CROSS)as
    LD = $(CROSS)ld
    OBJCOPY = $(CROSS)objcopy
    SIZE = $(CROSS)size

    CXXFLAGS = $(COMMON_FLAGS)
    ASFLAGS =
    LDFLAGS = -T linker/esp32.ld -nostdlib --gc-sections
    BOOT_SRC = boot/esp32/boot.S

    OUTPUT = solarpunk-esp32

else
    # Host build (for testing)
    CC = gcc
    CXX = g++
    CXXFLAGS = -Wall -Wextra -O2 -std=c++17 -DPLATFORM_HOST=1
    LDFLAGS =
    BOOT_SRC =
    OUTPUT = solarpunk-host
endif

# Object files
BOOT_OBJ = $(BOOT_SRC:.S=.o)
CPP_OBJ = $(ALL_CPP:.cpp=.o)
ALL_OBJ = $(BOOT_OBJ) $(CPP_OBJ)

.PHONY: all clean test

all: $(OUTPUT).elf
	@echo "Build complete: $(OUTPUT).elf"
ifneq ($(TARGET),host)
	$(OBJCOPY) -O binary $(OUTPUT).elf $(OUTPUT).bin
	$(OBJCOPY) -O ihex $(OUTPUT).elf $(OUTPUT).hex
	$(SIZE) $(OUTPUT).elf
	@echo "Binary: $(OUTPUT).bin"
endif

$(OUTPUT).elf: $(ALL_OBJ)
ifneq ($(TARGET),host)
	$(LD) $(LDFLAGS) -o $@ $^
else
	$(CXX) $(CXXFLAGS) -o $@ $(CPP_OBJ)
endif

%.o: %.S
	$(AS) $(ASFLAGS) -o $@ $<

%.o: %.cpp
	$(CXX) $(CXXFLAGS) -c -o $@ $<

# Tests (host only)
TEST_SRC = test/test_memory.cpp test/test_web3.cpp test/test_container.cpp
TEST_FLAGS = -Wall -Wextra -O2 -std=c++17 -DPLATFORM_HOST=1

test: $(TEST_SRC)
	g++ $(TEST_FLAGS) -o test/test_runner \
		test/test_memory.cpp kernel/memory.cpp \
		test/test_web3.cpp web3/web3.cpp \
		test/test_container.cpp container/container.cpp \
		kernel/scheduler.cpp kernel/kernel.cpp \
		drivers/uart.cpp drivers/gpio.cpp \
		net/net.cpp terminal/terminal.cpp \
		test/test_main.cpp
	@echo "Running tests..."
	./test/test_runner

clean:
	find . -name "*.o" -delete
	rm -f solarpunk-*.elf solarpunk-*.bin solarpunk-*.hex
	rm -f test/test_runner
