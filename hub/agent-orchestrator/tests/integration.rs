use std::process::Command;

#[test]
fn binary_runs_with_help() {
    let output = Command::new("cargo")
        .args(["run", "--", "--help"])
        .output()
        .expect("failed to run binary");

    let stdout = String::from_utf8_lossy(&output.stdout);
    assert!(stdout.contains("Solarpunk AI Agent Orchestrator"));
    assert!(stdout.contains("--backend"));
    assert!(stdout.contains("--api-key"));
    assert!(stdout.contains("--model"));
    assert!(stdout.contains("--endpoint"));
}

#[test]
fn binary_shows_version() {
    let output = Command::new("cargo")
        .args(["run", "--", "--version"])
        .output()
        .expect("failed to run binary");

    let stdout = String::from_utf8_lossy(&output.stdout);
    assert!(stdout.contains("solarpunk-agent 0.2.0"));
}
