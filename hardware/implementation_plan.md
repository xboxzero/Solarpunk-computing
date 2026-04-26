# Solarpunk Pi v3 — Schematic Review, BOM Update & Project Completion

Complete schematic review against datasheets, update BOM to match v3 design, and finish all incomplete sections (TODOs, missing components, empty directories).

## User Review Required

> [!IMPORTANT]
> **Battery Chemistry Choice**: The CN3722 schematic says "2S LiFePO4" but the old BOM lists a single-cell 3.7V LiPo. For a 2S LiFePO4 pack (6.4V nominal), the TPS61022 boost to 5V won't work — it's a boost converter and 6.4V > 5V. Options:
> 1. **Single-cell LiFePO4** (3.2V nom) — CN3722 still works, TPS61022 boost to 5V ✓
> 2. **Single-cell Li-ion** (3.7V nom) — Need different charger IC, TPS61022 boost to 5V ✓  
> 3. **2S LiFePO4** (6.4V nom) — Need a buck converter instead of boost for 5V
> **I'll assume Option 1 (single-cell LiFePO4, 3.2V) unless you specify otherwise.**

> [!WARNING]
> **HUSB238 Pinout Mismatch**: The current schematic uses `SEL0/SEL1/SEL2` pins, but the actual HUSB238 uses a single **VSET** pin with a resistor to GND to select voltage. The symbol and schematic need to be corrected per the real datasheet.

> [!IMPORTANT]
> **LTC4357 requires external N-channel MOSFET**: The schematic shows the LTC4357 with IN/GATE/OUT/GND pins (correct), but needs an external MOSFET (e.g., Si4456DY) on each OR-ing path. Currently only 1 LTC4357 exists for the boost path — need 2 more for PoE and USB-PD paths.

---

## Phase 1: Schematic Review & Fixes

### 1.1 Power System (05-power-system.kicad_sch) — Critical Fixes

#### [MODIFY] [05-power-system.kicad_sch](file:///home/xero2/Solarpunk-computing/hardware/solarpunk-pi-v3/05-power-system.kicad_sch)

**CN3722 Solar MPPT (Section 1):**
- Add programming resistors per datasheet:
  - **SS** (pin 3): 0.1µF soft-start cap to GND
  - **FB** (pin 4): Voltage divider for VBAT target (3.6V LiFePO4: R=49.9k/100k)
  - **COMP** (pin 5): 470pF compensation cap to GND
  - **RT** (pin 6): 200kΩ timing resistor to GND (sets ~300kHz switching)
  - **CS** (pin 14): 50mΩ current sense resistor (sets ~2A charge current)
  - **TS** (pin 15): NTC thermistor divider (10kΩ NTC + 10kΩ to GND)
  - **MPPT** (pin 16): Resistor divider from solar input (VMPPT ref = 1.04V; for 18V panel: 163k/10k)
  - **BST** (pin 10): 100nF bootstrap cap between BST and SW
  - **SW** (pin 9): Inductor (10µH, 3A) to VBAT output
- Add input/output bulk capacitors: 22µF ceramic on VIN, 22µF on VBAT

**TPS61022 Boost (Section 2):**
- Fix FB voltage divider: Per datasheet, R1=732kΩ, R2=100kΩ for 5V (VREF=0.5V). Current schematic has 750k/150k → **output is ~3V, not 5V!** Must fix.
- Add input cap: 10µF ceramic
- Add output caps: 3x 22µF ceramic (per TI datasheet recommendation)
- Inductor value OK (1µH SWPA4012S)

**SI3402-B PoE PD (Section 3):**
- Add RCLASS resistor (243Ω for Class 3 — 12.95W)
- Add DET detection cap (100nF)
- Add VSS/AGND proper grounding
- Add output DC-DC stage (the SI3402-B provides PoE detection/classification, but needs an external isolated flyback or buck stage to convert 48V→5V — currently missing)
- Add 100µF bulk output cap

**HUSB238 USB-PD (Section 4):**
- **Fix symbol**: Replace SEL0/SEL1/SEL2 with VSET pin + resistor
- Add VSET resistor: 10kΩ to GND (for 12V request)
- Add CC1/CC2 connections to USB-C connector
- Add I2C pull-ups (optional, for dynamic PD control)
- Add step-down after HUSB238: Need a buck converter (e.g., MP2315) to convert 12V→5V

**LTC4357 OR-ing (Section 5):**
- Add external N-channel MOSFETs (Si4456DY) for each path
- Add 2nd LTC4357 + MOSFET for PoE 5V path
- Add 3rd LTC4357 + MOSFET for USB-PD 5V path
- Add output bulk caps on 5V_SYS bus (100µF + 10µF)

**Always-On LDOs (Section 6):**
- U45 MIC5219: Add 1µF input cap, 1µF output cap, 470pF bypass cap
- U46 AP2112K: Add 1µF input cap, 1µF output cap

**ADC Monitors (New Section — TODO from notes):**
- Add VBAT monitoring: 100k/100k divider + 100Ω + 100nF RC filter → RP2350 GP26
- Add SOLAR_IN monitoring: 200k/100k divider + 100Ω + 100nF RC filter → RP2350 GP27

---

### 1.2 Compute Domain (01-rk3576-compute.kicad_sch)

#### [MODIFY] [01-rk3576-compute.kicad_sch](file:///home/xero2/Solarpunk-computing/hardware/solarpunk-pi-v3/01-rk3576-compute.kicad_sch)

- Add RK806-1 SPI communication wires (CLK/CS/MOSI/MISO) between RK3576 and RK806
- Add RK806 PWRGD → signal conditioning sheet
- Add bulk decoupling: 100nF per VDD ball (noted in design text), 10µF per power domain
- Add LPDDR4X routing notes (differential DQS, length-matched DQ groups)
- Add eMMC/SPI NOR chip connections (currently floating as IC_Generic)
- Add SPI2_CS global label (missing from current set)

---

### 1.3 Connectivity (02-connectivity.kicad_sch)

#### [MODIFY] [02-connectivity.kicad_sch](file:///home/xero2/Solarpunk-computing/hardware/solarpunk-pi-v3/02-connectivity.kicad_sch)

- Add 25MHz crystal for RTL8211F (TODO noted in schematic)
- Add crystal load caps (15pF x2)
- Add RTL8211F RGMII connection wires (currently just a label)
- Add RTL8211F ↔ RJ45 transformer connections
- Add RTL8852BS SDIO wiring details
- Add proper USB-C connector pinout (CC, D+/D-, VBUS, SBU for each port)

---

### 1.4 RP2350 Radio (03-rp2350-radio.kicad_sch)

#### [MODIFY] [03-rp2350-radio.kicad_sch](file:///home/xero2/Solarpunk-computing/hardware/solarpunk-pi-v3/03-rp2350-radio.kicad_sch)

- Add RP2350A decoupling: 100nF on IOVDD, 100nF on DVDD, 1µF on VREG_VIN
- Add 12MHz crystal load caps (15pF x2)
- Add W25Q16 SPI connections (QSPI_CLK/CS/D0-D3)
- Add CYW43439 SPI connections (GP2-GP5 → SPI0)
- Add SX1262 SPI connections (GP2-GP5 via CS mux or separate SPI bus)
- Add SX1262 LoRa matching network (pi-network for 868/915MHz)
- Add SX1262 TCXO or crystal (32MHz)
- Add Q1/Q2 PMOS gate pull-up resistors (100kΩ to 3V3_RP)
- Add hierarchical labels for UART4_TX_BUF, UART4_RX_BUF connections

---

### 1.5 RK3506J Industrial (04-rk3506j-industrial.kicad_sch)

#### [MODIFY] [04-rk3506j-industrial.kicad_sch](file:///home/xero2/Solarpunk-computing/hardware/solarpunk-pi-v3/04-rk3506j-industrial.kicad_sch)

- Add RK3506J crystal (24MHz + load caps)
- Add RK3506J decoupling (100nF × 8 + 10µF × 2)
- Add LPDDR3L connections (U31 — currently floating IC_Generic)
- Add NAND flash connections (U32 — currently floating)
- Add MCP2562FD CAN connections (TXD/RXD to RK3506J CAN0/CAN1)
- Add 120Ω termination resistors with jumpers on CAN1, CAN2, RS485
- Add ADUM1401 isolation connections
- Add SP3485 RS485 TX/RX/DE/RE connections
- Add industrial header pinout definition (30-pin J30)

---

### 1.6 Signal Conditioning (06-signal-conditioning.kicad_sch) — Complete ✓

This sheet is well-done. Minor additions:
- Add series resistors (33Ω) on UART lines for ESD/ringing suppression
- Add ESD TVS diodes (PESD5V0S1BA) on cross-domain signals

---

### 1.7 Symbol Library Updates

#### [MODIFY] [solarpunk-pi-v3.kicad_sym](file:///home/xero2/Solarpunk-computing/hardware/solarpunk-pi-v3/libraries/solarpunk-pi-v3.kicad_sym)

- Fix HUSB238 symbol: Remove SEL0/1/2 pins, add VSET pin
- Add missing connector symbols as needed (proper USB-C 16/24-pin)

---

## Phase 2: BOM Update

#### [NEW] [bom_v3.csv](file:///home/xero2/Solarpunk-computing/hardware/bom_v3.csv)

Replace the old ESP32-based BOM with an accurate v3 BOM covering all components:

| Category | Ref | Part | Qty | ~Price | Source |
|----------|-----|------|-----|--------|--------|
| **Processors** |
| Main SoC | U1 | RK3576 BGA-698 | 1 | $12.00 | Rockchip |
| PMIC | U2 | RK806-1 QFN-68 | 1 | $3.50 | Rockchip |
| LPDDR4X | U3,U4 | K4UBE3D4AB 4GB | 2 | $8.00 | Samsung/LCSC |
| eMMC | U5 | KLMAG2JENB 32GB | 1 | $5.00 | Samsung/LCSC |
| SPI NOR | U6 | W25Q128JVSIQ 16MB | 1 | $0.80 | LCSC |
| Microcontroller | U20 | RP2350A QFN-60 | 1 | $0.80 | RPi |
| RP Flash | U21 | W25Q16JVSSIQ 2MB | 1 | $0.30 | LCSC |
| Industrial MCU | U30 | RK3506J QFN-88 | 1 | $3.00 | Rockchip |
| Ind LPDDR3L | U31 | 512MB LPDDR3L | 1 | $2.00 | LCSC |
| Ind NAND | U32 | 256MB NAND | 1 | $1.50 | LCSC |
| **Connectivity** |
| GbE PHY | U7 | RTL8211F-CG QFN-40 | 1 | $1.80 | LCSC |
| WiFi 5 | U8 | RTL8852BS SDIO | 1 | $5.00 | Realtek |
| 4G LTE | U9 | EC25-E M.2 | 1 | $18.00 | Quectel |
| Audio Codec | U10 | ES8316 QFN-24 | 1 | $0.80 | LCSC |
| **Radio** |
| WiFi 4/BT | U22 | CYW43439 | 1 | $1.50 | Infineon |
| LoRa | U23 | SX1262IMLTRT | 1 | $3.50 | Semtech |
| **Industrial** |
| CAN FD x2 | U33,U34 | MCP2562FD | 2 | $0.60 | LCSC |
| Isolator | U35 | ADUM1401 SOIC-16 | 1 | $2.50 | ADI |
| RS485 | U36 | SP3485 SOP-8 | 1 | $0.40 | LCSC |
| Schmitt 6ch | U37 | SN74LVC14A TSSOP-14 | 1 | $0.20 | LCSC |
| ESD Industrial | U38 | PESD5V0S4UG | 1 | $0.15 | LCSC |
| **Power** |
| Solar MPPT | U40 | CN3722 SOP-16 | 1 | $0.80 | LCSC |
| Boost 5V | U41 | TPS61022DRLR SOT-23-6 | 1 | $1.20 | TI/LCSC |
| PoE PD | U42 | SI3402-B QFN-16 | 1 | $2.50 | Skyworks |
| USB-PD | U43 | HUSB238 QFN | 1 | $0.60 | Hynetek |
| OR-ing x3 | U44a-c | LTC4357 SOT-23-5 | 3 | $3.00 | ADI |
| LDO RP | U45 | MIC5219-3.3 SOT-23-5 | 1 | $0.30 | LCSC |
| LDO RK3506 | U46 | AP2112K-3.3 SOT-23-5 | 1 | $0.15 | LCSC |
| **Signal Conditioning** |
| Dual Schmitt x2 | U50,U51 | SN74LVC2G17 SOT-23-6 | 2 | $0.20 | LCSC |
| Single Schmitt x5 | U52–U56 | SN74LVC1G17 SOT-23-5 | 5 | $0.50 | LCSC |
| **ESD Protection** |
| USB ESD x4 | U11 | USBLC6-2SC6 SOT-23-6 | 4 | $0.40 | LCSC |
| HDMI ESD | U12 | PRTR5V0U2X SOT-363 | 1 | $0.10 | LCSC |
| SIM ESD | U13 | PRTR5V0U2X SOT-363 | 1 | $0.10 | LCSC |
| **Passives** |
| Bypass caps | C* | 100nF 0402 | 50+ | $1.00 | LCSC |
| Bulk caps | C* | 10µF/22µF 0805 | 20+ | $1.00 | LCSC |
| Resistors | R* | Various 0402 | 40+ | $0.50 | LCSC |
| Inductor | L1 | 1µH SWPA4012S | 1 | $0.30 | LCSC |
| Inductor Solar | L2 | 10µH 3A | 1 | $0.50 | LCSC |
| Ferrite Beads x3 | FB1–3 | BLM18AG102SN1D 0603 | 3 | $0.15 | LCSC |
| Crystal 12MHz | Y1 | 12MHz 3225 | 1 | $0.15 | LCSC |
| Crystal 25MHz | Y2 | 25MHz 3225 | 1 | $0.15 | LCSC |
| **Connectors** |
| RJ45 PoE | J1 | HR911105A | 1 | $1.50 | LCSC |
| Nano-SIM | J2 | Nano-SIM holder | 1 | $0.30 | LCSC |
| TRRS 3.5mm | J3 | 3.5mm TRRS | 1 | $0.20 | LCSC |
| USB-C x4 | J4–J7 | USB-C 16pin | 4 | $1.20 | LCSC |
| Micro-HDMI | J8 | Micro-HDMI D | 1 | $0.40 | LCSC |
| CSI FPC x2 | J9,J10 | FPC 22/15pin | 2 | $0.40 | LCSC |
| GPIO 2x20 | J11 | PinHeader 2x20 | 1 | $0.20 | LCSC |
| WiFi U.FL x2 | J12,J13 | U.FL | 2 | $0.20 | LCSC |
| 4G U.FL | J14 | U.FL | 1 | $0.10 | LCSC |
| NVMe M.2 | J15 | M.2 M-key 2230 | 1 | $0.80 | LCSC |
| LoRa U.FL | J20 | U.FL | 1 | $0.10 | LCSC |
| RP Expansion | J21 | 1x10 PinHeader | 1 | $0.05 | LCSC |
| Industrial | J30 | 3x10 PinHeader | 1 | $0.15 | LCSC |
| Solar JST | J40 | JST VH B2P | 1 | $0.10 | LCSC |
| Battery JST | J41 | JST PH B2B | 1 | $0.10 | LCSC |
| **Switches** |
| PMOS x3 | Q1–Q3 | Si2301 SOT-23 | 3 | $0.15 | LCSC |
| OR MOSFETs x3 | Q4–Q6 | Si4456DY | 3 | $0.90 | LCSC |
| **PCB** |
| PCB | — | 6-layer 85×56mm | 1 | $8.00 | JLCPCB |
| | | | | **~$98** | |

---

## Phase 3: Complete Missing Items

### 3.1 Update generate_project.py

#### [MODIFY] [generate_project.py](file:///home/xero2/Solarpunk-computing/hardware/solarpunk-pi-v3/generate_project.py)

- Fix HUSB238 symbol definition (VSET instead of SEL pins)
- Add missing symbols for buck converters if needed
- Add MP2315 symbol for USB-PD step-down
- Update schematic generator to include all TODO components

### 3.2 Regenerate Schematics

After updating `generate_project.py`, regenerate all `.kicad_sch` files with the fixes applied, adding:
- All missing passive components (caps, resistors per datasheets)
- Proper wiring for all IC pin connections
- Fixed voltage divider values
- Missing OR-ing MOSFETs and LTC4357 instances
- ADC monitoring circuits

---

## Open Questions

> [!IMPORTANT]
> 1. **Battery chemistry/configuration** — Single-cell LiFePO4 (3.2V) vs single-cell Li-ion (3.7V) vs 2S LiFePO4 (6.4V)?
> 2. **PoE isolation** — Do you need galvanic isolation (flyback transformer) or is non-isolated acceptable? Isolated is standard for PoE but adds cost/complexity.
> 3. **USB-PD voltage** — Request 12V (current design) or 20V (more headroom for buck)?
> 4. **Enclosure** — Should I design a 3D-printable enclosure for the 85×56mm board?

## Verification Plan

### Automated Tests
- Run KiCad DRC/ERC after schematic updates
- Validate net connectivity across hierarchical sheets
- Cross-check BOM against schematic reference designators

### Manual Verification
- Visual review of power tree (voltage domains, sequencing)
- Verify all datasheet-required components are present
- Check impedance matching for high-speed signals (DDR, USB3, HDMI, PCIe)
