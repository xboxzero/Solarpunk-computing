#pragma once

// Lightweight script engine
// Runs user scripts submitted from the web IDE
// Currently a simple command interpreter; can be extended
// to MicroPython or a JS subset

void engine_init();
int  engine_run(const char* script, char* output, int output_size);
