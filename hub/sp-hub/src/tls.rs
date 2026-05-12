use std::path::{Path, PathBuf};
use std::process::Command;

pub struct Tls {
    pub cert_pem: Vec<u8>,
    pub key_pem: Vec<u8>,
    pub sans: Vec<String>,
    pub dir: PathBuf,
}

pub fn tls_dir() -> PathBuf {
    if let Ok(xdg) = std::env::var("XDG_CONFIG_HOME") {
        return PathBuf::from(xdg).join("sp-hub").join("tls");
    }
    if let Ok(home) = std::env::var("HOME") {
        return PathBuf::from(home).join(".config").join("sp-hub").join("tls");
    }
    PathBuf::from("./sp-hub-tls")
}

pub fn local_ipv4s() -> Vec<String> {
    let out = match Command::new("hostname").arg("-I").output() {
        Ok(o) if o.status.success() => o.stdout,
        _ => return vec![],
    };
    String::from_utf8_lossy(&out)
        .split_whitespace()
        .filter(|s| !s.contains(':'))
        .map(|s| s.to_string())
        .collect()
}

fn collect_sans() -> Vec<String> {
    let mut sans = vec!["localhost".to_string(), "127.0.0.1".to_string()];
    for ip in local_ipv4s() {
        if !sans.contains(&ip) {
            sans.push(ip);
        }
    }
    sans
}

pub fn ensure_self_signed(dir: &Path) -> std::io::Result<Tls> {
    std::fs::create_dir_all(dir)?;
    let cert_path = dir.join("cert.pem");
    let key_path = dir.join("key.pem");
    let sans_path = dir.join("sans.txt");

    let want_sans = collect_sans();
    let want_sans_text = want_sans.join("\n");

    let prev_sans_text = std::fs::read_to_string(&sans_path).unwrap_or_default();
    let cert_exists = cert_path.exists() && key_path.exists();
    let sans_match = prev_sans_text.trim() == want_sans_text.trim();

    if cert_exists && sans_match {
        return Ok(Tls {
            cert_pem: std::fs::read(&cert_path)?,
            key_pem: std::fs::read(&key_path)?,
            sans: want_sans,
            dir: dir.to_path_buf(),
        });
    }

    let mut params = rcgen::CertificateParams::new(want_sans.clone())
        .map_err(|e| std::io::Error::new(std::io::ErrorKind::Other, e.to_string()))?;
    let mut dn = rcgen::DistinguishedName::new();
    dn.push(rcgen::DnType::CommonName, "sp-hub recorder");
    params.distinguished_name = dn;

    // iOS Safari rejects self-signed certs with validity > ~398 days outright (no click-through),
    // and requires extKeyUsage = serverAuth. Cap at 365 days and set EKU explicitly.
    let now = time::OffsetDateTime::now_utc();
    params.not_before = now - time::Duration::hours(1);
    params.not_after = now + time::Duration::days(365);
    params.extended_key_usages = vec![rcgen::ExtendedKeyUsagePurpose::ServerAuth];

    // ECDSA P-256 — accepted by iOS Safari; smaller and faster than RSA on Pi.
    let key_pair = rcgen::KeyPair::generate_for(&rcgen::PKCS_ECDSA_P256_SHA256)
        .map_err(|e| std::io::Error::new(std::io::ErrorKind::Other, e.to_string()))?;
    let cert = params
        .self_signed(&key_pair)
        .map_err(|e| std::io::Error::new(std::io::ErrorKind::Other, e.to_string()))?;

    let cert_pem = cert.pem();
    let key_pem = key_pair.serialize_pem();

    std::fs::write(&cert_path, &cert_pem)?;
    std::fs::write(&key_path, &key_pem)?;
    std::fs::write(&sans_path, &want_sans_text)?;

    Ok(Tls {
        cert_pem: cert_pem.into_bytes(),
        key_pem: key_pem.into_bytes(),
        sans: want_sans,
        dir: dir.to_path_buf(),
    })
}
