#pragma once

// Deep sleep + power saving
// Manages idle detection and mesh-sleep coordination

void sleep_init();
void sleep_reset_idle();
void sleep_check_idle();
void sleep_enter_deep(uint64_t duration_us);
void sleep_enter_mesh_sleep();
