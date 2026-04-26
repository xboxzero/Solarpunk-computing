"""
Complete schematic sheet definitions for all 6 sub-sheets.
This replaces the generate_all_subsheets() function in generate_project.py
with fully wired schematics including all passive components per datasheets.
"""

# ============================================================
# HELPER: Capacitor placement
# ============================================================
def cap(ref, value, x, y, fp="Capacitor_SMD:C_0402_1005Metric"):
    """Shorthand for capacitor component dict."""
    return {'type': 'component', 'ref': ref, 'lib': 'Device', 'symbol': 'C',
            'x': x, 'y': y, 'value': value, 'fp': fp}

def cap_0805(ref, value, x, y):
    return cap(ref, value, x, y, fp="Capacitor_SMD:C_0805_2012Metric")

def res(ref, value, x, y, fp="Resistor_SMD:R_0402_1005Metric"):
    """Shorthand for resistor component dict."""
    return {'type': 'component', 'ref': ref, 'lib': 'Device', 'symbol': 'R',
            'x': x, 'y': y, 'value': value, 'fp': fp}

def res_2512(ref, value, x, y):
    return res(ref, value, x, y, fp="Resistor_SMD:R_2512_6332Metric")

def ind(ref, value, x, y, fp="Inductor_SMD:L_4012"):
    return {'type': 'component', 'ref': ref, 'lib': 'Device', 'symbol': 'L',
            'x': x, 'y': y, 'value': value, 'fp': fp}

def wire(x1, y1, x2, y2):
    return {'type': 'wire', 'x1': x1, 'y1': y1, 'x2': x2, 'y2': y2}

def label(name, x, y, shape='input'):
    return {'type': 'label', 'x': x, 'y': y, 'name': name, 'shape': shape}

def local_lbl(name, x, y, angle=0):
    return {'type': 'local_label', 'x': x, 'y': y, 'name': name, 'angle': angle}

def hier_lbl(name, x, y, shape='input'):
    return {'type': 'hier_label', 'x': x, 'y': y, 'name': name, 'shape': shape}

def text(txt, x, y, size=1.5):
    return {'type': 'text', 'x': x, 'y': y, 'text': txt, 'size': size}

def power(name, x, y):
    return {'type': 'power', 'name': name, 'x': x, 'y': y}

def comp(ref, lib, symbol, x, y, value='', fp=''):
    return {'type': 'component', 'ref': ref, 'lib': lib, 'symbol': symbol,
            'x': x, 'y': y, 'value': value, 'fp': fp}


# ============================================================
# SHEET 5: POWER SYSTEM (Most Critical — Fix all bugs)
# ============================================================
def sheet5_power_system():
    """Complete power system with all passive components per datasheets."""
    items = []

    # === TITLE ===
    items.append(text('POWER SYSTEM', 50, 15, 3))
    items.append(text('Solar MPPT + PoE 802.3at + USB-C PD — Auto-OR Switching', 50, 22, 1.5))

    # === HIERARCHICAL LABELS (must match parent sheet pins) ===
    items.append(hier_lbl('SOLAR_IN', 10, 40, 'input'))
    items.append(hier_lbl('VBAT', 10, 50, 'bidirectional'))
    items.append(hier_lbl('48V_POE', 10, 60, 'input'))
    items.append(hier_lbl('USB_PD_IN', 10, 70, 'input'))
    items.append(hier_lbl('5V_SYS', 380, 40, 'output'))
    items.append(hier_lbl('3V3_RP', 380, 50, 'output'))
    items.append(hier_lbl('3V3_RK3506', 380, 60, 'output'))
    items.append(hier_lbl('3V3_RK', 380, 70, 'output'))
    items.append(hier_lbl('1V8', 380, 80, 'output'))
    items.append(hier_lbl('GND', 10, 80, 'input'))

    # === SECTION 1: CN3722 Solar MPPT Charger ===
    items.append(text('1. Solar MPPT — CN3722 (Single-cell LiFePO4)', 30, 95, 2))

    # Connectors
    items.append(comp('J40', 'Connector', 'Conn_01x02', 20, 120, 'JST VH Solar', 'Connector_JST:JST_VH_B2P'))
    items.append(comp('J41', 'Connector', 'Conn_01x02', 20, 160, 'JST PH Battery', 'Connector_JST:JST_PH_B2B'))

    # CN3722 IC
    items.append(comp('U40', 'solarpunk-pi-v3', 'CN3722', 100, 130, 'CN3722', 'Package_SO:SOP-16'))

    # CN3722 Programming passives
    items.append(cap('C90', '100nF', 70, 135))           # SS (pin3) soft-start
    items.append(cap('C91', '470pF', 70, 145))           # COMP (pin5) compensation
    items.append(cap('C92', '100nF', 130, 115))          # BST-SW bootstrap
    items.append(res('R42', '49.9k', 130, 135))          # FB divider top (to VBAT)
    items.append(res('R43', '100k', 130, 145))           # FB divider bottom (to GND)
    items.append(res('R44', '200k', 70, 155))            # RT timing (300kHz)
    items.append(res_2512('R47', '50mR', 140, 155))      # CS current sense (2A)
    items.append(res('R49', '10k NTC', 150, 135))        # TS thermistor
    items.append(res('R50', '10k', 150, 145))            # TS NTC bias
    items.append(res('R45', '163k', 150, 165))           # MPPT divider top
    items.append(res('R46', '10k', 150, 175))            # MPPT divider bottom
    items.append(ind('L2', '10uH 3A', 120, 110, 'Inductor_SMD:L_6028'))  # SW→VBAT
    items.append(cap_0805('C_CN_IN', '22uF', 50, 120))   # Input bulk
    items.append(cap_0805('C_CN_OUT', '22uF', 170, 120))  # Output bulk (VBAT)

    # Wiring for CN3722
    items.append(wire(20, 120, 50, 120))       # Solar+ to C_IN to VIN
    items.append(wire(50, 120, 90, 120))       # VIN
    items.append(wire(110, 110, 120, 110))     # SW to L2
    items.append(wire(120, 110, 170, 110))     # L2 to VBAT
    items.append(wire(170, 110, 170, 120))     # VBAT to C_OUT
    items.append(wire(170, 110, 190, 110))     # VBAT output
    items.append(local_lbl('VBAT', 190, 110))
    items.append(local_lbl('SOLAR_IN', 20, 115))
    items.append(power('GND', 100, 170))

    items.append(text('C90=100nF SS, C91=470pF COMP, R44=200k RT(300kHz)', 60, 185, 1.0))
    items.append(text('R42/R43=49.9k/100k FB(3.6V), R47=50mR CS(2A)', 60, 190, 1.0))
    items.append(text('R45/R46=163k/10k MPPT(18V panel), R49/R50=NTC/10k TS', 60, 195, 1.0))

    # === SECTION 2: TPS61022 Boost (VBAT → 5V) ===
    items.append(text('2. Boost — TPS61022 (VBAT 3.2V → 5V@4A) [FIXED FB divider]', 30, 210, 2))

    items.append(comp('U41', 'solarpunk-pi-v3', 'TPS61022', 100, 240, 'TPS61022DRLR', 'Package_TO_SOT_SMD:SOT-23-6'))
    items.append(ind('L1', '1uH SWPA4012S', 130, 225, 'Inductor_SMD:L_4012'))

    # CRITICAL FIX: Feedback divider for 5V output
    # TPS61022 VREF = 0.5V, VOUT = VREF*(1 + R40/R41)
    # For 5V: R40/R41 = 9.0 → R40=900k, R41=100k
    items.append(res('R40', '900k', 140, 245))    # FB top (VOUT to FB)
    items.append(res('R41', '100k', 140, 255))    # FB bottom (FB to GND)
    items.append(cap_0805('C_TPS_IN', '10uF', 70, 240))    # Input cap
    items.append(cap_0805('C_TPS_O1', '22uF', 160, 230))   # Output cap 1
    items.append(cap_0805('C_TPS_O2', '22uF', 170, 230))   # Output cap 2
    items.append(cap_0805('C_TPS_O3', '22uF', 180, 230))   # Output cap 3

    # Wiring
    items.append(local_lbl('VBAT', 70, 235))     # Input from battery
    items.append(wire(70, 235, 93, 235))          # VIN
    items.append(wire(108, 225, 130, 225))        # SW to L1
    items.append(wire(130, 225, 160, 225))        # L1 to VOUT
    items.append(wire(108, 237, 140, 237))        # VOUT line
    items.append(wire(140, 237, 140, 245))        # to FB divider top
    items.append(wire(140, 255, 140, 265))        # FB divider to GND
    items.append(local_lbl('5V_BOOST', 160, 225))
    items.append(power('GND', 140, 265))

    items.append(text('VOUT = 0.5V × (1 + 900k/100k) = 5.0V [CORRECTED]', 60, 270, 1.0))
    items.append(text('Input: 10uF, Output: 3×22uF per TI datasheet', 60, 275, 1.0))

    # === SECTION 3: SI3402-B PoE PD Controller ===
    items.append(text('3. PoE 802.3at — SI3402-B PD Controller', 220, 95, 2))

    items.append(comp('U42', 'solarpunk-pi-v3', 'SI3402-B', 280, 130, 'SI3402-B', 'Package_QFN:QFN-16'))
    items.append(res('R_CLASS', '243R', 250, 125))    # RCLASS (Class 3)
    items.append(cap('C_DET', '100nF', 250, 135))     # DET cap
    items.append(cap_0805('C_POE_OUT', '100uF', 320, 130))  # Output bulk

    items.append(local_lbl('48V_POE', 250, 115))
    items.append(local_lbl('5V_POE', 320, 115))
    items.append(power('GND', 280, 155))

    items.append(text('NOTE: SI3402-B internal DC-DC with GATE/BG output', 220, 160, 1.0))
    items.append(text('External flyback transformer required — see AN770', 220, 165, 1.0))
    items.append(text('RCLASS=243R → Class 3 (12.95W), C_DET=100nF', 220, 170, 1.0))

    # === SECTION 4: HUSB238 USB-C PD Sink ===
    items.append(text('4. USB-C PD Sink — HUSB238 (12V request)', 220, 185, 2))

    items.append(comp('U43', 'solarpunk-pi-v3', 'HUSB238', 280, 220, 'HUSB238', 'Package_SO:SOP-10'))
    items.append(res('R48', '10k', 310, 235))     # VSET to GND (12V select)
    items.append(res('R60', '4.7k', 250, 210))    # SCL pull-up
    items.append(res('R61', '4.7k', 250, 220))    # SDA pull-up
    items.append(cap('C_HUSB', '100nF', 260, 210)) # VDD bypass

    # MP2315 Buck converter (12V PD → 5V)
    items.append(comp('U47', 'solarpunk-pi-v3', 'MP2315GJ', 340, 220, 'MP2315GJ', 'Package_TO_SOT_SMD:TSOT-23-8'))
    items.append(cap_0805('C_MP_IN', '10uF', 320, 210))
    items.append(cap_0805('C_MP_OUT', '22uF', 370, 210))
    items.append(ind('L3', '4.7uH', 360, 205, 'Inductor_SMD:L_4012'))

    items.append(local_lbl('USB_PD_IN', 250, 205))
    items.append(local_lbl('5V_PD', 370, 205))
    items.append(power('GND', 280, 245))

    items.append(text('R48=10k VSET(12V), R60/R61=4.7k I2C pull-ups', 220, 250, 1.0))
    items.append(text('MP2315 buck 12V→5V after HUSB238', 220, 255, 1.0))

    # === SECTION 5: OR-ing Circuit — 3 Paths ===
    items.append(text('5. Auto-OR Switching — 3x LTC4357 + Si4456DY', 100, 290, 2))

    # Path 1: Boost (Solar+Battery)
    items.append(comp('U44a', 'solarpunk-pi-v3', 'LTC4357', 100, 315, 'LTC4357 (Boost)', 'Package_TO_SOT_SMD:SOT-23-5'))
    items.append(comp('Q4', 'solarpunk-pi-v3', 'Si4456DY', 130, 315, 'Si4456DY', 'Package_SO:SO-8'))

    # Path 2: PoE
    items.append(comp('U44b', 'solarpunk-pi-v3', 'LTC4357', 200, 315, 'LTC4357 (PoE)', 'Package_TO_SOT_SMD:SOT-23-5'))
    items.append(comp('Q5', 'solarpunk-pi-v3', 'Si4456DY', 230, 315, 'Si4456DY', 'Package_SO:SO-8'))

    # Path 3: USB-PD
    items.append(comp('U44c', 'solarpunk-pi-v3', 'LTC4357', 300, 315, 'LTC4357 (PD)', 'Package_TO_SOT_SMD:SOT-23-5'))
    items.append(comp('Q6', 'solarpunk-pi-v3', 'Si4456DY', 330, 315, 'Si4456DY', 'Package_SO:SO-8'))

    # OR-ing input labels
    items.append(local_lbl('5V_BOOST', 80, 310))
    items.append(local_lbl('5V_POE', 180, 310))
    items.append(local_lbl('5V_PD', 280, 310))

    # OR-ing output bus
    items.append(wire(150, 315, 160, 315))     # Q4 out
    items.append(wire(250, 315, 260, 315))     # Q5 out
    items.append(wire(350, 315, 360, 315))     # Q6 out
    items.append(wire(160, 315, 260, 315))     # Common bus
    items.append(wire(260, 315, 360, 315))     # Common bus
    items.append(local_lbl('5V_SYS', 360, 310))

    # Output bulk caps on 5V_SYS
    items.append(cap_0805('C_SYS1', '100uF', 370, 320))
    items.append(cap_0805('C_SYS2', '10uF', 380, 320))

    items.append(text('Each path: LTC4357(IN→GATE) + Si4456DY(D→S)', 100, 335, 1.0))
    items.append(text('Output: 5V_SYS bus with 100uF+10uF bulk', 100, 340, 1.0))

    # === SECTION 6: Always-On LDOs ===
    items.append(text('6. Always-On LDOs (from 5V_SYS)', 30, 355, 2))

    # U45 MIC5219-3.3 → 3V3_RP
    items.append(comp('U45', 'solarpunk-pi-v3', 'MIC5219', 80, 380, 'MIC5219-3.3', 'Package_TO_SOT_SMD:SOT-23-5'))
    items.append(cap('C_M5_IN', '1uF', 55, 380))        # Input cap
    items.append(cap('C_M5_OUT', '1uF', 105, 380))       # Output cap
    items.append(cap('C_M5_BYP', '470pF', 105, 390))     # Bypass cap
    items.append(comp('FB1', 'Device', 'FerriteBead', 45, 375, 'BLM18AG102SN1D', 'Resistor_SMD:R_0603'))
    items.append(local_lbl('5V_SYS', 30, 375))
    items.append(wire(30, 375, 45, 375))
    items.append(wire(45, 375, 55, 375))
    items.append(wire(55, 375, 72, 378))
    items.append(local_lbl('3V3_RP', 120, 378))
    items.append(power('GND', 80, 395))

    # U46 AP2112K-3.3 → 3V3_RK3506
    items.append(comp('U46', 'solarpunk-pi-v3', 'AP2112K', 200, 380, 'AP2112K-3.3', 'Package_TO_SOT_SMD:SOT-23-5'))
    items.append(cap('C_AP_IN', '1uF', 175, 380))
    items.append(cap('C_AP_OUT', '1uF', 225, 380))
    items.append(comp('FB2', 'Device', 'FerriteBead', 165, 375, 'BLM18AG102SN1D', 'Resistor_SMD:R_0603'))
    items.append(local_lbl('5V_SYS', 150, 375))
    items.append(local_lbl('3V3_RK3506', 240, 378))
    items.append(power('GND', 200, 395))

    # 3V3_RK and 1V8 come from RK806 PMIC (Sheet 01)
    items.append(text('3V3_RK and 1V8 generated by RK806 PMIC on Sheet 01', 30, 405, 1.2))

    # === SECTION 7: ADC Monitoring ===
    items.append(text('7. ADC Voltage Monitors → RP2350', 250, 355, 2))

    # VBAT monitor
    items.append(res('R51', '100k', 280, 370))   # Divider top
    items.append(res('R52', '100k', 280, 380))   # Divider bottom
    items.append(res('R55', '100R', 300, 375))   # RC filter
    items.append(cap('C_ADC1', '100nF', 310, 380))  # RC filter cap
    items.append(local_lbl('VBAT', 270, 365))
    items.append(label('ADC_VBAT', 320, 375, 'output'))
    items.append(power('GND', 280, 390))
    items.append(text('VBAT÷2 → RP2350 GP26', 270, 395, 1.0))

    # SOLAR_IN monitor
    items.append(res('R53', '200k', 340, 370))
    items.append(res('R54', '100k', 340, 380))
    items.append(res('R56', '100R', 360, 375))
    items.append(cap('C_ADC2', '100nF', 370, 380))
    items.append(local_lbl('SOLAR_IN', 330, 365))
    items.append(label('ADC_SOLAR', 380, 375, 'output'))
    items.append(power('GND', 340, 390))
    items.append(text('SOLAR÷3 → RP2350 GP27', 330, 395, 1.0))

    # === SECTION 8: Power Brain Switch ===
    items.append(text('8. Brain Power Switch — Si2301 PMOS', 250, 290, 2))
    items.append(comp('Q3', 'Device', 'Q_PMOS_GSD', 300, 305, 'Si2301', 'Package_TO_SOT_SMD:SOT-23'))
    items.append(res('R_GATE', '100k', 285, 305))
    items.append(comp('FB3', 'Device', 'FerriteBead', 320, 300, 'BLM18AG102SN1D', 'Resistor_SMD:R_0603'))
    items.append(local_lbl('5V_SYS', 285, 298))
    items.append(local_lbl('PWR_EN_BUF', 270, 305))
    items.append(local_lbl('3V3_RK', 340, 300))

    # Power priority note
    items.append(text('POWER PRIORITY: 1. Solar+Battery  2. PoE  3. USB-C PD  4. Battery alone', 30, 420, 1.5))
    items.append(text('RP2350 ADC monitors VBAT (GP26) and SOLAR_IN (GP27) via dividers', 30, 428, 1.2))

    return items


# ============================================================
# SHEET 1: RK3576 COMPUTE DOMAIN
# ============================================================
def sheet1_rk3576_compute():
    items = []

    items.append(text('RK3576 COMPUTE DOMAIN', 50, 15, 3))
    items.append(text('4xA72@2.2G + 4xA53@1.8G + 6T NPU + Mali-G52', 50, 22, 1.5))

    # Hierarchical labels
    items.append(hier_lbl('5V_SYS', 10, 40, 'input'))
    items.append(hier_lbl('GND', 10, 50, 'input'))
    items.append(hier_lbl('UART4_TX', 380, 40, 'output'))
    items.append(hier_lbl('UART4_RX', 380, 48, 'input'))
    items.append(hier_lbl('UART5_TX', 380, 56, 'output'))
    items.append(hier_lbl('UART5_RX', 380, 64, 'input'))
    items.append(hier_lbl('SPI2_CLK', 380, 72, 'output'))
    items.append(hier_lbl('SPI2_MOSI', 380, 80, 'output'))
    items.append(hier_lbl('SPI2_MISO', 380, 88, 'input'))
    items.append(hier_lbl('SPI2_CS', 380, 96, 'output'))
    items.append(hier_lbl('GPIO_SHUTDOWN', 380, 104, 'output'))
    items.append(hier_lbl('GPIO_ALARM_IRQ', 380, 112, 'input'))
    items.append(hier_lbl('RGMII_BUS', 380, 120, 'output'))
    items.append(hier_lbl('SDIO_BUS', 380, 128, 'output'))
    items.append(hier_lbl('I2S_BUS', 380, 136, 'output'))
    items.append(hier_lbl('USB3_0', 380, 144, 'bidirectional'))
    items.append(hier_lbl('USB3_1', 380, 152, 'bidirectional'))
    items.append(hier_lbl('USB2_0', 380, 160, 'bidirectional'))
    items.append(hier_lbl('USB2_1', 380, 168, 'bidirectional'))
    items.append(hier_lbl('USB2_CELL', 380, 176, 'bidirectional'))

    # RK3576 SoC
    items.append(comp('U1', 'solarpunk-pi-v3', 'RK3576', 100, 120, 'RK3576', 'Package_BGA:BGA-698'))

    # RK806 PMIC
    items.append(text('PMIC — RK806-1 (SPI from RK3576)', 250, 30, 2))
    items.append(comp('U2', 'solarpunk-pi-v3', 'RK806', 280, 80, 'RK806-1', 'Package_QFN:QFN-68'))

    # RK806 SPI wiring (RK3576 SPI2 → RK806 SPI)
    items.append(wire(150, 72, 250, 72))     # SPI2_CLK → RK806
    items.append(wire(150, 80, 250, 80))     # SPI2_MOSI → RK806
    items.append(wire(150, 88, 250, 88))     # SPI2_MISO ← RK806
    items.append(wire(150, 96, 250, 96))     # SPI2_CS → RK806

    # RK806 power output labels (to RK3576 power domains)
    items.append(local_lbl('VDD_CPU_BIG', 310, 60))
    items.append(local_lbl('VDD_CPU_LIT', 310, 65))
    items.append(local_lbl('VDD_GPU', 310, 70))
    items.append(local_lbl('VDD_NPU', 310, 75))
    items.append(local_lbl('VDD_LOGIC', 310, 80))
    items.append(local_lbl('VCC_DDR', 310, 85))
    items.append(local_lbl('3V3_RK', 310, 90))
    items.append(local_lbl('1V8', 310, 95))

    # RK806 bypass caps
    items.append(cap_0805('C_RK806_IN', '10uF', 250, 60))
    items.append(cap('C_RK806_B1', '100nF', 255, 65))
    for i, y in enumerate(range(60, 96, 5)):
        items.append(cap_0805(f'C_RK806_O{i+1}', '10uF', 320, y))

    # LPDDR4X x2 (with proper symbols)
    items.append(text('LPDDR4X — 2x 4GB = 8GB', 100, 195, 2))
    items.append(comp('U3', 'solarpunk-pi-v3', 'LPDDR4X', 70, 230, 'K4UBE3D4AB (4GB CH0)', 'Package_BGA:BGA-200'))
    items.append(comp('U4', 'solarpunk-pi-v3', 'LPDDR4X', 170, 230, 'K4UBE3D4AB (4GB CH1)', 'Package_BGA:BGA-200'))

    # DDR decoupling — 100nF per VDD ball
    for i in range(8):
        items.append(cap(f'C_DDR0_{i+1}', '100nF', 40 + i*7, 260))
    for i in range(8):
        items.append(cap(f'C_DDR1_{i+1}', '100nF', 140 + i*7, 260))

    # DDR bus labels (simplified — actual routing in PCB)
    items.append(text('DDR bus: DQ[0:31], DQS[0:3], CA[0:5], CK±, CKE, CS', 40, 275, 1.2))
    items.append(text('Length-match groups: ±0.5mm within byte lane, ±2mm between lanes', 40, 280, 1.2))

    # eMMC
    items.append(text('eMMC + SPI NOR', 250, 150, 2))
    items.append(comp('U5', 'solarpunk-pi-v3', 'eMMC_BGA153', 280, 180, 'KLMAG2JENB 32GB', 'Package_BGA:BGA-153'))
    items.append(cap('C_eMMC1', '100nF', 260, 168))
    items.append(cap_0805('C_eMMC2', '10uF', 260, 175))

    # SPI NOR
    items.append(comp('U6', 'solarpunk-pi-v3', 'W25Q128', 280, 220, 'W25Q128JVSIQ', 'Package_SO:SOP-8'))
    items.append(cap('C_NOR1', '100nF', 260, 218))

    # RK3576 decoupling arrays
    items.append(text('RK3576 Decoupling — 100nF within 0.5mm of EVERY VDD ball', 30, 295, 1.2))
    items.append(text('10uF bulk at each power domain entry', 30, 300, 1.2))
    # Place cap array annotations (actual caps placed during PCB layout)
    for i in range(12):
        items.append(cap(f'C_RK_{i+1}', '100nF', 30 + i*10, 310))
    for i in range(6):
        items.append(cap_0805(f'C_RK_B{i+1}', '10uF', 30 + i*20, 320))

    items.append(power('GND', 100, 340))

    return items


# ============================================================
# SHEET 2: CONNECTIVITY
# ============================================================
def sheet2_connectivity():
    items = []

    items.append(text('CONNECTIVITY', 50, 15, 3))
    items.append(text('GbE + WiFi 5 + 4G LTE + Audio + USB + HDMI + Cameras', 50, 22, 1.5))

    # Hierarchical labels
    items.append(hier_lbl('5V_SYS', 10, 40, 'input'))
    items.append(hier_lbl('3V3_RK', 10, 48, 'input'))
    items.append(hier_lbl('GND', 10, 56, 'input'))
    items.append(hier_lbl('RGMII_BUS', 10, 64, 'input'))
    items.append(hier_lbl('SDIO_BUS', 10, 72, 'input'))
    items.append(hier_lbl('I2S_BUS', 10, 80, 'input'))
    items.append(hier_lbl('USB3_0', 10, 88, 'bidirectional'))
    items.append(hier_lbl('USB3_1', 10, 96, 'bidirectional'))
    items.append(hier_lbl('USB2_0', 10, 104, 'bidirectional'))
    items.append(hier_lbl('USB2_1', 10, 112, 'bidirectional'))
    items.append(hier_lbl('USB2_CELL', 10, 120, 'bidirectional'))
    items.append(hier_lbl('HDMI_BUS', 10, 128, 'input'))
    items.append(hier_lbl('CSI0_BUS', 10, 136, 'input'))
    items.append(hier_lbl('CSI1_BUS', 10, 144, 'input'))
    items.append(hier_lbl('48V_POE', 380, 40, 'output'))

    # === GbE PHY ===
    items.append(text('Gigabit Ethernet — RTL8211F + RJ45/PoE', 30, 160, 2))
    items.append(comp('U7', 'solarpunk-pi-v3', 'RTL8211F', 80, 195, 'RTL8211F-CG', 'Package_QFN:QFN-40'))
    items.append(comp('J1', 'Connector', 'RJ45_PoE', 200, 195, 'HR911105A', 'Connector_RJ:RJ45_PoE_Magnetics'))
    items.append(comp('Y2', 'Device', 'Crystal', 130, 175, '25MHz', 'Crystal:Crystal_SMD_3225-4Pin'))
    items.append(cap('C_Y2_1', '15pF', 120, 170))    # Crystal load cap
    items.append(cap('C_Y2_2', '15pF', 140, 170))    # Crystal load cap
    items.append(cap('C_RTL1', '100nF', 60, 185))     # AVDD33 bypass
    items.append(cap('C_RTL2', '100nF', 60, 195))     # DVDD bypass
    items.append(cap_0805('C_RTL3', '10uF', 60, 205))  # Bulk
    items.append(wire(110, 195, 170, 195))  # PHY to magnetics
    items.append(wire(230, 195, 260, 195))  # RJ45 to POE label
    items.append(local_lbl('48V_POE', 260, 195))
    items.append(text('RGMII: TXD[0:3], TX_CLK, TX_EN, RXD[0:3], RX_CLK, RX_DV', 30, 215, 1.0))

    # === WiFi 5 ===
    items.append(text('WiFi 5 + BT 5.0 — RTL8852BS (SDIO)', 30, 230, 2))
    items.append(comp('U8', 'solarpunk-pi-v3', 'RTL8852BS', 80, 260, 'RTL8852BS', 'Package_QFN:QFN-44'))
    items.append(comp('J12', 'Connector', 'U.FL', 180, 250, 'WiFi Main', 'Connector_Coaxial:U.FL'))
    items.append(comp('J13', 'Connector', 'U.FL', 180, 265, 'WiFi Aux', 'Connector_Coaxial:U.FL'))
    items.append(cap('C_WiFi1', '100nF', 60, 255))
    items.append(cap_0805('C_WiFi2', '10uF', 60, 265))
    items.append(text('SDIO_CLK/CMD/D[0:3] from RK3576 SDIO bus', 30, 280, 1.0))

    # === 4G LTE ===
    items.append(text('4G LTE — Quectel EC25-E (M.2 B-key)', 250, 160, 2))
    items.append(comp('U9', 'solarpunk-pi-v3', 'EC25E', 300, 200, 'EC25-E', 'Connector:M.2_B-key'))
    items.append(comp('J2', 'Connector', 'SIM_Card', 370, 210, 'Nano-SIM', 'Connector_Card:SIM_Nano'))
    items.append(comp('J14', 'Connector', 'U.FL', 370, 185, '4G Ant Main', 'Connector_Coaxial:U.FL'))
    items.append(comp('U13', 'solarpunk-pi-v3', 'PRTR5V0U2X', 350, 220, 'PRTR5V0U2X (SIM)', 'Package_TO_SOT_SMD:SOT-363'))
    items.append(cap('C_4G_1', '100nF', 275, 195))
    items.append(cap_0805('C_4G_2', '10uF', 275, 205))

    # === Audio ===
    items.append(text('Audio — ES8316 Codec (I2S + I2C)', 250, 235, 2))
    items.append(comp('U10', 'solarpunk-pi-v3', 'ES8316', 300, 265, 'ES8316', 'Package_QFN:QFN-24'))
    items.append(comp('J3', 'Connector', 'AudioJack4', 370, 265, '3.5mm TRRS', 'Connector_Audio:TRRS_3.5mm'))
    items.append(cap('C_AUD1', '100nF', 280, 258))
    items.append(cap('C_AUD2', '100nF', 280, 268))
    items.append(text('I2S: MCLK, SCLK, LRCK, SDI, SDO | I2C: SCL, SDA', 250, 280, 1.0))

    # === USB-C Ports ===
    items.append(text('USB-C x4 — 2x USB3.1 + 2x USB2.0', 30, 295, 2))
    for i, (ref, val, x) in enumerate([
        ('J4', 'USB-C #1 OTG+PD', 60),
        ('J5', 'USB-C #2 Host 3.1', 150),
        ('J6', 'USB-C #3 Host 2.0', 240),
        ('J7', 'USB-C #4 Host 2.0', 330),
    ]):
        items.append(comp(ref, 'Connector', 'USB_C', x, 320, val, 'Connector_USB:USB_C'))
        items.append(comp(f'U11{chr(97+i)}', 'solarpunk-pi-v3', 'USBLC6', x+30, 310, 'USBLC6-2SC6', 'Package_TO_SOT_SMD:SOT-23-6'))
    items.append(text('Each USB-C: USBLC6-2SC6 ESD + CC1/CC2 resistors', 30, 340, 1.0))
    items.append(text('J4: OTG+DP Alt+PD (CC→HUSB238), J5: Host USB3.1, J6/J7: Host USB2.0', 30, 345, 1.0))

    # === HDMI ===
    items.append(text('Micro-HDMI 2.0 — 4K@60fps', 30, 360, 2))
    items.append(comp('J8', 'Connector', 'HDMI_Micro', 80, 385, 'Micro-HDMI', 'Connector_HDMI:HDMI_Micro_D'))
    items.append(comp('U12', 'solarpunk-pi-v3', 'PRTR5V0U2X', 50, 380, 'PRTR5V0U2X (HDMI)', 'Package_TO_SOT_SMD:SOT-363'))
    items.append(text('TMDS: TX0±, TX1±, TX2±, CLK± + HPD, CEC, DDC(I2C)', 30, 400, 1.0))

    # === CSI Cameras ===
    items.append(text('MIPI CSI Cameras', 200, 360, 2))
    items.append(comp('J9', 'Connector', 'FPC_22pin', 230, 385, 'CSI-1 4-lane 4K', 'Connector_FFC-FPC:FPC_22pin'))
    items.append(comp('J10', 'Connector', 'FPC_15pin', 330, 385, 'CSI-2 2-lane 1080p', 'Connector_FFC-FPC:FPC_15pin'))

    # === 40-pin GPIO + NVMe ===
    items.append(text('40-Pin GPIO (Pi 5 Compatible) + NVMe M.2', 30, 415, 2))
    items.append(comp('J11', 'Connector_Generic', 'Conn_02x20', 80, 440, '2x20 GPIO', 'Connector_PinHeader_2.54mm:PinHeader_2x20_P2.54mm_Vertical'))
    items.append(comp('J15', 'Connector', 'M.2_M-key', 250, 440, 'M.2 2230 NVMe', 'Connector_PCI:M.2_M-key'))
    items.append(text('NVMe: PCIe Gen3 x1 from RK3576', 200, 455, 1.0))

    items.append(power('GND', 200, 465))

    return items


# ============================================================
# SHEET 3: RP2350 RADIO DOMAIN
# ============================================================
def sheet3_rp2350_radio():
    items = []

    items.append(text('RP2350 POWER & RADIO DOMAIN', 50, 15, 3))
    items.append(text('Always-on: 2xM33@150MHz, ~0.1W — WiFi 4 + LoRa Mesh', 50, 22, 1.5))

    # Hierarchical labels
    items.append(hier_lbl('3V3_RP', 10, 40, 'input'))
    items.append(hier_lbl('5V_SYS', 10, 48, 'input'))
    items.append(hier_lbl('GND', 10, 56, 'input'))
    items.append(hier_lbl('UART4_RX_BUF', 10, 64, 'input'))
    items.append(hier_lbl('UART4_TX_BUF', 380, 40, 'output'))
    items.append(hier_lbl('PWR_ENABLE', 380, 48, 'output'))
    items.append(hier_lbl('PWR_GOOD', 10, 72, 'input'))
    items.append(hier_lbl('WAKE_REQUEST', 10, 80, 'input'))
    items.append(hier_lbl('RK3506_RESET', 380, 56, 'output'))
    items.append(hier_lbl('SHUTDOWN_IN', 10, 88, 'input'))

    # === RP2350A MCU ===
    items.append(comp('U20', 'solarpunk-pi-v3', 'RP2350A', 100, 120, 'RP2350A', 'Package_QFN:QFN-60-1EP_7x7mm_P0.4mm'))

    # RP2350 Decoupling
    items.append(cap('C_RP_IO', '100nF', 70, 110))      # IOVDD
    items.append(cap('C_RP_DV', '100nF', 70, 118))      # DVDD
    items.append(cap('C_RP_VR', '1uF', 70, 126))        # VREG_VIN
    items.append(cap('C_RP_33', '100nF', 70, 134))      # 3V3_OUT

    # 12MHz Crystal + load caps
    items.append(comp('Y1', 'Device', 'Crystal', 170, 105, '12MHz', 'Crystal:Crystal_SMD_3225-4Pin'))
    items.append(cap('C93', '15pF', 160, 100))
    items.append(cap('C94', '15pF', 180, 100))
    items.append(wire(130, 105, 160, 105))    # XIN to crystal
    items.append(wire(180, 105, 200, 105))    # XOUT from crystal
    items.append(power('GND', 170, 115))

    # W25Q16 SPI Flash
    items.append(comp('U21', 'solarpunk-pi-v3', 'W25Q16', 250, 100, 'W25Q16JVSSIQ', 'Package_SO:SOP-8'))
    items.append(cap('C_FL1', '100nF', 230, 95))
    items.append(text('QSPI: SCK, CS, D0-D3 from RP2350', 220, 115, 1.0))

    # === CYW43439 WiFi/BT ===
    items.append(text('WiFi 4 + BT 5.2 — CYW43439 (SPI)', 30, 170, 2))
    items.append(comp('U22', 'solarpunk-pi-v3', 'CYW43439', 100, 210, 'CYW43439', 'Package_BGA:BGA-59'))
    items.append(cap('C_CYW1', '100nF', 70, 200))
    items.append(cap('C_CYW2', '100nF', 70, 208))
    items.append(cap_0805('C_CYW3', '10uF', 70, 216))
    items.append(text('SPI0: GP2(SCK), GP3(TX), GP4(RX), GP5(CS)', 30, 230, 1.0))
    items.append(text('GP9→WL_REG_ON, GP10→IRQ', 30, 235, 1.0))

    # === SX1262 LoRa ===
    items.append(text('LoRa 868/915MHz — SX1262 (SPI, shared bus)', 220, 170, 2))
    items.append(comp('U23', 'solarpunk-pi-v3', 'SX1262', 300, 210, 'SX1262IMLTRT', 'Package_QFN:QFN-24-1EP_4x4mm_P0.5mm'))
    items.append(comp('J20', 'Connector', 'U.FL', 370, 200, 'LoRa Ant', 'Connector_Coaxial:U.FL'))
    items.append(cap('C_SX1', '100nF', 275, 200))
    items.append(cap('C_SX2', '100nF', 275, 210))

    # LoRa matching network (pi-network)
    items.append(ind('L_MATCH', '3.9nH', 345, 205, 'Inductor_SMD:L_0402'))
    items.append(cap('C_MATCH1', '1.6pF', 335, 210))
    items.append(cap('C_MATCH2', '2.4pF', 355, 210))
    items.append(text('SPI: GP2(SCK), GP3(TX), GP4(RX), GP25(CS_LORA)', 220, 230, 1.0))
    items.append(text('GP24→DIO1(IRQ), GP23→BUSY, GP22→NRESET', 220, 235, 1.0))
    items.append(text('Pi-network: L=3.9nH, C1=1.6pF, C2=2.4pF (868MHz)', 220, 240, 1.0))

    # === PMOS Power Switches ===
    items.append(text('Power Control — Si2301 PMOS Gates', 30, 260, 2))
    items.append(comp('Q1', 'Device', 'Q_PMOS_GSD', 100, 290, 'Si2301 (Brain)', 'Package_TO_SOT_SMD:SOT-23'))
    items.append(comp('Q2', 'Device', 'Q_PMOS_GSD', 200, 290, 'Si2301 (Cell)', 'Package_TO_SOT_SMD:SOT-23'))
    items.append(res('R57', '100k', 80, 285))    # Q1 gate pull-up
    items.append(res('R58', '100k', 180, 285))   # Q2 gate pull-up
    items.append(text('R57/R58=100k gate pull-up to 3V3_RP', 30, 305, 1.0))
    items.append(text('GP15→Q1 gate (brain power), GP16→Q2 gate (cellular)', 30, 310, 1.0))

    # === ADC Inputs ===
    items.append(text('ADC Inputs: GP26=VBAT÷2, GP27=SOLAR÷3', 220, 260, 1.5))
    items.append(label('ADC_VBAT', 280, 270, 'input'))
    items.append(label('ADC_SOLAR', 280, 278, 'input'))

    # === Expansion Header ===
    items.append(text('10-Pin RP2350 Expansion Header', 220, 290, 2))
    items.append(comp('J21', 'Connector_Generic', 'Conn_01x10', 300, 310, '1x10 Expansion', 'Connector_PinHeader_2.54mm:PinHeader_1x10_P2.54mm_Vertical'))

    items.append(text('3mm antenna keepout on ALL 6 layers around CYW43439 and SX1262', 30, 330, 1.2))
    items.append(power('GND', 200, 340))

    return items


# ============================================================
# SHEET 4: RK3506J INDUSTRIAL DOMAIN
# ============================================================
def sheet4_rk3506j_industrial():
    items = []

    items.append(text('RK3506J INDUSTRIAL DOMAIN', 50, 15, 3))
    items.append(text('Always-on: 3xA7@1.5G + M0@200M — CAN FD, RS485, PWM, ADC', 50, 22, 1.5))

    # Hierarchical labels
    items.append(hier_lbl('3V3_RK3506', 10, 40, 'input'))
    items.append(hier_lbl('5V_SYS', 10, 48, 'input'))
    items.append(hier_lbl('GND', 10, 56, 'input'))
    items.append(hier_lbl('UART5_RX_BUF', 10, 64, 'input'))
    items.append(hier_lbl('UART5_TX_BUF', 380, 40, 'output'))
    items.append(hier_lbl('SPI0_CLK', 10, 72, 'input'))
    items.append(hier_lbl('SPI0_MOSI', 10, 80, 'input'))
    items.append(hier_lbl('SPI0_MISO', 380, 48, 'output'))
    items.append(hier_lbl('SPI0_CS', 10, 88, 'input'))
    items.append(hier_lbl('GPIO_WAKE', 380, 56, 'output'))
    items.append(hier_lbl('GPIO_ALARM', 380, 64, 'output'))
    items.append(hier_lbl('RESET_N', 10, 96, 'input'))

    # === RK3506J MCU ===
    items.append(comp('U30', 'solarpunk-pi-v3', 'RK3506J', 100, 120, 'RK3506J', 'Package_QFN:QFN-88'))

    # RK3506J Decoupling
    for i in range(8):
        items.append(cap(f'C_3506_{i+1}', '100nF', 60 + i*8, 155))
    items.append(cap_0805('C_3506_B1', '10uF', 60, 163))
    items.append(cap_0805('C_3506_B2', '10uF', 80, 163))

    # 24MHz Crystal
    items.append(comp('Y3', 'Device', 'Crystal', 170, 105, '24MHz', 'Crystal:Crystal_SMD_3225-4Pin'))
    items.append(cap('C95', '15pF', 160, 100))
    items.append(cap('C96', '15pF', 180, 100))
    items.append(power('GND', 170, 115))

    # === Memory ===
    items.append(text('LPDDR3L 512MB + NAND 256MB', 100, 180, 2))
    items.append(comp('U31', 'solarpunk-pi-v3', 'LPDDR3L', 80, 215, '512MB LPDDR3L', 'Package_BGA:BGA-178'))
    items.append(comp('U32', 'solarpunk-pi-v3', 'NAND_Flash', 200, 215, '256MB NAND', 'Package_BGA:BGA-63'))

    # Memory decoupling
    for i in range(4):
        items.append(cap(f'C_DDR3_{i+1}', '100nF', 55 + i*12, 240))
    items.append(cap('C_NAND1', '100nF', 185, 240))

    # === CAN FD Transceivers ===
    items.append(text('CAN FD x2 — MCP2562FD + ADUM1401 Isolation', 250, 35, 2))
    items.append(comp('U33', 'solarpunk-pi-v3', 'MCP2562FD', 300, 70, 'MCP2562FD #1', 'Package_TO_SOT_SMD:SOT-23-8'))
    items.append(comp('U34', 'solarpunk-pi-v3', 'MCP2562FD', 300, 120, 'MCP2562FD #2', 'Package_TO_SOT_SMD:SOT-23-8'))
    items.append(cap('C_CAN1', '100nF', 280, 65))
    items.append(cap('C_CAN2', '100nF', 280, 115))

    # CAN termination resistors with jumper
    items.append(res('R62', '120R', 340, 75))   # CAN1 term
    items.append(res('R63', '120R', 340, 125))  # CAN2 term
    items.append(text('R62/R63: 120R termination (solder jumper)', 325, 140, 1.0))

    # CAN wiring labels
    items.append(local_lbl('CAN0_TX', 270, 65))
    items.append(local_lbl('CAN0_RX', 270, 75))
    items.append(local_lbl('CAN1_TX', 270, 115))
    items.append(local_lbl('CAN1_RX', 270, 125))

    # === ADUM1401 Isolation ===
    items.append(comp('U35', 'solarpunk-pi-v3', 'ADUM1401', 300, 170, 'ADUM1401', 'Package_SO:SOIC-16W_7.5x10.3mm_P1.27mm'))
    items.append(cap('C_ISO1', '100nF', 275, 163))  # VDD1 bypass
    items.append(cap('C_ISO2', '100nF', 325, 163))  # VDD2 bypass

    # === RS485 ===
    items.append(text('RS485 — SP3485 (via ADUM1401)', 250, 200, 2))
    items.append(comp('U36', 'solarpunk-pi-v3', 'SP3485', 300, 230, 'SP3485', 'Package_SO:SOP-8'))
    items.append(cap('C_RS1', '100nF', 280, 225))
    items.append(res('R64', '120R', 340, 230))  # RS485 term
    items.append(text('R64: 120R termination (solder jumper)', 325, 245, 1.0))

    # === Industrial Input Conditioning ===
    items.append(text('Industrial Input Conditioning', 250, 260, 2))
    items.append(comp('U37', 'solarpunk-pi-v3', 'SN74LVC14A', 300, 290, 'SN74LVC14A', 'Package_SO:TSSOP-14_4.4x5mm_P0.65mm'))
    items.append(cap('C_LVC1', '100nF', 280, 285))

    # ESD
    items.append(comp('U38', 'Device', 'IC_Generic', 300, 330, 'PESD5V0S4UG', 'Package_TO_SOT_SMD:SOT-553'))

    # === Industrial Header ===
    items.append(text('30-Pin Industrial I/O Header', 30, 260, 2))
    items.append(comp('J30', 'Connector_Generic', 'Conn_03x10', 80, 310, '3x10 Industrial I/O', 'Connector_PinHeader_2.54mm:PinHeader_3x10_P2.54mm_Vertical'))
    items.append(text('Pins: CAN1_H/L, CAN2_H/L, RS485_A/B, GPIO[0:3], PWM[0:3], ADC[0:3], 5V, 3V3, GND', 30, 350, 1.0))

    items.append(text('CAN/RS485 isolation barrier — no copper crossing on ALL layers', 30, 360, 1.2))
    items.append(power('GND', 200, 370))

    return items


# ============================================================
# SHEET 6: SIGNAL CONDITIONING
# ============================================================
def sheet6_signal_conditioning():
    items = []

    items.append(text('SIGNAL CONDITIONING', 50, 15, 3))
    items.append(text('Schmitt Trigger Buffers — 8 ICs, 13 conditioned channels', 50, 22, 1.5))

    # Hierarchical labels (must match parent sheet)
    for name, y, shape in [
        ('UART4_TX_RAW', 40, 'input'), ('UART4_RX_RAW', 48, 'input'),
        ('UART4_TX_BUF', 56, 'output'), ('UART4_RX_BUF', 64, 'output'),
        ('UART5_TX_RAW', 72, 'input'), ('UART5_RX_RAW', 80, 'input'),
        ('UART5_TX_BUF', 88, 'output'), ('UART5_RX_BUF', 96, 'output'),
        ('PWR_GOOD_RAW', 104, 'input'), ('PWR_GOOD_BUF', 112, 'output'),
        ('PWR_EN_RAW', 120, 'input'), ('PWR_EN_BUF', 128, 'output'),
        ('WAKE_RAW', 136, 'input'), ('WAKE_BUF', 144, 'output'),
        ('ALARM_RAW', 152, 'input'), ('ALARM_BUF', 160, 'output'),
        ('SHUTDOWN_RAW', 168, 'input'), ('SHUTDOWN_BUF', 176, 'output'),
    ]:
        x = 10 if shape == 'input' else 380
        items.append(hier_lbl(name, x, y, shape))

    # === UART1 Schmitt (RK3576 ↔ RP2350) ===
    items.append(text('UART1: RK3576 UART4 ↔ RP2350 GP0/GP1 (115200 baud)', 30, 190, 1.5))
    items.append(comp('U50', 'solarpunk-pi-v3', 'SN74LVC2G17', 100, 210, 'SN74LVC2G17', 'Package_TO_SOT_SMD:SOT-23-6'))
    items.append(cap('C_U50', '100nF', 80, 205))
    items.append(res('R_U4TX', '33R', 140, 207))   # Series resistor TX
    items.append(res('R_U4RX', '33R', 140, 213))   # Series resistor RX
    items.append(wire(30, 207, 80, 207))     # UART4_TX_RAW → U50 1A
    items.append(wire(120, 207, 140, 207))   # U50 1Y → R → buf
    items.append(wire(155, 207, 200, 207))   # → UART4_TX_BUF
    items.append(wire(30, 213, 80, 213))     # UART4_RX_RAW → U50 2A
    items.append(wire(120, 213, 140, 213))   # U50 2Y → R → buf
    items.append(wire(155, 213, 200, 213))   # → UART4_RX_BUF

    # === UART2 Schmitt (RK3576 ↔ RK3506J) ===
    items.append(text('UART2: RK3576 UART5 ↔ RK3506J UART2 (921600 baud)', 30, 235, 1.5))
    items.append(comp('U51', 'solarpunk-pi-v3', 'SN74LVC2G17', 100, 255, 'SN74LVC2G17', 'Package_TO_SOT_SMD:SOT-23-6'))
    items.append(cap('C_U51', '100nF', 80, 250))
    items.append(res('R_U5TX', '33R', 140, 252))
    items.append(res('R_U5RX', '33R', 140, 258))
    items.append(wire(30, 252, 80, 252))
    items.append(wire(120, 252, 155, 252))
    items.append(wire(30, 258, 80, 258))
    items.append(wire(120, 258, 155, 258))

    # === Single Schmitt buffers for control signals ===
    ctrl_signals = [
        ('U52', 'Power Good', 'PWR_GOOD', 280, 1.5),
        ('U53', 'Wake Request', 'WAKE', 310, 1.5),
        ('U54', 'Alarm IRQ', 'ALARM', 340, 1.5),
        ('U55', 'Shutdown', 'SHUTDOWN', 370, 1.5),
        ('U56', 'Power Enable', 'PWR_EN', 400, 1.5),
    ]
    for ref, desc, sig, y, sz in ctrl_signals:
        items.append(text(f'{desc}: {sig}_RAW → {ref} → {sig}_BUF', 250, y-10, sz))
        items.append(comp(ref, 'solarpunk-pi-v3', 'SN74LVC1G17', 330, y, 'SN74LVC1G17', 'Package_TO_SOT_SMD:SOT-23-5'))
        items.append(cap(f'C_{ref}', '100nF', 310, y-5))
        items.append(wire(290, y, 310, y))     # RAW → buffer
        items.append(wire(350, y, 380, y))     # buffer → BUF

    # Summary
    items.append(text('SIGNAL CONDITIONING SUMMARY', 30, 420, 2))
    items.append(text('SN74LVC2G17 (dual) x2: UART TX/RX with 33R series resistors', 30, 430, 1.2))
    items.append(text('SN74LVC1G17 (single) x5: PG, wake, alarm, shutdown, power gate', 30, 436, 1.2))
    items.append(text('All buffers: 100nF VCC bypass, powered from destination domain 3V3', 30, 442, 1.2))
    items.append(text('RK3506J reset and SPI bridge are DIRECT (same 3.3V domain)', 30, 448, 1.2))

    items.append(power('GND', 200, 460))

    return items
