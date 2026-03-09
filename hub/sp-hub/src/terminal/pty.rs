use std::time::Instant;

pub struct PtySession {
    pub pid: i32,
    pub master_fd: i32,
    pub created: Instant,
    pub last_activity: Instant,
    pub alive: bool,
}

impl PtySession {
    pub fn touch(&mut self) {
        self.last_activity = Instant::now();
    }
}

pub fn fork_pty() -> Result<PtySession, String> {
    // Use libc directly for forkpty since nix's API varies between versions
    let mut master_fd: libc::c_int = 0;
    let pid = unsafe { libc::forkpty(&mut master_fd, std::ptr::null_mut(), std::ptr::null_mut(), std::ptr::null_mut()) };

    if pid < 0 {
        return Err("forkpty failed".into());
    }

    if pid == 0 {
        // Child process
        // Set new process group for clean killpg
        unsafe { libc::setpgid(0, 0) };

        // SAFETY: we're in a forked child process, single-threaded before exec
        unsafe {
            std::env::set_var("TERM", "xterm-256color");
            std::env::set_var("COLUMNS", "80");
            std::env::set_var("LINES", "24");
        }

        let home = std::env::var("HOME").unwrap_or_else(|_| "/home/xero2".into());
        let project_dir = format!("{home}/Solarpunk-computing");
        if std::path::Path::new(&project_dir).exists() {
            let _ = std::env::set_current_dir(&project_dir);
        }

        // Exec bash
        let shell = std::ffi::CString::new("/bin/bash").unwrap();
        let args = [
            std::ffi::CString::new("/bin/bash").unwrap(),
            std::ffi::CString::new("--login").unwrap(),
        ];
        let arg_ptrs: Vec<&std::ffi::CStr> = args.iter().map(|a| a.as_c_str()).collect();
        let _ = nix::unistd::execvp(&shell, &arg_ptrs);
        std::process::exit(1);
    }

    // Parent
    tracing::info!("PTY session started (PID {pid})");
    Ok(PtySession {
        pid,
        master_fd,
        created: Instant::now(),
        last_activity: Instant::now(),
        alive: true,
    })
}

pub fn kill_session(session: &PtySession) {
    if !session.alive {
        return;
    }
    let pid = session.pid;

    // SIGTERM the process group
    unsafe {
        let pgid = libc::getpgid(pid);
        if pgid > 0 {
            libc::killpg(pgid, libc::SIGTERM);
        } else {
            libc::kill(pid, libc::SIGTERM);
        }
    }

    std::thread::sleep(std::time::Duration::from_millis(500));

    // SIGKILL
    unsafe {
        let pgid = libc::getpgid(pid);
        if pgid > 0 {
            libc::killpg(pgid, libc::SIGKILL);
        } else {
            libc::kill(pid, libc::SIGKILL);
        }
    }

    // Reap
    unsafe {
        libc::waitpid(pid, std::ptr::null_mut(), libc::WNOHANG);
    }

    // Close fd
    unsafe {
        libc::close(session.master_fd);
    }

    tracing::info!("PTY session killed (PID {pid})");
}

pub fn set_pty_size(fd: i32, rows: u16, cols: u16) {
    let winsize = libc::winsize {
        ws_row: rows,
        ws_col: cols,
        ws_xpixel: 0,
        ws_ypixel: 0,
    };
    unsafe {
        libc::ioctl(fd, libc::TIOCSWINSZ, &winsize);
    }
}
