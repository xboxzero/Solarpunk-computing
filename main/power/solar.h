#pragma once

// Solar + battery power management
// Reads ADC for battery voltage and solar panel output

void solar_init();
void solar_update();
int  solar_battery_percent();
int  solar_battery_mv();
int  solar_panel_mv();
bool solar_is_charging();
