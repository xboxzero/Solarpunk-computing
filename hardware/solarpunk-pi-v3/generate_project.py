#!/usr/bin/env python3
"""
Solarpunk Pi v3 — KiCad 9 Project Generator
Generates hierarchical schematics, custom symbol library, PCB with 6-layer stackup,
and project configuration from the v3 datasheet specification.
"""

import uuid
import json
import os
import math

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_NAME = "solarpunk-pi-v3"

def uid():
    return str(uuid.uuid4())

# ============================================================
# 1. PROJECT FILE (.kicad_pro)
# ============================================================
def generate_project_file():
    project = {
        "board": {
            "3dviewports": [],
            "design_settings": {
                "defaults": {
                    "apply_defaults_to_fp_fields": False,
                    "apply_defaults_to_fp_shapes": False,
                    "apply_defaults_to_fp_text": False,
                    "board_outline_line_width": 0.1,
                    "copper_line_width": 0.2,
                    "copper_text_italic": False,
                    "copper_text_size_h": 1.5,
                    "copper_text_size_v": 1.5,
                    "copper_text_thickness": 0.3,
                    "copper_text_upright": False,
                    "courtyard_line_width": 0.05,
                    "dimension_precision": 4,
                    "fab_line_width": 0.1,
                    "fab_text_italic": False,
                    "fab_text_size_h": 1.0,
                    "fab_text_size_v": 1.0,
                    "fab_text_thickness": 0.15,
                    "fab_text_upright": False,
                    "other_line_width": 0.1,
                    "other_text_italic": False,
                    "other_text_size_h": 1.0,
                    "other_text_size_v": 1.0,
                    "other_text_thickness": 0.15,
                    "other_text_upright": False,
                    "pads": {
                        "drill": 0.762,
                        "height": 1.524,
                        "width": 1.524
                    },
                    "silk_line_width": 0.1,
                    "silk_text_italic": False,
                    "silk_text_size_h": 1.0,
                    "silk_text_size_v": 1.0,
                    "silk_text_thickness": 0.1,
                    "silk_text_upright": False,
                    "zones": {
                        "min_clearance": 0.5
                    }
                },
                "diff_pair_dimensions": [
                    {"gap": 0.1, "via_gap": 0, "width": 0.09},
                    {"gap": 0.12, "via_gap": 0, "width": 0.085},
                    {"gap": 0.12, "via_gap": 0, "width": 0.12},
                    {"gap": 0.15, "via_gap": 0, "width": 0.075},
                    {"gap": 0.12, "via_gap": 0, "width": 0.10}
                ],
                "drc_exclusions": [],
                "meta": {"version": 2},
                "rule_severities": {
                    "annular_width": "error",
                    "clearance": "error",
                    "connection_width": "warning",
                    "copper_edge_clearance": "error",
                    "courtyards_overlap": "error",
                    "diff_pair_gap_out_of_range": "error",
                    "diff_pair_uncoupled_length_too_long": "error",
                    "drill_out_of_range": "error",
                    "duplicate_footprints": "warning",
                    "extra_footprint": "warning",
                    "footprint": "error",
                    "hole_clearance": "error",
                    "hole_near_hole": "error",
                    "holes_co_located": "warning",
                    "invalid_outline": "error",
                    "isolated_copper": "warning",
                    "item_on_disabled_layer": "error",
                    "items_not_allowed": "error",
                    "length_out_of_range": "error",
                    "lib_footprint_issues": "warning",
                    "lib_footprint_mismatch": "warning",
                    "malformed_courtyard": "error",
                    "microvia_drill_out_of_range": "error",
                    "missing_courtyard": "ignore",
                    "missing_footprint": "warning",
                    "net_conflict": "warning",
                    "npth_inside_courtyard": "ignore",
                    "padstack": "warning",
                    "pth_inside_courtyard": "ignore",
                    "shorting_items": "error",
                    "silk_edge_clearance": "warning",
                    "silk_over_copper": "warning",
                    "silk_overlap": "warning",
                    "skew_out_of_range": "error",
                    "solder_mask_bridge": "warning",
                    "starved_thermal": "warning",
                    "text_height": "warning",
                    "text_thickness": "warning",
                    "through_hole_pad_without_hole": "error",
                    "too_many_vias": "warning",
                    "track_dangling": "warning",
                    "track_width": "error",
                    "tracks_crossing": "error",
                    "unconnected_items": "error",
                    "unresolved_variable": "error",
                    "via_dangling": "warning",
                    "zones_intersect": "error"
                },
                "rules": {
                    "max_error": 0.005,
                    "min_clearance": 0.09,
                    "min_connection": 0,
                    "min_copper_edge_clearance": 0.3,
                    "min_hole_clearance": 0.25,
                    "min_hole_to_hole": 0.25,
                    "min_microvia_diameter": 0.3,
                    "min_microvia_drill": 0.1,
                    "min_resolved_spokes": 2,
                    "min_silk_clearance": 0.0,
                    "min_text_height": 0.5,
                    "min_text_thickness": 0.08,
                    "min_through_hole_diameter": 0.2,
                    "min_track_width": 0.09,
                    "min_via_annular_width": 0.1,
                    "min_via_diameter": 0.4,
                    "solder_mask_to_copper_clearance": 0.0,
                    "use_height_for_length_calcs": True
                },
                "teardrop_options": [
                    {"td_onpadsmd": True, "td_onroundshapesonly": False,
                     "td_ontrackend": False, "td_onviapad": True}
                ],
                "teardrop_parameters": [
                    {"td_allow_use_two_tracks": True, "td_curve_segcount": 0,
                     "td_height_ratio": 1.0, "td_length_ratio": 0.5,
                     "td_maxheight": 2.0, "td_maxlen": 1.0,
                     "td_on_pad_in_zone": False, "td_target_name": "td_round_shape",
                     "td_width_to_size_filter_ratio": 0.9},
                    {"td_allow_use_two_tracks": True, "td_curve_segcount": 0,
                     "td_height_ratio": 1.0, "td_length_ratio": 0.5,
                     "td_maxheight": 2.0, "td_maxlen": 1.0,
                     "td_on_pad_in_zone": False, "td_target_name": "td_rect_shape",
                     "td_width_to_size_filter_ratio": 0.9},
                    {"td_allow_use_two_tracks": True, "td_curve_segcount": 0,
                     "td_height_ratio": 1.0, "td_length_ratio": 0.5,
                     "td_maxheight": 2.0, "td_maxlen": 1.0,
                     "td_on_pad_in_zone": False, "td_target_name": "td_track_end",
                     "td_width_to_size_filter_ratio": 0.9}
                ],
                "track_widths": [0.0, 0.09, 0.1, 0.12, 0.15, 0.2, 0.25, 0.5],
                "tuning_pattern_settings": {
                    "diff_pair_defaults": {"corner_radius_percentage": 80,
                                           "corner_style": 1, "max_amplitude": 1.0,
                                           "min_amplitude": 0.2, "single_sided": False,
                                           "spacing": 0.6},
                    "diff_pair_skew_defaults": {"corner_radius_percentage": 80,
                                                "corner_style": 1, "max_amplitude": 1.0,
                                                "min_amplitude": 0.2, "single_sided": False,
                                                "spacing": 0.6},
                    "single_track_defaults": {"corner_radius_percentage": 80,
                                              "corner_style": 1, "max_amplitude": 1.0,
                                              "min_amplitude": 0.2, "single_sided": False,
                                              "spacing": 0.6}
                },
                "via_dimensions": [
                    {"diameter": 0, "drill": 0},
                    {"diameter": 0.4, "drill": 0.2},
                    {"diameter": 0.6, "drill": 0.3}
                ],
                "zones_allow_external_fillets": False
            },
            "ipc2581": {"dist": "", "fabr": "", "fileformatversion": ""},
            "layer_pairs": [],
            "layer_presets": [],
            "viewports": []
        },
        "boards": [],
        "cvpcb": {"equivalence_files": []},
        "libraries": {
            "pinned_footprint_libs": [],
            "pinned_symbol_libs": []
        },
        "meta": {
            "filename": f"{PROJECT_NAME}.kicad_pro",
            "version": 2
        },
        "net_settings": {
            "classes": [
                {
                    "bus_width": 12,
                    "clearance": 0.15,
                    "diff_pair_gap": 0.15,
                    "diff_pair_via_gap": 0.25,
                    "diff_pair_width": 0.15,
                    "line_style": 0,
                    "microvia_diameter": 0.3,
                    "microvia_drill": 0.1,
                    "name": "Default",
                    "pcb_color": "rgba(0, 0, 0, 0.000)",
                    "schematic_color": "rgba(0, 0, 0, 0.000)",
                    "track_width": 0.15,
                    "via_diameter": 0.4,
                    "via_drill": 0.2,
                    "wire_width": 6
                },
                {
                    "bus_width": 12,
                    "clearance": 0.1,
                    "diff_pair_gap": 0.1,
                    "diff_pair_via_gap": 0.25,
                    "diff_pair_width": 0.1,
                    "line_style": 0,
                    "microvia_diameter": 0.3,
                    "microvia_drill": 0.1,
                    "name": "DDR_DQ",
                    "pcb_color": "rgba(255, 0, 0, 0.800)",
                    "schematic_color": "rgba(255, 0, 0, 0.800)",
                    "track_width": 0.1,
                    "via_diameter": 0.4,
                    "via_drill": 0.2,
                    "wire_width": 6
                },
                {
                    "bus_width": 12,
                    "clearance": 0.1,
                    "diff_pair_gap": 0.1,
                    "diff_pair_via_gap": 0.25,
                    "diff_pair_width": 0.09,
                    "line_style": 0,
                    "microvia_diameter": 0.3,
                    "microvia_drill": 0.1,
                    "name": "DDR_CLK",
                    "pcb_color": "rgba(255, 50, 50, 0.800)",
                    "schematic_color": "rgba(255, 50, 50, 0.800)",
                    "track_width": 0.09,
                    "via_diameter": 0.4,
                    "via_drill": 0.2,
                    "wire_width": 6
                },
                {
                    "bus_width": 12,
                    "clearance": 0.12,
                    "diff_pair_gap": 0.12,
                    "diff_pair_via_gap": 0.25,
                    "diff_pair_width": 0.085,
                    "line_style": 0,
                    "microvia_diameter": 0.3,
                    "microvia_drill": 0.1,
                    "name": "USB_HS",
                    "pcb_color": "rgba(0, 200, 0, 0.800)",
                    "schematic_color": "rgba(0, 200, 0, 0.800)",
                    "track_width": 0.085,
                    "via_diameter": 0.4,
                    "via_drill": 0.2,
                    "wire_width": 6
                },
                {
                    "bus_width": 12,
                    "clearance": 0.12,
                    "diff_pair_gap": 0.12,
                    "diff_pair_via_gap": 0.25,
                    "diff_pair_width": 0.12,
                    "line_style": 0,
                    "microvia_diameter": 0.3,
                    "microvia_drill": 0.1,
                    "name": "PCIE",
                    "pcb_color": "rgba(0, 100, 255, 0.800)",
                    "schematic_color": "rgba(0, 100, 255, 0.800)",
                    "track_width": 0.12,
                    "via_diameter": 0.4,
                    "via_drill": 0.2,
                    "wire_width": 6
                },
                {
                    "bus_width": 12,
                    "clearance": 0.15,
                    "diff_pair_gap": 0.15,
                    "diff_pair_via_gap": 0.25,
                    "diff_pair_width": 0.075,
                    "line_style": 0,
                    "microvia_diameter": 0.3,
                    "microvia_drill": 0.1,
                    "name": "HDMI",
                    "pcb_color": "rgba(200, 0, 200, 0.800)",
                    "schematic_color": "rgba(200, 0, 200, 0.800)",
                    "track_width": 0.075,
                    "via_diameter": 0.4,
                    "via_drill": 0.2,
                    "wire_width": 6
                },
                {
                    "bus_width": 12,
                    "clearance": 0.12,
                    "diff_pair_gap": 0.12,
                    "diff_pair_via_gap": 0.25,
                    "diff_pair_width": 0.1,
                    "line_style": 0,
                    "microvia_diameter": 0.3,
                    "microvia_drill": 0.1,
                    "name": "MIPI_CSI",
                    "pcb_color": "rgba(0, 200, 200, 0.800)",
                    "schematic_color": "rgba(0, 200, 200, 0.800)",
                    "track_width": 0.1,
                    "via_diameter": 0.4,
                    "via_drill": 0.2,
                    "wire_width": 6
                },
                {
                    "bus_width": 12,
                    "clearance": 0.15,
                    "diff_pair_gap": 0.15,
                    "diff_pair_via_gap": 0.25,
                    "diff_pair_width": 0.15,
                    "line_style": 0,
                    "microvia_diameter": 0.3,
                    "microvia_drill": 0.1,
                    "name": "SDIO",
                    "pcb_color": "rgba(255, 165, 0, 0.800)",
                    "schematic_color": "rgba(255, 165, 0, 0.800)",
                    "track_width": 0.15,
                    "via_diameter": 0.4,
                    "via_drill": 0.2,
                    "wire_width": 6
                },
                {
                    "bus_width": 12,
                    "clearance": 0.25,
                    "diff_pair_gap": 0.25,
                    "diff_pair_via_gap": 0.25,
                    "diff_pair_width": 0.5,
                    "line_style": 0,
                    "microvia_diameter": 0.3,
                    "microvia_drill": 0.1,
                    "name": "POWER",
                    "pcb_color": "rgba(255, 0, 0, 1.000)",
                    "schematic_color": "rgba(255, 0, 0, 1.000)",
                    "track_width": 0.5,
                    "via_diameter": 0.6,
                    "via_drill": 0.3,
                    "wire_width": 6
                }
            ],
            "meta": {"version": 3},
            "net_colors": None
        },
        "pcbnew": {
            "last_paths": {"gencad": "", "idf": "", "netlist": "", "plot": "",
                           "pos_files": "", "specctra_dsn": "", "step": "",
                           "svg": "", "vrml": ""},
            "page_layout_descr_file": ""
        },
        "schematic": {
            "annotate_start_num": 1,
            "bom_export_filename": "",
            "bom_fmt_presets": [],
            "bom_fmt_settings": {"field_delimiter": ",", "keep_line_breaks": False,
                                 "keep_tabs": False, "name": "", "ref_delimiter": ",",
                                 "ref_range_delimiter": "", "string_delimiter": "\""},
            "bom_presets": [],
            "connection_grid_size": 50.0,
            "drawing": {
                "dashed_lines_dash_length_ratio": 12.0,
                "dashed_lines_gap_length_ratio": 3.0,
                "default_line_thickness": 6.0,
                "default_text_size": 50.0,
                "field_names": [],
                "intersheets_ref_own_page": False,
                "intersheets_ref_prefix": "",
                "intersheets_ref_short": False,
                "intersheets_ref_show": False,
                "intersheets_ref_suffix": "",
                "junction_size_choice": 3,
                "label_size_ratio": 0.375,
                "operating_point_overlay_i_precision": 3,
                "operating_point_overlay_i_range": "~A",
                "operating_point_overlay_v_precision": 3,
                "operating_point_overlay_v_range": "~V",
                "overbar_offset_ratio": 1.23,
                "pin_symbol_size": 25.0,
                "text_offset_ratio": 0.15
            },
            "legacy_lib_dir": "",
            "legacy_lib_list": [],
            "meta": {"version": 1},
            "net_format_name": "",
            "page_layout_descr_file": "",
            "plot_directory": "",
            "ng_spice": {
                "fix_include_paths": True,
                "meta": {"version": 0},
                "model_mode": 0,
                "ngspice": {"model_mode": 0}
            }
        },
        "sheets": [],
        "text_variables": {
            "REVISION": "3.0",
            "COMPANY": "Solarpunk Computing",
            "TITLE": "Solarpunk Pi v3 — Triple-Processor Solar Edge Computer",
            "DATE": "2026-03"
        }
    }

    path = os.path.join(PROJECT_DIR, f"{PROJECT_NAME}.kicad_pro")
    with open(path, 'w') as f:
        json.dump(project, f, indent=2)
    print(f"  Created {path}")


# ============================================================
# 2. CUSTOM SYMBOL LIBRARY
# ============================================================
def sym_property(idx, key, value, x, y, size=1.27, hide=True):
    hide_str = "hide yes" if hide else ""
    return f"""    (property "{key}" "{value}"
      (at {x} {y} 0)
      (effects (font (size {size} {size})) {hide_str})
      (id {idx})
    )"""

# Pin registry — populated automatically by make_symbol()
CUSTOM_PINS = {}

def make_symbol(name, ref_prefix, footprint, description, pins, width=20, datasheet=""):
    """Generate a KiCad symbol with given pins.
    pins: list of (name, number, x, y, direction, etype)
    direction: L/R/U/D  etype: input/output/bidirectional/passive/power_in/power_out
    """
    # Auto-register pin positions for wired_sym()
    CUSTOM_PINS[name] = [(pname, px, py) for pname, _pnum, px, py, _dir, _etype in pins]
    # Calculate bounding box
    pin_entries = []
    for pname, pnum, px, py, direction, etype in pins:
        dir_map = {"L": 180, "R": 0, "U": 90, "D": 270}
        angle = dir_map.get(direction, 0)
        pin_entries.append(
            f'      (pin {etype} line (at {px} {py} {angle}) (length 2.54)\n'
            f'        (name "{pname}" (effects (font (size 1.016 1.016))))\n'
            f'        (number "{pnum}" (effects (font (size 1.016 1.016))))\n'
            f'      )'
        )

    hw = width / 2
    # Find Y extent from pins
    ys = [py for _, _, _, py, _, _ in pins] if pins else [0]
    y_min = min(ys) - 2.54
    y_max = max(ys) + 2.54

    symbol_uuid = uid()

    return f"""  (symbol "{name}"
    (pin_names (offset 1.016))
    (exclude_from_sim no)
    (in_bom yes)
    (on_board yes)
{sym_property(0, "Reference", ref_prefix, 0, y_max + 2.54, hide=False)}
{sym_property(1, "Value", name, 0, y_max + 0.5, hide=False)}
{sym_property(2, "Footprint", footprint, 0, y_min - 1.5)}
{sym_property(3, "Datasheet", datasheet, 0, y_min - 3.5)}
{sym_property(4, "Description", description, 0, y_min - 5.5)}
    (symbol "{name}_1_1"
      (rectangle (start {-hw} {y_max}) (end {hw} {y_min})
        (stroke (width 0.254) (type default))
        (fill (type background))
      )
{chr(10).join(pin_entries)}
    )
  )"""


def generate_symbol_library():
    symbols = []

    # --- RK3576 (simplified — key interface pins grouped) ---
    rk3576_pins = []
    y = 30
    # Power pins (left side)
    power_pins = [
        ("VDD_CPU_BIG", "A1"), ("VDD_CPU_LIT", "A2"), ("VDD_GPU", "A3"),
        ("VDD_NPU", "A4"), ("VDD_LOGIC", "A5"), ("VCC_DDR", "A6"),
        ("VCC_3V3", "A7"), ("VCC_1V8", "A8"), ("GND", "A9"),
        ("PWRGD", "A10"), ("RESET_N", "A11"),
    ]
    for pname, pnum in power_pins:
        etype = "power_in" if pname != "PWRGD" else "input"
        if pname == "RESET_N":
            etype = "input"
        rk3576_pins.append((pname, pnum, -22.86, y, "R", etype))
        y -= 2.54

    y -= 2.54
    # DDR interface (left side)
    ddr_pins = [
        ("DDR_DQ[0:31]", "B1"), ("DDR_DQS[0:3]", "B2"), ("DDR_DM[0:3]", "B3"),
        ("DDR_A[0:15]", "B4"), ("DDR_BA[0:2]", "B5"), ("DDR_CK_P", "B6"),
        ("DDR_CK_N", "B7"), ("DDR_CKE", "B8"), ("DDR_CS_N", "B9"),
        ("DDR_RAS_N", "B10"), ("DDR_CAS_N", "B11"), ("DDR_WE_N", "B12"),
        ("DDR_ODT", "B13"), ("DDR_RESET_N", "B14"),
    ]
    for pname, pnum in ddr_pins:
        rk3576_pins.append((pname, pnum, -22.86, y, "R", "bidirectional"))
        y -= 2.54

    y = 30
    # Right side — interfaces
    iface_pins = [
        ("PCIe_TX_P", "C1", "output"), ("PCIe_TX_N", "C2", "output"),
        ("PCIe_RX_P", "C3", "input"), ("PCIe_RX_N", "C4", "input"),
        ("PCIe_REFCLK_P", "C5", "input"), ("PCIe_REFCLK_N", "C6", "input"),
        ("USB3_TX_P", "C7", "output"), ("USB3_TX_N", "C8", "output"),
        ("USB3_RX_P", "C9", "input"), ("USB3_RX_N", "C10", "input"),
        ("USB2_OTG0_DP", "C11", "bidirectional"), ("USB2_OTG0_DM", "C12", "bidirectional"),
        ("USB2_HOST1_DP", "C13", "bidirectional"), ("USB2_HOST1_DM", "C14", "bidirectional"),
        ("USB2_HOST2_DP", "C15", "bidirectional"), ("USB2_HOST2_DM", "C16", "bidirectional"),
        ("USB2_HOST3_DP", "C17", "bidirectional"), ("USB2_HOST3_DM", "C18", "bidirectional"),
        ("HDMI_TX0_P", "C19", "output"), ("HDMI_TX0_N", "C20", "output"),
        ("HDMI_TX1_P", "C21", "output"), ("HDMI_TX1_N", "C22", "output"),
        ("HDMI_TX2_P", "C23", "output"), ("HDMI_TX2_N", "C24", "output"),
        ("HDMI_CLK_P", "C25", "output"), ("HDMI_CLK_N", "C26", "output"),
        ("HDMI_HPD", "C27", "input"), ("HDMI_CEC", "C28", "bidirectional"),
        ("HDMI_SCL", "C29", "output"), ("HDMI_SDA", "C30", "bidirectional"),
        ("MIPI_CSI0_D0_P", "D1", "input"), ("MIPI_CSI0_D0_N", "D2", "input"),
        ("MIPI_CSI0_D1_P", "D3", "input"), ("MIPI_CSI0_D1_N", "D4", "input"),
        ("MIPI_CSI0_D2_P", "D5", "input"), ("MIPI_CSI0_D2_N", "D6", "input"),
        ("MIPI_CSI0_D3_P", "D7", "input"), ("MIPI_CSI0_D3_N", "D8", "input"),
        ("MIPI_CSI0_CLK_P", "D9", "input"), ("MIPI_CSI0_CLK_N", "D10", "input"),
        ("MIPI_CSI1_D0_P", "D11", "input"), ("MIPI_CSI1_D0_N", "D12", "input"),
        ("MIPI_CSI1_D1_P", "D13", "input"), ("MIPI_CSI1_D1_N", "D14", "input"),
        ("MIPI_CSI1_CLK_P", "D15", "input"), ("MIPI_CSI1_CLK_N", "D16", "input"),
    ]
    for item in iface_pins:
        pname, pnum, etype = item
        rk3576_pins.append((pname, pnum, 22.86, y, "L", etype))
        y -= 2.54

    # Bottom — bus interfaces
    y2 = min(y, -22) - 5
    bus_pins = [
        ("RGMII_TXD[0:3]", "E1", "output"), ("RGMII_TX_CLK", "E2", "output"),
        ("RGMII_TX_EN", "E3", "output"), ("RGMII_RXD[0:3]", "E4", "input"),
        ("RGMII_RX_CLK", "E5", "input"), ("RGMII_RX_DV", "E6", "input"),
        ("RGMII_MDC", "E7", "output"), ("RGMII_MDIO", "E8", "bidirectional"),
        ("SDIO_CLK", "F1", "output"), ("SDIO_CMD", "F2", "bidirectional"),
        ("SDIO_D[0:3]", "F3", "bidirectional"),
        ("eMMC_CLK", "F4", "output"), ("eMMC_CMD", "F5", "bidirectional"),
        ("eMMC_D[0:7]", "F6", "bidirectional"), ("eMMC_DS", "F7", "input"),
        ("eMMC_RST", "F8", "output"),
        ("FSPI_CLK", "F9", "output"), ("FSPI_CS", "F10", "output"),
        ("FSPI_D[0:3]", "F11", "bidirectional"),
        ("I2S_SCLK", "G1", "output"), ("I2S_LRCK", "G2", "output"),
        ("I2S_SDO", "G3", "output"), ("I2S_SDI", "G4", "input"),
        ("I2S_MCLK", "G5", "output"),
        ("UART4_TX", "H1", "output"), ("UART4_RX", "H2", "input"),
        ("UART5_TX", "H3", "output"), ("UART5_RX", "H4", "input"),
        ("SPI2_CLK", "H5", "output"), ("SPI2_MOSI", "H6", "output"),
        ("SPI2_MISO", "H7", "input"), ("SPI2_CS", "H8", "output"),
        ("GPIO_SHUTDOWN", "H9", "output"), ("GPIO_ALARM_IRQ", "H10", "input"),
    ]
    x = -20
    for item in bus_pins:
        pname, pnum, etype = item
        rk3576_pins.append((pname, pnum, -22.86, y2, "R", etype))
        y2 -= 2.54

    # GPIO header pins (right side bottom)
    y3 = min(y, -22) - 5
    gpio_pins = [(f"GPIO{i}_{'ABCD'[i//8]}{i%8}", f"J{i}", "bidirectional") for i in range(28)]
    for pname, pnum, etype in gpio_pins:
        rk3576_pins.append((pname, pnum, 22.86, y3, "L", etype))
        y3 -= 2.54

    symbols.append(make_symbol(
        "RK3576", "U", "Package_BGA:BGA-698",
        "Rockchip RK3576 — 4xA72+4xA53, 6T NPU, Multi-media SoC",
        rk3576_pins, width=40
    ))

    # --- RK806 PMIC ---
    rk806_pins = []
    y = 20
    left_pins = [
        ("VIN", "1", "power_in"), ("PGND", "2", "passive"),
        ("DCDC1_SW", "3", "power_out"), ("DCDC1_FB", "4", "input"),
        ("DCDC2_SW", "5", "power_out"), ("DCDC2_FB", "6", "input"),
        ("DCDC3_SW", "7", "power_out"), ("DCDC3_FB", "8", "input"),
        ("DCDC4_SW", "9", "power_out"), ("DCDC4_FB", "10", "input"),
        ("DCDC5_SW", "11", "power_out"), ("DCDC5_FB", "12", "input"),
        ("DCDC6_SW", "13", "power_out"), ("DCDC6_FB", "14", "input"),
        ("PWRGD", "15", "output"), ("RESET_OUT", "16", "output"),
    ]
    for pname, pnum, etype in left_pins:
        rk806_pins.append((pname, pnum, -12.7, y, "R", etype))
        y -= 2.54
    y = 20
    right_pins = [
        ("LDO1_OUT", "17", "power_out"), ("LDO2_OUT", "18", "power_out"),
        ("LDO3_OUT", "19", "power_out"), ("LDO4_OUT", "20", "power_out"),
        ("LDO5_OUT", "21", "power_out"), ("LDO6_OUT", "22", "power_out"),
        ("SPI_CLK", "23", "input"), ("SPI_CS", "24", "input"),
        ("SPI_MOSI", "25", "input"), ("SPI_MISO", "26", "output"),
        ("INT_N", "27", "output"), ("SCL", "28", "input"),
        ("SDA", "29", "bidirectional"), ("EN", "30", "input"),
        ("GND", "31", "passive"), ("AGND", "32", "passive"),
    ]
    for pname, pnum, etype in right_pins:
        rk806_pins.append((pname, pnum, 12.7, y, "L", etype))
        y -= 2.54

    symbols.append(make_symbol(
        "RK806", "U", "Package_QFN:QFN-68",
        "Rockchip RK806-1 PMIC for RK3576",
        rk806_pins, width=20
    ))

    # --- RP2350A ---
    rp2350_pins = []
    y = 25
    left_pins = [
        ("GP0/UART0_TX", "1", "bidirectional"), ("GP1/UART0_RX", "2", "bidirectional"),
        ("GP2/SPI0_SCK", "3", "bidirectional"), ("GP3/SPI0_TX", "4", "bidirectional"),
        ("GP4/SPI0_RX", "5", "bidirectional"), ("GP5/SPI0_CS", "6", "bidirectional"),
        ("GP9", "7", "bidirectional"),
        ("GP12/ADC_PWRGD", "8", "bidirectional"), ("GP13/WAKE_REQ", "9", "bidirectional"),
        ("GP14/RK3506_RST", "10", "bidirectional"), ("GP15/PWR_EN", "11", "bidirectional"),
        ("GP23", "12", "bidirectional"), ("GP24", "13", "bidirectional"),
        ("GP25", "14", "bidirectional"), ("GP26/ADC0", "15", "bidirectional"),
        ("GP27/ADC1", "16", "bidirectional"), ("GP28/SHUTDOWN", "17", "bidirectional"),
        ("GP29/ADC3", "18", "bidirectional"),
    ]
    for pname, pnum, etype in left_pins:
        rp2350_pins.append((pname, pnum, -17.78, y, "R", etype))
        y -= 2.54
    y = 25
    right_pins = [
        ("IOVDD", "19", "power_in"), ("DVDD", "20", "power_in"),
        ("USB_DP", "21", "bidirectional"), ("USB_DM", "22", "bidirectional"),
        ("VREG_VIN", "23", "power_in"), ("VREG_VOUT", "24", "power_out"),
        ("XIN", "25", "input"), ("XOUT", "26", "output"),
        ("TESTEN", "27", "input"), ("SWCLK", "28", "input"),
        ("SWDIO", "29", "bidirectional"), ("GND", "30", "passive"),
        ("QSPI_SCK", "31", "output"), ("QSPI_CS", "32", "output"),
        ("QSPI_D0", "33", "bidirectional"), ("QSPI_D1", "34", "bidirectional"),
        ("QSPI_D2", "35", "bidirectional"), ("QSPI_D3", "36", "bidirectional"),
        ("RUN", "37", "input"), ("3V3_OUT", "38", "power_out"),
    ]
    for pname, pnum, etype in right_pins:
        rp2350_pins.append((pname, pnum, 17.78, y, "L", etype))
        y -= 2.54

    symbols.append(make_symbol(
        "RP2350A", "U", "Package_QFN:QFN-60-1EP_7x7mm_P0.4mm",
        "Raspberry Pi RP2350A — Dual Cortex-M33/RISC-V, 520KB SRAM",
        rp2350_pins, width=30
    ))

    # --- RK3506J ---
    rk3506_pins = []
    y = 25
    left_pins = [
        ("VDD_CORE", "1", "power_in"), ("VDD_IO", "2", "power_in"),
        ("GND", "3", "passive"), ("RESET_N", "4", "input"),
        ("UART0_TX", "5", "output"), ("UART0_RX", "6", "input"),
        ("UART2_TX", "7", "output"), ("UART2_RX", "8", "input"),
        ("UART3_TX", "9", "output"), ("UART3_RX", "10", "input"),
        ("UART4_TX", "11", "output"), ("UART4_RX", "12", "input"),
        ("SPI0_CLK", "13", "bidirectional"), ("SPI0_MOSI", "14", "output"),
        ("SPI0_MISO", "15", "input"), ("SPI0_CS", "16", "output"),
        ("SPI2_CLK", "17", "output"), ("SPI2_MOSI", "18", "output"),
        ("SPI2_MISO", "19", "input"), ("SPI2_CS", "20", "output"),
        ("I2C0_SCL", "21", "output"), ("I2C0_SDA", "22", "bidirectional"),
        ("I2C1_SCL", "23", "output"), ("I2C1_SDA", "24", "bidirectional"),
        ("I2C2_SCL", "25", "output"), ("I2C2_SDA", "26", "bidirectional"),
    ]
    for pname, pnum, etype in left_pins:
        rk3506_pins.append((pname, pnum, -17.78, y, "R", etype))
        y -= 2.54
    y = 25
    right_pins = [
        ("CAN0_TX", "27", "output"), ("CAN0_RX", "28", "input"),
        ("CAN1_TX", "29", "output"), ("CAN1_RX", "30", "input"),
        ("PWM0", "31", "output"), ("PWM1", "32", "output"),
        ("PWM2", "33", "output"), ("PWM3", "34", "output"),
        ("PWM4", "35", "output"), ("PWM5", "36", "output"),
        ("PWM6", "37", "output"), ("PWM7", "38", "output"),
        ("PWM8", "39", "output"), ("PWM9", "40", "output"),
        ("PWM10", "41", "output"), ("PWM11", "42", "output"),
        ("ADC_IN0", "43", "input"), ("ADC_IN1", "44", "input"),
        ("ADC_IN2", "45", "input"), ("ADC_IN3", "46", "input"),
        ("GPIO_0", "47", "bidirectional"), ("GPIO_1", "48", "bidirectional"),
        ("GPIO_2", "49", "bidirectional"), ("GPIO_3", "50", "bidirectional"),
        ("GPIO_WAKE", "51", "output"), ("GPIO_ALARM", "52", "output"),
    ]
    for pname, pnum, etype in right_pins:
        rk3506_pins.append((pname, pnum, 17.78, y, "L", etype))
        y -= 2.54

    symbols.append(make_symbol(
        "RK3506J", "U", "Package_QFN:QFN-88",
        "Rockchip RK3506J — 3xCortex-A7 + Cortex-M0, industrial automation",
        rk3506_pins, width=30
    ))

    # --- CN3722 MPPT Solar Charger ---
    cn3722_pins = []
    y = 10
    left = [
        ("VIN", "1", "power_in"), ("EN", "2", "input"),
        ("SS", "3", "passive"), ("FB", "4", "input"),
        ("COMP", "5", "passive"), ("RT", "6", "passive"),
        ("GND", "7", "passive"), ("PGND", "8", "passive"),
    ]
    right = [
        ("SW", "9", "passive"), ("BST", "10", "passive"),
        ("VBAT", "11", "power_out"), ("CHRG", "12", "output"),
        ("DONE", "13", "output"), ("CS", "14", "input"),
        ("TS", "15", "input"), ("MPPT", "16", "input"),
    ]
    for pname, pnum, etype in left:
        cn3722_pins.append((pname, pnum, -10.16, y, "R", etype))
        y -= 2.54
    y = 10
    for pname, pnum, etype in right:
        cn3722_pins.append((pname, pnum, 10.16, y, "L", etype))
        y -= 2.54
    symbols.append(make_symbol("CN3722", "U", "Package_SO:SOP-16",
        "CN3722 — Solar MPPT LiFePO4 Charger", cn3722_pins, width=15))

    # --- TPS61022 Boost Converter ---
    tps_pins = []
    left = [("VIN", "1", "power_in"), ("EN", "2", "input"), ("GND", "3", "passive")]
    right = [("SW", "4", "passive"), ("VOUT", "5", "power_out"), ("FB", "6", "input")]
    y = 5
    for pname, pnum, etype in left:
        tps_pins.append((pname, pnum, -7.62, y, "R", etype))
        y -= 2.54
    y = 5
    for pname, pnum, etype in right:
        tps_pins.append((pname, pnum, 7.62, y, "L", etype))
        y -= 2.54
    symbols.append(make_symbol("TPS61022", "U", "Package_TO_SOT_SMD:SOT-23-6",
        "TPS61022 — 5V 4A Boost Converter", tps_pins, width=10))

    # --- SI3402-B PoE PD ---
    si_pins = []
    left = [("VDD", "1", "power_in"), ("RCLASS", "2", "passive"),
            ("DET", "3", "passive"), ("VSS", "4", "passive"),
            ("AGND", "5", "passive"), ("GND", "6", "passive")]
    right = [("VOUT", "7", "power_out"), ("VEE", "8", "passive"),
             ("GATE", "9", "output"), ("BG", "10", "output"),
             ("FB", "11", "input"), ("COMP", "12", "passive")]
    y = 8
    for pname, pnum, etype in left:
        si_pins.append((pname, pnum, -10.16, y, "R", etype))
        y -= 2.54
    y = 8
    for pname, pnum, etype in right:
        si_pins.append((pname, pnum, 10.16, y, "L", etype))
        y -= 2.54
    symbols.append(make_symbol("SI3402-B", "U", "Package_QFN:QFN-16",
        "Silicon Labs SI3402-B — 802.3at PoE PD Controller", si_pins, width=15))

    # --- HUSB238 USB-C PD Controller (corrected per real datasheet) ---
    husb_pins = []
    left = [("VDD", "1", "power_in"), ("CC1", "2", "bidirectional"),
            ("CC2", "3", "bidirectional"), ("GND", "4", "passive"),
            ("SCL", "5", "input"), ("SDA", "6", "bidirectional")]
    right = [("VBUS_DET", "7", "input"), ("OUT_EN", "8", "output"),
             ("GO", "9", "input"), ("VSET", "10", "input"),
             ("INT_N", "11", "output"), ("ATTACH", "12", "output")]
    y = 8
    for pname, pnum, etype in left:
        husb_pins.append((pname, pnum, -10.16, y, "R", etype))
        y -= 2.54
    y = 8
    for pname, pnum, etype in right:
        husb_pins.append((pname, pnum, 10.16, y, "L", etype))
        y -= 2.54
    symbols.append(make_symbol("HUSB238", "U", "Package_SO:SOP-10",
        "HUSB238 — USB-C PD Sink Controller (VSET resistor selects voltage)", husb_pins, width=15))

    # --- CYW43439 WiFi/BT ---
    cyw_pins = []
    left = [("VDD", "1", "power_in"), ("GND", "2", "passive"),
            ("SPI_CLK", "3", "input"), ("SPI_MOSI", "4", "input"),
            ("SPI_MISO", "5", "output"), ("SPI_CS", "6", "input"),
            ("IRQ", "7", "output"), ("WL_REG_ON", "8", "input")]
    right = [("BT_REG_ON", "9", "input"), ("BT_HOST_WAKE", "10", "output"),
             ("BT_DEV_WAKE", "11", "input"), ("RF_OUT", "12", "passive"),
             ("XTAL_IN", "13", "input"), ("XTAL_OUT", "14", "output"),
             ("ANT", "15", "passive"), ("GND2", "16", "passive")]
    y = 10
    for pname, pnum, etype in left:
        cyw_pins.append((pname, pnum, -10.16, y, "R", etype))
        y -= 2.54
    y = 10
    for pname, pnum, etype in right:
        cyw_pins.append((pname, pnum, 10.16, y, "L", etype))
        y -= 2.54
    symbols.append(make_symbol("CYW43439", "U", "Package_BGA:BGA-59",
        "Infineon CYW43439 — WiFi 4 + Bluetooth 5.2", cyw_pins, width=15))

    # --- SX1262 LoRa ---
    sx_pins = []
    left = [("VDD", "1", "power_in"), ("GND", "2", "passive"),
            ("SCK", "3", "input"), ("MOSI", "4", "input"),
            ("MISO", "5", "output"), ("NSS", "6", "input"),
            ("BUSY", "7", "output"), ("DIO1", "8", "output")]
    right = [("DIO2", "9", "output"), ("DIO3", "10", "output"),
             ("NRESET", "11", "input"), ("RFI", "12", "passive"),
             ("RFO", "13", "passive"), ("XTA", "14", "passive"),
             ("XTB", "15", "passive"), ("VBAT_IO", "16", "power_in")]
    y = 10
    for pname, pnum, etype in left:
        sx_pins.append((pname, pnum, -10.16, y, "R", etype))
        y -= 2.54
    y = 10
    for pname, pnum, etype in right:
        sx_pins.append((pname, pnum, 10.16, y, "L", etype))
        y -= 2.54
    symbols.append(make_symbol("SX1262", "U", "Package_QFN:QFN-24-1EP_4x4mm_P0.5mm",
        "Semtech SX1262 — LoRa 868/915MHz Transceiver", sx_pins, width=15))

    # --- RTL8852BS WiFi 5 ---
    rtl_pins = []
    left = [("VDD33", "1", "power_in"), ("VDD12", "2", "power_in"),
            ("GND", "3", "passive"), ("SDIO_CLK", "4", "input"),
            ("SDIO_CMD", "5", "bidirectional"), ("SDIO_D0", "6", "bidirectional"),
            ("SDIO_D1", "7", "bidirectional"), ("SDIO_D2", "8", "bidirectional"),
            ("SDIO_D3", "9", "bidirectional"), ("BT_UART_TX", "10", "output")]
    right = [("BT_UART_RX", "11", "input"), ("WL_DIS_N", "12", "input"),
             ("BT_DIS_N", "13", "input"), ("WAKE_HOST", "14", "output"),
             ("HOST_WAKE", "15", "input"), ("ANT_MAIN", "16", "passive"),
             ("ANT_AUX", "17", "passive"), ("XTAL_IN", "18", "input"),
             ("XTAL_OUT", "19", "output"), ("AVDD33", "20", "power_in")]
    y = 12
    for pname, pnum, etype in left:
        rtl_pins.append((pname, pnum, -12.7, y, "R", etype))
        y -= 2.54
    y = 12
    for pname, pnum, etype in right:
        rtl_pins.append((pname, pnum, 12.7, y, "L", etype))
        y -= 2.54
    symbols.append(make_symbol("RTL8852BS", "U", "Package_LCC:LCC",
        "Realtek RTL8852BS — WiFi 5 + BT 5.0, SDIO 3.0", rtl_pins, width=20))

    # --- ES8316 Audio Codec ---
    es_pins = []
    left = [("DVDD", "1", "power_in"), ("AVDD", "2", "power_in"),
            ("GND", "3", "passive"), ("SCL", "4", "input"),
            ("SDA", "5", "bidirectional"), ("MCLK", "6", "input"),
            ("SCLK", "7", "input"), ("LRCK", "8", "input")]
    right = [("SDOUT", "9", "output"), ("SDIN", "10", "input"),
             ("LINP", "11", "input"), ("LINN", "12", "input"),
             ("HPOUTL", "13", "output"), ("HPOUTR", "14", "output"),
             ("MICBIAS", "15", "output"), ("AD_DA_SEL", "16", "input")]
    y = 10
    for pname, pnum, etype in left:
        es_pins.append((pname, pnum, -10.16, y, "R", etype))
        y -= 2.54
    y = 10
    for pname, pnum, etype in right:
        es_pins.append((pname, pnum, 10.16, y, "L", etype))
        y -= 2.54
    symbols.append(make_symbol("ES8316", "U", "Package_QFN:QFN-24",
        "Everest ES8316 — Low-Power Stereo Audio Codec", es_pins, width=15))

    # --- RTL8211F GbE PHY ---
    rtl_phy_pins = []
    left = [("AVDD33", "1", "power_in"), ("DVDD", "2", "power_in"),
            ("GND", "3", "passive"), ("TXCLK", "4", "input"),
            ("TXD0", "5", "input"), ("TXD1", "6", "input"),
            ("TXD2", "7", "input"), ("TXD3", "8", "input"),
            ("TX_EN", "9", "input"), ("RXCLK", "10", "output")]
    right = [("RXD0", "11", "output"), ("RXD1", "12", "output"),
             ("RXD2", "13", "output"), ("RXD3", "14", "output"),
             ("RX_DV", "15", "output"), ("MDC", "16", "input"),
             ("MDIO", "17", "bidirectional"), ("RESET_N", "18", "input"),
             ("TXP", "19", "output"), ("TXN", "20", "output"),
             ("RXP", "21", "input"), ("RXN", "22", "input"),
             ("LED0", "23", "output"), ("LED1", "24", "output"),
             ("PHYAD0", "25", "input"), ("INT_N", "26", "output")]
    y = 15
    for pname, pnum, etype in left:
        rtl_phy_pins.append((pname, pnum, -12.7, y, "R", etype))
        y -= 2.54
    y = 15
    for pname, pnum, etype in right:
        rtl_phy_pins.append((pname, pnum, 12.7, y, "L", etype))
        y -= 2.54
    symbols.append(make_symbol("RTL8211F", "U", "Package_QFN:QFN-40",
        "Realtek RTL8211F — 10/100/1000 GbE PHY, RGMII", rtl_phy_pins, width=20))

    # --- SN74LVC2G17 Dual Schmitt ---
    schmitt2_pins = [
        ("1A", "1", -7.62, 2.54, "R", "input"),
        ("1Y", "2", 7.62, 2.54, "L", "output"),
        ("2A", "3", -7.62, -2.54, "R", "input"),
        ("2Y", "4", 7.62, -2.54, "L", "output"),
        ("VCC", "5", 0, 7.62, "D", "power_in"),
        ("GND", "6", 0, -7.62, "U", "passive"),
    ]
    symbols.append(make_symbol("SN74LVC2G17", "U", "Package_TO_SOT_SMD:SOT-23-6",
        "TI SN74LVC2G17 — Dual Schmitt-Trigger Buffer", schmitt2_pins, width=10))

    # --- SN74LVC1G17 Single Schmitt ---
    schmitt1_pins = [
        ("A", "1", -7.62, 0, "R", "input"),
        ("Y", "2", 7.62, 0, "L", "output"),
        ("VCC", "3", 0, 5.08, "D", "power_in"),
        ("GND", "4", 0, -5.08, "U", "passive"),
    ]
    symbols.append(make_symbol("SN74LVC1G17", "U", "Package_TO_SOT_SMD:SOT-23-5",
        "TI SN74LVC1G17 — Single Schmitt-Trigger Buffer", schmitt1_pins, width=10))

    # --- SN74LVC14A Hex Schmitt Inverter ---
    schmitt6_pins = []
    y = 10
    for i in range(6):
        schmitt6_pins.append((f"{i+1}A", str(2*i+1), -10.16, y, "R", "input"))
        schmitt6_pins.append((f"{i+1}Y", str(2*i+2), 10.16, y, "L", "output"))
        y -= 2.54
    schmitt6_pins.append(("VCC", "14", 0, 15.24, "D", "power_in"))
    schmitt6_pins.append(("GND", "7", 0, -10.16, "U", "passive"))
    symbols.append(make_symbol("SN74LVC14A", "U", "Package_SO:TSSOP-14_4.4x5mm_P0.65mm",
        "TI SN74LVC14A — Hex Schmitt-Trigger Inverter", schmitt6_pins, width=15))

    # --- MCP2562FD CAN FD Transceiver ---
    can_pins = [
        ("TXD", "1", -7.62, 5.08, "R", "input"),
        ("VSS", "2", 0, -10.16, "U", "passive"),
        ("VDD", "3", 0, 10.16, "D", "power_in"),
        ("RXD", "4", -7.62, 2.54, "R", "output"),
        ("Vio", "5", -7.62, -2.54, "R", "power_in"),
        ("CANH", "6", 7.62, 5.08, "L", "passive"),
        ("CANL", "7", 7.62, 2.54, "L", "passive"),
        ("STBY", "8", -7.62, -5.08, "R", "input"),
    ]
    symbols.append(make_symbol("MCP2562FD", "U", "Package_TO_SOT_SMD:SOT-23-8",
        "Microchip MCP2562FD — CAN FD Transceiver", can_pins, width=10))

    # --- LTC4357 OR-ing Controller ---
    ltc_pins = [
        ("IN", "1", -7.62, 2.54, "R", "power_in"),
        ("GATE", "2", 7.62, 2.54, "L", "output"),
        ("OUT", "3", 7.62, -2.54, "L", "power_out"),
        ("GND", "4", 0, -7.62, "U", "passive"),
    ]
    symbols.append(make_symbol("LTC4357", "U", "Package_TO_SOT_SMD:SOT-23-5",
        "ADI LTC4357 — Positive Voltage Ideal Diode OR-ing Controller", ltc_pins, width=10))

    # --- ADUM1401 Digital Isolator ---
    adum_pins = [
        ("VDD1", "1", -12.7, 7.62, "R", "power_in"),
        ("GND1", "2", -12.7, -7.62, "R", "passive"),
        ("VIA", "3", -12.7, 5.08, "R", "input"),
        ("VIB", "4", -12.7, 2.54, "R", "input"),
        ("VOC", "5", -12.7, 0, "R", "output"),
        ("VOD", "6", -12.7, -2.54, "R", "output"),
        ("EN1", "7", -12.7, -5.08, "R", "input"),
        ("NC", "8", -12.7, -10.16, "R", "passive"),
        ("VDD2", "9", 12.7, 7.62, "L", "power_in"),
        ("GND2", "10", 12.7, -7.62, "L", "passive"),
        ("VOA", "11", 12.7, 5.08, "L", "output"),
        ("VOB", "12", 12.7, 2.54, "L", "output"),
        ("VIC", "13", 12.7, 0, "L", "input"),
        ("VID", "14", 12.7, -2.54, "L", "input"),
        ("EN2", "15", 12.7, -5.08, "L", "input"),
        ("NC2", "16", 12.7, -10.16, "L", "passive"),
    ]
    symbols.append(make_symbol("ADUM1401", "U", "Package_SO:SOIC-16W_7.5x10.3mm_P1.27mm",
        "ADI ADUM1401 — Quad-Channel Digital Isolator, 2.5kV", adum_pins, width=20))

    # --- W25Q128 SPI NOR Flash ---
    symbols.append(make_symbol("W25Q128", "U", "Package_SO:SOP-8",
        "Winbond W25Q128 128Mbit SPI NOR Flash",
        [("CS", "1", -10, 5, "L", "input"),
         ("DO", "2", -10, 2.5, "L", "output"),
         ("WP", "3", -10, 0, "L", "input"),
         ("GND", "4", -10, -2.5, "L", "passive"),
         ("DI", "5", 10, 5, "R", "input"),
         ("CLK", "6", 10, 2.5, "R", "input"),
         ("HOLD", "7", 10, 0, "R", "input"),
         ("VCC", "8", 10, -2.5, "R", "power_in")], width=16))

    # --- W25Q16 SPI NOR Flash ---
    symbols.append(make_symbol("W25Q16", "U", "Package_SO:SOP-8",
        "Winbond W25Q16 16Mbit SPI NOR Flash",
        [("CS", "1", -10, 5, "L", "input"),
         ("DO", "2", -10, 2.5, "L", "output"),
         ("WP", "3", -10, 0, "L", "input"),
         ("GND", "4", -10, -2.5, "L", "passive"),
         ("DI", "5", 10, 5, "R", "input"),
         ("CLK", "6", 10, 2.5, "R", "input"),
         ("HOLD", "7", 10, 0, "R", "input"),
         ("VCC", "8", 10, -2.5, "R", "power_in")], width=16))

    # --- LPDDR4X SDRAM ---
    symbols.append(make_symbol("LPDDR4X", "U", "Package_BGA:BGA-200",
        "LPDDR4X 4GB SDRAM (simplified)",
        [("VDD1", "A1", -14, 18, "L", "power_in"),
         ("VDD2", "A2", -14, 15.5, "L", "power_in"),
         ("VDDQ", "A3", -14, 13, "L", "power_in"),
         ("VSS", "A4", -14, 10.5, "L", "passive"),
         ("CK_P", "B1", -14, 7, "L", "input"),
         ("CK_N", "B2", -14, 4.5, "L", "input"),
         ("CKE", "B3", -14, 2, "L", "input"),
         ("CS", "B4", -14, -0.5, "L", "input"),
         ("CA0", "C1", -14, -3, "L", "input"),
         ("CA1", "C2", -14, -5.5, "L", "input"),
         ("CA2", "C3", -14, -8, "L", "input"),
         ("CA3", "C4", -14, -10.5, "L", "input"),
         ("CA4", "C5", -14, -13, "L", "input"),
         ("CA5", "C6", -14, -15.5, "L", "input"),
         ("RESET_N", "D1", -14, -18, "L", "input"),
         ("DQ0", "E1", 14, 18, "R", "bidirectional"),
         ("DQ1", "E2", 14, 15.5, "R", "bidirectional"),
         ("DQ2", "E3", 14, 13, "R", "bidirectional"),
         ("DQ3", "E4", 14, 10.5, "R", "bidirectional"),
         ("DQ4", "E5", 14, 8, "R", "bidirectional"),
         ("DQ5", "E6", 14, 5.5, "R", "bidirectional"),
         ("DQ6", "E7", 14, 3, "R", "bidirectional"),
         ("DQ7", "E8", 14, 0.5, "R", "bidirectional"),
         ("DQS0_P", "F1", 14, -2, "R", "bidirectional"),
         ("DQS0_N", "F2", 14, -4.5, "R", "bidirectional"),
         ("DMI0", "F3", 14, -7, "R", "bidirectional"),
         ("DQ8", "G1", 14, -10, "R", "bidirectional"),
         ("DQ9", "G2", 14, -12.5, "R", "bidirectional"),
         ("DQS1_P", "H1", 14, -15, "R", "bidirectional"),
         ("DQS1_N", "H2", 14, -17.5, "R", "bidirectional")], width=24))

    # --- eMMC_BGA153 ---
    symbols.append(make_symbol("eMMC_BGA153", "U", "Package_BGA:BGA-153",
        "eMMC 5.1 32GB Flash Storage (simplified)",
        [("VCCQ", "A1", -12, 12, "L", "power_in"),
         ("VCC", "A2", -12, 9.5, "L", "power_in"),
         ("VSS", "A3", -12, 7, "L", "passive"),
         ("CMD", "B1", -12, 3.5, "L", "bidirectional"),
         ("CLK", "B2", -12, 1, "L", "input"),
         ("DS", "B3", -12, -1.5, "L", "output"),
         ("RST_N", "B4", -12, -4, "L", "input"),
         ("D0", "C1", 12, 12, "R", "bidirectional"),
         ("D1", "C2", 12, 9.5, "R", "bidirectional"),
         ("D2", "C3", 12, 7, "R", "bidirectional"),
         ("D3", "C4", 12, 4.5, "R", "bidirectional"),
         ("D4", "C5", 12, 2, "R", "bidirectional"),
         ("D5", "C6", 12, -0.5, "R", "bidirectional"),
         ("D6", "C7", 12, -3, "R", "bidirectional"),
         ("D7", "C8", 12, -5.5, "R", "bidirectional")], width=20))

    # --- LPDDR3L SDRAM ---
    symbols.append(make_symbol("LPDDR3L", "U", "Package_BGA:BGA-178",
        "LPDDR3L 512MB SDRAM (simplified)",
        [("VDD1", "A1", -14, 15, "L", "power_in"),
         ("VDD2", "A2", -14, 12.5, "L", "power_in"),
         ("VDDQ", "A3", -14, 10, "L", "power_in"),
         ("VSS", "A4", -14, 7.5, "L", "passive"),
         ("CK_P", "B1", -14, 4, "L", "input"),
         ("CK_N", "B2", -14, 1.5, "L", "input"),
         ("CKE", "B3", -14, -1, "L", "input"),
         ("CS_N", "B4", -14, -3.5, "L", "input"),
         ("RAS_N", "C1", -14, -6, "L", "input"),
         ("CAS_N", "C2", -14, -8.5, "L", "input"),
         ("WE_N", "C3", -14, -11, "L", "input"),
         ("A0", "D1", -14, -14, "L", "input"),
         ("DQ0", "E1", 14, 15, "R", "bidirectional"),
         ("DQ1", "E2", 14, 12.5, "R", "bidirectional"),
         ("DQ2", "E3", 14, 10, "R", "bidirectional"),
         ("DQ3", "E4", 14, 7.5, "R", "bidirectional"),
         ("DQS0_P", "F1", 14, 4, "R", "bidirectional"),
         ("DQS0_N", "F2", 14, 1.5, "R", "bidirectional"),
         ("DM0", "F3", 14, -1, "R", "bidirectional"),
         ("ODT", "G1", 14, -4, "R", "input"),
         ("RESET_N", "G2", 14, -7, "R", "input"),
         ("ZQ", "G3", 14, -10, "R", "passive")], width=24))

    # --- NAND_Flash ---
    symbols.append(make_symbol("NAND_Flash", "U", "Package_BGA:BGA-63",
        "256MB SLC NAND Flash (simplified)",
        [("VCC", "1", -10, 8, "L", "power_in"),
         ("VSS", "2", -10, 5.5, "L", "passive"),
         ("CE_N", "3", -10, 2, "L", "input"),
         ("RE_N", "4", -10, -0.5, "L", "input"),
         ("WE_N", "5", -10, -3, "L", "input"),
         ("ALE", "6", -10, -5.5, "L", "input"),
         ("CLE", "7", -10, -8, "L", "input"),
         ("WP_N", "8", 10, 8, "R", "input"),
         ("R_B", "9", 10, 5.5, "R", "output"),
         ("IO0", "10", 10, 2, "R", "bidirectional"),
         ("IO1", "11", 10, -0.5, "R", "bidirectional"),
         ("IO2", "12", 10, -3, "R", "bidirectional"),
         ("IO3", "13", 10, -5.5, "R", "bidirectional"),
         ("IO4", "14", 10, -8, "R", "bidirectional")], width=16))

    # --- SP3485 RS-485 Transceiver ---
    symbols.append(make_symbol("SP3485", "U", "Package_SO:SOP-8",
        "SP3485 RS-485/RS-422 Half-Duplex Transceiver",
        [("RO", "1", -10, 5, "L", "output"),
         ("RE_N", "2", -10, 2.5, "L", "input"),
         ("DE", "3", -10, 0, "L", "input"),
         ("DI", "4", -10, -2.5, "L", "input"),
         ("GND", "5", 10, -2.5, "R", "passive"),
         ("A", "6", 10, 0, "R", "bidirectional"),
         ("B", "7", 10, 2.5, "R", "bidirectional"),
         ("VCC", "8", 10, 5, "R", "power_in")], width=16))

    # --- MIC5219 LDO ---
    symbols.append(make_symbol("MIC5219", "U", "Package_TO_SOT_SMD:SOT-23-5",
        "MIC5219 500mA Ultra-Low-Noise LDO",
        [("IN", "1", -8, 2.5, "L", "power_in"),
         ("GND", "2", -8, 0, "L", "passive"),
         ("EN", "3", -8, -2.5, "L", "input"),
         ("BYP", "4", 8, -2.5, "R", "passive"),
         ("OUT", "5", 8, 2.5, "R", "power_out")], width=12))

    # --- AP2112K LDO ---
    symbols.append(make_symbol("AP2112K", "U", "Package_TO_SOT_SMD:SOT-23-5",
        "AP2112K 600mA LDO Regulator",
        [("VIN", "1", -8, 2.5, "L", "power_in"),
         ("GND", "2", -8, 0, "L", "passive"),
         ("EN", "3", -8, -2.5, "L", "input"),
         ("NC", "4", 8, -2.5, "R", "passive"),
         ("VOUT", "5", 8, 2.5, "R", "power_out")], width=12))

    # --- USBLC6 USB ESD ---
    symbols.append(make_symbol("USBLC6", "U", "Package_TO_SOT_SMD:SOT-23-6",
        "USBLC6-2SC6 USB ESD Protection",
        [("IO1", "1", -8, 2.5, "L", "passive"),
         ("GND", "2", -8, 0, "L", "passive"),
         ("IO2", "3", -8, -2.5, "L", "passive"),
         ("IO2_O", "4", 8, -2.5, "R", "passive"),
         ("VBUS", "5", 8, 0, "R", "passive"),
         ("IO1_O", "6", 8, 2.5, "R", "passive")], width=12))

    # --- PRTR5V0U2X ESD ---
    symbols.append(make_symbol("PRTR5V0U2X", "U", "Package_TO_SOT_SMD:SOT-363",
        "PRTR5V0U2X Low-Cap ESD Protection",
        [("GND", "1", -8, 2.5, "L", "passive"),
         ("IO1", "2", -8, 0, "L", "passive"),
         ("IO2", "3", -8, -2.5, "L", "passive"),
         ("VCC", "4", 8, -2.5, "R", "passive"),
         ("IO2_O", "5", 8, 0, "R", "passive"),
         ("IO1_O", "6", 8, 2.5, "R", "passive")], width=12))

    # --- EC25E 4G LTE Modem ---
    symbols.append(make_symbol("EC25E", "U", "Connector:M.2_B-key",
        "Quectel EC25-E LTE Cat.4 Modem",
        [("VCC_3V3", "1", -14, 15, "L", "power_in"),
         ("GND", "2", -14, 12.5, "L", "passive"),
         ("USB_D_P", "3", -14, 9, "L", "bidirectional"),
         ("USB_D_N", "4", -14, 6.5, "L", "bidirectional"),
         ("UART_TXD", "5", -14, 3, "L", "output"),
         ("UART_RXD", "6", -14, 0.5, "L", "input"),
         ("RESET_N", "7", -14, -2, "L", "input"),
         ("PWRKEY", "8", -14, -4.5, "L", "input"),
         ("STATUS", "9", -14, -7, "L", "output"),
         ("RI", "10", -14, -9.5, "L", "output"),
         ("DTR", "11", -14, -12, "L", "input"),
         ("MAIN_ANT", "12", 14, 15, "R", "passive"),
         ("DIV_ANT", "13", 14, 12.5, "R", "passive"),
         ("GNSS_ANT", "14", 14, 10, "R", "passive"),
         ("SIM_VCC", "15", 14, 6.5, "R", "power_out"),
         ("SIM_RST", "16", 14, 4, "R", "output"),
         ("SIM_CLK", "17", 14, 1.5, "R", "output"),
         ("SIM_DATA", "18", 14, -1, "R", "bidirectional")], width=24))

    # Write library file
    lib_content = f"""(kicad_symbol_lib
  (version 20231120)
  (generator "solarpunk_gen")
  (generator_version "1.0")
{chr(10).join(symbols)}
)"""

    path = os.path.join(PROJECT_DIR, "libraries", f"{PROJECT_NAME}.kicad_sym")
    with open(path, 'w') as f:
        f.write(lib_content)
    print(f"  Created {path}")


# ============================================================
# 3. SCHEMATIC GENERATION
# ============================================================

def sch_header(title, paper="A3"):
    return f"""(kicad_sch
  (version 20231120)
  (generator "solarpunk_gen")
  (generator_version "1.0")
  (uuid "{uid()}")
  (paper "{paper}")
  (title_block
    (title "{title}")
    (date "2026-03")
    (rev "3.0")
    (company "Solarpunk Computing")
  )
  (lib_symbols)
"""

def sch_text(x, y, text, size=2.54):
    return f"""  (text "{text}"
    (exclude_from_sim no)
    (at {x} {y} 0)
    (effects (font (size {size} {size})))
    (uuid "{uid()}")
  )
"""

def sch_label(x, y, name, shape="input"):
    return f"""  (global_label "{name}"
    (shape {shape})
    (at {x} {y} 0)
    (effects (font (size 1.27 1.27)))
    (uuid "{uid()}")
    (property "Intersheets" ""
      (at 0 0 0)
      (effects (font (size 1.27 1.27)) hide)
    )
  )
"""

def sch_wire(x1, y1, x2, y2):
    """Generate a wire segment."""
    return f"""  (wire (pts (xy {x1} {y1}) (xy {x2} {y2}))
    (stroke (width 0) (type default))
    (uuid "{uid()}")
  )
"""

def sch_no_connect(x, y):
    """Mark an unused pin."""
    return f"""  (no_connect (at {x} {y}) (uuid "{uid()}"))
"""

def sch_junction(x, y):
    """Wire junction."""
    return f"""  (junction (at {x} {y}) (diameter 0) (color 0 0 0 0) (uuid "{uid()}"))
"""

def sch_local_label(x, y, name, angle=0):
    """Local net label (within single sheet)."""
    return f"""  (label "{name}"
    (at {x} {y} {angle})
    (effects (font (size 1.27 1.27)))
    (uuid "{uid()}")
  )
"""

def sch_hier_label(x, y, name, shape="input"):
    """Hierarchical label for connecting to parent sheet pins."""
    return f"""  (hierarchical_label "{name}" (shape {shape})
    (at {x} {y} 0)
    (effects (font (size 1.27 1.27)))
    (uuid "{uid()}")
  )
"""

def sch_hier_pin(x, y, name, direction="input"):
    return f"""    (pin "{name}" {direction}
      (at {x} {y} 0)
      (effects (font (size 1.27 1.27)))
      (uuid "{uid()}")
    )
"""

def sch_sheet(x, y, w, h, name, filename, pins, color=(0,0,0)):
    """Generate a hierarchical sheet reference with pins."""
    pin_strs = []
    py = y + 5
    for pname, pdir in pins:
        pin_strs.append(sch_hier_pin(x if pdir == "input" else x+w, py, pname, pdir))
        py += 3

    return f"""  (sheet
    (at {x} {y})
    (size {w} {h})
    (fields_autoplaced yes)
    (stroke (width 0.1524) (type solid))
    (fill (color 255 255 235 1.0))
    (uuid "{uid()}")
    (property "Sheetname" "{name}"
      (at {x} {y-1.5} 0)
      (effects (font (size 1.524 1.524)))
      (id 0)
    )
    (property "Sheetfile" "{filename}"
      (at {x} {y+h+1} 0)
      (effects (font (size 1.27 1.27)) hide)
      (id 1)
    )
{"".join(pin_strs)}  )
"""

def generate_top_schematic():
    """Top-level schematic with hierarchical sheet references."""
    content = sch_header("Solarpunk Pi v3 — Top Level", "A2")

    # Title text
    content += sch_text(150, 20, "SOLARPUNK PI v3.0", 5)
    content += sch_text(150, 28, "Triple-Processor Solar-Powered Edge Computer", 2.5)
    content += sch_text(150, 34, "RK3576 + RP2350 + RK3506J", 2)
    content += sch_text(150, 40, "85×56mm Pi 5 Form Factor — 6-Layer PCB", 1.5)

    # Domain labels
    content += sch_text(35, 55, "BRAIN — Linux/Docker/Ollama", 1.5)
    content += sch_text(145, 55, "CONNECTIVITY", 1.5)
    content += sch_text(35, 145, "NERVES — Power/Radio/LoRa", 1.5)
    content += sch_text(145, 145, "MUSCLE — CAN/RS485/Motors", 1.5)
    content += sch_text(90, 220, "POWER SYSTEM", 1.5)
    content += sch_text(200, 220, "SIGNAL CONDITIONING", 1.5)

    # Sheet 1: RK3576 Compute
    content += sch_sheet(20, 60, 80, 70, "RK3576_Compute", "01-rk3576-compute.kicad_sch", [
        ("5V_SYS", "input"), ("GND", "input"),
        ("UART4_TX", "output"), ("UART4_RX", "input"),
        ("UART5_TX", "output"), ("UART5_RX", "input"),
        ("SPI2_CLK", "output"), ("SPI2_MOSI", "output"),
        ("SPI2_MISO", "input"), ("SPI2_CS", "output"),
        ("GPIO_SHUTDOWN", "output"), ("GPIO_ALARM_IRQ", "input"),
        ("RGMII_BUS", "output"), ("SDIO_BUS", "output"),
        ("I2S_BUS", "output"), ("USB3_0", "bidirectional"),
        ("USB3_1", "bidirectional"), ("USB2_0", "bidirectional"),
        ("USB2_1", "bidirectional"), ("USB2_CELL", "bidirectional"),
    ])

    # Sheet 2: Connectivity
    content += sch_sheet(130, 60, 80, 70, "Connectivity", "02-connectivity.kicad_sch", [
        ("5V_SYS", "input"), ("3V3_RK", "input"), ("GND", "input"),
        ("RGMII_BUS", "input"), ("SDIO_BUS", "input"), ("I2S_BUS", "input"),
        ("USB3_0", "bidirectional"), ("USB3_1", "bidirectional"),
        ("USB2_0", "bidirectional"), ("USB2_1", "bidirectional"),
        ("USB2_CELL", "bidirectional"),
        ("HDMI_BUS", "input"), ("CSI0_BUS", "input"), ("CSI1_BUS", "input"),
        ("48V_POE", "output"),
    ])

    # Sheet 3: RP2350 Radio
    content += sch_sheet(20, 150, 80, 60, "RP2350_Radio", "03-rp2350-radio.kicad_sch", [
        ("3V3_RP", "input"), ("5V_SYS", "input"), ("GND", "input"),
        ("UART4_RX_BUF", "input"), ("UART4_TX_BUF", "output"),
        ("PWR_ENABLE", "output"), ("PWR_GOOD", "input"),
        ("WAKE_REQUEST", "input"), ("RK3506_RESET", "output"),
        ("SHUTDOWN_IN", "input"),
    ])

    # Sheet 4: RK3506J Industrial
    content += sch_sheet(130, 150, 80, 60, "RK3506J_Industrial", "04-rk3506j-industrial.kicad_sch", [
        ("3V3_RK3506", "input"), ("5V_SYS", "input"), ("GND", "input"),
        ("UART5_RX_BUF", "input"), ("UART5_TX_BUF", "output"),
        ("SPI0_CLK", "input"), ("SPI0_MOSI", "input"),
        ("SPI0_MISO", "output"), ("SPI0_CS", "input"),
        ("GPIO_WAKE", "output"), ("GPIO_ALARM", "output"),
        ("RESET_N", "input"),
    ])

    # Sheet 5: Power System
    content += sch_sheet(20, 225, 100, 55, "Power_System", "05-power-system.kicad_sch", [
        ("SOLAR_IN", "input"), ("VBAT", "bidirectional"),
        ("48V_POE", "input"), ("USB_PD_IN", "input"),
        ("5V_SYS", "output"), ("3V3_RP", "output"),
        ("3V3_RK3506", "output"), ("3V3_RK", "output"),
        ("1V8", "output"), ("GND", "input"),
    ])

    # Sheet 6: Signal Conditioning
    content += sch_sheet(150, 225, 80, 55, "Signal_Conditioning", "06-signal-conditioning.kicad_sch", [
        ("UART4_TX_RAW", "input"), ("UART4_RX_RAW", "input"),
        ("UART4_TX_BUF", "output"), ("UART4_RX_BUF", "output"),
        ("UART5_TX_RAW", "input"), ("UART5_RX_RAW", "input"),
        ("UART5_TX_BUF", "output"), ("UART5_RX_BUF", "output"),
        ("PWR_GOOD_RAW", "input"), ("PWR_GOOD_BUF", "output"),
        ("PWR_EN_RAW", "input"), ("PWR_EN_BUF", "output"),
        ("WAKE_RAW", "input"), ("WAKE_BUF", "output"),
        ("ALARM_RAW", "input"), ("ALARM_BUF", "output"),
        ("SHUTDOWN_RAW", "input"), ("SHUTDOWN_BUF", "output"),
    ])

    content += ")\n"

    path = os.path.join(PROJECT_DIR, f"{PROJECT_NAME}.kicad_sch")
    with open(path, 'w') as f:
        f.write(content)
    print(f"  Created {path}")


def sch_symbol_instance(ref, lib, symbol_name, x, y, unit=1, value="", fp=""):
    """Place a symbol instance in a schematic."""
    u = uid()
    val_str = value if value else symbol_name
    return f"""  (symbol
    (lib_id "{lib}:{symbol_name}")
    (at {x} {y} 0)
    (unit {unit})
    (exclude_from_sim no)
    (in_bom yes)
    (on_board yes)
    (dnp no)
    (uuid "{u}")
    (property "Reference" "{ref}"
      (at {x} {y - 3} 0)
      (effects (font (size 1.27 1.27)))
    )
    (property "Value" "{val_str}"
      (at {x} {y - 5} 0)
      (effects (font (size 1.27 1.27)))
    )
    (property "Footprint" "{fp}"
      (at {x} {y - 7} 0)
      (effects (font (size 1.27 1.27)) hide)
    )
  )
"""

def sch_power_flag(name, x, y):
    """Place a power flag/symbol."""
    return f"""  (symbol
    (lib_id "power:{name}")
    (at {x} {y} 0)
    (unit 1)
    (exclude_from_sim no)
    (in_bom no)
    (on_board yes)
    (dnp no)
    (uuid "{uid()}")
    (property "Reference" "#PWR?"
      (at {x} {y+2} 0)
      (effects (font (size 1.27 1.27)) hide)
    )
    (property "Value" "{name}"
      (at {x} {y-2} 0)
      (effects (font (size 1.27 1.27)))
    )
  )
"""

# ============================================================
# PIN REGISTRY — maps symbol names to pin connection points
# CUSTOM_PINS: auto-populated by make_symbol() during generate_symbol_library()
# DEVICE_PINS: KiCad standard Device library (not created by make_symbol)
# Pin format: (pin_name, local_x, local_y)
# When symbol placed at (sx, sy), absolute position = (sx + local_x, sy - local_y)
# ============================================================

DEVICE_PINS = {
    'R':             [('1', 0, 3.81), ('2', 0, -3.81)],
    'C':             [('1', 0, 3.81), ('2', 0, -3.81)],
    'C_Polarized':   [('1', 0, 3.81), ('2', 0, -3.81)],
    'L':             [('1', 0, 3.81), ('2', 0, -3.81)],
    'FerriteBead':   [('1', 0, 3.81), ('2', 0, -3.81)],
    'Crystal':       [('1', -3.81, 0), ('2', 3.81, 0)],
    'Q_PMOS_GSD':    [('G', -5.08, 0), ('S', 2.54, -5.08), ('D', 2.54, 5.08)],
}


def pin_abs(sx, sy, local_x, local_y):
    """Convert symbol-local pin position to schematic absolute position.
    Symbol coordinates are Y-up; schematic is Y-down."""
    return (round(sx + local_x, 2), round(sy - local_y, 2))


def get_pin_positions(symbol_name, sx, sy):
    """Get dict of pin_name → (abs_x, abs_y) for a symbol placed at (sx, sy)."""
    pins = CUSTOM_PINS.get(symbol_name) or DEVICE_PINS.get(symbol_name, [])
    return {name: pin_abs(sx, sy, lx, ly) for name, lx, ly in pins}


def wired_sym(ref, lib, symbol_name, sx, sy, value='', fp='', connections=None):
    """Place a symbol and generate wire+label connections at its pins.

    connections: dict of pin_name → net_name (or None to skip that pin)
    Returns list of items for generate_subsheet().
    """
    items = [{'type': 'component', 'ref': ref, 'lib': lib, 'symbol': symbol_name,
              'x': sx, 'y': sy, 'value': value or symbol_name, 'fp': fp}]

    if not connections:
        return items

    pin_pos = get_pin_positions(symbol_name, sx, sy)

    for pin_name, net_name in connections.items():
        if net_name is None:
            continue
        if pin_name not in pin_pos:
            continue
        px, py = pin_pos[pin_name]

        # Place label at pin connection point
        if net_name == 'GND':
            items.append({'type': 'power', 'name': 'GND', 'x': px, 'y': py})
        elif net_name.startswith('~'):  # ~name means hier_label
            items.append({'type': 'hier_label', 'x': px, 'y': py,
                         'name': net_name[1:], 'shape': 'bidirectional'})
        else:
            items.append({'type': 'local_label', 'x': px, 'y': py, 'name': net_name})

    return items


def generate_subsheet(filename, title, components_and_labels):
    """Generate a sub-schematic with placed components and labels.
    components_and_labels: list of dicts with type='component' or 'label' or 'text'
    """
    content = sch_header(title, "A3")

    for item in components_and_labels:
        if item['type'] == 'component':
            content += sch_symbol_instance(
                item['ref'], item['lib'], item['symbol'],
                item['x'], item['y'],
                value=item.get('value', ''),
                fp=item.get('fp', '')
            )
        elif item['type'] == 'label':
            content += sch_label(item['x'], item['y'], item['name'],
                               item.get('shape', 'input'))
        elif item['type'] == 'text':
            content += sch_text(item['x'], item['y'], item['text'],
                              item.get('size', 1.5))
        elif item['type'] == 'wire':
            content += sch_wire(item['x1'], item['y1'], item['x2'], item['y2'])
        elif item['type'] == 'no_connect':
            content += sch_no_connect(item['x'], item['y'])
        elif item['type'] == 'junction':
            content += sch_junction(item['x'], item['y'])
        elif item['type'] == 'local_label':
            content += sch_local_label(item['x'], item['y'], item['name'], item.get('angle', 0))
        elif item['type'] == 'hier_label':
            content += sch_hier_label(item['x'], item['y'], item['name'], item.get('shape', 'input'))
        elif item['type'] == 'power':
            content += sch_power_flag(item['name'], item['x'], item['y'])

    content += ")\n"

    path = os.path.join(PROJECT_DIR, filename)
    with open(path, 'w') as f:
        f.write(content)
    print(f"  Created {path}")


def generate_all_subsheets():
    # ============ Sheet 1: RK3576 Compute ============
    items = [
        {'type': 'text', 'x': 50, 'y': 15, 'text': 'RK3576 COMPUTE DOMAIN', 'size': 3},
        {'type': 'text', 'x': 50, 'y': 22, 'text': '4xA72@2.2G + 4xA53@1.8G + 6T NPU + Mali-G52', 'size': 1.5},

        # ===== RK3576 SoC =====
        {'type': 'component', 'ref': 'U1', 'lib': 'solarpunk-pi-v3', 'symbol': 'RK3576',
         'x': 100, 'y': 120, 'value': 'RK3576', 'fp': 'Package_BGA:BGA-698'},

        # ===== RK806 PMIC =====
        {'type': 'text', 'x': 250, 'y': 30, 'text': 'PMIC — RK806-1', 'size': 2},
        {'type': 'component', 'ref': 'U2', 'lib': 'solarpunk-pi-v3', 'symbol': 'RK806',
         'x': 280, 'y': 80, 'value': 'RK806-1', 'fp': 'Package_QFN:QFN-68'},
        # RK806 SPI bus (connects to RK3576 SPI2)
        {'type': 'local_label', 'x': 255, 'y': 65, 'name': 'PMIC_SPI_CLK'},
        {'type': 'local_label', 'x': 255, 'y': 70, 'name': 'PMIC_SPI_MOSI'},
        {'type': 'local_label', 'x': 255, 'y': 75, 'name': 'PMIC_SPI_MISO'},
        {'type': 'local_label', 'x': 255, 'y': 80, 'name': 'PMIC_SPI_CS'},
        {'type': 'wire', 'x1': 130, 'y1': 105, 'x2': 160, 'y2': 105},
        {'type': 'local_label', 'x': 160, 'y': 105, 'name': 'PMIC_SPI_CLK'},
        {'type': 'wire', 'x1': 130, 'y1': 110, 'x2': 160, 'y2': 110},
        {'type': 'local_label', 'x': 160, 'y': 110, 'name': 'PMIC_SPI_MOSI'},
        {'type': 'wire', 'x1': 130, 'y1': 115, 'x2': 160, 'y2': 115},
        {'type': 'local_label', 'x': 160, 'y': 115, 'name': 'PMIC_SPI_MISO'},
        {'type': 'wire', 'x1': 130, 'y1': 120, 'x2': 160, 'y2': 120},
        {'type': 'local_label', 'x': 160, 'y': 120, 'name': 'PMIC_SPI_CS'},
        # RK806 power outputs → local labels
        {'type': 'text', 'x': 310, 'y': 50, 'text': 'PMIC Power Outputs', 'size': 1.2},
        {'type': 'local_label', 'x': 310, 'y': 58, 'name': 'VDD_CPU_BIG'},
        {'type': 'local_label', 'x': 310, 'y': 63, 'name': 'VDD_CPU_LIT'},
        {'type': 'local_label', 'x': 310, 'y': 68, 'name': 'VDD_GPU'},
        {'type': 'local_label', 'x': 310, 'y': 73, 'name': 'VDD_NPU'},
        {'type': 'local_label', 'x': 310, 'y': 78, 'name': 'VDD_LOGIC'},
        {'type': 'local_label', 'x': 310, 'y': 83, 'name': 'VDD_DDR'},
        {'type': 'local_label', 'x': 310, 'y': 88, 'name': 'VDDQ_DDR'},
        {'type': 'local_label', 'x': 310, 'y': 93, 'name': 'VCC_3V3_RK'},
        {'type': 'local_label', 'x': 310, 'y': 98, 'name': 'VCC_1V8'},
        {'type': 'local_label', 'x': 310, 'y': 103, 'name': 'PWRGD'},
        # RK806 input bypass caps
        {'type': 'component', 'ref': 'C1', 'lib': 'Device', 'symbol': 'C',
         'x': 260, 'y': 55, 'value': '100nF', 'fp': 'Capacitor_SMD:C_0402'},
        {'type': 'component', 'ref': 'C2', 'lib': 'Device', 'symbol': 'C',
         'x': 270, 'y': 55, 'value': '10uF', 'fp': 'Capacitor_SMD:C_0805'},
        {'type': 'local_label', 'x': 265, 'y': 50, 'name': '5V_BRAIN'},
        {'type': 'power', 'name': 'GND', 'x': 265, 'y': 60},
        # RK806 DCDC output bulk caps (10uF each)
        {'type': 'component', 'ref': 'C3', 'lib': 'Device', 'symbol': 'C',
         'x': 330, 'y': 58, 'value': '10uF', 'fp': 'Capacitor_SMD:C_0805'},
        {'type': 'component', 'ref': 'C4', 'lib': 'Device', 'symbol': 'C',
         'x': 330, 'y': 68, 'value': '10uF', 'fp': 'Capacitor_SMD:C_0805'},
        {'type': 'component', 'ref': 'C5', 'lib': 'Device', 'symbol': 'C',
         'x': 330, 'y': 78, 'value': '10uF', 'fp': 'Capacitor_SMD:C_0805'},
        {'type': 'component', 'ref': 'C6', 'lib': 'Device', 'symbol': 'C',
         'x': 330, 'y': 88, 'value': '10uF', 'fp': 'Capacitor_SMD:C_0805'},
        {'type': 'component', 'ref': 'C7', 'lib': 'Device', 'symbol': 'C',
         'x': 330, 'y': 98, 'value': '10uF', 'fp': 'Capacitor_SMD:C_0805'},
        {'type': 'component', 'ref': 'C8', 'lib': 'Device', 'symbol': 'C',
         'x': 330, 'y': 108, 'value': '10uF', 'fp': 'Capacitor_SMD:C_0805'},

        # ===== LPDDR4X x2 = 8GB =====
        {'type': 'text', 'x': 30, 'y': 250, 'text': 'LPDDR4X — 2x Samsung K4UBE3D4AB = 8GB', 'size': 2},
        {'type': 'component', 'ref': 'U3', 'lib': 'solarpunk-pi-v3', 'symbol': 'LPDDR4X',
         'x': 70, 'y': 280, 'value': 'K4UBE3D4AB CH0', 'fp': 'Package_BGA:BGA-200'},
        {'type': 'component', 'ref': 'U4', 'lib': 'solarpunk-pi-v3', 'symbol': 'LPDDR4X',
         'x': 180, 'y': 280, 'value': 'K4UBE3D4AB CH1', 'fp': 'Package_BGA:BGA-200'},
        # DDR bus labels CH0 (RK3576 left side → U3)
        {'type': 'text', 'x': 30, 'y': 260, 'text': 'CH0: DQ[0:15], DQS[0:1], DM[0:1], CA[0:5], CK/CKE/CS/ODT', 'size': 1},
        {'type': 'local_label', 'x': 50, 'y': 268, 'name': 'DDR_CH0_DQ'},
        {'type': 'local_label', 'x': 50, 'y': 273, 'name': 'DDR_CH0_DQS'},
        {'type': 'local_label', 'x': 50, 'y': 278, 'name': 'DDR_CH0_CA'},
        {'type': 'local_label', 'x': 50, 'y': 283, 'name': 'DDR_CH0_CK'},
        # DDR bus labels CH1 (RK3576 right side → U4)
        {'type': 'text', 'x': 150, 'y': 260, 'text': 'CH1: DQ[16:31], DQS[2:3], DM[2:3], CA[0:5], CK/CKE/CS/ODT', 'size': 1},
        {'type': 'local_label', 'x': 160, 'y': 268, 'name': 'DDR_CH1_DQ'},
        {'type': 'local_label', 'x': 160, 'y': 273, 'name': 'DDR_CH1_DQS'},
        {'type': 'local_label', 'x': 160, 'y': 278, 'name': 'DDR_CH1_CA'},
        {'type': 'local_label', 'x': 160, 'y': 283, 'name': 'DDR_CH1_CK'},
        # DDR decoupling: 100nF per VDD/VDDQ ball (represented as groups)
        {'type': 'component', 'ref': 'C10', 'lib': 'Device', 'symbol': 'C',
         'x': 70, 'y': 300, 'value': '100nF x8 VDD', 'fp': 'Capacitor_SMD:C_0402'},
        {'type': 'component', 'ref': 'C11', 'lib': 'Device', 'symbol': 'C',
         'x': 90, 'y': 300, 'value': '100nF x8 VDDQ', 'fp': 'Capacitor_SMD:C_0402'},
        {'type': 'component', 'ref': 'C12', 'lib': 'Device', 'symbol': 'C',
         'x': 180, 'y': 300, 'value': '100nF x8 VDD', 'fp': 'Capacitor_SMD:C_0402'},
        {'type': 'component', 'ref': 'C13', 'lib': 'Device', 'symbol': 'C',
         'x': 200, 'y': 300, 'value': '100nF x8 VDDQ', 'fp': 'Capacitor_SMD:C_0402'},
        {'type': 'local_label', 'x': 80, 'y': 295, 'name': 'VDD_DDR'},
        {'type': 'local_label', 'x': 190, 'y': 295, 'name': 'VDDQ_DDR'},
        {'type': 'power', 'name': 'GND', 'x': 80, 'y': 305},
        {'type': 'power', 'name': 'GND', 'x': 190, 'y': 305},

        # ===== eMMC 32GB =====
        {'type': 'text', 'x': 250, 'y': 150, 'text': 'eMMC 5.1 — Samsung KLMAG2JENB 32GB', 'size': 2},
        {'type': 'component', 'ref': 'U5', 'lib': 'solarpunk-pi-v3', 'symbol': 'eMMC_BGA153',
         'x': 280, 'y': 180, 'value': 'KLMAG2JENB 32GB', 'fp': 'Package_BGA:BGA-153'},
        # eMMC bus labels
        {'type': 'local_label', 'x': 260, 'y': 170, 'name': 'EMMC_CLK'},
        {'type': 'local_label', 'x': 260, 'y': 175, 'name': 'EMMC_CMD'},
        {'type': 'local_label', 'x': 260, 'y': 180, 'name': 'EMMC_D0'},
        {'type': 'local_label', 'x': 260, 'y': 185, 'name': 'EMMC_D7'},
        {'type': 'local_label', 'x': 260, 'y': 190, 'name': 'EMMC_DS'},
        {'type': 'local_label', 'x': 260, 'y': 195, 'name': 'EMMC_RST'},
        {'type': 'text', 'x': 250, 'y': 165, 'text': 'HS400: CLK, CMD, D[0:7], DS, RST', 'size': 1},
        # eMMC decoupling
        {'type': 'component', 'ref': 'C14', 'lib': 'Device', 'symbol': 'C',
         'x': 300, 'y': 170, 'value': '100nF', 'fp': 'Capacitor_SMD:C_0402'},
        {'type': 'component', 'ref': 'C15', 'lib': 'Device', 'symbol': 'C',
         'x': 310, 'y': 170, 'value': '10uF', 'fp': 'Capacitor_SMD:C_0805'},
        {'type': 'local_label', 'x': 305, 'y': 165, 'name': 'VCC_1V8'},
        {'type': 'local_label', 'x': 305, 'y': 200, 'name': 'VCC_3V3_RK'},
        {'type': 'power', 'name': 'GND', 'x': 305, 'y': 205},

        # ===== SPI NOR Flash (boot) =====
        {'type': 'text', 'x': 250, 'y': 210, 'text': 'SPI NOR — W25Q128 (QSPI boot)', 'size': 2},
        {'type': 'component', 'ref': 'U6', 'lib': 'solarpunk-pi-v3', 'symbol': 'W25Q128',
         'x': 280, 'y': 230, 'value': 'W25Q128JVSIQ', 'fp': 'Package_SO:SOP-8'},
        # QSPI bus labels
        {'type': 'local_label', 'x': 260, 'y': 225, 'name': 'FSPI_CLK'},
        {'type': 'local_label', 'x': 260, 'y': 230, 'name': 'FSPI_CS'},
        {'type': 'local_label', 'x': 260, 'y': 235, 'name': 'FSPI_D0'},
        {'type': 'local_label', 'x': 260, 'y': 240, 'name': 'FSPI_D1'},
        {'type': 'local_label', 'x': 260, 'y': 245, 'name': 'FSPI_D2'},
        {'type': 'local_label', 'x': 260, 'y': 250, 'name': 'FSPI_D3'},
        # W25Q128 bypass + pull-ups
        {'type': 'component', 'ref': 'C16', 'lib': 'Device', 'symbol': 'C',
         'x': 300, 'y': 225, 'value': '100nF', 'fp': 'Capacitor_SMD:C_0402'},
        {'type': 'component', 'ref': 'R1', 'lib': 'Device', 'symbol': 'R',
         'x': 300, 'y': 235, 'value': '10k', 'fp': 'Resistor_SMD:R_0402'},
        {'type': 'text', 'x': 305, 'y': 235, 'text': 'CS pull-up', 'size': 0.8},
        {'type': 'local_label', 'x': 300, 'y': 220, 'name': 'VCC_1V8'},
        {'type': 'power', 'name': 'GND', 'x': 300, 'y': 255},

        # ===== RK3576 decoupling =====
        {'type': 'text', 'x': 30, 'y': 175, 'text': 'RK3576 Decoupling (representative — 30+ caps total)', 'size': 1.5},
        {'type': 'component', 'ref': 'C20', 'lib': 'Device', 'symbol': 'C',
         'x': 40, 'y': 190, 'value': '100nF x12 VDD_CPU', 'fp': 'Capacitor_SMD:C_0402'},
        {'type': 'component', 'ref': 'C21', 'lib': 'Device', 'symbol': 'C',
         'x': 60, 'y': 190, 'value': '100nF x8 VDD_GPU', 'fp': 'Capacitor_SMD:C_0402'},
        {'type': 'component', 'ref': 'C22', 'lib': 'Device', 'symbol': 'C',
         'x': 80, 'y': 190, 'value': '100nF x6 VDD_NPU', 'fp': 'Capacitor_SMD:C_0402'},
        {'type': 'component', 'ref': 'C23', 'lib': 'Device', 'symbol': 'C',
         'x': 100, 'y': 190, 'value': '100nF x4 VDD_LOGIC', 'fp': 'Capacitor_SMD:C_0402'},
        {'type': 'component', 'ref': 'C24', 'lib': 'Device', 'symbol': 'C',
         'x': 120, 'y': 190, 'value': '10uF x4 bulk', 'fp': 'Capacitor_SMD:C_0805'},
        {'type': 'local_label', 'x': 40, 'y': 185, 'name': 'VDD_CPU_BIG'},
        {'type': 'local_label', 'x': 60, 'y': 185, 'name': 'VDD_GPU'},
        {'type': 'local_label', 'x': 80, 'y': 185, 'name': 'VDD_NPU'},
        {'type': 'local_label', 'x': 100, 'y': 185, 'name': 'VDD_LOGIC'},
        {'type': 'power', 'name': 'GND', 'x': 80, 'y': 200},

        # ===== RK3576 interface bus labels =====
        # Connect to RK3576 SoC outputs (right side)
        {'type': 'local_label', 'x': 130, 'y': 130, 'name': 'RGMII_BUS'},
        {'type': 'local_label', 'x': 130, 'y': 135, 'name': 'SDIO_BUS'},
        {'type': 'local_label', 'x': 130, 'y': 140, 'name': 'I2S_BUS'},
        {'type': 'local_label', 'x': 130, 'y': 145, 'name': 'USB3_0'},
        {'type': 'local_label', 'x': 130, 'y': 150, 'name': 'USB3_1'},
        {'type': 'local_label', 'x': 130, 'y': 155, 'name': 'USB2_0'},
        {'type': 'local_label', 'x': 130, 'y': 160, 'name': 'USB2_1'},
        {'type': 'local_label', 'x': 130, 'y': 165, 'name': 'HDMI_BUS'},
        {'type': 'local_label', 'x': 70, 'y': 130, 'name': 'CSI0_BUS'},
        {'type': 'local_label', 'x': 70, 'y': 135, 'name': 'CSI1_BUS'},

        # ===== Hierarchical labels =====
        {'type': 'hier_label', 'x': 20, 'y': 40, 'name': '5V_SYS', 'shape': 'input'},
        {'type': 'hier_label', 'x': 20, 'y': 48, 'name': 'GND', 'shape': 'input'},
        {'type': 'hier_label', 'x': 380, 'y': 40, 'name': 'UART4_TX', 'shape': 'output'},
        {'type': 'hier_label', 'x': 380, 'y': 48, 'name': 'UART4_RX', 'shape': 'input'},
        {'type': 'hier_label', 'x': 380, 'y': 56, 'name': 'UART5_TX', 'shape': 'output'},
        {'type': 'hier_label', 'x': 380, 'y': 64, 'name': 'UART5_RX', 'shape': 'input'},
        {'type': 'hier_label', 'x': 380, 'y': 72, 'name': 'SPI2_CLK', 'shape': 'output'},
        {'type': 'hier_label', 'x': 380, 'y': 80, 'name': 'SPI2_MOSI', 'shape': 'output'},
        {'type': 'hier_label', 'x': 380, 'y': 88, 'name': 'SPI2_MISO', 'shape': 'input'},
        {'type': 'hier_label', 'x': 380, 'y': 96, 'name': 'SPI2_CS', 'shape': 'output'},
        {'type': 'hier_label', 'x': 380, 'y': 104, 'name': 'GPIO_SHUTDOWN', 'shape': 'output'},
        {'type': 'hier_label', 'x': 380, 'y': 112, 'name': 'GPIO_ALARM_IRQ', 'shape': 'input'},
        {'type': 'hier_label', 'x': 380, 'y': 120, 'name': 'RGMII_BUS', 'shape': 'output'},
        {'type': 'hier_label', 'x': 380, 'y': 128, 'name': 'SDIO_BUS', 'shape': 'output'},
        {'type': 'hier_label', 'x': 380, 'y': 136, 'name': 'I2S_BUS', 'shape': 'output'},
        {'type': 'hier_label', 'x': 380, 'y': 144, 'name': 'USB3_0', 'shape': 'bidirectional'},
        {'type': 'hier_label', 'x': 380, 'y': 152, 'name': 'USB3_1', 'shape': 'bidirectional'},
        {'type': 'hier_label', 'x': 380, 'y': 160, 'name': 'USB2_0', 'shape': 'bidirectional'},
        {'type': 'hier_label', 'x': 380, 'y': 168, 'name': 'USB2_1', 'shape': 'bidirectional'},
        {'type': 'hier_label', 'x': 380, 'y': 176, 'name': 'USB2_CELL', 'shape': 'bidirectional'},

        # Notes
        {'type': 'text', 'x': 30, 'y': 320, 'text': 'NOTE: 100nF 0402 cap within 0.5mm of EVERY RK3576 VDD ball (30+ total)', 'size': 1.2},
        {'type': 'text', 'x': 30, 'y': 326, 'text': 'NOTE: 10uF 0805 bulk cap at each power domain entry', 'size': 1.2},
        {'type': 'text', 'x': 30, 'y': 332, 'text': 'NOTE: DDR traces matched to ±5ps within each byte lane', 'size': 1.2},
        {'type': 'text', 'x': 30, 'y': 338, 'text': 'NOTE: eMMC HS400 requires 33R series on CLK, match D[0:7] ±10ps', 'size': 1.2},
    ]
    generate_subsheet("01-rk3576-compute.kicad_sch", "RK3576 Compute Domain", items)

    # ============ Sheet 2: Connectivity ============
    items = [
        {'type': 'text', 'x': 50, 'y': 15, 'text': 'CONNECTIVITY', 'size': 3},
        {'type': 'text', 'x': 50, 'y': 22, 'text': 'GbE + WiFi 5 + 4G LTE + Audio + USB + HDMI + Cameras', 'size': 1.5},
        # GbE PHY
        {'type': 'text', 'x': 30, 'y': 35, 'text': 'Gigabit Ethernet — RTL8211F + RJ45/PoE', 'size': 2},
        {'type': 'component', 'ref': 'U7', 'lib': 'solarpunk-pi-v3', 'symbol': 'RTL8211F',
         'x': 80, 'y': 80, 'value': 'RTL8211F-CG', 'fp': 'Package_QFN:QFN-40'},
        {'type': 'component', 'ref': 'J1', 'lib': 'Connector', 'symbol': 'RJ45_PoE',
         'x': 200, 'y': 80, 'value': 'HR911105A', 'fp': 'Connector_RJ:RJ45_PoE_Magnetics'},
        # WiFi 5
        {'type': 'text', 'x': 30, 'y': 130, 'text': 'WiFi 5 + BT 5.0 — RTL8852BS (SDIO)', 'size': 2},
        {'type': 'component', 'ref': 'U8', 'lib': 'solarpunk-pi-v3', 'symbol': 'RTL8852BS',
         'x': 80, 'y': 165, 'value': 'RTL8852BS', 'fp': ''},
        # Cellular
        {'type': 'text', 'x': 250, 'y': 35, 'text': '4G LTE — Quectel EC25-E', 'size': 2},
        {'type': 'component', 'ref': 'U9', 'lib': 'Device', 'symbol': 'IC_Generic',
         'x': 300, 'y': 70, 'value': 'EC25-E', 'fp': 'Connector:M.2_B-key'},
        {'type': 'component', 'ref': 'J2', 'lib': 'Connector', 'symbol': 'SIM_Card',
         'x': 300, 'y': 120, 'value': 'Nano-SIM', 'fp': 'Connector_Card:SIM_Nano'},
        # Audio
        {'type': 'text', 'x': 250, 'y': 140, 'text': 'Audio — ES8316 Codec', 'size': 2},
        {'type': 'component', 'ref': 'U10', 'lib': 'solarpunk-pi-v3', 'symbol': 'ES8316',
         'x': 300, 'y': 175, 'value': 'ES8316', 'fp': 'Package_QFN:QFN-24'},
        {'type': 'component', 'ref': 'J3', 'lib': 'Connector', 'symbol': 'AudioJack4',
         'x': 380, 'y': 175, 'value': '3.5mm TRRS', 'fp': 'Connector_Audio:TRRS_3.5mm'},
        # USB-C x4
        {'type': 'text', 'x': 30, 'y': 210, 'text': 'USB-C x4 — 2x USB3.1 + 2x USB2.0', 'size': 2},
        {'type': 'component', 'ref': 'J4', 'lib': 'Connector', 'symbol': 'USB_C',
         'x': 50, 'y': 240, 'value': 'USB-C #1 OTG+DP+PD', 'fp': 'Connector_USB:USB_C'},
        {'type': 'component', 'ref': 'J5', 'lib': 'Connector', 'symbol': 'USB_C',
         'x': 150, 'y': 240, 'value': 'USB-C #2 Host 3.1', 'fp': 'Connector_USB:USB_C'},
        {'type': 'component', 'ref': 'J6', 'lib': 'Connector', 'symbol': 'USB_C',
         'x': 250, 'y': 240, 'value': 'USB-C #3 Host 2.0', 'fp': 'Connector_USB:USB_C'},
        {'type': 'component', 'ref': 'J7', 'lib': 'Connector', 'symbol': 'USB_C',
         'x': 350, 'y': 240, 'value': 'USB-C #4 Host 2.0', 'fp': 'Connector_USB:USB_C'},
        # HDMI
        {'type': 'text', 'x': 30, 'y': 280, 'text': 'Micro-HDMI 2.0 — 4K@60fps', 'size': 2},
        {'type': 'component', 'ref': 'J8', 'lib': 'Connector', 'symbol': 'HDMI_Micro',
         'x': 80, 'y': 310, 'value': 'Micro-HDMI', 'fp': 'Connector_HDMI:HDMI_Micro_D'},
        # CSI Cameras
        {'type': 'text', 'x': 200, 'y': 280, 'text': 'MIPI CSI Cameras', 'size': 2},
        {'type': 'component', 'ref': 'J9', 'lib': 'Connector', 'symbol': 'FPC_22pin',
         'x': 230, 'y': 310, 'value': 'CSI-1 4-lane 4K', 'fp': 'Connector_FFC-FPC:FPC_22pin'},
        {'type': 'component', 'ref': 'J10', 'lib': 'Connector', 'symbol': 'FPC_15pin',
         'x': 330, 'y': 310, 'value': 'CSI-2 2-lane 1080p', 'fp': 'Connector_FFC-FPC:FPC_15pin'},
        # 40-pin GPIO
        {'type': 'text', 'x': 30, 'y': 340, 'text': '40-Pin GPIO Header (Pi 5 Compatible)', 'size': 2},
        {'type': 'component', 'ref': 'J11', 'lib': 'Connector_Generic', 'symbol': 'Conn_02x20',
         'x': 80, 'y': 370, 'value': '2x20 GPIO', 'fp': 'Connector_PinHeader_2.54mm:PinHeader_2x20_P2.54mm_Vertical'},
        # U.FL antennas
        {'type': 'component', 'ref': 'J12', 'lib': 'Connector', 'symbol': 'U.FL',
         'x': 200, 'y': 165, 'value': 'WiFi Main', 'fp': 'Connector_Coaxial:U.FL'},
        {'type': 'component', 'ref': 'J13', 'lib': 'Connector', 'symbol': 'U.FL',
         'x': 200, 'y': 180, 'value': 'WiFi Aux', 'fp': 'Connector_Coaxial:U.FL'},
        # ESD protection
        {'type': 'text', 'x': 30, 'y': 400, 'text': 'ESD Protection', 'size': 2},
        {'type': 'component', 'ref': 'U11', 'lib': 'Device', 'symbol': 'IC_Generic',
         'x': 80, 'y': 420, 'value': 'USBLC6-2SC6 x4', 'fp': 'Package_TO_SOT_SMD:SOT-23-6'},
        {'type': 'component', 'ref': 'U12', 'lib': 'Device', 'symbol': 'IC_Generic',
         'x': 200, 'y': 420, 'value': 'PRTR5V0U2X (HDMI)', 'fp': 'Package_TO_SOT_SMD:SOT-363'},
        {'type': 'component', 'ref': 'U13', 'lib': 'Device', 'symbol': 'IC_Generic',
         'x': 320, 'y': 420, 'value': 'PRTR5V0U2X (SIM)', 'fp': 'Package_TO_SOT_SMD:SOT-363'},
        # RTL8211F bypass caps
        {'type': 'component', 'ref': 'C70', 'lib': 'Device', 'symbol': 'C',
         'x': 60, 'y': 65, 'value': '100nF', 'fp': 'Capacitor_SMD:C_0402'},
        {'type': 'component', 'ref': 'C71', 'lib': 'Device', 'symbol': 'C',
         'x': 70, 'y': 65, 'value': '10uF', 'fp': 'Capacitor_SMD:C_0805'},
        # RTL8211F 25MHz crystal
        {'type': 'component', 'ref': 'Y3', 'lib': 'Device', 'symbol': 'Crystal',
         'x': 60, 'y': 100, 'value': '25MHz', 'fp': 'Crystal:Crystal_SMD_3225-4Pin'},
        {'type': 'component', 'ref': 'C72', 'lib': 'Device', 'symbol': 'C',
         'x': 50, 'y': 105, 'value': '20pF', 'fp': 'Capacitor_SMD:C_0402'},
        {'type': 'component', 'ref': 'C73', 'lib': 'Device', 'symbol': 'C',
         'x': 70, 'y': 105, 'value': '20pF', 'fp': 'Capacitor_SMD:C_0402'},
        # ES8316 bypass
        {'type': 'component', 'ref': 'C74', 'lib': 'Device', 'symbol': 'C',
         'x': 280, 'y': 170, 'value': '100nF', 'fp': 'Capacitor_SMD:C_0402'},
        {'type': 'component', 'ref': 'C75', 'lib': 'Device', 'symbol': 'C',
         'x': 290, 'y': 170, 'value': '10uF', 'fp': 'Capacitor_SMD:C_0805'},
        # USB ESD bypass
        {'type': 'component', 'ref': 'C76', 'lib': 'Device', 'symbol': 'C',
         'x': 80, 'y': 415, 'value': '100nF x4', 'fp': 'Capacitor_SMD:C_0402'},
        # Hierarchical labels (matching parent sheet pins)
        {'type': 'hier_label', 'x': 10, 'y': 40, 'name': '5V_SYS', 'shape': 'input'},
        {'type': 'hier_label', 'x': 10, 'y': 48, 'name': '3V3_RK', 'shape': 'input'},
        {'type': 'hier_label', 'x': 10, 'y': 56, 'name': 'GND', 'shape': 'input'},
        {'type': 'hier_label', 'x': 10, 'y': 64, 'name': 'RGMII_BUS', 'shape': 'input'},
        {'type': 'hier_label', 'x': 10, 'y': 72, 'name': 'SDIO_BUS', 'shape': 'input'},
        {'type': 'hier_label', 'x': 10, 'y': 80, 'name': 'I2S_BUS', 'shape': 'input'},
        {'type': 'hier_label', 'x': 10, 'y': 88, 'name': 'USB3_0', 'shape': 'bidirectional'},
        {'type': 'hier_label', 'x': 10, 'y': 96, 'name': 'USB3_1', 'shape': 'bidirectional'},
        {'type': 'hier_label', 'x': 10, 'y': 104, 'name': 'USB2_0', 'shape': 'bidirectional'},
        {'type': 'hier_label', 'x': 10, 'y': 112, 'name': 'USB2_1', 'shape': 'bidirectional'},
        {'type': 'hier_label', 'x': 10, 'y': 120, 'name': 'USB2_CELL', 'shape': 'bidirectional'},
        {'type': 'hier_label', 'x': 10, 'y': 128, 'name': 'HDMI_BUS', 'shape': 'input'},
        {'type': 'hier_label', 'x': 10, 'y': 136, 'name': 'CSI0_BUS', 'shape': 'input'},
        {'type': 'hier_label', 'x': 10, 'y': 144, 'name': 'CSI1_BUS', 'shape': 'input'},
        {'type': 'hier_label', 'x': 400, 'y': 40, 'name': '48V_POE', 'shape': 'output'},
    ]
    generate_subsheet("02-connectivity.kicad_sch", "Connectivity — Ethernet, WiFi, Cellular, USB, HDMI, Camera, Audio", items)

    # ============ Sheet 3: RP2350 Radio ============
    items = [
        {'type': 'text', 'x': 50, 'y': 15, 'text': 'RP2350 POWER & RADIO DOMAIN', 'size': 3},
        {'type': 'text', 'x': 50, 'y': 22, 'text': 'Always-on: 2xM33@150MHz, ~0.1W — WiFi 4 + LoRa Mesh', 'size': 1.5},

        # ===== Power/GND border hier_labels → wire → local_label =====
        # 3V3_RP rail
        {'type': 'hier_label', 'x': 20, 'y': 40, 'name': '3V3_RP', 'shape': 'input'},
        {'type': 'wire', 'x1': 20, 'y1': 40, 'x2': 30, 'y2': 40},
        {'type': 'local_label', 'x': 30, 'y': 40, 'name': '3V3_RP'},
        # 5V_SYS rail
        {'type': 'hier_label', 'x': 20, 'y': 48, 'name': '5V_SYS', 'shape': 'input'},
        {'type': 'wire', 'x1': 20, 'y1': 48, 'x2': 30, 'y2': 48},
        {'type': 'local_label', 'x': 30, 'y': 48, 'name': '5V_SYS'},
        # GND rail
        {'type': 'hier_label', 'x': 20, 'y': 56, 'name': 'GND', 'shape': 'input'},
        {'type': 'wire', 'x1': 20, 'y1': 56, 'x2': 30, 'y2': 56},
        {'type': 'local_label', 'x': 30, 'y': 56, 'name': 'GND'},
        # Signal hier_labels (right border) — connect via ~NAME in wired_sym at IC pin positions
        {'type': 'hier_label', 'x': 380, 'y': 40, 'name': 'PWR_ENABLE', 'shape': 'output'},
        {'type': 'hier_label', 'x': 380, 'y': 48, 'name': 'PWR_GOOD', 'shape': 'input'},
        {'type': 'hier_label', 'x': 380, 'y': 56, 'name': 'UART4_RX_BUF', 'shape': 'input'},
        {'type': 'hier_label', 'x': 380, 'y': 64, 'name': 'UART4_TX_BUF', 'shape': 'output'},
        {'type': 'hier_label', 'x': 380, 'y': 72, 'name': 'WAKE_REQUEST', 'shape': 'input'},
        {'type': 'hier_label', 'x': 380, 'y': 80, 'name': 'RK3506_RESET', 'shape': 'output'},
        {'type': 'hier_label', 'x': 380, 'y': 88, 'name': 'SHUTDOWN_IN', 'shape': 'input'},

        # ===== RP2350A — U20 at (100, 100) =====
        # Left pins: GP* signals; Right pins: power/QSPI/clock
        *wired_sym('U20', 'solarpunk-pi-v3', 'RP2350A', 100, 100,
            'RP2350A', 'Package_QFN:QFN-60-1EP_7x7mm_P0.4mm', {
            # Left side GP pins
            'GP0/UART0_TX':    '~UART4_TX_BUF',
            'GP1/UART0_RX':    '~UART4_RX_BUF',
            'GP2/SPI0_SCK':    'CYW_SPI_CLK',
            'GP3/SPI0_TX':     'CYW_SPI_MOSI',
            'GP4/SPI0_RX':     'CYW_SPI_MISO',
            'GP5/SPI0_CS':     'CYW_SPI_CS',
            'GP9':             'LORA_SPI_CLK',
            'GP12/ADC_PWRGD':  '~PWR_GOOD',
            'GP13/WAKE_REQ':   '~WAKE_REQUEST',
            'GP14/RK3506_RST': '~RK3506_RESET',
            'GP15/PWR_EN':     '~PWR_ENABLE',
            'GP23':            'LORA_SPI_MOSI',
            'GP24':            'LORA_SPI_MISO',
            'GP25':            'LORA_CS',
            'GP26/ADC0':       'ADC_VBAT',
            'GP27/ADC1':       'ADC_SOLAR',
            'GP28/SHUTDOWN':   '~SHUTDOWN_IN',
            'GP29/ADC3':       None,
            # Right side power/clock/QSPI
            'IOVDD':           '3V3_RP',
            'DVDD':            '3V3_RP',
            'USB_DP':          None,
            'USB_DM':          None,
            'VREG_VIN':        '3V3_RP',
            'VREG_VOUT':       None,
            'XIN':             'RP_XIN',
            'XOUT':            'RP_XOUT',
            'TESTEN':          None,
            'SWCLK':           None,
            'SWDIO':           None,
            'GND':             'GND',
            'QSPI_SCK':        'QSPI_SCK',
            'QSPI_CS':         'QSPI_CS',
            'QSPI_D0':         'QSPI_D0',
            'QSPI_D1':         'QSPI_D1',
            'QSPI_D2':         'QSPI_D2',
            'QSPI_D3':         'QSPI_D3',
            'RUN':             '3V3_RP',
            '3V3_OUT':         None,
        }),

        # ===== RP2350 decoupling caps — 100nF per IOVDD/DVDD, 1uF VREG_VIN, 100nF USB =====
        *wired_sym('C30', 'Device', 'C', 75, 85,
            '100nF', 'Capacitor_SMD:C_0402',
            {'1': '3V3_RP', '2': 'GND'}),  # IOVDD bypass
        *wired_sym('C31', 'Device', 'C', 85, 85,
            '100nF', 'Capacitor_SMD:C_0402',
            {'1': '3V3_RP', '2': 'GND'}),  # DVDD bypass
        *wired_sym('C32', 'Device', 'C', 95, 85,
            '1uF', 'Capacitor_SMD:C_0402',
            {'1': '3V3_RP', '2': 'GND'}),  # VREG bypass
        *wired_sym('C33', 'Device', 'C', 105, 85,
            '100nF', 'Capacitor_SMD:C_0402',
            {'1': '3V3_RP', '2': 'GND'}),  # USB bypass

        # ===== 12MHz Crystal — Y1 at (70, 115) =====
        # Crystal pin 1 = XIN side, pin 2 = XOUT side
        *wired_sym('Y1', 'Device', 'Crystal', 70, 115,
            '12MHz', 'Crystal:Crystal_SMD_3225-4Pin',
            {'1': 'RP_XIN', '2': 'RP_XOUT'}),
        # Crystal load caps: C34 on XIN, C35 on XOUT
        *wired_sym('C34', 'Device', 'C', 60, 120,
            '15pF', 'Capacitor_SMD:C_0402',
            {'1': 'RP_XIN', '2': 'GND'}),
        *wired_sym('C35', 'Device', 'C', 80, 120,
            '15pF', 'Capacitor_SMD:C_0402',
            {'1': 'RP_XOUT', '2': 'GND'}),

        # ===== W25Q16 QSPI Flash — U21 at (230, 70) =====
        {'type': 'text', 'x': 200, 'y': 45, 'text': 'QSPI Flash — W25Q16 2MB', 'size': 1.5},
        *wired_sym('U21', 'solarpunk-pi-v3', 'W25Q16', 230, 70,
            'W25Q16JVSSIQ', 'Package_SO:SOP-8', {
            'CS':   'QSPI_CS',
            'DO':   'QSPI_D1',
            'WP':   '3V3_RP',
            'GND':  'GND',
            'DI':   'QSPI_D0',
            'CLK':  'QSPI_SCK',
            'HOLD': '3V3_RP',
            'VCC':  '3V3_RP',
        }),
        # Flash bypass cap + CS pull-up resistor
        *wired_sym('C36', 'Device', 'C', 250, 80,
            '100nF', 'Capacitor_SMD:C_0402',
            {'1': '3V3_RP', '2': 'GND'}),  # VCC bypass
        *wired_sym('R2', 'Device', 'R', 215, 60,
            '10k', 'Resistor_SMD:R_0402',
            {'1': '3V3_RP', '2': 'QSPI_CS'}),  # CS pull-up

        # ===== CYW43439 WiFi/BT — U22 at (100, 190) =====
        {'type': 'text', 'x': 30, 'y': 150, 'text': 'WiFi 4 + BT 5.2 — CYW43439 (SPI0: GP2-5)', 'size': 2},
        *wired_sym('U22', 'solarpunk-pi-v3', 'CYW43439', 100, 190,
            'CYW43439', '', {
            'VDD':          '3V3_RP',
            'GND':          'GND',
            'SPI_CLK':      'CYW_SPI_CLK',
            'SPI_MOSI':     'CYW_SPI_MOSI',
            'SPI_MISO':     'CYW_SPI_MISO',
            'SPI_CS':       'CYW_SPI_CS',
            'IRQ':          'CYW_IRQ',
            'WL_REG_ON':    '3V3_RP',
            'BT_REG_ON':    None,
            'BT_HOST_WAKE': None,
            'BT_DEV_WAKE':  None,
            'RF_OUT':       'CYW_RF',
            'XTAL_IN':      None,
            'XTAL_OUT':     None,
            'ANT':          None,
            'GND2':         'GND',
        }),
        # CYW43439 decoupling: 100nF + 10uF
        *wired_sym('C37', 'Device', 'C', 80, 175,
            '100nF', 'Capacitor_SMD:C_0402',
            {'1': '3V3_RP', '2': 'GND'}),
        *wired_sym('C38', 'Device', 'C', 90, 175,
            '10uF', 'Capacitor_SMD:C_0805',
            {'1': '3V3_RP', '2': 'GND'}),

        # ===== SX1262 LoRa — U23 at (300, 190) =====
        {'type': 'text', 'x': 250, 'y': 150, 'text': 'LoRa 868/915MHz — SX1262 (SPI1 shared, CS=GP25)', 'size': 2},
        *wired_sym('U23', 'solarpunk-pi-v3', 'SX1262', 300, 190,
            'SX1262IMLTRT', 'Package_QFN:QFN-24-1EP_4x4mm_P0.5mm', {
            'VDD':     '3V3_RP',
            'GND':     'GND',
            'SCK':     'LORA_SPI_CLK',
            'MOSI':    'LORA_SPI_MOSI',
            'MISO':    'LORA_SPI_MISO',
            'NSS':     'LORA_CS',
            'BUSY':    'LORA_BUSY',
            'DIO1':    'LORA_DIO1',
            'DIO2':    None,
            'DIO3':    None,
            'NRESET':  'LORA_NRST',
            'RFI':     'LORA_RF',
            'RFO':     'LORA_RF',
            'XTA':     None,
            'XTB':     None,
            'VBAT_IO': '3V3_RP',
        }),
        # SX1262 decoupling: 100nF + 10uF
        *wired_sym('C39', 'Device', 'C', 280, 175,
            '100nF', 'Capacitor_SMD:C_0402',
            {'1': '3V3_RP', '2': 'GND'}),
        *wired_sym('C40', 'Device', 'C', 290, 175,
            '10uF', 'Capacitor_SMD:C_0805',
            {'1': '3V3_RP', '2': 'GND'}),
        # LoRa RF matching network (pi-network placeholder)
        {'type': 'text', 'x': 340, 'y': 195, 'text': 'RF Match: C-L-C pi (calc for 50Ω)', 'size': 1},
        *wired_sym('C41', 'Device', 'C', 345, 200,
            '1.5pF', 'Capacitor_SMD:C_0402',
            {'1': 'LORA_RF', '2': 'GND'}),
        *wired_sym('L3', 'Device', 'L', 355, 200,
            '3.9nH', 'Inductor_SMD:L_0402',
            {'1': 'LORA_RF', '2': 'LORA_ANT'}),
        *wired_sym('C42', 'Device', 'C', 365, 200,
            '1.0pF', 'Capacitor_SMD:C_0402',
            {'1': 'LORA_ANT', '2': 'GND'}),
        # U.FL antenna connector
        {'type': 'component', 'ref': 'J20', 'lib': 'Connector', 'symbol': 'U.FL',
         'x': 380, 'y': 200, 'value': 'LoRa Ant', 'fp': 'Connector_Coaxial:U.FL'},

        # ===== Power Control — Si2301 PMOS Gates =====
        {'type': 'text', 'x': 30, 'y': 240, 'text': 'Power Control — Si2301 PMOS Gates', 'size': 2},
        # R58: 3V3_RP pull-up on Q1 gate; R59: 5V_SYS pull-up on Q2 gate
        *wired_sym('R58', 'Device', 'R', 85, 290,
            '100k', 'Resistor_SMD:R_0402',
            {'1': '3V3_RP', '2': 'PWR_EN_GATE'}),
        *wired_sym('R59', 'Device', 'R', 185, 290,
            '100k', 'Resistor_SMD:R_0402',
            {'1': '5V_SYS', '2': 'CELL_EN_GATE'}),
        # Q1: WiFi/LoRa power switch (3V3_RP → RADIO_3V3)
        *wired_sym('Q1', 'Device', 'Q_PMOS_GSD', 100, 270,
            'Si2301 (WiFi/LoRa)', 'Package_TO_SOT_SMD:SOT-23', {
            'G': 'PWR_EN_GATE',
            'S': '3V3_RP',
            'D': 'RADIO_3V3',
        }),
        # Q2: Cellular power switch (5V_SYS → CELL_5V)
        *wired_sym('Q2', 'Device', 'Q_PMOS_GSD', 200, 270,
            'Si2301 (cellular)', 'Package_TO_SOT_SMD:SOT-23', {
            'G': 'CELL_EN_GATE',
            'S': '5V_SYS',
            'D': 'CELL_5V',
        }),

        # 10-pin expansion header
        {'type': 'text', 'x': 250, 'y': 240, 'text': '10-Pin RP2350 Expansion Header', 'size': 2},
        {'type': 'component', 'ref': 'J21', 'lib': 'Connector_Generic', 'symbol': 'Conn_01x10',
         'x': 300, 'y': 270, 'value': '1x10 Expansion', 'fp': 'Connector_PinHeader_2.54mm:PinHeader_1x10_P2.54mm_Vertical'},

        # Notes
        {'type': 'text', 'x': 30, 'y': 310, 'text': 'NOTE: 3mm antenna keepout on ALL 6 layers around CYW43439 and SX1262', 'size': 1.2},
        {'type': 'text', 'x': 30, 'y': 316, 'text': 'NOTE: LoRa RF match values depend on antenna — tune with VNA', 'size': 1.2},
        {'type': 'text', 'x': 30, 'y': 322, 'text': 'GPIO MAP: GP0/1=UART, GP2-5=CYW SPI0, GP8-11=LoRa SPI1, GP25=LoRa CS', 'size': 1.2},
        {'type': 'text', 'x': 30, 'y': 328, 'text': 'GP12=PWR_GOOD, GP13=WAKE, GP14=RK3506_RST, GP15=PWR_EN, GP26=ADC_VBAT, GP27=ADC_SOLAR, GP28=SHUTDOWN', 'size': 1.2},
    ]
    generate_subsheet("03-rp2350-radio.kicad_sch", "RP2350 Power & Radio Domain", items)

    # ============ Sheet 4: RK3506J Industrial ============
    items = [
        {'type': 'text', 'x': 50, 'y': 15, 'text': 'RK3506J INDUSTRIAL DOMAIN', 'size': 3},
        {'type': 'text', 'x': 50, 'y': 22, 'text': 'Always-on: 3xA7@1.5G + M0@200M, ~0.7W — CAN FD, RS485, PWM, ADC', 'size': 1.5},

        # ===== RK3506J SoC =====
        {'type': 'component', 'ref': 'U30', 'lib': 'solarpunk-pi-v3', 'symbol': 'RK3506J',
         'x': 100, 'y': 100, 'value': 'RK3506J', 'fp': 'Package_QFN:QFN-88'},
        # RK3506J decoupling: 100nF x8 + 10uF x2
        {'type': 'component', 'ref': 'C50', 'lib': 'Device', 'symbol': 'C',
         'x': 70, 'y': 80, 'value': '100nF x4 VDD', 'fp': 'Capacitor_SMD:C_0402'},
        {'type': 'component', 'ref': 'C51', 'lib': 'Device', 'symbol': 'C',
         'x': 85, 'y': 80, 'value': '100nF x4 VDDIO', 'fp': 'Capacitor_SMD:C_0402'},
        {'type': 'component', 'ref': 'C52', 'lib': 'Device', 'symbol': 'C',
         'x': 100, 'y': 80, 'value': '10uF bulk', 'fp': 'Capacitor_SMD:C_0805'},
        {'type': 'component', 'ref': 'C53', 'lib': 'Device', 'symbol': 'C',
         'x': 115, 'y': 80, 'value': '10uF bulk', 'fp': 'Capacitor_SMD:C_0805'},
        {'type': 'local_label', 'x': 90, 'y': 75, 'name': '3V3_RK3506'},
        {'type': 'power', 'name': 'GND', 'x': 90, 'y': 85},
        # 24MHz crystal + load caps
        {'type': 'component', 'ref': 'Y2', 'lib': 'Device', 'symbol': 'Crystal',
         'x': 70, 'y': 115, 'value': '24MHz', 'fp': 'Crystal:Crystal_SMD_3225-4Pin'},
        {'type': 'component', 'ref': 'C54', 'lib': 'Device', 'symbol': 'C',
         'x': 60, 'y': 120, 'value': '20pF', 'fp': 'Capacitor_SMD:C_0402'},
        {'type': 'component', 'ref': 'C55', 'lib': 'Device', 'symbol': 'C',
         'x': 80, 'y': 120, 'value': '20pF', 'fp': 'Capacitor_SMD:C_0402'},
        {'type': 'power', 'name': 'GND', 'x': 70, 'y': 125},

        # ===== LPDDR3L 512MB =====
        {'type': 'text', 'x': 30, 'y': 170, 'text': 'LPDDR3L — 512MB (embedded in PoP or discrete)', 'size': 2},
        {'type': 'component', 'ref': 'U31', 'lib': 'Device', 'symbol': 'IC_Generic',
         'x': 100, 'y': 200, 'value': '512MB LPDDR3L', 'fp': 'Package_BGA:BGA'},
        {'type': 'local_label', 'x': 80, 'y': 190, 'name': 'DDR3_DQ'},
        {'type': 'local_label', 'x': 80, 'y': 195, 'name': 'DDR3_DQS'},
        {'type': 'local_label', 'x': 80, 'y': 200, 'name': 'DDR3_A'},
        {'type': 'local_label', 'x': 80, 'y': 205, 'name': 'DDR3_CK'},
        {'type': 'component', 'ref': 'C56', 'lib': 'Device', 'symbol': 'C',
         'x': 100, 'y': 215, 'value': '100nF x4', 'fp': 'Capacitor_SMD:C_0402'},
        {'type': 'power', 'name': 'GND', 'x': 100, 'y': 220},

        # ===== NAND 256MB =====
        {'type': 'text', 'x': 150, 'y': 170, 'text': 'NAND Flash — 256MB (SLC)', 'size': 2},
        {'type': 'component', 'ref': 'U32', 'lib': 'Device', 'symbol': 'IC_Generic',
         'x': 200, 'y': 200, 'value': '256MB NAND', 'fp': 'Package_BGA:BGA'},
        {'type': 'local_label', 'x': 180, 'y': 195, 'name': 'NAND_D0_7'},
        {'type': 'local_label', 'x': 180, 'y': 200, 'name': 'NAND_CLE_ALE'},
        {'type': 'local_label', 'x': 180, 'y': 205, 'name': 'NAND_CE_RE_WE'},
        {'type': 'component', 'ref': 'C57', 'lib': 'Device', 'symbol': 'C',
         'x': 200, 'y': 215, 'value': '100nF', 'fp': 'Capacitor_SMD:C_0402'},
        {'type': 'power', 'name': 'GND', 'x': 200, 'y': 220},

        # ===== CAN FD x2 =====
        {'type': 'text', 'x': 250, 'y': 35, 'text': 'CAN FD x2 — MCP2562FD + ADUM1401 Isolation', 'size': 2},
        {'type': 'component', 'ref': 'U33', 'lib': 'solarpunk-pi-v3', 'symbol': 'MCP2562FD',
         'x': 300, 'y': 70, 'value': 'MCP2562FD #1', 'fp': 'Package_TO_SOT_SMD:SOT-23-8'},
        {'type': 'component', 'ref': 'U34', 'lib': 'solarpunk-pi-v3', 'symbol': 'MCP2562FD',
         'x': 300, 'y': 120, 'value': 'MCP2562FD #2', 'fp': 'Package_TO_SOT_SMD:SOT-23-8'},
        # CAN bus labels
        {'type': 'local_label', 'x': 275, 'y': 65, 'name': 'CAN0_TX'},
        {'type': 'local_label', 'x': 275, 'y': 70, 'name': 'CAN0_RX'},
        {'type': 'local_label', 'x': 325, 'y': 65, 'name': 'CAN0H'},
        {'type': 'local_label', 'x': 325, 'y': 70, 'name': 'CAN0L'},
        {'type': 'local_label', 'x': 275, 'y': 115, 'name': 'CAN1_TX'},
        {'type': 'local_label', 'x': 275, 'y': 120, 'name': 'CAN1_RX'},
        {'type': 'local_label', 'x': 325, 'y': 115, 'name': 'CAN1H'},
        {'type': 'local_label', 'x': 325, 'y': 120, 'name': 'CAN1L'},
        # CAN termination resistors
        {'type': 'component', 'ref': 'R62', 'lib': 'Device', 'symbol': 'R',
         'x': 340, 'y': 68, 'value': '120R', 'fp': 'Resistor_SMD:R_0402'},
        {'type': 'component', 'ref': 'R63', 'lib': 'Device', 'symbol': 'R',
         'x': 340, 'y': 118, 'value': '120R', 'fp': 'Resistor_SMD:R_0402'},
        {'type': 'text', 'x': 345, 'y': 68, 'text': 'CAN0 term', 'size': 0.8},
        {'type': 'text', 'x': 345, 'y': 118, 'text': 'CAN1 term', 'size': 0.8},
        # CAN transceiver bypass
        {'type': 'component', 'ref': 'C58', 'lib': 'Device', 'symbol': 'C',
         'x': 320, 'y': 60, 'value': '100nF', 'fp': 'Capacitor_SMD:C_0402'},
        {'type': 'component', 'ref': 'C59', 'lib': 'Device', 'symbol': 'C',
         'x': 320, 'y': 110, 'value': '100nF', 'fp': 'Capacitor_SMD:C_0402'},

        # ===== Isolation =====
        {'type': 'component', 'ref': 'U35', 'lib': 'solarpunk-pi-v3', 'symbol': 'ADUM1401',
         'x': 300, 'y': 160, 'value': 'ADUM1401', 'fp': 'Package_SO:SOIC-16W_7.5x10.3mm_P1.27mm'},
        {'type': 'component', 'ref': 'C60', 'lib': 'Device', 'symbol': 'C',
         'x': 280, 'y': 155, 'value': '100nF VDD1', 'fp': 'Capacitor_SMD:C_0402'},
        {'type': 'component', 'ref': 'C61', 'lib': 'Device', 'symbol': 'C',
         'x': 320, 'y': 155, 'value': '100nF VDD2', 'fp': 'Capacitor_SMD:C_0402'},

        # ===== RS485 =====
        {'type': 'text', 'x': 250, 'y': 200, 'text': 'RS485 — SP3485 through ADUM1401', 'size': 2},
        {'type': 'component', 'ref': 'U36', 'lib': 'solarpunk-pi-v3', 'symbol': 'SP3485',
         'x': 300, 'y': 230, 'value': 'SP3485', 'fp': 'Package_SO:SOP-8'},
        {'type': 'local_label', 'x': 275, 'y': 225, 'name': 'RS485_DI'},
        {'type': 'local_label', 'x': 275, 'y': 230, 'name': 'RS485_RO'},
        {'type': 'local_label', 'x': 275, 'y': 235, 'name': 'RS485_DE'},
        {'type': 'local_label', 'x': 275, 'y': 240, 'name': 'RS485_RE'},
        {'type': 'local_label', 'x': 325, 'y': 228, 'name': 'RS485_A'},
        {'type': 'local_label', 'x': 325, 'y': 233, 'name': 'RS485_B'},
        # RS485 termination
        {'type': 'component', 'ref': 'R64', 'lib': 'Device', 'symbol': 'R',
         'x': 340, 'y': 230, 'value': '120R', 'fp': 'Resistor_SMD:R_0402'},
        {'type': 'text', 'x': 345, 'y': 230, 'text': 'RS485 term', 'size': 0.8},
        {'type': 'component', 'ref': 'C62', 'lib': 'Device', 'symbol': 'C',
         'x': 320, 'y': 225, 'value': '100nF', 'fp': 'Capacitor_SMD:C_0402'},
        {'type': 'power', 'name': 'GND', 'x': 300, 'y': 245},

        # ===== Schmitt trigger =====
        {'type': 'text', 'x': 250, 'y': 260, 'text': 'Industrial Input Conditioning — SN74LVC14A', 'size': 2},
        {'type': 'component', 'ref': 'U37', 'lib': 'solarpunk-pi-v3', 'symbol': 'SN74LVC14A',
         'x': 300, 'y': 290, 'value': 'SN74LVC14A', 'fp': 'Package_SO:TSSOP-14_4.4x5mm_P0.65mm'},
        {'type': 'component', 'ref': 'C63', 'lib': 'Device', 'symbol': 'C',
         'x': 280, 'y': 285, 'value': '100nF', 'fp': 'Capacitor_SMD:C_0402'},
        {'type': 'local_label', 'x': 280, 'y': 280, 'name': '3V3_RK3506'},

        # ===== ESD protection =====
        {'type': 'component', 'ref': 'U38', 'lib': 'Device', 'symbol': 'IC_Generic',
         'x': 300, 'y': 330, 'value': 'PESD5V0S4UG', 'fp': 'Package_TO_SOT_SMD:SOT-553'},

        # ===== 30-pin Industrial Header =====
        {'type': 'text', 'x': 30, 'y': 250, 'text': '30-Pin Industrial Header', 'size': 2},
        {'type': 'text', 'x': 30, 'y': 258, 'text': 'CAN0H/L, CAN1H/L, RS485 A/B, GPIO×4, PWM×2, ADC×2, UART3/4, 5V, 3V3, GND×4', 'size': 1},
        {'type': 'component', 'ref': 'J30', 'lib': 'Connector_Generic', 'symbol': 'Conn_03x10',
         'x': 80, 'y': 290, 'value': '3x10 Industrial I/O', 'fp': 'Connector_PinHeader_2.54mm:PinHeader_3x10_P2.54mm_Vertical'},
        # 33R series on UART lines
        {'type': 'component', 'ref': 'R66', 'lib': 'Device', 'symbol': 'R',
         'x': 130, 'y': 130, 'value': '33R', 'fp': 'Resistor_SMD:R_0402'},
        {'type': 'component', 'ref': 'R67', 'lib': 'Device', 'symbol': 'R',
         'x': 130, 'y': 135, 'value': '33R', 'fp': 'Resistor_SMD:R_0402'},
        {'type': 'text', 'x': 135, 'y': 133, 'text': 'UART series', 'size': 0.8},

        # Hierarchical labels
        {'type': 'hier_label', 'x': 20, 'y': 40, 'name': '3V3_RK3506', 'shape': 'input'},
        {'type': 'hier_label', 'x': 20, 'y': 48, 'name': '5V_SYS', 'shape': 'input'},
        {'type': 'hier_label', 'x': 20, 'y': 56, 'name': 'GND', 'shape': 'input'},
        {'type': 'hier_label', 'x': 380, 'y': 40, 'name': 'UART5_RX_BUF', 'shape': 'input'},
        {'type': 'hier_label', 'x': 380, 'y': 48, 'name': 'UART5_TX_BUF', 'shape': 'output'},
        {'type': 'hier_label', 'x': 380, 'y': 56, 'name': 'SPI0_CLK', 'shape': 'input'},
        {'type': 'hier_label', 'x': 380, 'y': 64, 'name': 'SPI0_MOSI', 'shape': 'input'},
        {'type': 'hier_label', 'x': 380, 'y': 72, 'name': 'SPI0_MISO', 'shape': 'output'},
        {'type': 'hier_label', 'x': 380, 'y': 80, 'name': 'SPI0_CS', 'shape': 'input'},
        {'type': 'hier_label', 'x': 380, 'y': 88, 'name': 'GPIO_WAKE', 'shape': 'output'},
        {'type': 'hier_label', 'x': 380, 'y': 96, 'name': 'GPIO_ALARM', 'shape': 'output'},
        {'type': 'hier_label', 'x': 380, 'y': 104, 'name': 'RESET_N', 'shape': 'input'},

        # Notes
        {'type': 'text', 'x': 30, 'y': 350, 'text': 'NOTE: CAN/RS485 isolation barrier — no copper crossing between isolated and non-isolated sides', 'size': 1.2},
        {'type': 'text', 'x': 30, 'y': 356, 'text': 'NOTE: 120R termination resistors with solder jumpers (populate if end-of-bus)', 'size': 1.2},
        {'type': 'text', 'x': 30, 'y': 362, 'text': 'NOTE: ADUM1401 channels: A1=CAN0_TX, B1=CAN0_RX, A2=RS485_DI/DE, B2=RS485_RO', 'size': 1.2},
    ]
    generate_subsheet("04-rk3506j-industrial.kicad_sch", "RK3506J Industrial Domain", items)

    # ============ Sheet 5: Power System ============
    items = [
        {'type': 'text', 'x': 50, 'y': 15, 'text': 'POWER SYSTEM', 'size': 3},
        {'type': 'text', 'x': 50, 'y': 22, 'text': 'Solar MPPT + PoE 802.3at + USB-C PD — Auto-OR Switching', 'size': 1.5},

        # ========== SECTION A: Solar MPPT — CN3722 ==========
        {'type': 'text', 'x': 30, 'y': 35, 'text': 'A. Solar MPPT — CN3722 → 2S LiFePO4 (7.2V nom)', 'size': 2},
        # ========== CN3722 Solar MPPT — fully wired ==========
        *wired_sym('U40', 'solarpunk-pi-v3', 'CN3722', 80, 80, 'CN3722', 'Package_SO:SOP-16',
            {'VIN': 'SOLAR_IN', 'EN': 'SOLAR_IN', 'SS': 'CN_SS', 'FB': 'CN_FB',
             'COMP': 'CN_COMP', 'RT': 'CN_RT', 'GND': 'GND', 'PGND': 'GND',
             'SW': 'CN_SW', 'BST': 'CN_BST', 'VBAT': 'VBAT', 'CHRG': None, 'DONE': None,
             'CS': 'CN_CS', 'TS': 'CN_TS', 'MPPT': 'CN_MPPT'}),
        # C90: SS soft-start cap
        {'type': 'component', 'ref': 'C90', 'lib': 'Device', 'symbol': 'C',
         'x': 65, 'y': 68, 'value': '100nF', 'fp': 'Capacitor_SMD:C_0402'},
        {'type': 'local_label', 'x': 65, 'y': 64.19, 'name': 'CN_SS'},
        {'type': 'power', 'name': 'GND', 'x': 65, 'y': 71.81},
        # C91: COMP compensation cap
        {'type': 'component', 'ref': 'C91', 'lib': 'Device', 'symbol': 'C',
         'x': 65, 'y': 78, 'value': '470pF', 'fp': 'Capacitor_SMD:C_0402'},
        {'type': 'local_label', 'x': 65, 'y': 74.19, 'name': 'CN_COMP'},
        {'type': 'power', 'name': 'GND', 'x': 65, 'y': 81.81},
        # C92: BST bootstrap cap
        {'type': 'component', 'ref': 'C92', 'lib': 'Device', 'symbol': 'C',
         'x': 95, 'y': 65, 'value': '100nF', 'fp': 'Capacitor_SMD:C_0402'},
        {'type': 'local_label', 'x': 95, 'y': 61.19, 'name': 'CN_BST'},
        {'type': 'local_label', 'x': 95, 'y': 68.81, 'name': 'CN_SW'},
        # R44: RT timing (25k → 300kHz)
        {'type': 'component', 'ref': 'R44', 'lib': 'Device', 'symbol': 'R',
         'x': 55, 'y': 80, 'value': '25k', 'fp': 'Resistor_SMD:R_0402'},
        {'type': 'local_label', 'x': 55, 'y': 76.19, 'name': 'CN_RT'},
        {'type': 'power', 'name': 'GND', 'x': 55, 'y': 83.81},
        # R47: CS current sense (100mR → 2A)
        {'type': 'component', 'ref': 'R47', 'lib': 'Device', 'symbol': 'R',
         'x': 105, 'y': 80, 'value': '100mR', 'fp': 'Resistor_SMD:R_1206'},
        {'type': 'local_label', 'x': 105, 'y': 76.19, 'name': 'CN_CS'},
        {'type': 'power', 'name': 'GND', 'x': 105, 'y': 83.81},
        # R42/R43: FB divider (49.9k/10k → 7.21V)
        {'type': 'component', 'ref': 'R42', 'lib': 'Device', 'symbol': 'R',
         'x': 100, 'y': 95, 'value': '49.9k', 'fp': 'Resistor_SMD:R_0402'},
        {'type': 'local_label', 'x': 100, 'y': 91.19, 'name': 'VBAT'},
        {'type': 'local_label', 'x': 100, 'y': 98.81, 'name': 'CN_FB'},
        {'type': 'component', 'ref': 'R43', 'lib': 'Device', 'symbol': 'R',
         'x': 100, 'y': 105, 'value': '10k', 'fp': 'Resistor_SMD:R_0402'},
        {'type': 'wire', 'x1': 100, 'y1': 98.81, 'x2': 100, 'y2': 101.19},
        {'type': 'power', 'name': 'GND', 'x': 100, 'y': 108.81},
        # R49/R50: TS thermistor (10k NTC / 10k bias)
        {'type': 'component', 'ref': 'R49', 'lib': 'Device', 'symbol': 'R',
         'x': 120, 'y': 73, 'value': '10k NTC', 'fp': 'Resistor_SMD:R_0402'},
        {'type': 'local_label', 'x': 120, 'y': 69.19, 'name': 'VBAT'},
        {'type': 'local_label', 'x': 120, 'y': 76.81, 'name': 'CN_TS'},
        {'type': 'component', 'ref': 'R50', 'lib': 'Device', 'symbol': 'R',
         'x': 120, 'y': 83, 'value': '10k', 'fp': 'Resistor_SMD:R_0402'},
        {'type': 'wire', 'x1': 120, 'y1': 76.81, 'x2': 120, 'y2': 79.19},
        {'type': 'power', 'name': 'GND', 'x': 120, 'y': 86.81},
        # R45/R46: MPPT divider (140k/10k)
        {'type': 'component', 'ref': 'R45', 'lib': 'Device', 'symbol': 'R',
         'x': 55, 'y': 58, 'value': '140k', 'fp': 'Resistor_SMD:R_0402'},
        {'type': 'local_label', 'x': 55, 'y': 54.19, 'name': 'SOLAR_IN'},
        {'type': 'local_label', 'x': 55, 'y': 61.81, 'name': 'CN_MPPT'},
        {'type': 'component', 'ref': 'R46', 'lib': 'Device', 'symbol': 'R',
         'x': 55, 'y': 68, 'value': '10k', 'fp': 'Resistor_SMD:R_0402'},
        {'type': 'wire', 'x1': 55, 'y1': 61.81, 'x2': 55, 'y2': 64.19},
        {'type': 'power', 'name': 'GND', 'x': 55, 'y': 71.81},
        # L2: SW inductor (10uH)
        {'type': 'component', 'ref': 'L2', 'lib': 'Device', 'symbol': 'L',
         'x': 95, 'y': 55, 'value': '10uH', 'fp': 'Inductor_SMD:L_6030'},
        {'type': 'local_label', 'x': 95, 'y': 51.19, 'name': 'CN_SW'},
        {'type': 'local_label', 'x': 95, 'y': 58.81, 'name': 'VBAT'},
        # Input/output bulk caps
        {'type': 'component', 'ref': 'C93', 'lib': 'Device', 'symbol': 'C',
         'x': 35, 'y': 55, 'value': '22uF/25V', 'fp': 'Capacitor_SMD:C_1206'},
        {'type': 'local_label', 'x': 35, 'y': 51.19, 'name': 'SOLAR_IN'},
        {'type': 'power', 'name': 'GND', 'x': 35, 'y': 58.81},
        {'type': 'component', 'ref': 'C94', 'lib': 'Device', 'symbol': 'C',
         'x': 120, 'y': 55, 'value': '22uF/16V', 'fp': 'Capacitor_SMD:C_1206'},
        {'type': 'local_label', 'x': 120, 'y': 51.19, 'name': 'VBAT'},
        {'type': 'power', 'name': 'GND', 'x': 120, 'y': 58.81},
        # Connectors
        {'type': 'component', 'ref': 'J40', 'lib': 'Connector', 'symbol': 'Conn_01x02',
         'x': 20, 'y': 55, 'value': 'JST VH Solar', 'fp': 'Connector_JST:JST_VH_B2P'},
        {'type': 'component', 'ref': 'J41', 'lib': 'Connector', 'symbol': 'Conn_01x02',
         'x': 20, 'y': 100, 'value': 'JST PH Battery', 'fp': 'Connector_JST:JST_PH_B2B'},

        # ========== TPS61022 Boost — fully wired ==========
        {'type': 'text', 'x': 30, 'y': 140, 'text': 'B. Boost — TPS61022 VBAT→5V@4A', 'size': 2},
        {'type': 'text', 'x': 30, 'y': 146, 'text': 'VREF=0.5V, R40=900k R41=100k → 5.0V (FIXED)', 'size': 1},
        *wired_sym('U41', 'solarpunk-pi-v3', 'TPS61022', 80, 170, 'TPS61022DRLR', 'Package_TO_SOT_SMD:SOT-23-6',
            {'VIN': 'VBAT', 'EN': 'VBAT', 'GND': 'GND', 'SW': 'BOOST_SW', 'VOUT': '5V_BOOST', 'FB': 'BOOST_FB'}),
        # L1: boost inductor
        {'type': 'component', 'ref': 'L1', 'lib': 'Device', 'symbol': 'L',
         'x': 92, 'y': 155, 'value': '1uH', 'fp': 'Inductor_SMD:L_4012'},
        {'type': 'local_label', 'x': 92, 'y': 151.19, 'name': 'BOOST_SW'},
        {'type': 'local_label', 'x': 92, 'y': 158.81, 'name': '5V_BOOST'},
        # R40/R41: FB divider (900k/100k → 5.0V)
        {'type': 'component', 'ref': 'R40', 'lib': 'Device', 'symbol': 'R',
         'x': 100, 'y': 180, 'value': '900k', 'fp': 'Resistor_SMD:R_0402'},
        {'type': 'local_label', 'x': 100, 'y': 176.19, 'name': '5V_BOOST'},
        {'type': 'local_label', 'x': 100, 'y': 183.81, 'name': 'BOOST_FB'},
        {'type': 'component', 'ref': 'R41', 'lib': 'Device', 'symbol': 'R',
         'x': 100, 'y': 190, 'value': '100k', 'fp': 'Resistor_SMD:R_0402'},
        {'type': 'wire', 'x1': 100, 'y1': 183.81, 'x2': 100, 'y2': 186.19},
        {'type': 'power', 'name': 'GND', 'x': 100, 'y': 193.81},
        # Input/output caps
        {'type': 'component', 'ref': 'C95', 'lib': 'Device', 'symbol': 'C',
         'x': 60, 'y': 170, 'value': '10uF', 'fp': 'Capacitor_SMD:C_0805'},
        {'type': 'local_label', 'x': 60, 'y': 166.19, 'name': 'VBAT'},
        {'type': 'power', 'name': 'GND', 'x': 60, 'y': 173.81},
        {'type': 'component', 'ref': 'C96', 'lib': 'Device', 'symbol': 'C',
         'x': 110, 'y': 155, 'value': '22uF x3', 'fp': 'Capacitor_SMD:C_1206'},
        {'type': 'local_label', 'x': 110, 'y': 151.19, 'name': '5V_BOOST'},
        {'type': 'power', 'name': 'GND', 'x': 110, 'y': 158.81},

        # ========== SI3402-B PoE — fully wired ==========
        {'type': 'text', 'x': 200, 'y': 35, 'text': 'C. PoE 802.3at — SI3402-B PD', 'size': 2},
        *wired_sym('U42', 'solarpunk-pi-v3', 'SI3402-B', 260, 70, 'SI3402-B', 'Package_QFN:QFN-16',
            {'VDD': '48V_POE', 'RCLASS': 'POE_RCLASS', 'DET': 'POE_DET', 'VSS': 'GND',
             'AGND': 'GND', 'GND': 'GND', 'VOUT': '5V_POE', 'VEE': 'GND',
             'GATE': None, 'BG': None, 'FB': 'POE_FB', 'COMP': 'POE_COMP'}),
        # R65: classification (243R)
        {'type': 'component', 'ref': 'R65', 'lib': 'Device', 'symbol': 'R',
         'x': 240, 'y': 60, 'value': '243R', 'fp': 'Resistor_SMD:R_0402'},
        {'type': 'local_label', 'x': 240, 'y': 56.19, 'name': 'POE_RCLASS'},
        {'type': 'power', 'name': 'GND', 'x': 240, 'y': 63.81},
        # C99: detection cap
        {'type': 'component', 'ref': 'C99', 'lib': 'Device', 'symbol': 'C',
         'x': 240, 'y': 73, 'value': '100nF', 'fp': 'Capacitor_SMD:C_0402'},
        {'type': 'local_label', 'x': 240, 'y': 69.19, 'name': 'POE_DET'},
        {'type': 'power', 'name': 'GND', 'x': 240, 'y': 76.81},
        # C100: output bulk
        {'type': 'component', 'ref': 'C100', 'lib': 'Device', 'symbol': 'C_Polarized',
         'x': 285, 'y': 65, 'value': '100uF/63V', 'fp': 'Capacitor_SMD:CP_Elec_8x10.5'},
        {'type': 'local_label', 'x': 285, 'y': 61.19, 'name': '5V_POE'},
        {'type': 'power', 'name': 'GND', 'x': 285, 'y': 68.81},

        # ========== HUSB238 USB-C PD — fully wired ==========
        {'type': 'text', 'x': 200, 'y': 110, 'text': 'D. USB-C PD Sink — HUSB238', 'size': 2},
        *wired_sym('U43', 'solarpunk-pi-v3', 'HUSB238', 260, 140, 'HUSB238', 'Package_SO:SOP-10',
            {'VDD': 'USB_PD_VBUS', 'CC1': 'USB_CC1', 'CC2': 'USB_CC2', 'GND': 'GND',
             'SCL': 'SCL_PD', 'SDA': 'SDA_PD',
             'VBUS_DET': 'USB_PD_VBUS', 'OUT_EN': '5V_USB_PD', 'GO': None,
             'VSET': 'HUSB_VSET', 'INT_N': None, 'ATTACH': None}),
        # R48: VSET (10k → 12V)
        {'type': 'component', 'ref': 'R48', 'lib': 'Device', 'symbol': 'R',
         'x': 278, 'y': 150, 'value': '10k', 'fp': 'Resistor_SMD:R_0402'},
        {'type': 'local_label', 'x': 278, 'y': 146.19, 'name': 'HUSB_VSET'},
        {'type': 'power', 'name': 'GND', 'x': 278, 'y': 153.81},
        # I2C pull-ups
        {'type': 'component', 'ref': 'R60', 'lib': 'Device', 'symbol': 'R',
         'x': 240, 'y': 128, 'value': '4.7k', 'fp': 'Resistor_SMD:R_0402'},
        {'type': 'local_label', 'x': 240, 'y': 124.19, 'name': '3V3_RP'},
        {'type': 'local_label', 'x': 240, 'y': 131.81, 'name': 'SCL_PD'},
        {'type': 'component', 'ref': 'R61', 'lib': 'Device', 'symbol': 'R',
         'x': 248, 'y': 128, 'value': '4.7k', 'fp': 'Resistor_SMD:R_0402'},
        {'type': 'local_label', 'x': 248, 'y': 124.19, 'name': '3V3_RP'},
        {'type': 'local_label', 'x': 248, 'y': 131.81, 'name': 'SDA_PD'},
        # Bypass cap
        {'type': 'component', 'ref': 'C101', 'lib': 'Device', 'symbol': 'C',
         'x': 240, 'y': 138, 'value': '100nF', 'fp': 'Capacitor_SMD:C_0402'},
        {'type': 'local_label', 'x': 240, 'y': 134.19, 'name': 'USB_PD_VBUS'},
        {'type': 'power', 'name': 'GND', 'x': 240, 'y': 141.81},

        # ========== LTC4357 OR-ing — fully wired ==========
        {'type': 'text', 'x': 130, 'y': 200, 'text': 'E. Auto-OR Switching — 3× LTC4357', 'size': 2},
        # Boost path
        *wired_sym('U44a', 'solarpunk-pi-v3', 'LTC4357', 160, 225, 'LTC4357', 'Package_TO_SOT_SMD:SOT-23-5',
            {'IN': '5V_BOOST', 'GATE': None, 'OUT': '5V_SYS', 'GND': 'GND'}),
        # PoE path
        *wired_sym('U44b', 'solarpunk-pi-v3', 'LTC4357', 220, 225, 'LTC4357', 'Package_TO_SOT_SMD:SOT-23-5',
            {'IN': '5V_POE', 'GATE': None, 'OUT': '5V_SYS', 'GND': 'GND'}),
        # USB-PD path
        *wired_sym('U44c', 'solarpunk-pi-v3', 'LTC4357', 280, 225, 'LTC4357', 'Package_TO_SOT_SMD:SOT-23-5',
            {'IN': '5V_USB_PD', 'GATE': None, 'OUT': '5V_SYS', 'GND': 'GND'}),
        # 5V_SYS output bulk caps
        {'type': 'component', 'ref': 'C102', 'lib': 'Device', 'symbol': 'C_Polarized',
         'x': 320, 'y': 228, 'value': '100uF/10V', 'fp': 'Capacitor_SMD:CP_Elec_6.3x5.8'},
        {'type': 'local_label', 'x': 320, 'y': 224.19, 'name': '5V_SYS'},
        {'type': 'power', 'name': 'GND', 'x': 320, 'y': 231.81},
        {'type': 'component', 'ref': 'C103', 'lib': 'Device', 'symbol': 'C',
         'x': 335, 'y': 228, 'value': '10uF', 'fp': 'Capacitor_SMD:C_0805'},
        {'type': 'local_label', 'x': 335, 'y': 224.19, 'name': '5V_SYS'},
        {'type': 'power', 'name': 'GND', 'x': 335, 'y': 231.81},

        # ========== LDOs — fully wired ==========
        {'type': 'text', 'x': 30, 'y': 245, 'text': 'F. Always-On LDOs', 'size': 2},
        *wired_sym('U45', 'solarpunk-pi-v3', 'MIC5219', 60, 265, 'MIC5219-3.3', 'Package_TO_SOT_SMD:SOT-23-5',
            {'IN': '5V_SYS', 'GND': 'GND', 'EN': '5V_SYS', 'OUT': '3V3_RP', 'BYP': 'MIC_BYP'}),
        {'type': 'component', 'ref': 'C104', 'lib': 'Device', 'symbol': 'C',
         'x': 45, 'y': 265, 'value': '1uF', 'fp': 'Capacitor_SMD:C_0402'},
        {'type': 'local_label', 'x': 45, 'y': 261.19, 'name': '5V_SYS'},
        {'type': 'power', 'name': 'GND', 'x': 45, 'y': 268.81},
        {'type': 'component', 'ref': 'C105', 'lib': 'Device', 'symbol': 'C',
         'x': 80, 'y': 265, 'value': '1uF', 'fp': 'Capacitor_SMD:C_0402'},
        {'type': 'local_label', 'x': 80, 'y': 261.19, 'name': '3V3_RP'},
        {'type': 'power', 'name': 'GND', 'x': 80, 'y': 268.81},
        {'type': 'component', 'ref': 'C106', 'lib': 'Device', 'symbol': 'C',
         'x': 75, 'y': 258, 'value': '470pF', 'fp': 'Capacitor_SMD:C_0402'},
        {'type': 'local_label', 'x': 75, 'y': 254.19, 'name': 'MIC_BYP'},
        {'type': 'power', 'name': 'GND', 'x': 75, 'y': 261.81},

        *wired_sym('U46', 'solarpunk-pi-v3', 'AP2112K', 60, 295, 'AP2112K-3.3', 'Package_TO_SOT_SMD:SOT-23-5',
            {'VIN': '5V_SYS', 'GND': 'GND', 'EN': '5V_SYS', 'VOUT': '3V3_RK3506', 'NC': None}),
        {'type': 'component', 'ref': 'C107', 'lib': 'Device', 'symbol': 'C',
         'x': 45, 'y': 295, 'value': '1uF', 'fp': 'Capacitor_SMD:C_0402'},
        {'type': 'local_label', 'x': 45, 'y': 291.19, 'name': '5V_SYS'},
        {'type': 'power', 'name': 'GND', 'x': 45, 'y': 298.81},
        {'type': 'component', 'ref': 'C108', 'lib': 'Device', 'symbol': 'C',
         'x': 80, 'y': 295, 'value': '1uF', 'fp': 'Capacitor_SMD:C_0402'},
        {'type': 'local_label', 'x': 80, 'y': 291.19, 'name': '3V3_RK3506'},
        {'type': 'power', 'name': 'GND', 'x': 80, 'y': 298.81},

        # ========== Ferrite beads + brain PMOS ==========
        {'type': 'text', 'x': 30, 'y': 315, 'text': 'G. Isolation + Brain Gate', 'size': 2},
        {'type': 'component', 'ref': 'FB1', 'lib': 'Device', 'symbol': 'FerriteBead',
         'x': 60, 'y': 330, 'value': 'BLM18AG102SN1D', 'fp': 'Resistor_SMD:R_0603'},
        {'type': 'local_label', 'x': 60, 'y': 326.19, 'name': '3V3_RP'},
        {'type': 'local_label', 'x': 60, 'y': 333.81, 'name': '3V3_RP_FILT'},
        {'type': 'component', 'ref': 'FB2', 'lib': 'Device', 'symbol': 'FerriteBead',
         'x': 120, 'y': 330, 'value': 'BLM18AG102SN1D', 'fp': 'Resistor_SMD:R_0603'},
        {'type': 'local_label', 'x': 120, 'y': 326.19, 'name': '3V3_RK3506'},
        {'type': 'local_label', 'x': 120, 'y': 333.81, 'name': '3V3_RK3506_FILT'},
        # Brain PMOS gate
        {'type': 'component', 'ref': 'Q3', 'lib': 'Device', 'symbol': 'Q_PMOS_GSD',
         'x': 200, 'y': 330, 'value': 'Si2301', 'fp': 'Package_TO_SOT_SMD:SOT-23'},
        {'type': 'local_label', 'x': 194.92, 'y': 330, 'name': 'PWR_EN_BUF'},
        {'type': 'local_label', 'x': 202.54, 'y': 324.92, 'name': '5V_SYS'},
        {'type': 'local_label', 'x': 202.54, 'y': 335.08, 'name': '5V_BRAIN'},
        {'type': 'component', 'ref': 'R57', 'lib': 'Device', 'symbol': 'R',
         'x': 190, 'y': 322, 'value': '100k', 'fp': 'Resistor_SMD:R_0402'},
        {'type': 'local_label', 'x': 190, 'y': 318.19, 'name': '5V_SYS'},
        {'type': 'local_label', 'x': 190, 'y': 325.81, 'name': 'PWR_EN_BUF'},

        # ========== ADC monitors ==========
        {'type': 'text', 'x': 200, 'y': 170, 'text': 'H. ADC Monitors', 'size': 2},
        # VBAT divider: R51(100k)/R52(100k) → ÷2
        {'type': 'component', 'ref': 'R51', 'lib': 'Device', 'symbol': 'R',
         'x': 220, 'y': 182, 'value': '100k', 'fp': 'Resistor_SMD:R_0402'},
        {'type': 'local_label', 'x': 220, 'y': 178.19, 'name': 'VBAT'},
        {'type': 'local_label', 'x': 220, 'y': 185.81, 'name': 'ADC_VBAT_DIV'},
        {'type': 'component', 'ref': 'R52', 'lib': 'Device', 'symbol': 'R',
         'x': 220, 'y': 192, 'value': '100k', 'fp': 'Resistor_SMD:R_0402'},
        {'type': 'wire', 'x1': 220, 'y1': 185.81, 'x2': 220, 'y2': 188.19},
        {'type': 'power', 'name': 'GND', 'x': 220, 'y': 195.81},
        # R55 + C109: RC filter
        {'type': 'component', 'ref': 'R55', 'lib': 'Device', 'symbol': 'R',
         'x': 235, 'y': 186, 'value': '100R', 'fp': 'Resistor_SMD:R_0402'},
        {'type': 'local_label', 'x': 235, 'y': 182.19, 'name': 'ADC_VBAT_DIV'},
        {'type': 'local_label', 'x': 235, 'y': 189.81, 'name': 'ADC_VBAT'},
        {'type': 'component', 'ref': 'C109', 'lib': 'Device', 'symbol': 'C',
         'x': 245, 'y': 192, 'value': '100nF', 'fp': 'Capacitor_SMD:C_0402'},
        {'type': 'local_label', 'x': 245, 'y': 188.19, 'name': 'ADC_VBAT'},
        {'type': 'power', 'name': 'GND', 'x': 245, 'y': 195.81},
        # SOLAR divider: R53(200k)/R54(100k) → ÷3
        {'type': 'component', 'ref': 'R53', 'lib': 'Device', 'symbol': 'R',
         'x': 280, 'y': 182, 'value': '200k', 'fp': 'Resistor_SMD:R_0402'},
        {'type': 'local_label', 'x': 280, 'y': 178.19, 'name': 'SOLAR_IN'},
        {'type': 'local_label', 'x': 280, 'y': 185.81, 'name': 'ADC_SOL_DIV'},
        {'type': 'component', 'ref': 'R54', 'lib': 'Device', 'symbol': 'R',
         'x': 280, 'y': 192, 'value': '100k', 'fp': 'Resistor_SMD:R_0402'},
        {'type': 'wire', 'x1': 280, 'y1': 185.81, 'x2': 280, 'y2': 188.19},
        {'type': 'power', 'name': 'GND', 'x': 280, 'y': 195.81},
        {'type': 'component', 'ref': 'R56', 'lib': 'Device', 'symbol': 'R',
         'x': 295, 'y': 186, 'value': '100R', 'fp': 'Resistor_SMD:R_0402'},
        {'type': 'local_label', 'x': 295, 'y': 182.19, 'name': 'ADC_SOL_DIV'},
        {'type': 'local_label', 'x': 295, 'y': 189.81, 'name': 'ADC_SOLAR'},
        {'type': 'component', 'ref': 'C110', 'lib': 'Device', 'symbol': 'C',
         'x': 305, 'y': 192, 'value': '100nF', 'fp': 'Capacitor_SMD:C_0402'},
        {'type': 'local_label', 'x': 305, 'y': 188.19, 'name': 'ADC_SOLAR'},
        {'type': 'power', 'name': 'GND', 'x': 305, 'y': 195.81},

        # ========== Hierarchical labels ==========
        {'type': 'hier_label', 'x': 380, 'y': 40, 'name': '5V_SYS', 'shape': 'output'},
        {'type': 'hier_label', 'x': 380, 'y': 50, 'name': '3V3_RP', 'shape': 'output'},
        {'type': 'hier_label', 'x': 380, 'y': 60, 'name': '3V3_RK3506', 'shape': 'output'},
        {'type': 'hier_label', 'x': 380, 'y': 70, 'name': '3V3_RK', 'shape': 'output'},
        {'type': 'hier_label', 'x': 380, 'y': 80, 'name': '1V8', 'shape': 'output'},
        {'type': 'hier_label', 'x': 380, 'y': 90, 'name': 'VBAT', 'shape': 'bidirectional'},
        {'type': 'hier_label', 'x': 10, 'y': 55, 'name': 'SOLAR_IN', 'shape': 'input'},
        {'type': 'hier_label', 'x': 210, 'y': 50, 'name': '48V_POE', 'shape': 'input'},
        {'type': 'hier_label', 'x': 200, 'y': 135, 'name': 'USB_PD_IN', 'shape': 'input'},

        # Notes
        {'type': 'text', 'x': 30, 'y': 355, 'text': 'POWER PRIORITY: 1. Solar+Battery  2. PoE  3. USB-C PD  4. Battery alone', 'size': 1.5},
        {'type': 'text', 'x': 30, 'y': 361, 'text': 'TPS61022: VREF=0.5V, R40=900k, R41=100k → 5.0V (CORRECTED)', 'size': 1.2},
        {'type': 'text', 'x': 30, 'y': 367, 'text': 'CN3722: VREF=1.205V, R42=49.9k, R43=10k → 7.21V (2S LiFePO4)', 'size': 1.2},
    ]
    generate_subsheet("05-power-system.kicad_sch", "Power System — Solar, PoE, USB-C PD, OR-ing, Regulation", items)

    # ============ Sheet 6: Signal Conditioning ============
    # All components wired via wired_sym() — labels placed at exact pin positions.
    #
    # Pin position reference (absolute, from pin_abs(sx, sy, lx, ly) = (sx+lx, sy-ly)):
    #   SN74LVC2G17 at (sx,sy): 1A=(sx-7.62,sy-2.54) 1Y=(sx+7.62,sy-2.54)
    #                            2A=(sx-7.62,sy+2.54) 2Y=(sx+7.62,sy+2.54)
    #                            VCC=(sx,sy-7.62)      GND=(sx,sy+7.62)
    #   SN74LVC1G17 at (sx,sy): A=(sx-7.62,sy)   Y=(sx+7.62,sy)
    #                            VCC=(sx,sy-5.08)  GND=(sx,sy+5.08)
    #   Device R/C at (rx,ry):  pin1=(rx,ry-3.81) pin2=(rx,ry+3.81)
    #
    # Series resistors (R70-R73) are placed vertically so pin2 lands exactly on
    # the IC input pin; pin1 receives the hier_label for the incoming signal.
    # A shared local net (e.g. 'R70_OUT') joins R pin2 to the IC input pin.
    # Bypass caps: pin1='3V3_RP' (local), pin2='GND' (power), placed so pin1
    # aligns with each IC VCC pin via the shared '3V3_RP' local label.
    #
    # Power rail entry: one hier_label '3V3_RP' + wire + local_label '3V3_RP'
    # drives all IC VCC and bypass cap pin1 nodes in this sheet.
    items = [
        {'type': 'text', 'x': 50, 'y': 15, 'text': 'SIGNAL CONDITIONING', 'size': 3},
        {'type': 'text', 'x': 50, 'y': 22, 'text': 'Schmitt Trigger Buffers — 7 ICs, 13 conditioned channels', 'size': 1.5},

        # ── Power rail entry ──────────────────────────────────────────────────
        # hier_label drives the 3V3_RP local net used by all IC VCC / bypass pins
        {'type': 'hier_label', 'x': 20, 'y': 35, 'name': '3V3_RP', 'shape': 'input'},
        {'type': 'wire',       'x1': 20, 'y1': 35, 'x2': 30, 'y2': 35},
        {'type': 'local_label','x': 30, 'y': 35, 'name': '3V3_RP'},

        # ── UART1: RK3576 UART4 ↔ RP2350 GP0/GP1 ────────────────────────────
        # U50 (SN74LVC2G17) at (100, 65)
        #   1A=(92.38,62.46)  1Y=(107.62,62.46)
        #   2A=(92.38,67.54)  2Y=(107.62,67.54)
        #   VCC=(100,57.38)   GND=(100,72.62)
        # R70: pin2 → 1A(92.38,62.46) → R at (92.38,58.65) pin1=(92.38,54.84)
        # R71: pin2 → 2A(92.38,67.54) → R at (92.38,63.73) pin1=(92.38,59.92)
        # C80: pin1 → VCC(100,57.38)  → C at (100,61.19)   pin2=(100,65.00)
        {'type': 'text', 'x': 30, 'y': 40, 'text': 'UART1: RK3576 UART4 ↔ RP2350 GP0/GP1', 'size': 1.5},
        # R70 — 33R series on UART4_TX
        *wired_sym('R70', 'Device', 'R', 92.38, 58.65, '33R', 'Resistor_SMD:R_0402',
            {'1': '~UART4_TX_RAW', '2': 'R70_OUT'}),
        # R71 — 33R series on UART4_RX
        *wired_sym('R71', 'Device', 'R', 92.38, 63.73, '33R', 'Resistor_SMD:R_0402',
            {'1': '~UART4_RX_RAW', '2': 'R71_OUT'}),
        # U50 — dual Schmitt buffer
        *wired_sym('U50', 'solarpunk-pi-v3', 'SN74LVC2G17', 100, 65,
            'SN74LVC2G17', 'Package_TO_SOT_SMD:SOT-23-6',
            {'1A': 'R70_OUT', '1Y': '~UART4_TX_BUF',
             '2A': 'R71_OUT', '2Y': '~UART4_RX_BUF',
             'VCC': '3V3_RP', 'GND': 'GND'}),
        # C80 — 100nF bypass, pin1 at VCC (100,57.38)
        *wired_sym('C80', 'Device', 'C', 100, 61.19, '100nF', 'Capacitor_SMD:C_0402',
            {'1': '3V3_RP', '2': 'GND'}),

        # ── UART2: RK3576 UART5 ↔ RK3506J UART2 ────────────────────────────
        # U51 (SN74LVC2G17) at (100, 125)
        #   1A=(92.38,122.46) 1Y=(107.62,122.46)
        #   2A=(92.38,127.54) 2Y=(107.62,127.54)
        #   VCC=(100,117.38)  GND=(100,132.62)
        # R72: R at (92.38,118.65) pin1=(92.38,114.84) pin2→1A(92.38,122.46)
        # R73: R at (92.38,123.73) pin1=(92.38,119.92) pin2→2A(92.38,127.54)
        # C81: C at (100,121.19)  pin1→VCC(100,117.38) pin2=(100,125.00)
        {'type': 'text', 'x': 30, 'y': 100, 'text': 'UART2: RK3576 UART5 ↔ RK3506J UART2', 'size': 1.5},
        # R72 — 33R series on UART5_TX
        *wired_sym('R72', 'Device', 'R', 92.38, 118.65, '33R', 'Resistor_SMD:R_0402',
            {'1': '~UART5_TX_RAW', '2': 'R72_OUT'}),
        # R73 — 33R series on UART5_RX
        *wired_sym('R73', 'Device', 'R', 92.38, 123.73, '33R', 'Resistor_SMD:R_0402',
            {'1': '~UART5_RX_RAW', '2': 'R73_OUT'}),
        # U51 — dual Schmitt buffer
        *wired_sym('U51', 'solarpunk-pi-v3', 'SN74LVC2G17', 100, 125,
            'SN74LVC2G17', 'Package_TO_SOT_SMD:SOT-23-6',
            {'1A': 'R72_OUT', '1Y': '~UART5_TX_BUF',
             '2A': 'R73_OUT', '2Y': '~UART5_RX_BUF',
             'VCC': '3V3_RP', 'GND': 'GND'}),
        # C81 — 100nF bypass, pin1 at VCC (100,117.38)
        *wired_sym('C81', 'Device', 'C', 100, 121.19, '100nF', 'Capacitor_SMD:C_0402',
            {'1': '3V3_RP', '2': 'GND'}),

        # ── Power Good: RK806 PWRGD → RP2350 GP12 ───────────────────────────
        # U52 (SN74LVC1G17) at (330, 65)
        #   A=(322.38,65)   Y=(337.62,65)
        #   VCC=(330,59.92) GND=(330,70.08)
        # C82: C at (330,63.73) pin1→VCC(330,59.92) pin2=(330,67.54)
        {'type': 'text', 'x': 250, 'y': 40, 'text': 'Power Good: RK806 PWRGD → RP2350 GP12', 'size': 1.5},
        *wired_sym('U52', 'solarpunk-pi-v3', 'SN74LVC1G17', 330, 65,
            'SN74LVC1G17', 'Package_TO_SOT_SMD:SOT-23-5',
            {'A': '~PWR_GOOD_RAW', 'Y': '~PWR_GOOD_BUF',
             'VCC': '3V3_RP', 'GND': 'GND'}),
        # C82 — 100nF bypass, pin1 at VCC (330,59.92)
        *wired_sym('C82', 'Device', 'C', 330, 63.73, '100nF', 'Capacitor_SMD:C_0402',
            {'1': '3V3_RP', '2': 'GND'}),

        # ── Wake Request: RK3506J → RP2350 GP13 ─────────────────────────────
        # U53 (SN74LVC1G17) at (330, 125)
        #   A=(322.38,125)   Y=(337.62,125)
        #   VCC=(330,119.92) GND=(330,130.08)
        # C83: C at (330,123.73) pin1→VCC(330,119.92) pin2=(330,127.54)
        {'type': 'text', 'x': 250, 'y': 100, 'text': 'Wake Request: RK3506J → RP2350 GP13', 'size': 1.5},
        *wired_sym('U53', 'solarpunk-pi-v3', 'SN74LVC1G17', 330, 125,
            'SN74LVC1G17', 'Package_TO_SOT_SMD:SOT-23-5',
            {'A': '~WAKE_RAW', 'Y': '~WAKE_BUF',
             'VCC': '3V3_RP', 'GND': 'GND'}),
        # C83 — 100nF bypass, pin1 at VCC (330,119.92)
        *wired_sym('C83', 'Device', 'C', 330, 123.73, '100nF', 'Capacitor_SMD:C_0402',
            {'1': '3V3_RP', '2': 'GND'}),

        # ── Alarm IRQ: RK3506J → RK3576 ─────────────────────────────────────
        # U54 (SN74LVC1G17) at (100, 185)
        #   A=(92.38,185)   Y=(107.62,185)
        #   VCC=(100,179.92) GND=(100,190.08)
        # C84: C at (100,183.73) pin1→VCC(100,179.92) pin2=(100,187.54)
        {'type': 'text', 'x': 30, 'y': 160, 'text': 'Alarm IRQ: RK3506J → RK3576', 'size': 1.5},
        *wired_sym('U54', 'solarpunk-pi-v3', 'SN74LVC1G17', 100, 185,
            'SN74LVC1G17', 'Package_TO_SOT_SMD:SOT-23-5',
            {'A': '~ALARM_RAW', 'Y': '~ALARM_BUF',
             'VCC': '3V3_RP', 'GND': 'GND'}),
        # C84 — 100nF bypass, pin1 at VCC (100,179.92)
        *wired_sym('C84', 'Device', 'C', 100, 183.73, '100nF', 'Capacitor_SMD:C_0402',
            {'1': '3V3_RP', '2': 'GND'}),

        # ── Shutdown: RK3576 → RP2350 GP28 ──────────────────────────────────
        # U55 (SN74LVC1G17) at (330, 185)
        #   A=(322.38,185)   Y=(337.62,185)
        #   VCC=(330,179.92) GND=(330,190.08)
        # C85: C at (330,183.73) pin1→VCC(330,179.92) pin2=(330,187.54)
        {'type': 'text', 'x': 250, 'y': 160, 'text': 'Shutdown: RK3576 → RP2350 GP28', 'size': 1.5},
        *wired_sym('U55', 'solarpunk-pi-v3', 'SN74LVC1G17', 330, 185,
            'SN74LVC1G17', 'Package_TO_SOT_SMD:SOT-23-5',
            {'A': '~SHUTDOWN_RAW', 'Y': '~SHUTDOWN_BUF',
             'VCC': '3V3_RP', 'GND': 'GND'}),
        # C85 — 100nF bypass, pin1 at VCC (330,179.92)
        *wired_sym('C85', 'Device', 'C', 330, 183.73, '100nF', 'Capacitor_SMD:C_0402',
            {'1': '3V3_RP', '2': 'GND'}),

        # ── Power Enable: RP2350 GP15 → PMOS Gate ───────────────────────────
        # U56 (SN74LVC1G17) at (100, 245)
        #   A=(92.38,245)   Y=(107.62,245)
        #   VCC=(100,239.92) GND=(100,250.08)
        # C86: C at (100,243.73) pin1→VCC(100,239.92) pin2=(100,247.54)
        {'type': 'text', 'x': 30, 'y': 220, 'text': 'Power Enable: RP2350 GP15 → PMOS Gate', 'size': 1.5},
        *wired_sym('U56', 'solarpunk-pi-v3', 'SN74LVC1G17', 100, 245,
            'SN74LVC1G17', 'Package_TO_SOT_SMD:SOT-23-5',
            {'A': '~PWR_EN_RAW', 'Y': '~PWR_EN_BUF',
             'VCC': '3V3_RP', 'GND': 'GND'}),
        # C86 — 100nF bypass, pin1 at VCC (100,239.92)
        *wired_sym('C86', 'Device', 'C', 100, 243.73, '100nF', 'Capacitor_SMD:C_0402',
            {'1': '3V3_RP', '2': 'GND'}),

        # ── Notes ─────────────────────────────────────────────────────────────
        {'type': 'text', 'x': 30, 'y': 280, 'text': 'SIGNAL CONDITIONING SUMMARY', 'size': 2},
        {'type': 'text', 'x': 30, 'y': 290, 'text': 'SN74LVC2G17 (dual) x2: UART1 TX/RX, UART2 TX/RX — with 33R series', 'size': 1.2},
        {'type': 'text', 'x': 30, 'y': 296, 'text': 'SN74LVC1G17 (single) x5: PG, wake, alarm, shutdown, power gate', 'size': 1.2},
        {'type': 'text', 'x': 30, 'y': 302, 'text': 'SN74LVC14A (hex) x1: on Sheet 04 (U37) — industrial inputs', 'size': 1.2},
        {'type': 'text', 'x': 30, 'y': 308, 'text': 'Total: 100nF bypass on each IC VCC', 'size': 1.2},
        {'type': 'text', 'x': 30, 'y': 320, 'text': 'NOTE: RK3506J reset is DIRECT (same 3.3V domain, no Schmitt)', 'size': 1.2},
        {'type': 'text', 'x': 30, 'y': 326, 'text': 'NOTE: SPI bridge is DIRECT (same 3.3V domain, 10MHz)', 'size': 1.2},
    ]
    generate_subsheet("06-signal-conditioning.kicad_sch", "Signal Conditioning — Schmitt Trigger Buffers & ESD", items)


# ============================================================
# 4. PCB FILE
# ============================================================
def generate_pcb():
    """Generate PCB file with 6-layer stackup, board outline, mounting holes, and design rules."""

    # Board dimensions: 85x56mm (Pi 5 form factor)
    # Origin at bottom-left corner
    bw, bh = 85.0, 56.0

    # Mounting holes at Pi 5 positions (measured from bottom-left)
    # Pi 5 holes: 3.5mm from edges, 58mm apart horizontally, 49mm vertically
    holes = [
        (3.5, 3.5),
        (3.5 + 58.0, 3.5),
        (3.5, 3.5 + 49.0),
        (3.5 + 58.0, 3.5 + 49.0),
    ]

    hole_footprints = ""
    for i, (hx, hy) in enumerate(holes):
        hole_footprints += f"""
  (footprint "MountingHole:MountingHole_2.7mm_M2.5_Pad"
    (layer "F.Cu")
    (uuid "{uid()}")
    (at {hx} {hy})
    (property "Reference" "H{i+1}"
      (at 0 -3 0)
      (layer "F.SilkS")
      (uuid "{uid()}")
      (effects (font (size 1 1) (thickness 0.15)))
    )
    (property "Value" "MountingHole_2.7mm"
      (at 0 3 0)
      (layer "F.Fab")
      (uuid "{uid()}")
      (effects (font (size 1 1) (thickness 0.15)))
    )
    (pad "1" thru_hole circle
      (at 0 0)
      (size 5.4 5.4)
      (drill 2.7)
      (layers "*.Cu" "*.Mask")
      (uuid "{uid()}")
    )
  )
"""

    # Generate GND zone fills on L2-GND (In1.Cu) and L5-GND (In4.Cu) — full board
    def make_zone(net_name, layer, priority=0):
        return f"""  (zone
    (net 0)
    (net_name "{net_name}")
    (layer "{layer}")
    (uuid "{uid()}")
    (name "{net_name}_{layer}")
    (hatch edge 0.5)
    (priority {priority})
    (connect_pads (clearance 0.2))
    (min_thickness 0.15)
    (filled_areas_thickness no)
    (fill yes (thermal_gap 0.3) (thermal_bridge_width 0.3))
    (polygon
      (pts
        (xy 0 0) (xy {bw} 0) (xy {bw} {bh}) (xy 0 {bh})
      )
    )
  )
"""

    zone_fills = ""
    # GND zones on dedicated ground layers (full board, highest priority)
    zone_fills += make_zone("GND", "In1.Cu", 1)
    zone_fills += make_zone("GND", "In4.Cu", 1)
    # GND zones on signal layers (lower priority, fills unused space)
    zone_fills += make_zone("GND", "F.Cu", 0)
    zone_fills += make_zone("GND", "B.Cu", 0)
    # Power zone splits on In3.Cu (L4-PWR)
    # 5V_SYS: left half of board
    zone_fills += f"""  (zone
    (net 0)
    (net_name "5V_SYS")
    (layer "In3.Cu")
    (uuid "{uid()}")
    (name "5V_SYS_zone")
    (hatch edge 0.5)
    (priority 1)
    (connect_pads (clearance 0.3))
    (min_thickness 0.2)
    (filled_areas_thickness no)
    (fill yes (thermal_gap 0.3) (thermal_bridge_width 0.5))
    (polygon
      (pts
        (xy 0 0) (xy {bw*0.5} 0) (xy {bw*0.5} {bh}) (xy 0 {bh})
      )
    )
  )
"""
    # 3V3 rails: right half split vertically
    zone_fills += f"""  (zone
    (net 0)
    (net_name "3V3_RK")
    (layer "In3.Cu")
    (uuid "{uid()}")
    (name "3V3_RK_zone")
    (hatch edge 0.5)
    (priority 1)
    (connect_pads (clearance 0.3))
    (min_thickness 0.2)
    (filled_areas_thickness no)
    (fill yes (thermal_gap 0.3) (thermal_bridge_width 0.3))
    (polygon
      (pts
        (xy {bw*0.5} 0) (xy {bw} 0) (xy {bw} {bh*0.5}) (xy {bw*0.5} {bh*0.5})
      )
    )
  )
"""
    zone_fills += f"""  (zone
    (net 0)
    (net_name "VBAT")
    (layer "In3.Cu")
    (uuid "{uid()}")
    (name "VBAT_zone")
    (hatch edge 0.5)
    (priority 1)
    (connect_pads (clearance 0.3))
    (min_thickness 0.2)
    (filled_areas_thickness no)
    (fill yes (thermal_gap 0.3) (thermal_bridge_width 0.5))
    (polygon
      (pts
        (xy {bw*0.5} {bh*0.5}) (xy {bw} {bh*0.5}) (xy {bw} {bh}) (xy {bw*0.5} {bh})
      )
    )
  )
"""

    # Generate via stitching grid (3mm pitch, GND, across full board)
    # Avoid mounting hole areas (4mm exclusion radius)
    via_stitching = ""
    via_pitch = 3.0
    margin = 2.0  # Keep away from board edge
    hole_excl = 4.0  # Exclusion radius around mounting holes
    x = margin
    while x < bw - margin:
        y = margin
        while y < bh - margin:
            # Check distance to all mounting holes
            too_close = False
            for hx, hy in holes:
                if ((x - hx)**2 + (y - hy)**2) < hole_excl**2:
                    too_close = True
                    break
            if not too_close:
                via_stitching += f"""  (via
    (at {x:.1f} {y:.1f})
    (size 0.6)
    (drill 0.3)
    (layers "F.Cu" "B.Cu")
    (net 0)
    (uuid "{uid()}")
  )
"""
            y += via_pitch
        x += via_pitch

    pcb = f"""(kicad_pcb
  (version 20240108)
  (generator "solarpunk_gen")
  (generator_version "1.0")
  (general
    (thickness 1.6)
    (legacy_teardrops no)
  )
  (paper "A4")
  (title_block
    (title "Solarpunk Pi v3 — Triple-Processor Solar Edge Computer")
    (date "2026-03")
    (rev "3.0")
    (company "Solarpunk Computing")
    (comment 1 "85x56mm Pi 5 Form Factor — 6-Layer PCB")
    (comment 2 "JLCPCB JLC06161H-3313 Stackup — ENIG — Impedance Controlled")
    (comment 3 "RK3576 + RP2350 + RK3506J")
  )
  (layers
    (0 "F.Cu" signal)
    (1 "In1.Cu" signal "GND")
    (2 "In2.Cu" signal "Signal")
    (3 "In3.Cu" signal "Power")
    (4 "In4.Cu" signal "GND")
    (31 "B.Cu" signal)
    (32 "B.Adhes" user "B.Adhesive")
    (33 "F.Adhes" user "F.Adhesive")
    (34 "B.Paste" user)
    (35 "F.Paste" user)
    (36 "B.SilkS" user "B.Silkscreen")
    (37 "F.SilkS" user "F.Silkscreen")
    (38 "B.Mask" user "B.Mask")
    (39 "F.Mask" user "F.Mask")
    (40 "Dwgs.User" user "User.Drawings")
    (41 "Cmts.User" user "User.Comments")
    (42 "Eco1.User" user "User.Eco1")
    (43 "Eco2.User" user "User.Eco2")
    (44 "Edge.Cuts" user)
    (45 "Margin" user)
    (46 "B.CrtYd" user "B.Courtyard")
    (47 "F.CrtYd" user "F.Courtyard")
    (48 "B.Fab" user "B.Fabrication")
    (49 "F.Fab" user "F.Fabrication")
    (50 "User.1" user)
    (51 "User.2" user)
  )
  (setup
    (stackup
      (layer "F.SilkS" (type "Top Silk Screen"))
      (layer "F.Paste" (type "Top Solder Paste"))
      (layer "F.Mask" (type "Top Solder Mask") (thickness 0.01) (material "Epoxy") (epsilon_r 3.3))
      (layer "F.Cu" (type "copper") (thickness 0.035) (material "Copper"))
      (layer "dielectric 1" (type "prepreg") (thickness 0.1) (material "FR4") (epsilon_r 4.5) (loss_tangent 0.02))
      (layer "In1.Cu" (type "copper") (thickness 0.0175) (material "Copper"))
      (layer "dielectric 2" (type "core") (thickness 0.36) (material "FR4") (epsilon_r 4.6) (loss_tangent 0.02))
      (layer "In2.Cu" (type "copper") (thickness 0.0175) (material "Copper"))
      (layer "dielectric 3" (type "prepreg") (thickness 0.36) (material "FR4") (epsilon_r 4.5) (loss_tangent 0.02))
      (layer "In3.Cu" (type "copper") (thickness 0.0175) (material "Copper"))
      (layer "dielectric 4" (type "core") (thickness 0.36) (material "FR4") (epsilon_r 4.6) (loss_tangent 0.02))
      (layer "In4.Cu" (type "copper") (thickness 0.0175) (material "Copper"))
      (layer "dielectric 5" (type "prepreg") (thickness 0.1) (material "FR4") (epsilon_r 4.5) (loss_tangent 0.02))
      (layer "B.Cu" (type "copper") (thickness 0.035) (material "Copper"))
      (layer "B.Mask" (type "Bottom Solder Mask") (thickness 0.01) (material "Epoxy") (epsilon_r 3.3))
      (layer "B.Paste" (type "Bottom Solder Paste"))
      (layer "B.SilkS" (type "Bottom Silk Screen"))
      (copper_finish "ENIG")
      (dielectric_constraints yes)
    )
    (pad_to_mask_clearance 0)
    (allow_soldermask_bridges_in_footprints no)
    (pcbplotparams
      (layerselection 0x0001000_ffffffff)
      (plot_on_all_layers_selection 0x0000000_00000000)
      (disableapertmacros no)
      (usegerberextensions no)
      (usegerberattributes yes)
      (usegerberadvancedattributes yes)
      (creategerberjobfile yes)
      (dashed_line_dash_ratio 12.000000)
      (dashed_line_gap_ratio 3.000000)
      (svgprecision 4)
      (plotframeref no)
      (viasonmask no)
      (mode 1)
      (useauxorigin no)
      (hpglpennumber 1)
      (hpglpenspeed 20)
      (hpglpendiameter 15.000000)
      (pdf_front_fp_property_popups yes)
      (pdf_back_fp_property_popups yes)
      (dxfpolygonmode yes)
      (dxfimperialunits yes)
      (dxfusepcbnewfont yes)
      (psnegative no)
      (psa4output no)
      (plotreference yes)
      (plotvalue no)
      (plotfptext yes)
      (plotinvisibletext no)
      (sketchpadsonfab no)
      (subtractmaskfromsilk no)
      (outputformat 1)
      (mirror no)
      (drillshape 1)
      (scaleselection 1)
      (outputdirectory "gerber/")
    )
  )
  (net 0 "")
  (net 1 "GND")
  (net 2 "5V_SYS")
  (net 3 "3V3_RP")
  (net 4 "3V3_RK3506")
  (net 5 "3V3_RK")
  (net 6 "1V8")
  (net 7 "VDD_CPU_BIG")
  (net 8 "VDD_CPU_LIT")
  (net 9 "VDD_GPU")
  (net 10 "VDD_NPU")
  (net 11 "VDD_LOGIC")
  (net 12 "VCC_DDR")
  (net 13 "VBAT")
  (net 14 "SOLAR_IN")
  (net 15 "48V_POE")

  (gr_rect (start 0 0) (end {bw} {bh})
    (stroke (width 0.1) (type solid))
    (fill no)
    (layer "Edge.Cuts")
    (uuid "{uid()}")
  )

  (gr_text "SOLARPUNK PI v3.0"
    (at {bw/2} {bh/2 - 5})
    (layer "F.SilkS")
    (uuid "{uid()}")
    (effects (font (size 3 3) (thickness 0.3)))
  )
  (gr_text "RK3576 + RP2350 + RK3506J"
    (at {bw/2} {bh/2})
    (layer "F.SilkS")
    (uuid "{uid()}")
    (effects (font (size 1.5 1.5) (thickness 0.15)))
  )
  (gr_text "Rev 3.0 — 2026-03"
    (at {bw/2} {bh/2 + 4})
    (layer "F.SilkS")
    (uuid "{uid()}")
    (effects (font (size 1 1) (thickness 0.15)))
  )

  (gr_text "TOP: RK3576, DDR, PMIC, eMMC, WiFi, GbE, Audio, USB, HDMI, CSI, GPIO"
    (at {bw/2} 2)
    (layer "Cmts.User")
    (uuid "{uid()}")
    (effects (font (size 1 1) (thickness 0.1)))
  )
  (gr_text "BOTTOM: RP2350, RK3506J, LoRa, CYW43439, CN3722, TPS61022, PoE, CAN/RS485, Schmitt"
    (at {bw/2} {bh - 2})
    (layer "Cmts.User")
    (uuid "{uid()}")
    (effects (font (size 1 1) (thickness 0.1)))
  )

  (gr_text "L1-TOP: BGA fanout, DDR CH0, USB, CSI, RGMII"
    (at 10 6)
    (layer "Cmts.User")
    (uuid "{uid()}")
    (effects (font (size 0.8 0.8) (thickness 0.08)) (justify left))
  )
  (gr_text "L2-GND: Solid ground pour — NEVER CUT"
    (at 10 8)
    (layer "Cmts.User")
    (uuid "{uid()}")
    (effects (font (size 0.8 0.8) (thickness 0.08)) (justify left))
  )
  (gr_text "L3-SIG: DDR CH1, NVMe PCIe, HDMI, USB3"
    (at 10 10)
    (layer "Cmts.User")
    (uuid "{uid()}")
    (effects (font (size 0.8 0.8) (thickness 0.08)) (justify left))
  )
  (gr_text "L4-PWR: Copper fills 5V, 3V3, 1V8, VBAT"
    (at 10 12)
    (layer "Cmts.User")
    (uuid "{uid()}")
    (effects (font (size 0.8 0.8) (thickness 0.08)) (justify left))
  )
  (gr_text "L5-GND: Solid ground pour — NEVER CUT"
    (at 10 14)
    (layer "Cmts.User")
    (uuid "{uid()}")
    (effects (font (size 0.8 0.8) (thickness 0.08)) (justify left))
  )
  (gr_text "L6-BOT: RP2350, RK3506J, LoRa, MPPT, PoE"
    (at 10 16)
    (layer "Cmts.User")
    (uuid "{uid()}")
    (effects (font (size 0.8 0.8) (thickness 0.08)) (justify left))
  )

  (gr_text "PLACEMENT ZONES"
    (at {bw/2} 20)
    (layer "Cmts.User")
    (uuid "{uid()}")
    (effects (font (size 1.2 1.2) (thickness 0.12)))
  )

  (gr_rect (start 15 20) (end 55 42)
    (stroke (width 0.15) (type dash))
    (fill no)
    (layer "Cmts.User")
    (uuid "{uid()}")
  )
  (gr_text "RK3576 BGA (TOP)"
    (at 35 31)
    (layer "Cmts.User")
    (uuid "{uid()}")
    (effects (font (size 1.2 1.2) (thickness 0.12)))
  )

  (gr_rect (start 20 15) (end 50 20)
    (stroke (width 0.1) (type dash))
    (fill no)
    (layer "Cmts.User")
    (uuid "{uid()}")
  )
  (gr_text "DDR (TOP)"
    (at 35 17.5)
    (layer "Cmts.User")
    (uuid "{uid()}")
    (effects (font (size 0.8 0.8) (thickness 0.08)))
  )

  (gr_rect (start 56 20) (end 72 35)
    (stroke (width 0.1) (type dash))
    (fill no)
    (layer "Cmts.User")
    (uuid "{uid()}")
  )
  (gr_text "RK806 PMIC (TOP)"
    (at 64 27.5)
    (layer "Cmts.User")
    (uuid "{uid()}")
    (effects (font (size 0.8 0.8) (thickness 0.08)))
  )

  (gr_rect (start 60 37) (end 80 50)
    (stroke (width 0.1) (type dash))
    (fill no)
    (layer "Cmts.User")
    (uuid "{uid()}")
  )
  (gr_text "GbE + RJ45 (TOP)"
    (at 70 43.5)
    (layer "Cmts.User")
    (uuid "{uid()}")
    (effects (font (size 0.8 0.8) (thickness 0.08)))
  )

  (gr_rect (start 15 42) (end 50 52)
    (stroke (width 0.1) (type dash))
    (fill no)
    (layer "Cmts.User")
    (uuid "{uid()}")
  )
  (gr_text "RP2350 + CYW + SX1262 (BOT)"
    (at 32.5 47)
    (layer "Cmts.User")
    (uuid "{uid()}")
    (effects (font (size 0.8 0.8) (thickness 0.08)))
  )

  (gr_rect (start 50 42) (end 80 52)
    (stroke (width 0.1) (type dash))
    (fill no)
    (layer "Cmts.User")
    (uuid "{uid()}")
  )
  (gr_text "RK3506J + Industrial (BOT)"
    (at 65 47)
    (layer "Cmts.User")
    (uuid "{uid()}")
    (effects (font (size 0.8 0.8) (thickness 0.08)))
  )

  (gr_rect (start 5 42) (end 15 52)
    (stroke (width 0.1) (type dash))
    (fill no)
    (layer "Cmts.User")
    (uuid "{uid()}")
  )
  (gr_text "MPPT+Boost (BOT)"
    (at 10 47)
    (layer "Cmts.User")
    (uuid "{uid()}")
    (effects (font (size 0.6 0.6) (thickness 0.06)))
  )

{hole_footprints}

{zone_fills}

{via_stitching}

)
"""
    path = os.path.join(PROJECT_DIR, f"{PROJECT_NAME}.kicad_pcb")
    with open(path, 'w') as f:
        f.write(pcb)
    print(f"  Created {path}")


# ============================================================
# 5. LIBRARY TABLES
# ============================================================
def generate_lib_tables():
    sym_table = f"""(sym_lib_table
  (version 7)
  (lib (name "{PROJECT_NAME}")(type "KiCad")(uri "${{KIPRJMOD}}/libraries/{PROJECT_NAME}.kicad_sym")(options "")(descr "Solarpunk Pi v3 custom symbols"))
)
"""
    fp_table = f"""(fp_lib_table
  (version 7)
  (lib (name "{PROJECT_NAME}")(type "KiCad")(uri "${{KIPRJMOD}}/libraries/{PROJECT_NAME}.pretty")(options "")(descr "Solarpunk Pi v3 custom footprints"))
)
"""

    sym_path = os.path.join(PROJECT_DIR, "sym-lib-table")
    fp_path = os.path.join(PROJECT_DIR, "fp-lib-table")

    with open(sym_path, 'w') as f:
        f.write(sym_table)
    print(f"  Created {sym_path}")

    with open(fp_path, 'w') as f:
        f.write(fp_table)
    print(f"  Created {fp_path}")


# ============================================================
# MAIN
# ============================================================
if __name__ == "__main__":
    print("Generating Solarpunk Pi v3 KiCad Project...")
    print()

    print("[1/5] Project configuration...")
    generate_project_file()

    print("[2/5] Custom symbol library (15 symbols)...")
    generate_symbol_library()

    print("[3/5] Hierarchical schematics (7 sheets)...")
    generate_top_schematic()
    generate_all_subsheets()

    print("[4/5] PCB with 6-layer stackup...")
    generate_pcb()

    print("[5/5] Library tables...")
    generate_lib_tables()

    print()
    print("=" * 60)
    print("  Solarpunk Pi v3 KiCad project generated successfully!")
    print("=" * 60)
    print()
    print("Project directory:")
    print(f"  {PROJECT_DIR}/")
    print()
    print("Files created:")
    for f in sorted(os.listdir(PROJECT_DIR)):
        if f.endswith(('.py', '.pyc')):
            continue
        full = os.path.join(PROJECT_DIR, f)
        if os.path.isdir(full):
            for sub in sorted(os.listdir(full)):
                subf = os.path.join(full, sub)
                if os.path.isdir(subf):
                    for subsub in os.listdir(subf):
                        print(f"  {f}/{sub}/{subsub}")
                else:
                    print(f"  {f}/{sub}")
        else:
            print(f"  {f}")
    print()
    print("To open in KiCad:")
    print(f"  kicad {PROJECT_DIR}/{PROJECT_NAME}.kicad_pro")
    print()
    print("Net classes configured:")
    print("  Default (50Ω SE)  |  DDR_DQ (50Ω SE)  |  DDR_CLK (85Ω diff)")
    print("  USB_HS (90Ω diff) |  PCIE (85Ω diff)   |  HDMI (100Ω diff)")
    print("  MIPI_CSI (100Ω)  |  SDIO (50Ω SE)     |  POWER (wide trace)")
    print()
    print("PCB stackup: JLC06161H-3313 (6-layer)")
    print("  L1-TOP: Signal (1oz)  |  L2-GND: Ground (0.5oz)")
    print("  L3-SIG: Signal (0.5oz)|  L4-PWR: Power (0.5oz)")
    print("  L5-GND: Ground (0.5oz)|  L6-BOT: Signal (1oz)")
    print()
    print("NEXT STEPS:")
    print("  1. Open project in KiCad 9")
    print("  2. Assign proper footprints (some use placeholder library refs)")
    print("  3. Wire up schematics — components are placed and labeled")
    print("  4. Run ERC (Electrical Rules Check)")
    print("  5. Import netlist to PCB")
    print("  6. Place components per Section 8 placement order")
    print("  7. Route per Section 11 priority order (DDR first!)")
    print("  8. Run DRC with impedance constraints")
