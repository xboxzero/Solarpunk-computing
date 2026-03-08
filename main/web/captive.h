#pragma once

// Captive portal -- makes iPhone auto-open Safari to our web IDE
// Works by running a DNS server that redirects all domains to our IP

void captive_init();
void captive_stop();
