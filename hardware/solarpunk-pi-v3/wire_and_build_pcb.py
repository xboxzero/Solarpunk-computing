#!/usr/bin/env python3
"""
Solarpunk Pi v3 — Complete Wiring & PCB Generation Script
=========================================================
1) Wires the top-level schematic (inter-sheet connections via net labels)
2) Generates PCB with all component footprints placed in logical zones

Run:  python3 wire_and_build_pcb.py
"""

import uuid
import re
import os
import sys

# Headless display for pcbnew on systems without X11
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
os.environ.setdefault('DISPLAY', ':99')

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
TOP_SCH = os.path.join(PROJECT_DIR, "solarpunk-pi-v3.kicad_sch")
PCB_FILE = os.path.join(PROJECT_DIR, "solarpunk-pi-v3.kicad_pcb")

def uid():
    return str(uuid.uuid4())

# ============================================================
# PART 1: TOP-LEVEL SCHEMATIC WIRING
# ============================================================

# Each entry: (sheet_pin_x, sheet_pin_y, side, net_label_name)
# side: 'left' = wire extends left, label faces right (angle 0)
#        'right' = wire extends right, label faces left (angle 180... actually 0 for right-pointing)
# In KiCad, label at angle 0 means text goes right, wire connects on left side of label
# For a pin on the LEFT edge of a sheet, wire goes LEFT and label at the wire end
# For a pin on the RIGHT edge, wire goes RIGHT and label at the wire end

WIRE_LEN = 8  # mm extension for wire + label

# --- RK3576_Compute (sheet at 20,60 size 80x70, left=20, right=100) ---
RK3576_PINS = [
    # Left-side pins (x=20, wire extends LEFT to x=12)
    (20, 65, 'left',  '5V_SYS'),
    (20, 68, 'left',  'GND'),
    (20, 74, 'left',  'UART4_RX_BUF'),
    (20, 80, 'left',  'UART5_RX_BUF'),
    (20, 89, 'left',  'SPI2_MISO'),
    (20, 98, 'left',  'ALARM_BUF'),
    # Right-side pins (x=100, wire extends RIGHT to x=108)
    (100, 71,  'right', 'UART4_TX_RAW'),
    (100, 77,  'right', 'UART5_TX_RAW'),
    (100, 83,  'right', 'SPI2_CLK'),
    (100, 86,  'right', 'SPI2_MOSI'),
    (100, 92,  'right', 'SPI2_CS'),
    (100, 95,  'right', 'SHUTDOWN_RAW'),
    (100, 101, 'right', 'RGMII_BUS'),
    (100, 104, 'right', 'SDIO_BUS'),
    (100, 107, 'right', 'I2S_BUS'),
    (100, 110, 'right', 'USB3_0'),
    (100, 113, 'right', 'USB3_1'),
    (100, 116, 'right', 'USB2_0'),
    (100, 119, 'right', 'USB2_1'),
    (100, 122, 'right', 'USB2_CELL'),
]

# --- Connectivity (sheet at 130,60 size 80x70, left=130, right=210) ---
CONN_PINS = [
    (130, 65,  'left',  '5V_SYS'),
    (130, 68,  'left',  '3V3_RK'),
    (130, 71,  'left',  'GND'),
    (130, 74,  'left',  'RGMII_BUS'),
    (130, 77,  'left',  'SDIO_BUS'),
    (130, 80,  'left',  'I2S_BUS'),
    (130, 98,  'left',  'HDMI_BUS'),
    (130, 101, 'left',  'CSI0_BUS'),
    (130, 104, 'left',  'CSI1_BUS'),
    (210, 83,  'right', 'USB3_0'),
    (210, 86,  'right', 'USB3_1'),
    (210, 89,  'right', 'USB2_0'),
    (210, 92,  'right', 'USB2_1'),
    (210, 95,  'right', 'USB2_CELL'),
    (210, 107, 'right', '48V_POE'),
]

# --- RP2350_Radio (sheet at 20,150 size 80x60, left=20, right=100) ---
RP2350_PINS = [
    (20, 155,  'left',  '3V3_RP'),
    (20, 158,  'left',  '5V_SYS'),
    (20, 161,  'left',  'GND'),
    (20, 164,  'left',  'UART4_TX_BUF'),
    (20, 173,  'left',  'PWR_GOOD_BUF'),
    (20, 176,  'left',  'WAKE_BUF'),
    (20, 182,  'left',  'SHUTDOWN_BUF'),
    (100, 167, 'right', 'UART4_RX_RAW'),
    (100, 170, 'right', 'PWR_EN_RAW'),
    (100, 179, 'right', 'RK3506_RESET'),
]

# --- RK3506J_Industrial (sheet at 130,150 size 80x60, left=130, right=210) ---
RK3506_PINS = [
    (130, 155, 'left',  '3V3_RK3506'),
    (130, 158, 'left',  '5V_SYS'),
    (130, 161, 'left',  'GND'),
    (130, 164, 'left',  'UART5_TX_BUF'),
    (130, 170, 'left',  'SPI2_CLK'),
    (130, 173, 'left',  'SPI2_MOSI'),
    (130, 179, 'left',  'SPI2_CS'),
    (130, 188, 'left',  'RK3506_RESET'),
    (210, 167, 'right', 'UART5_RX_RAW'),
    (210, 176, 'right', 'SPI2_MISO'),
    (210, 182, 'right', 'WAKE_RAW'),
    (210, 185, 'right', 'ALARM_RAW'),
]

# --- Power_System (sheet at 20,225 size 100x55, left=20, right=120) ---
POWER_PINS = [
    (20, 230,  'left',  'SOLAR_IN'),
    (20, 236,  'left',  '48V_POE'),
    (20, 239,  'left',  'USB_PD_IN'),
    (20, 257,  'left',  'GND'),
    (120, 233, 'right', 'VBAT'),
    (120, 242, 'right', '5V_SYS'),
    (120, 245, 'right', '3V3_RP'),
    (120, 248, 'right', '3V3_RK3506'),
    (120, 251, 'right', '3V3_RK'),
    (120, 254, 'right', '1V8'),
]

# --- Signal_Conditioning (sheet at 150,225 size 80x55, left=150, right=230) ---
SIGCOND_PINS = [
    (150, 230, 'left',  'UART4_TX_RAW'),
    (150, 233, 'left',  'UART4_RX_RAW'),
    (150, 242, 'left',  'UART5_TX_RAW'),
    (150, 245, 'left',  'UART5_RX_RAW'),
    (150, 254, 'left',  'PWR_GOOD_RAW'),
    (150, 260, 'left',  'PWR_EN_RAW'),
    (150, 266, 'left',  'WAKE_RAW'),
    (150, 272, 'left',  'ALARM_RAW'),
    (150, 278, 'left',  'SHUTDOWN_RAW'),
    (230, 236, 'right', 'UART4_TX_BUF'),
    (230, 239, 'right', 'UART4_RX_BUF'),
    (230, 248, 'right', 'UART5_TX_BUF'),
    (230, 251, 'right', 'UART5_RX_BUF'),
    (230, 257, 'right', 'PWR_GOOD_BUF'),
    (230, 263, 'right', 'PWR_EN_BUF'),
    (230, 269, 'right', 'WAKE_BUF'),
    (230, 275, 'right', 'ALARM_BUF'),
    (230, 281, 'right', 'SHUTDOWN_BUF'),
]

ALL_PINS = (RK3576_PINS + CONN_PINS + RP2350_PINS + RK3506_PINS
            + POWER_PINS + SIGCOND_PINS)


def generate_wire_and_label(px, py, side, net_name):
    """Generate KiCad wire + label S-expressions for one pin connection."""
    if side == 'left':
        wx = px - WIRE_LEN
        lx = wx
        angle = 0  # label text points right, wire attaches on left
    else:  # right
        wx = px + WIRE_LEN
        lx = wx
        angle = 180  # label text points left, wire attaches on right

    wire = f"""  (wire (pts (xy {px} {py}) (xy {wx} {py}))
    (stroke (width 0) (type default))
    (uuid "{uid()}")
  )"""

    label = f"""  (label "{net_name}"
    (at {lx} {py} {angle})
    (effects (font (size 1.27 1.27)))
    (uuid "{uid()}")
  )"""

    return wire + "\n" + label


def wire_top_level_schematic():
    """Add all inter-sheet wires and net labels to the top-level schematic."""
    with open(TOP_SCH, 'r') as f:
        content = f.read()

    # Check if already wired
    if '(wire' in content:
        print("  Top-level schematic already contains wires — skipping")
        return False

    # Generate all wires and labels
    additions = []
    additions.append("\n  ;; === AUTO-GENERATED INTER-SHEET WIRING ===")
    additions.append("  ;; Generated by wire_and_build_pcb.py")
    additions.append("")

    # Group by net for readability
    net_groups = {}
    for px, py, side, net in ALL_PINS:
        if net not in net_groups:
            net_groups[net] = []
        net_groups[net].append((px, py, side))

    for net_name in sorted(net_groups.keys()):
        pins = net_groups[net_name]
        additions.append(f"  ;; Net: {net_name} ({len(pins)} connection{'s' if len(pins)>1 else ''})")
        for px, py, side in pins:
            additions.append(generate_wire_and_label(px, py, side, net_name))
        additions.append("")

    # Insert before the final closing paren
    insert_text = "\n".join(additions) + "\n"
    content = content.rstrip()
    if content.endswith(')'):
        content = content[:-1] + insert_text + ")\n"
    else:
        content += insert_text

    with open(TOP_SCH, 'w') as f:
        f.write(content)

    print(f"  Added {len(ALL_PINS)} wire+label pairs for {len(net_groups)} nets")
    return True


# ============================================================
# PART 2: PCB GENERATION WITH FOOTPRINT PLACEMENT
# ============================================================

# Component placement map: (ref, value, footprint_lib, footprint_name, x_mm, y_mm, layer, rotation)
# Board is 85x56mm. Placement zones:
#   TOP (F.Cu):    RK3576 center-left, DDR above/below, PMIC right of SoC
#                  Connectivity (Ethernet, USB, HDMI) along right edge
#                  eMMC/Flash near SoC
#   BOTTOM (B.Cu): RP2350, RK3506J, LoRa, power system, signal conditioning
#
# Coordinate system: origin at top-left of board outline
# Mounting holes at Pi 5 positions: (3.5,3.5), (61.5,3.5), (3.5,52.5), (61.5,52.5)

# Footprint resolution mapping: schematic name -> (library_dir, footprint_file_stem)
# KiCad 9 footprints are at /usr/share/kicad/footprints/
FP_BASE = "/usr/share/kicad/footprints"

FOOTPRINT_MAP = {
    # BGA packages
    "Package_BGA:BGA-698": ("Package_BGA.pretty", "BGA-625_21.0x21.0mm_Layout25x25_P0.8mm"),  # closest to 698-ball
    "Package_BGA:BGA-200": ("Package_BGA.pretty", "BGA-200_10x14.5mm_Layout12x22_P0.8x0.65mm"),
    "Package_BGA:BGA-153": ("Package_BGA.pretty", "BGA-153_8.0x8.0mm_Layout15x15_P0.5mm_Ball0.3mm_Pad0.25mm_NSMD"),
    "Package_BGA:BGA": ("Package_BGA.pretty", "BGA-100_11.0x11.0mm_Layout10x10_P1.0mm_Ball0.5mm_Pad0.4mm_NSMD"),
    # QFN packages
    "Package_QFN:QFN-88": ("Package_DFN_QFN.pretty", "ArtInChip_QFN-88-1EP_10x10mm_P0.4mm_EP6.74x6.74mm"),
    "Package_QFN:QFN-68": ("Package_DFN_QFN.pretty", "QFN-68-1EP_8x8mm_P0.4mm_EP5.2x5.2mm"),
    "Package_QFN:QFN-60-1EP_7x7mm_P0.4mm": ("Package_DFN_QFN.pretty", "QFN-60-1EP_7x7mm_P0.4mm_EP3.4x3.4mm"),
    "Package_QFN:QFN-40": ("Package_DFN_QFN.pretty", "QFN-40-1EP_5x5mm_P0.4mm_EP3.6x3.6mm"),
    "Package_QFN:QFN-24-1EP_4x4mm_P0.5mm": ("Package_DFN_QFN.pretty", "HVQFN-24-1EP_4x4mm_P0.5mm_EP2.5x2.5mm"),
    "Package_QFN:QFN-24": ("Package_DFN_QFN.pretty", "HVQFN-24-1EP_4x4mm_P0.5mm_EP2.5x2.5mm"),
    "Package_QFN:QFN-16": ("Package_DFN_QFN.pretty", "QFN-16-1EP_3x3mm_P0.5mm_EP1.7x1.7mm"),
    # SOT/SOD packages
    "Package_TO_SOT_SMD:SOT-23-6": ("Package_TO_SOT_SMD.pretty", "SOT-23-6"),
    "Package_TO_SOT_SMD:SOT-23-5": ("Package_TO_SOT_SMD.pretty", "SOT-23-5"),
    "Package_TO_SOT_SMD:SOT-23-8": ("Package_TO_SOT_SMD.pretty", "SOT-23-8"),
    "Package_TO_SOT_SMD:SOT-23": ("Package_TO_SOT_SMD.pretty", "SOT-23"),
    "Package_TO_SOT_SMD:SOT-363": ("Package_TO_SOT_SMD.pretty", "SOT-363_SC-70-6"),
    "Package_TO_SOT_SMD:SOT-553": ("Package_TO_SOT_SMD.pretty", "SOT-553"),
    # SO packages
    "Package_SO:SOP-16": ("Package_SO.pretty", "SOP-16_4.4x10.4mm_P1.27mm"),
    "Package_SO:SOP-10": ("Package_SO.pretty", "SOIC-8_3.9x4.9mm_P1.27mm"),  # SOP-10 not available, use SOIC-8 placeholder
    "Package_SO:SOP-8": ("Package_SO.pretty", "SOP-8_3.76x4.96mm_P1.27mm"),
    "Package_SO:SOIC-16W_7.5x10.3mm_P1.27mm": ("Package_SO.pretty", "SOIC-16W_7.5x10.3mm_P1.27mm"),
    "Package_SO:TSSOP-14_4.4x5mm_P0.65mm": ("Package_SO.pretty", "TSSOP-14_4.4x5mm_P0.65mm"),
    # Passive SMD
    "Capacitor_SMD:C_0402": ("Capacitor_SMD.pretty", "C_0402_1005Metric"),
    "Capacitor_SMD:C_0805": ("Capacitor_SMD.pretty", "C_0805_2012Metric"),
    "Capacitor_SMD:C_1206": ("Capacitor_SMD.pretty", "C_1206_3216Metric"),
    "Capacitor_SMD:CP_Elec_8x10.5": ("Capacitor_SMD.pretty", "CP_Elec_8x10.5"),
    "Capacitor_SMD:CP_Elec_6.3x5.8": ("Capacitor_SMD.pretty", "CP_Elec_6.3x5.8"),
    "Resistor_SMD:R_0402": ("Resistor_SMD.pretty", "R_0402_1005Metric"),
    "Resistor_SMD:R_0603": ("Resistor_SMD.pretty", "R_0603_1608Metric"),
    "Resistor_SMD:R_1206": ("Resistor_SMD.pretty", "R_1206_3216Metric"),
    "Resistor_SMD:R_2512": ("Resistor_SMD.pretty", "R_2512_6332Metric"),
    "Inductor_SMD:L_0402": ("Inductor_SMD.pretty", "L_0402_1005Metric"),
    "Inductor_SMD:L_4012": ("Inductor_SMD.pretty", "L_0805_2012Metric_Pad1.15x1.40mm_HandSolder"),
    "Inductor_SMD:L_6030": ("Inductor_SMD.pretty", "L_6.3x6.3_H3"),
    # SOP with different naming
    "Package_SO:SOP-10_3.9x4.9mm_P1.0mm": ("Package_SO.pretty", "SOIC-8_3.9x4.9mm_P1.27mm"),  # closest
    # Crystals
    "Crystal:Crystal_SMD_3225-4Pin": ("Crystal.pretty", "Crystal_SMD_3225-4Pin_3.2x2.5mm"),
    # Connectors
    "Connector_RJ:RJ45_PoE_Magnetics": ("Connector_RJ.pretty", "RJ45_Hanrun_HR911105A_Horizontal"),
    "Connector:M.2_B-key": ("Connector_PinHeader_2.54mm.pretty", "PinHeader_2x20_P2.54mm_Vertical"),  # M.2 placeholder
    "Connector_Card:SIM_Nano": ("Connector_Card.pretty", "nanoSIM_GCT_SIM8060-6-0-14-00"),
    "Connector_Audio:TRRS_3.5mm": ("Connector_Audio.pretty", "Jack_3.5mm_CUI_SJ1-3523N_Horizontal"),
    "Connector_USB:USB_C": ("Connector_USB.pretty", "USB_C_Receptacle_GCT_USB4105-xx-A_16P_TopMnt_Horizontal"),
    "Connector_HDMI:HDMI_Micro_D": ("Connector_Video.pretty", "HDMI_Micro-D_Molex_46765-2x0x"),
    "Connector_FFC-FPC:FPC_22pin": ("Connector_FFC-FPC.pretty", "Hirose_FH12-22S-0.5SH_1x22-1MP_P0.50mm_Horizontal"),
    "Connector_FFC-FPC:FPC_15pin": ("Connector_FFC-FPC.pretty", "Hirose_FH12-15S-0.5SH_1x15-1MP_P0.50mm_Horizontal"),
    "Connector_PinHeader_2.54mm:PinHeader_2x20_P2.54mm_Vertical": ("Connector_PinHeader_2.54mm.pretty", "PinHeader_2x20_P2.54mm_Vertical"),
    "Connector_PinHeader_2.54mm:PinHeader_1x10_P2.54mm_Vertical": ("Connector_PinHeader_2.54mm.pretty", "PinHeader_1x10_P2.54mm_Vertical"),
    "Connector_PinHeader_2.54mm:PinHeader_3x10_P2.54mm_Vertical": ("Connector_PinHeader_2.54mm.pretty", "PinHeader_2x20_P2.54mm_Vertical"),  # 3x10 not avail, use 2x20 placeholder
    "Connector_Coaxial:U.FL": ("Connector_Coaxial.pretty", "U.FL_Hirose_U.FL-R-SMT-1_Vertical"),
    "Connector_JST:JST_VH_B2P": ("Connector_JST.pretty", "JST_VH_B2P-VH_1x02_P3.96mm_Vertical"),
    "Connector_JST:JST_PH_B2B": ("Connector_JST.pretty", "JST_PH_B2B-PH-K_1x02_P2.00mm_Vertical"),
    # Mounting holes (already in PCB)
    "MountingHole:MountingHole_2.7mm_M2.5_Pad": ("MountingHole.pretty", "MountingHole_2.7mm_M2.5_Pad"),
}

# Component placement definitions
# Format: (reference, value, schematic_footprint, x_mm, y_mm, layer, rotation_deg)
# layer: "F.Cu" (top) or "B.Cu" (bottom)

PLACEMENTS = [
    # ========== TOP SIDE (F.Cu) ==========
    # --- RK3576 Compute Core (center-left) ---
    ("U1",  "RK3576",               "Package_BGA:BGA-698",           25, 28, "F.Cu", 0),
    ("U2",  "RK806-1",              "Package_QFN:QFN-68",            42, 16, "F.Cu", 0),

    # DDR4 (flanking SoC)
    ("U3",  "K4UBE3D4AB CH0",       "Package_BGA:BGA-200",           12, 12, "F.Cu", 0),
    ("U4",  "K4UBE3D4AB CH1",       "Package_BGA:BGA-200",           12, 44, "F.Cu", 0),

    # RK3576 decoupling caps
    ("C1",  "100nF",                "Capacitor_SMD:C_0402",          35, 20, "F.Cu", 0),
    ("C2",  "10uF",                 "Capacitor_SMD:C_0805",          35, 22, "F.Cu", 0),
    ("C4",  "10uF",                 "Capacitor_SMD:C_0805",          37, 20, "F.Cu", 0),
    ("C5",  "10uF",                 "Capacitor_SMD:C_0805",          37, 22, "F.Cu", 0),
    ("C6",  "10uF",                 "Capacitor_SMD:C_0805",          39, 20, "F.Cu", 0),
    ("C7",  "10uF",                 "Capacitor_SMD:C_0805",          39, 22, "F.Cu", 0),
    ("C8",  "10uF",                 "Capacitor_SMD:C_0805",          41, 20, "F.Cu", 0),
    ("C10", "100nF x8 VDD",         "Capacitor_SMD:C_0402",          6,  8,  "F.Cu", 0),
    ("C11", "100nF x8 VDDQ",        "Capacitor_SMD:C_0402",          8,  8,  "F.Cu", 0),
    ("C12", "100nF x8 VDD",         "Capacitor_SMD:C_0402",          6,  48, "F.Cu", 0),
    ("C13", "100nF x8 VDDQ",        "Capacitor_SMD:C_0402",          8,  48, "F.Cu", 0),
    ("C14", "100nF",                "Capacitor_SMD:C_0402",          40, 38, "F.Cu", 0),
    ("C15", "10uF",                 "Capacitor_SMD:C_0805",          42, 38, "F.Cu", 0),
    ("C16", "100nF",                "Capacitor_SMD:C_0402",          40, 42, "F.Cu", 0),
    ("R1",  "10k",                  "Resistor_SMD:R_0402",           42, 42, "F.Cu", 0),
    ("C21", "100nF x8 VDD_GPU",     "Capacitor_SMD:C_0402",          17, 20, "F.Cu", 0),
    ("C22", "100nF x6 VDD_NPU",     "Capacitor_SMD:C_0402",          17, 22, "F.Cu", 0),
    ("C23", "100nF x4 VDD_LOGIC",   "Capacitor_SMD:C_0402",          17, 24, "F.Cu", 0),
    ("C24", "10uF x4 bulk",         "Capacitor_SMD:C_0805",          17, 36, "F.Cu", 0),

    # --- Connectivity (right side of board) ---
    # Ethernet PHY + jack
    ("U7",  "RTL8211F-CG",          "Package_QFN:QFN-40",            58, 8,  "F.Cu", 0),
    ("J1",  "HR911105A",            "Connector_RJ:RJ45_PoE_Magnetics", 75, 8, "F.Cu", 90),
    ("Y3",  "25MHz",                "Crystal:Crystal_SMD_3225-4Pin",  54, 6,  "F.Cu", 0),
    ("C70", "100nF",                "Capacitor_SMD:C_0402",          54, 10, "F.Cu", 0),
    ("C71", "10uF",                 "Capacitor_SMD:C_0805",          56, 10, "F.Cu", 0),
    ("C72", "20pF",                 "Capacitor_SMD:C_0402",          52, 4,  "F.Cu", 0),
    ("C73", "20pF",                 "Capacitor_SMD:C_0402",          52, 8,  "F.Cu", 0),

    # WiFi M.2 module
    ("U8",  "RTL8852BS",            "Connector:M.2_B-key",           52, 28, "F.Cu", 0),
    ("J12", "WiFi Main",            "Connector_Coaxial:U.FL",        48, 22, "F.Cu", 0),
    ("J13", "WiFi Aux",             "Connector_Coaxial:U.FL",        48, 24, "F.Cu", 0),
    ("C74", "100nF",                "Capacitor_SMD:C_0402",          60, 22, "F.Cu", 0),
    ("C75", "10uF",                 "Capacitor_SMD:C_0805",          60, 24, "F.Cu", 0),
    ("C76", "100nF x4",             "Capacitor_SMD:C_0402",          60, 26, "F.Cu", 0),

    # SIM slot
    ("J2",  "Nano-SIM",             "Connector_Card:SIM_Nano",       70, 22, "F.Cu", 0),

    # Audio
    ("U10", "ES8316",               "Package_QFN:QFN-24",            65, 38, "F.Cu", 0),
    ("J3",  "3.5mm TRRS",           "Connector_Audio:TRRS_3.5mm",    80, 38, "F.Cu", 90),

    # USB-C connectors (along bottom-right edge)
    ("J4",  "USB-C #1",             "Connector_USB:USB_C",           80, 18, "F.Cu", 90),
    ("J5",  "USB-C #2",             "Connector_USB:USB_C",           80, 26, "F.Cu", 90),
    ("J6",  "USB-C #3",             "Connector_USB:USB_C",           80, 34, "F.Cu", 90),
    ("J7",  "USB-C #4",             "Connector_USB:USB_C",           80, 42, "F.Cu", 90),

    # HDMI
    ("J8",  "Micro-HDMI",           "Connector_HDMI:HDMI_Micro_D",   70, 50, "F.Cu", 0),

    # CSI camera connectors
    ("J9",  "CSI-1 4-lane",         "Connector_FFC-FPC:FPC_22pin",   50, 50, "F.Cu", 0),
    ("J10", "CSI-2 2-lane",         "Connector_FFC-FPC:FPC_15pin",   35, 50, "F.Cu", 0),

    # GPIO header (Pi 5 compatible position)
    ("J11", "2x20 GPIO",            "Connector_PinHeader_2.54mm:PinHeader_2x20_P2.54mm_Vertical", 42, 3.5, "F.Cu", 0),

    # ESD protection
    ("U11", "USBLC6-2SC6 x4",       "Package_TO_SOT_SMD:SOT-23-6",  72, 30, "F.Cu", 0),
    ("U12", "PRTR5V0U2X (HDMI)",     "Package_TO_SOT_SMD:SOT-363",   68, 48, "F.Cu", 0),
    ("U13", "PRTR5V0U2X (SIM)",      "Package_TO_SOT_SMD:SOT-363",   68, 20, "F.Cu", 0),

    # ========== BOTTOM SIDE (B.Cu) ==========
    # --- RP2350 Radio Module (bottom-left) ---
    ("U20", "RP2350A",              "Package_QFN:QFN-60-1EP_7x7mm_P0.4mm", 15, 15, "B.Cu", 0),
    ("C30", "100nF IOVDD",          "Capacitor_SMD:C_0402",          10, 10, "B.Cu", 0),
    ("C31", "100nF DVDD",           "Capacitor_SMD:C_0402",          12, 10, "B.Cu", 0),
    ("C32", "1uF VREG",             "Capacitor_SMD:C_0402",          10, 12, "B.Cu", 0),
    ("C33", "100nF USB",            "Capacitor_SMD:C_0402",          12, 12, "B.Cu", 0),
    ("C34", "15pF",                 "Capacitor_SMD:C_0402",          20, 10, "B.Cu", 0),
    ("C35", "15pF",                 "Capacitor_SMD:C_0402",          22, 10, "B.Cu", 0),
    ("C36", "100nF",                "Capacitor_SMD:C_0402",          10, 22, "B.Cu", 0),
    ("R2",  "10k CS",               "Resistor_SMD:R_0402",           22, 22, "B.Cu", 0),
    ("C38", "10uF",                 "Capacitor_SMD:C_0805",          22, 12, "B.Cu", 0),

    # WiFi/BLE (CYW43439) near RP2350
    ("C39", "100nF",                "Capacitor_SMD:C_0402",          28, 10, "B.Cu", 0),
    ("C40", "10uF",                 "Capacitor_SMD:C_0805",          28, 12, "B.Cu", 0),

    # LoRa (SX1262) near RP2350
    ("C41", "1.5pF",                "Capacitor_SMD:C_0402",          10, 26, "B.Cu", 0),
    ("L3",  "3.9nH",               "Inductor_SMD:L_0402",           12, 26, "B.Cu", 0),
    ("C42", "1.0pF",                "Capacitor_SMD:C_0402",          14, 26, "B.Cu", 0),

    # RP2350 expansion + power switches
    ("J21", "1x10 Expansion",       "Connector_PinHeader_2.54mm:PinHeader_1x10_P2.54mm_Vertical", 5, 35, "B.Cu", 0),
    ("R58", "100k",                 "Resistor_SMD:R_0402",           20, 24, "B.Cu", 0),
    ("R59", "100k",                 "Resistor_SMD:R_0402",           22, 24, "B.Cu", 0),
    ("Q1",  "Si2301 WiFi/LoRa",     "Package_TO_SOT_SMD:SOT-23",    24, 24, "B.Cu", 0),
    ("Q2",  "Si2301 cellular",      "Package_TO_SOT_SMD:SOT-23",    26, 24, "B.Cu", 0),

    # --- RK3506J Industrial (bottom center-right) ---
    ("U30", "RK3506J",              "Package_QFN:QFN-88",            55, 40, "B.Cu", 0),
    ("C50", "100nF x4 VDD",         "Capacitor_SMD:C_0402",          48, 36, "B.Cu", 0),
    ("C51", "100nF x4 VDDIO",       "Capacitor_SMD:C_0402",          48, 38, "B.Cu", 0),
    ("C52", "10uF bulk",            "Capacitor_SMD:C_0805",          48, 40, "B.Cu", 0),
    ("C53", "10uF bulk",            "Capacitor_SMD:C_0805",          48, 42, "B.Cu", 0),
    ("C54", "20pF",                 "Capacitor_SMD:C_0402",          62, 36, "B.Cu", 0),
    ("C55", "20pF",                 "Capacitor_SMD:C_0402",          62, 38, "B.Cu", 0),
    ("C56", "100nF x4",             "Capacitor_SMD:C_0402",          62, 40, "B.Cu", 0),
    ("C57", "100nF",                "Capacitor_SMD:C_0402",          62, 42, "B.Cu", 0),

    # CAN bus transceivers
    ("U34", "MCP2562FD #2",         "Package_TO_SOT_SMD:SOT-23-8",  70, 38, "B.Cu", 0),
    ("R62", "120R",                 "Resistor_SMD:R_0402",           68, 36, "B.Cu", 0),
    ("R63", "120R",                 "Resistor_SMD:R_0402",           68, 40, "B.Cu", 0),
    ("C58", "100nF",                "Capacitor_SMD:C_0402",          72, 36, "B.Cu", 0),
    ("C59", "100nF",                "Capacitor_SMD:C_0402",          72, 40, "B.Cu", 0),

    # Digital isolator + RS485
    ("U35", "ADUM1401",             "Package_SO:SOIC-16W_7.5x10.3mm_P1.27mm", 68, 46, "B.Cu", 0),
    ("C60", "100nF VDD1",           "Capacitor_SMD:C_0402",          62, 46, "B.Cu", 0),
    ("C61", "100nF VDD2",           "Capacitor_SMD:C_0402",          74, 46, "B.Cu", 0),
    ("U36", "SP3485",               "Package_SO:SOP-8",              78, 46, "B.Cu", 0),
    ("R64", "120R",                 "Resistor_SMD:R_0402",           78, 42, "B.Cu", 0),
    ("C62", "100nF",                "Capacitor_SMD:C_0402",          78, 44, "B.Cu", 0),

    # ESD + industrial I/O header
    ("U38", "PESD5V0S4UG",          "Package_TO_SOT_SMD:SOT-553",   78, 50, "B.Cu", 0),
    ("J30", "3x10 Industrial I/O",  "Connector_PinHeader_2.54mm:PinHeader_3x10_P2.54mm_Vertical", 75, 52, "B.Cu", 0),
    ("R66", "33R",                  "Resistor_SMD:R_0402",           64, 44, "B.Cu", 0),
    ("R67", "33R",                  "Resistor_SMD:R_0402",           64, 48, "B.Cu", 0),
    ("C63", "100nF",                "Capacitor_SMD:C_0402",          64, 50, "B.Cu", 0),

    # --- Power System (bottom-left to center) ---
    # Solar MPPT
    ("U40", "CN3722",               "Package_SO:SOP-16",             30, 36, "B.Cu", 0),
    ("J41", "JST PH Battery",       "Connector_JST:JST_PH_B2B",     5,  50, "B.Cu", 0),
    ("R43", "10k",                  "Resistor_SMD:R_0402",           24, 34, "B.Cu", 0),
    ("R44", "25k",                  "Resistor_SMD:R_0402",           24, 36, "B.Cu", 0),
    ("R46", "10k",                  "Resistor_SMD:R_0402",           24, 38, "B.Cu", 0),
    ("R50", "10k",                  "Resistor_SMD:R_0402",           24, 40, "B.Cu", 0),
    ("C93", "22uF/25V",             "Capacitor_SMD:C_1206",          36, 34, "B.Cu", 0),

    # Buck-boost 5V
    ("U41", "TPS61022DRLR",         "Package_TO_SOT_SMD:SOT-23-6",  36, 40, "B.Cu", 0),
    ("R40", "900k",                 "Resistor_SMD:R_0402",           34, 42, "B.Cu", 0),
    ("R41", "100k",                 "Resistor_SMD:R_0402",           34, 44, "B.Cu", 0),

    # LDO regulators
    ("R61", "4.7k",                 "Resistor_SMD:R_0402",           40, 34, "B.Cu", 0),
    ("C101","100nF",                "Capacitor_SMD:C_0402",          40, 36, "B.Cu", 0),

    # Power switches & monitoring
    ("Q3",  "Si2301",               "Package_TO_SOT_SMD:SOT-23",    42, 40, "B.Cu", 0),
    ("R57", "100k",                 "Resistor_SMD:R_0402",           42, 42, "B.Cu", 0),
    ("R51", "100k",                 "Resistor_SMD:R_0402",           42, 44, "B.Cu", 0),
    ("R52", "100k",                 "Resistor_SMD:R_0402",           44, 42, "B.Cu", 0),
    ("R54", "100k",                 "Resistor_SMD:R_0402",           44, 44, "B.Cu", 0),
    ("C109","100nF",                "Capacitor_SMD:C_0402",          44, 40, "B.Cu", 0),
    ("C110","100nF",                "Capacitor_SMD:C_0402",          44, 46, "B.Cu", 0),
    ("FB2", "BLM18AG102SN1D",       "Resistor_SMD:R_0603",           40, 40, "B.Cu", 0),

    # --- Signal Conditioning (bottom center) ---
    ("U50", "SN74LVC2G17",          "Package_TO_SOT_SMD:SOT-23-6",  30, 28, "B.Cu", 0),
    ("C80", "100nF",                "Capacitor_SMD:C_0402",          28, 28, "B.Cu", 0),
    ("R70", "33R",                  "Resistor_SMD:R_0402",           28, 30, "B.Cu", 0),
    ("R71", "33R",                  "Resistor_SMD:R_0402",           32, 30, "B.Cu", 0),
    ("U51", "SN74LVC2G17",          "Package_TO_SOT_SMD:SOT-23-6",  36, 28, "B.Cu", 0),
    ("C81", "100nF",                "Capacitor_SMD:C_0402",          34, 28, "B.Cu", 0),
    ("R72", "33R",                  "Resistor_SMD:R_0402",           34, 30, "B.Cu", 0),
    ("R73", "33R",                  "Resistor_SMD:R_0402",           38, 30, "B.Cu", 0),
    ("U52", "SN74LVC1G17",          "Package_TO_SOT_SMD:SOT-23-5",  40, 28, "B.Cu", 0),
    ("C82", "100nF",                "Capacitor_SMD:C_0402",          40, 30, "B.Cu", 0),
    ("U53", "SN74LVC1G17",          "Package_TO_SOT_SMD:SOT-23-5",  42, 28, "B.Cu", 0),
    ("C83", "100nF",                "Capacitor_SMD:C_0402",          42, 30, "B.Cu", 0),
    ("U54", "SN74LVC1G17",          "Package_TO_SOT_SMD:SOT-23-5",  44, 28, "B.Cu", 0),
    ("C84", "100nF",                "Capacitor_SMD:C_0402",          44, 30, "B.Cu", 0),
    ("U55", "SN74LVC1G17",          "Package_TO_SOT_SMD:SOT-23-5",  46, 28, "B.Cu", 0),
    ("C85", "100nF",                "Capacitor_SMD:C_0402",          46, 30, "B.Cu", 0),
    ("U56", "SN74LVC1G17",          "Package_TO_SOT_SMD:SOT-23-5",  48, 28, "B.Cu", 0),
    ("C86", "100nF",                "Capacitor_SMD:C_0402",          48, 30, "B.Cu", 0),
]


def resolve_footprint(fp_key):
    """Resolve schematic footprint name to library path and footprint name."""
    if fp_key in FOOTPRINT_MAP:
        lib_dir, fp_name = FOOTPRINT_MAP[fp_key]
        lib_path = os.path.join(FP_BASE, lib_dir)
        return lib_path, fp_name
    # Try fuzzy match — strip trailing details
    for key, (lib_dir, fp_name) in FOOTPRINT_MAP.items():
        if fp_key.startswith(key.split(':')[0] + ':'):
            base = fp_key.split(':')[1]
            if base in fp_name or fp_name.startswith(base):
                return os.path.join(FP_BASE, lib_dir), fp_name
    return None, None


def generate_pcb():
    """Use pcbnew Python API to place all footprints on the PCB."""
    try:
        import pcbnew
    except ImportError:
        print("  ERROR: pcbnew Python module not available.")
        print("  Run this script from KiCad's scripting console or ensure")
        print("  the pcbnew Python bindings are in your PYTHONPATH.")
        return False

    board = pcbnew.LoadBoard(PCB_FILE)

    # Track existing references to avoid duplicates
    existing_refs = set()
    for fp in board.GetFootprints():
        existing_refs.add(fp.GetReference())

    placed = 0
    skipped = 0
    failed = 0

    for ref, value, fp_key, x, y, layer, rot in PLACEMENTS:
        if ref in existing_refs:
            skipped += 1
            continue

        lib_path, fp_name = resolve_footprint(fp_key)
        if lib_path is None:
            print(f"  WARNING: No footprint mapping for {fp_key} ({ref})")
            failed += 1
            continue

        try:
            fp = pcbnew.FootprintLoad(lib_path, fp_name)
        except Exception as e:
            print(f"  WARNING: Could not load {fp_name} from {lib_path}: {e}")
            failed += 1
            continue

        if fp is None:
            print(f"  WARNING: FootprintLoad returned None for {fp_name} in {lib_path} ({ref})")
            failed += 1
            continue

        fp.SetReference(ref)
        fp.SetValue(value)

        # Position in nanometers
        pos = pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(y))
        fp.SetPosition(pos)

        # Layer
        if layer == "B.Cu":
            fp.Flip(pos, False)

        # Rotation
        if rot != 0:
            fp.SetOrientationDegrees(rot)

        board.Add(fp)
        existing_refs.add(ref)
        placed += 1

    # Add ground zone pours on In1.Cu (GND plane) and In4.Cu (GND plane)
    for layer_name in ["In1.Cu", "In4.Cu"]:
        layer_id = board.GetLayerID(layer_name)
        zone = pcbnew.ZONE(board)
        zone.SetLayer(layer_id)
        zone.SetNetCode(1)  # GND net
        zone.SetPriority(0)

        outline = zone.Outline()
        outline.NewOutline()
        outline.Append(pcbnew.FromMM(0), pcbnew.FromMM(0))
        outline.Append(pcbnew.FromMM(85), pcbnew.FromMM(0))
        outline.Append(pcbnew.FromMM(85), pcbnew.FromMM(56))
        outline.Append(pcbnew.FromMM(0), pcbnew.FromMM(56))
        board.Add(zone)

    # Add power zone on In3.Cu (Power plane) — 5V fill
    pwr_layer = board.GetLayerID("In3.Cu")
    zone5v = pcbnew.ZONE(board)
    zone5v.SetLayer(pwr_layer)
    zone5v.SetNetCode(2)  # 5V_SYS
    zone5v.SetPriority(1)

    outline = zone5v.Outline()
    outline.NewOutline()
    outline.Append(pcbnew.FromMM(0), pcbnew.FromMM(0))
    outline.Append(pcbnew.FromMM(85), pcbnew.FromMM(0))
    outline.Append(pcbnew.FromMM(85), pcbnew.FromMM(56))
    outline.Append(pcbnew.FromMM(0), pcbnew.FromMM(56))
    board.Add(zone5v)

    board.Save(PCB_FILE)

    print(f"  Placed: {placed} footprints")
    print(f"  Skipped (already exist): {skipped}")
    print(f"  Failed: {failed}")
    print(f"  Added GND zones on In1.Cu and In4.Cu, 5V zone on In3.Cu")

    return True


# ============================================================
# MAIN
# ============================================================

def main():
    print("=" * 60)
    print("Solarpunk Pi v3 — Wiring & PCB Generation")
    print("=" * 60)

    # Step 1: Wire schematic
    print("\n[1/2] Wiring top-level schematic...")
    wired = wire_top_level_schematic()
    if wired:
        print("  ✓ Schematic wiring complete")
    else:
        print("  → Schematic already wired or unchanged")

    # Step 2: Generate PCB
    print("\n[2/2] Generating PCB footprint placement...")
    pcb_ok = generate_pcb()
    if pcb_ok:
        print("  ✓ PCB generation complete")
    else:
        print("  → PCB generation skipped or failed")

    print("\n" + "=" * 60)
    print("NEXT STEPS:")
    print("  1. Open solarpunk-pi-v3.kicad_pro in KiCad 9")
    print("  2. In schematic editor: Inspect → Electrical Rules Check")
    print("  3. In PCB editor: Tools → Update PCB from Schematic")
    print("     (this will update net assignments from the wired schematic)")
    print("  4. In PCB editor: Inspect → Design Rules Check")
    print("  5. Route traces (interactive router or autorouter)")
    print("  6. Edit → Fill All Zones (B shortcut)")
    print("=" * 60)


if __name__ == "__main__":
    main()
