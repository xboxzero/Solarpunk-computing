use std::process::Command;

pub async fn run(port: &str, target: &str) -> Result<(), Box<dyn std::error::Error>> {
    let project_dir = dirs_or_default();

    println!("Building and flashing (target: {target}, port: {port})...");

    let script = format!(
        "source ~/esp/esp-idf/export.sh 2>/dev/null && \
         cd {project_dir} && \
         idf.py set-target {target} && \
         idf.py build && \
         idf.py -p {port} flash monitor"
    );

    let status = Command::new("bash")
        .args(["-c", &script])
        .stdin(std::process::Stdio::inherit())
        .stdout(std::process::Stdio::inherit())
        .stderr(std::process::Stdio::inherit())
        .status()?;

    if !status.success() {
        return Err(format!("idf.py exited with status {status}").into());
    }

    Ok(())
}

fn dirs_or_default() -> String {
    // Try to find the Solarpunk-computing directory
    let home = std::env::var("HOME").unwrap_or_else(|_| "/home/xero2".into());
    let project = format!("{home}/Solarpunk-computing");
    if std::path::Path::new(&project).exists() {
        project
    } else {
        ".".into()
    }
}
