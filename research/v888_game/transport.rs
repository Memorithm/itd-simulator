//! Bounded request/reply transport for trusted single-process research workers.
//! Separate address space is NOT a filesystem/network/security sandbox.
#![forbid(unsafe_code)]

use std::io::{BufReader, Read, Write};
use std::path::Path;
use std::process::{Child, Command, Stdio};
use std::sync::mpsc::{self, Receiver, SyncSender};
use std::thread::{self, JoinHandle};
use std::time::{Duration, Instant};

pub const FRAME_LIMIT: usize = 128;

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Fault { Spawn, Io, Eof, Truncated, Oversize, Encoding, Timeout, Closed, Protocol }
impl Fault {
    pub fn name(self) -> &'static str {
        match self {
            Self::Spawn => "spawn", Self::Io => "io", Self::Eof => "eof",
            Self::Truncated => "truncated", Self::Oversize => "oversize",
            Self::Encoding => "encoding", Self::Timeout => "timeout",
            Self::Closed => "closed", Self::Protocol => "protocol",
        }
    }
}

/// ASCII frame, excluding LF; rejects arbitrary buffering, CR and partial frames.
pub fn read_frame<R: Read>(reader: &mut R) -> Result<String, Fault> {
    let mut bytes = Vec::with_capacity(FRAME_LIMIT);
    loop {
        let mut one = [0];
        match reader.read(&mut one) {
            Ok(0) => return Err(if bytes.is_empty() { Fault::Eof } else { Fault::Truncated }),
            Ok(_) => {
                if one[0] == b'\n' {
                    if bytes.is_empty() { return Err(Fault::Protocol); }
                    return String::from_utf8(bytes).map_err(|_| Fault::Encoding);
                }
                if bytes.len() == FRAME_LIMIT { return Err(Fault::Oversize); }
                if !(b' '..=b'~').contains(&one[0]) { return Err(Fault::Encoding); }
                bytes.push(one[0]);
            }
            Err(e) if e.kind() == std::io::ErrorKind::Interrupted => {},
            Err(_) => return Err(Fault::Io),
        }
    }
}

/// One in-flight exchange; deadline includes pipe write, flush and read.
/// The OS spawn and cleanup durations are measured separately by the caller.
/// Workers must not spawn descendants or escape the direct-child lifecycle.
pub struct Session {
    child: Child,
    requests: Option<SyncSender<String>>,
    replies: Option<Receiver<Result<String, Fault>>>,
    io_thread: Option<JoinHandle<()>>,
    failed: bool,
    closed: bool,
    pub requests_enqueued: u64,
    pub request_bytes_enqueued: u64,
    pub response_bytes_received: u64,
    pub child_reaped: bool,
    pub io_thread_joined: bool,
}
impl Session {
    pub fn spawn(executable: &Path, args: &[String], cwd: &Path) -> Result<Self, Fault> {
        // No shell, no inherited secret environment, no inherited fixture stdin.
        let mut child = Command::new(executable).args(args).current_dir(cwd)
            .env_clear().env("LC_ALL", "C")
            .stdin(Stdio::piped()).stdout(Stdio::piped()).stderr(Stdio::null())
            .spawn().map_err(|_| Fault::Spawn)?;
        let mut input = child.stdin.take().expect("piped stdin");
        let mut output = BufReader::with_capacity(FRAME_LIMIT + 1, child.stdout.take().expect("piped stdout"));
        let (tx, request_rx) = mpsc::sync_channel::<String>(1);
        let (reply_tx, rx) = mpsc::sync_channel(1);
        let handle = thread::spawn(move || {
            while let Ok(request) = request_rx.recv() {
                let reply = input.write_all(request.as_bytes()).and_then(|_| input.write_all(b"\n"))
                    .and_then(|_| input.flush()).map_err(|_| Fault::Io)
                    .and_then(|_| read_frame(&mut output))
                    .and_then(|line| if output.buffer().is_empty() { Ok(line) } else { Err(Fault::Protocol) });
                let failed = reply.is_err();
                if reply_tx.send(reply).is_err() || failed { break; }
            }
        });
        Ok(Self { child, requests: Some(tx), replies: Some(rx), io_thread: Some(handle),
            failed: false, closed: false, requests_enqueued: 0, request_bytes_enqueued: 0,
            response_bytes_received: 0, child_reaped: false, io_thread_joined: false })
    }
    pub fn pid(&self) -> u32 { self.child.id() }
    pub fn reject(&mut self) { self.failed = true; }
    pub fn exchange(&mut self, request: &str, timeout: Duration) -> Result<String, Fault> {
        if self.failed || self.closed { return Err(Fault::Closed); }
        if request.is_empty() || request.len() > FRAME_LIMIT ||
            !request.bytes().all(|b| (b' '..=b'~').contains(&b)) || timeout.is_zero() {
            self.failed = true;
            return Err(Fault::Protocol);
        }
        let deadline = Instant::now().checked_add(timeout).ok_or(Fault::Protocol)?;
        self.requests.as_ref().ok_or(Fault::Closed)?.try_send(request.to_owned()).map_err(|_| Fault::Closed)?;
        self.requests_enqueued += 1;
        self.request_bytes_enqueued += (request.len() + 1) as u64;
        let remaining = deadline.saturating_duration_since(Instant::now());
        let result = self.replies.as_ref().ok_or(Fault::Closed)?.recv_timeout(remaining)
            .map_err(|e| match e { mpsc::RecvTimeoutError::Timeout => Fault::Timeout,
                                  mpsc::RecvTimeoutError::Disconnected => Fault::Closed })
            .and_then(|r| r);
        match &result {
            Ok(line) => self.response_bytes_received += (line.len() + 1) as u64,
            Err(_) => self.failed = true,
        }
        result
    }
    /// Kill/reap the direct child, close channels and join its I/O thread.
    /// Returns false rather than hiding a cleanup failure. Not descendant isolation.
    pub fn shutdown(&mut self) -> bool {
        if self.closed { return self.child_reaped && self.io_thread_joined; }
        self.closed = true;
        self.requests.take();
        let _ = self.child.kill();
        self.child_reaped = self.child.wait().is_ok();
        self.replies.take();
        if let Some(handle) = self.io_thread.take() {
            let until = Instant::now() + Duration::from_millis(250);
            while !handle.is_finished() && Instant::now() < until { thread::sleep(Duration::from_millis(1)); }
            self.io_thread_joined = handle.is_finished() && handle.join().is_ok();
        }
        self.child_reaped && self.io_thread_joined
    }
}
impl Drop for Session { fn drop(&mut self) { self.shutdown(); } }

#[cfg(test)]
mod tests {
    use super::*;
    #[test] fn bounded_valid_frame() { assert_eq!(read_frame(&mut &b"ACT 1 wait\n"[..]), Ok("ACT 1 wait".into())); }
    #[test] fn empty_and_partial_eof_are_distinct() {
        assert_eq!(read_frame(&mut &b""[..]), Err(Fault::Eof));
        assert_eq!(read_frame(&mut &b"ACT 1"[..]), Err(Fault::Truncated));
    }
    #[test] fn oversized_unterminated_frame_is_bounded() { assert_eq!(read_frame(&mut &vec![b'a'; 10000][..]), Err(Fault::Oversize)); }
    #[test] fn binary_and_cr_are_rejected() {
        assert_eq!(read_frame(&mut &b"\xff\n"[..]), Err(Fault::Encoding));
        assert_eq!(read_frame(&mut &b"ACK 0\r\n"[..]), Err(Fault::Encoding));
    }
    #[test] fn empty_line_is_invalid() { assert_eq!(read_frame(&mut &b"\n"[..]), Err(Fault::Protocol)); }
    #[test] fn limit_is_exact() {
        let mut b = vec![b'a'; FRAME_LIMIT]; b.push(b'\n');
        assert_eq!(read_frame(&mut &b[..]).unwrap().len(), FRAME_LIMIT);
    }
}
