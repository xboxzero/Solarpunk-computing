#!/usr/bin/env python3
"""Place all footprints on the PCB. Run with: QT_QPA_PLATFORM=offscreen python3 place_pcb.py"""
import os, sys, gc

os.environ['QT_QPA_PLATFORM'] = 'offscreen'
os.environ.setdefault('DISPLAY', ':99')

import pcbnew

PCB = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'solarpunk-pi-v3.kicad_pcb')
FP = '/usr/share/kicad/footprints'

FPMAP = {
    'BGA698': ('Package_BGA.pretty', 'BGA-625_21.0x21.0mm_Layout25x25_P0.8mm'),
    'BGA200': ('Package_BGA.pretty', 'BGA-200_10x14.5mm_Layout12x22_P0.8x0.65mm'),
    'BGA153': ('Package_BGA.pretty', 'BGA-153_8.0x8.0mm_Layout15x15_P0.5mm_Ball0.3mm_Pad0.25mm_NSMD'),
    'BGA100': ('Package_BGA.pretty', 'BGA-100_11.0x11.0mm_Layout10x10_P1.0mm_Ball0.5mm_Pad0.4mm_NSMD'),
    'QFN88': ('Package_DFN_QFN.pretty', 'ArtInChip_QFN-88-1EP_10x10mm_P0.4mm_EP6.74x6.74mm'),
    'QFN68': ('Package_DFN_QFN.pretty', 'QFN-68-1EP_8x8mm_P0.4mm_EP5.2x5.2mm'),
    'QFN60': ('Package_DFN_QFN.pretty', 'QFN-60-1EP_7x7mm_P0.4mm_EP3.4x3.4mm'),
    'QFN40': ('Package_DFN_QFN.pretty', 'QFN-40-1EP_5x5mm_P0.4mm_EP3.6x3.6mm'),
    'QFN24': ('Package_DFN_QFN.pretty', 'HVQFN-24-1EP_4x4mm_P0.5mm_EP2.5x2.5mm'),
    'QFN16': ('Package_DFN_QFN.pretty', 'QFN-16-1EP_3x3mm_P0.5mm_EP1.7x1.7mm'),
    'SOT236': ('Package_TO_SOT_SMD.pretty', 'SOT-23-6'),
    'SOT235': ('Package_TO_SOT_SMD.pretty', 'SOT-23-5'),
    'SOT238': ('Package_TO_SOT_SMD.pretty', 'SOT-23-8'),
    'SOT23': ('Package_TO_SOT_SMD.pretty', 'SOT-23'),
    'SOT363': ('Package_TO_SOT_SMD.pretty', 'SOT-363_SC-70-6'),
    'SOT553': ('Package_TO_SOT_SMD.pretty', 'SOT-553'),
    'SOP16': ('Package_SO.pretty', 'SOP-16_4.4x10.4mm_P1.27mm'),
    'SOP8': ('Package_SO.pretty', 'SOP-8_3.76x4.96mm_P1.27mm'),
    'SOIC16W': ('Package_SO.pretty', 'SOIC-16W_7.5x10.3mm_P1.27mm'),
    'TSSOP14': ('Package_SO.pretty', 'TSSOP-14_4.4x5mm_P0.65mm'),
    'C0402': ('Capacitor_SMD.pretty', 'C_0402_1005Metric'),
    'C0805': ('Capacitor_SMD.pretty', 'C_0805_2012Metric'),
    'C1206': ('Capacitor_SMD.pretty', 'C_1206_3216Metric'),
    'R0402': ('Resistor_SMD.pretty', 'R_0402_1005Metric'),
    'R0603': ('Resistor_SMD.pretty', 'R_0603_1608Metric'),
    'L0402': ('Inductor_SMD.pretty', 'L_0402_1005Metric'),
    'L6030': ('Inductor_SMD.pretty', 'L_6.3x6.3_H3'),
    'XTAL': ('Crystal.pretty', 'Crystal_SMD_3225-4Pin_3.2x2.5mm'),
    'RJ45': ('Connector_RJ.pretty', 'RJ45_Hanrun_HR911105A_Horizontal'),
    'NSIM': ('Connector_Card.pretty', 'nanoSIM_GCT_SIM8060-6-0-14-00'),
    'TRRS': ('Connector_Audio.pretty', 'Jack_3.5mm_CUI_SJ1-3523N_Horizontal'),
    'USBC': ('Connector_USB.pretty', 'USB_C_Receptacle_GCT_USB4105-xx-A_16P_TopMnt_Horizontal'),
    'HDMI': ('Connector_Video.pretty', 'HDMI_Micro-D_Molex_46765-2x0x'),
    'FPC22': ('Connector_FFC-FPC.pretty', 'Hirose_FH12-22S-0.5SH_1x22-1MP_P0.50mm_Horizontal'),
    'FPC15': ('Connector_FFC-FPC.pretty', 'Hirose_FH12-15S-0.5SH_1x15-1MP_P0.50mm_Horizontal'),
    'PH2x20': ('Connector_PinHeader_2.54mm.pretty', 'PinHeader_2x20_P2.54mm_Vertical'),
    'PH1x10': ('Connector_PinHeader_2.54mm.pretty', 'PinHeader_1x10_P2.54mm_Vertical'),
    'UFL': ('Connector_Coaxial.pretty', 'U.FL_Hirose_U.FL-R-SMT-1_Vertical'),
    'JSTVH': ('Connector_JST.pretty', 'JST_VH_B2P-VH_1x02_P3.96mm_Vertical'),
    'JSTPH': ('Connector_JST.pretty', 'JST_PH_B2B-PH-K_1x02_P2.00mm_Vertical'),
}

# (ref, val, fpkey, x, y, side, rot)
P = [
    # === TOP (F.Cu) ===
    # RK3576 compute
    ('U1','RK3576','BGA698',25,28,'F',0),
    ('U2','RK806-1','QFN68',42,16,'F',0),
    ('U3','DDR CH0','BGA200',12,12,'F',0),
    ('U4','DDR CH1','BGA200',12,44,'F',0),
    ('C1','100nF','C0402',35,20,'F',0),
    ('C2','10uF','C0805',35,22,'F',0),
    ('C4','10uF','C0805',37,20,'F',0),
    ('C5','10uF','C0805',37,22,'F',0),
    ('C6','10uF','C0805',39,20,'F',0),
    ('C7','10uF','C0805',39,22,'F',0),
    ('C8','10uF','C0805',41,20,'F',0),
    ('C10','100nF','C0402',6,8,'F',0),
    ('C11','100nF','C0402',8,8,'F',0),
    ('C12','100nF','C0402',6,48,'F',0),
    ('C13','100nF','C0402',8,48,'F',0),
    ('C14','100nF','C0402',40,38,'F',0),
    ('C15','10uF','C0805',42,38,'F',0),
    ('C16','100nF','C0402',40,42,'F',0),
    ('R1','10k','R0402',42,42,'F',0),
    ('C21','100nF','C0402',17,20,'F',0),
    ('C22','100nF','C0402',17,22,'F',0),
    ('C23','100nF','C0402',17,24,'F',0),
    ('C24','10uF','C0805',17,36,'F',0),
    # Ethernet
    ('U7','RTL8211F','QFN40',58,8,'F',0),
    ('J1','RJ45','RJ45',75,8,'F',90),
    ('Y3','25MHz','XTAL',54,6,'F',0),
    ('C70','100nF','C0402',54,10,'F',0),
    ('C71','10uF','C0805',56,10,'F',0),
    ('C72','20pF','C0402',52,4,'F',0),
    ('C73','20pF','C0402',52,8,'F',0),
    # WiFi M.2
    ('U8','RTL8852BS','PH2x20',52,28,'F',0),
    ('J12','WiFi Main','UFL',48,22,'F',0),
    ('J13','WiFi Aux','UFL',48,24,'F',0),
    ('C74','100nF','C0402',60,22,'F',0),
    ('C75','10uF','C0805',60,24,'F',0),
    ('C76','100nF','C0402',60,26,'F',0),
    # SIM
    ('J2','Nano-SIM','NSIM',70,22,'F',0),
    # Audio
    ('U10','ES8316','QFN24',65,38,'F',0),
    ('J3','TRRS','TRRS',80,38,'F',90),
    # USB-C
    ('J4','USB-C 1','USBC',80,18,'F',90),
    ('J5','USB-C 2','USBC',80,26,'F',90),
    ('J6','USB-C 3','USBC',80,34,'F',90),
    ('J7','USB-C 4','USBC',80,42,'F',90),
    # HDMI
    ('J8','HDMI','HDMI',70,50,'F',0),
    # CSI
    ('J9','CSI-1','FPC22',50,50,'F',0),
    ('J10','CSI-2','FPC15',35,50,'F',0),
    # GPIO
    ('J11','GPIO','PH2x20',42,3.5,'F',0),
    # ESD
    ('U11','USBLC6','SOT236',72,30,'F',0),
    ('U12','PRTR5V0U2X','SOT363',68,48,'F',0),
    ('U13','PRTR5V0U2X','SOT363',68,20,'F',0),

    # === BOTTOM (B.Cu) ===
    # RP2350
    ('U20','RP2350A','QFN60',15,15,'B',0),
    ('C30','100nF','C0402',10,10,'B',0),
    ('C31','100nF','C0402',12,10,'B',0),
    ('C32','1uF','C0402',10,12,'B',0),
    ('C33','100nF','C0402',12,12,'B',0),
    ('C34','15pF','C0402',20,10,'B',0),
    ('C35','15pF','C0402',22,10,'B',0),
    ('C36','100nF','C0402',10,22,'B',0),
    ('R2','10k','R0402',22,22,'B',0),
    ('C38','10uF','C0805',22,12,'B',0),
    ('C39','100nF','C0402',28,10,'B',0),
    ('C40','10uF','C0805',28,12,'B',0),
    ('C41','1.5pF','C0402',10,26,'B',0),
    ('L3','3.9nH','L0402',12,26,'B',0),
    ('C42','1.0pF','C0402',14,26,'B',0),
    ('J21','Expansion','PH1x10',5,35,'B',0),
    ('R58','100k','R0402',20,24,'B',0),
    ('R59','100k','R0402',22,24,'B',0),
    ('Q1','Si2301','SOT23',24,24,'B',0),
    ('Q2','Si2301','SOT23',26,24,'B',0),
    # RK3506J
    ('U30','RK3506J','QFN88',55,40,'B',0),
    ('C50','100nF','C0402',48,36,'B',0),
    ('C51','100nF','C0402',48,38,'B',0),
    ('C52','10uF','C0805',48,40,'B',0),
    ('C53','10uF','C0805',48,42,'B',0),
    ('C54','20pF','C0402',62,36,'B',0),
    ('C55','20pF','C0402',62,38,'B',0),
    ('C56','100nF','C0402',62,40,'B',0),
    ('C57','100nF','C0402',62,42,'B',0),
    # CAN
    ('U34','MCP2562FD','SOT238',70,38,'B',0),
    ('R62','120R','R0402',68,36,'B',0),
    ('R63','120R','R0402',68,40,'B',0),
    ('C58','100nF','C0402',72,36,'B',0),
    ('C59','100nF','C0402',72,40,'B',0),
    # Isolator + RS485
    ('U35','ADUM1401','SOIC16W',68,46,'B',0),
    ('C60','100nF','C0402',62,46,'B',0),
    ('C61','100nF','C0402',74,46,'B',0),
    ('U36','SP3485','SOP8',78,46,'B',0),
    ('R64','120R','R0402',78,42,'B',0),
    ('C62','100nF','C0402',78,44,'B',0),
    # ESD + I/O
    ('U38','PESD5V0S4UG','SOT553',78,50,'B',0),
    ('J30','Ind I/O','PH2x20',75,52,'B',0),
    ('R66','33R','R0402',64,44,'B',0),
    ('R67','33R','R0402',64,48,'B',0),
    ('C63','100nF','C0402',64,50,'B',0),
    # Power - Solar MPPT
    ('U40','CN3722','SOP16',30,36,'B',0),
    ('J41','Battery','JSTPH',5,50,'B',0),
    ('R43','10k','R0402',24,34,'B',0),
    ('R44','25k','R0402',24,36,'B',0),
    ('R46','10k','R0402',24,38,'B',0),
    ('R50','10k','R0402',24,40,'B',0),
    ('C93','22uF','C1206',36,34,'B',0),
    # Buck-boost
    ('U41','TPS61022','SOT236',36,40,'B',0),
    ('R40','900k','R0402',34,42,'B',0),
    ('R41','100k','R0402',34,44,'B',0),
    # LDO
    ('R61','4.7k','R0402',40,34,'B',0),
    ('C101','100nF','C0402',40,36,'B',0),
    # Power switches
    ('Q3','Si2301','SOT23',42,40,'B',0),
    ('R57','100k','R0402',42,42,'B',0),
    ('R51','100k','R0402',42,44,'B',0),
    ('R52','100k','R0402',44,42,'B',0),
    ('R54','100k','R0402',44,44,'B',0),
    ('C109','100nF','C0402',44,40,'B',0),
    ('C110','100nF','C0402',44,46,'B',0),
    ('FB2','BLM18AG','R0603',40,40,'B',0),
    # Signal conditioning
    ('U50','SN74LVC2G17','SOT236',30,28,'B',0),
    ('C80','100nF','C0402',28,28,'B',0),
    ('R70','33R','R0402',28,30,'B',0),
    ('R71','33R','R0402',32,30,'B',0),
    ('U51','SN74LVC2G17','SOT236',36,28,'B',0),
    ('C81','100nF','C0402',34,28,'B',0),
    ('R72','33R','R0402',34,30,'B',0),
    ('R73','33R','R0402',38,30,'B',0),
    ('U52','SN74LVC1G17','SOT235',40,28,'B',0),
    ('C82','100nF','C0402',40,30,'B',0),
    ('U53','SN74LVC1G17','SOT235',42,28,'B',0),
    ('C83','100nF','C0402',42,30,'B',0),
    ('U54','SN74LVC1G17','SOT235',44,28,'B',0),
    ('C84','100nF','C0402',44,30,'B',0),
    ('U55','SN74LVC1G17','SOT235',46,28,'B',0),
    ('C85','100nF','C0402',46,30,'B',0),
    ('U56','SN74LVC1G17','SOT235',48,28,'B',0),
    ('C86','100nF','C0402',48,30,'B',0),
]


def main():
    board = pcbnew.LoadBoard(PCB)
    existing = set(f.GetReference() for f in board.GetFootprints())
    print(f'Board loaded: {len(existing)} existing footprints')

    placed = 0
    failed = 0

    for ref, val, fpk, x, y, side, rot in P:
        if ref in existing:
            continue

        m = FPMAP.get(fpk)
        if not m:
            print(f'  NO MAP: {fpk} ({ref})')
            failed += 1
            continue

        lib_dir, fp_name = m
        lib_path = os.path.join(FP, lib_dir)

        try:
            fp = pcbnew.FootprintLoad(lib_path, fp_name)
        except Exception as e:
            print(f'  LOAD ERR: {fp_name} ({ref}): {e}')
            fp = None

        if fp is None:
            print(f'  LOAD FAIL: {fp_name} ({ref})')
            failed += 1
            continue

        fp.SetReference(ref)
        fp.SetValue(val)
        pos = pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(y))
        fp.SetPosition(pos)

        if side == 'B':
            fp.Flip(pos, False)
        if rot:
            fp.SetOrientationDegrees(rot)

        board.Add(fp)
        existing.add(ref)
        placed += 1

    print(f'Placed: {placed}, Failed: {failed}')
    print(f'Total footprints: {len(board.GetFootprints())}')

    # GND zone pours
    for lname in ['In1.Cu', 'In4.Cu']:
        lid = board.GetLayerID(lname)
        z = pcbnew.ZONE(board)
        z.SetLayer(lid)
        z.SetNetCode(1)  # GND
        z.SetPriority(0)
        o = z.Outline()
        o.NewOutline()
        for cx, cy in [(0,0),(85,0),(85,56),(0,56)]:
            o.Append(pcbnew.FromMM(cx), pcbnew.FromMM(cy))
        board.Add(z)

    # 5V zone on power plane
    lid = board.GetLayerID('In3.Cu')
    z = pcbnew.ZONE(board)
    z.SetLayer(lid)
    z.SetNetCode(2)  # 5V_SYS
    z.SetPriority(1)
    o = z.Outline()
    o.NewOutline()
    for cx, cy in [(0,0),(85,0),(85,56),(0,56)]:
        o.Append(pcbnew.FromMM(cx), pcbnew.FromMM(cy))
    board.Add(z)

    print('Saving board...')
    board.Save(PCB)
    print('DONE')


if __name__ == '__main__':
    main()
