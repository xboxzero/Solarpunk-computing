#pragma once

// LLM Client + Agent System
// Queries Pi 5's local llama.cpp server
// Agent mode: LLM can execute commands and self-program

void llm_init();

// Simple Q&A - ask and get response
int llm_ask(const char* prompt, char* response, int response_size);

// Agent mode - LLM autonomously executes commands to complete a task
// Sends progress to WebSocket clients in real-time
// Returns 0 on success, -1 on error
int llm_agent(const char* task, char* summary, int summary_size);

// Check if Pi LLM server is reachable
bool llm_is_connected();
