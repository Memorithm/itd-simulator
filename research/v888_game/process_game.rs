//! GAME-IO1: causal, bounded external worker bridge. No neural model or learning.
#![forbid(unsafe_code)]
#[allow(dead_code)]
#[path = "game.rs"]
mod game;
mod transport;

use game::{Action, Condition, Episode, ExactPolicy, CurrentOnly, Mode, Observation, Phase, Policy, Reason};
use std::io::{self, BufReader, Write};
use std::path::{Path, PathBuf};
use std::time::{Duration, Instant};
use transport::{Fault, Session};

fn bit(s: &str) -> Result<bool, String> {
    match s { "0" => Ok(false), "1" => Ok(true), _ => Err("expected 0 or 1".into()) }
}
fn optional(s: &str) -> Result<Option<bool>, String> { if s == "-" { Ok(None) } else { bit(s).map(Some) } }
fn shown(b: Option<bool>) -> &'static str { match b { Some(true) => "1", Some(false) => "0", None => "-" } }
fn condition(s: &str) -> Result<Condition, String> {
    match s { "memory" => Ok(Condition::Memory), "logic" => Ok(Condition::Logic), "combined" => Ok(Condition::Combined), _ => Err("unknown condition".into()) }
}
fn cond(c: Condition) -> &'static str { match c { Condition::Memory => "memory", Condition::Logic => "logic", Condition::Combined => "combined" } }
fn phase(p: Phase) -> &'static str { match p { Phase::CueA => "cue_a", Phase::CueB => "cue_b", Phase::Distractor => "distractor", Phase::Choice => "choice" } }
fn action(a: Action) -> &'static str {
    match a { Action::Wait => "wait", Action::Door(false) => "0", Action::Door(true) => "1",
        Action::Missing => "missing", Action::Invalid => "invalid", Action::Timeout => "timeout" }
}
fn reason(r: Reason) -> &'static str {
    match r { Reason::Correct => "correct", Reason::Wrong => "wrong", Reason::EarlyAction => "early_action",
        Reason::MissingAction => "missing_action", Reason::InvalidAction => "invalid_action", Reason::Timeout => "timeout" }
}
fn observation_line(seq: u64, o: Observation) -> String {
    format!("OBS {seq} {} {} {} {} {} {}", cond(o.condition), phase(o.phase), shown(o.a), shown(o.b), shown(o.rule), shown(o.distractor))
}
fn decode_observation(s: &str) -> Result<(u64, Observation), String> {
    let f: Vec<_> = s.split(' ').collect();
    if f.len() != 8 || f[0] != "OBS" { return Err("bad observation frame".into()); }
    let seq: u64 = f[1].parse().map_err(|_| "bad sequence")?;
    if seq == 0 || seq.to_string() != f[1] { return Err("noncanonical sequence".into()); }
    let p = match f[3] { "cue_a" => Phase::CueA, "cue_b" => Phase::CueB, "distractor" => Phase::Distractor, "choice" => Phase::Choice, _ => return Err("bad phase".into()) };
    Ok((seq, Observation { condition: condition(f[2])?, phase: p, a: optional(f[4])?, b: optional(f[5])?, rule: optional(f[6])?, distractor: optional(f[7])? }))
}
fn parse_action(s: &str, expected: u64) -> Result<Action, Fault> {
    let f: Vec<_> = s.split(' ').collect();
    if f.len() != 3 || f[0] != "ACT" || f[1] != expected.to_string() { return Err(Fault::Protocol); }
    match f[2] { "wait" => Ok(Action::Wait), "0" => Ok(Action::Door(false)), "1" => Ok(Action::Door(true)),
        "missing" => Ok(Action::Missing), _ => Err(Fault::Protocol) }
}
fn failure(f: Fault) -> Action { match f { Fault::Timeout => Action::Timeout, Fault::Eof => Action::Missing, _ => Action::Invalid } }
fn js(s: &str) -> String { format!("\"{}\"", s.replace('\\', "\\\\").replace('"', "\\\"")) }
fn array(values: &[String]) -> String { format!("[{}]", values.iter().map(|s| js(s)).collect::<Vec<_>>().join(",")) }

/// Administrative fixtures stay in this process. Worker argv/env/stdin never get them.
fn execute(line: &str, executable: &Path, worker_args: &[String], cwd: &Path, timeout: Duration) -> Result<String, String> {
    let fields: Vec<_> = line.split(' ').collect();
    if fields.len() != 6 { return Err("expected: condition A B R distractors-or-dash train|eval".into()); }
    let c = condition(fields[0])?;
    let noise = if fields[4] == "-" { Vec::new() } else {
        if fields[4].len() > 64 { return Err("delay exceeds 64".into()); }
        fields[4].chars().map(|b| match b { '0' => Ok(false), '1' => Ok(true), _ => Err("bad distractor") }).collect::<Result<Vec<_>, _>>()?
    };
    let mode = match fields[5] { "train" => Mode::Training, "eval" => Mode::Evaluation, _ => return Err("bad mode".into()) };
    let mut episode = Episode::new(c, bit(fields[1])?, bit(fields[2])?, bit(fields[3])?, noise, mode)?;
    let start = Instant::now();
    let mut session = match Session::spawn(executable, worker_args, cwd) {
        Ok(s) => s,
        Err(_) => return Ok("{\"schema\":\"itd-two-doors-io-v1\",\"success\":false,\"reason\":\"invalid_action\",\"fault\":\"spawn\",\"spawned\":false,\"child_reaped\":true,\"io_thread_joined\":true,\"requests\":[],\"responses\":[],\"actions\":[],\"learning_performed\":false}".into()),
    };
    let mut requests = vec!["RESET 0 v1".to_string()];
    let mut responses = Vec::new();
    let mut actions = Vec::new();
    let mut fault = None;
    match session.exchange(&requests[0], Duration::from_millis(1000)) {
        Ok(s) if s == "ACK 0 v1" => responses.push(s),
        Ok(_) => { session.reject(); fault = Some(Fault::Protocol); },
        Err(e) => fault = Some(e),
    }
    let mut seq = 0;
    let outcome = loop {
        let observation = episode.observe()?;
        let a = if let Some(e) = fault { failure(e) } else {
            seq += 1;
            let request = observation_line(seq, observation);
            requests.push(request.clone());
            match session.exchange(&request, timeout).and_then(|reply| {
                let a = parse_action(&reply, seq)?;
                responses.push(reply);
                Ok(a)
            }) {
                Ok(a) => a,
                Err(e) => { session.reject(); fault = Some(e); failure(e) },
            }
        };
        actions.push(action(a).to_string());
        if let Some(outcome) = episode.apply(a)? { break outcome; }
    };
    // Failed transports receive no follow-up; evaluation never sends feedback.
    let mut feedback_delivered = false;
    let mut feedback_fault = None;
    if fault.is_none() {
        if let Some(value) = outcome.training_feedback {
            seq += 1;
            let request = format!("FEEDBACK {seq} {}", u8::from(value));
            requests.push(request.clone());
            match session.exchange(&request, timeout) {
                Ok(s) if s == format!("ACK {seq}") => { responses.push(s); feedback_delivered = true; },
                Ok(_) => feedback_fault = Some(Fault::Protocol),
                Err(e) => feedback_fault = Some(e),
            }
        }
    }
    let pid = session.pid();
    let cleaned = session.shutdown();
    let report = format!("{{\"schema\":\"itd-two-doors-io-v1\",\"success\":{},\"reason\":{},\"fault\":{},\"feedback_fault\":{},\"feedback_delivered\":{},\"spawned\":true,\"child_pid\":{},\"child_reaped\":{},\"io_thread_joined\":{},\"requests\":{},\"responses\":{},\"actions\":{},\"request_bytes_enqueued\":{},\"response_bytes_received\":{},\"requests_enqueued\":{},\"elapsed_us\":{},\"learning_performed\":false}}",
        outcome.success, js(reason(outcome.reason)), fault.map_or("null".to_string(), |f| js(f.name())),
        feedback_fault.map_or("null".to_string(), |f| js(f.name())), feedback_delivered, pid,
        session.child_reaped, session.io_thread_joined, array(&requests), array(&responses), array(&actions),
        session.request_bytes_enqueued, session.response_bytes_received, session.requests_enqueued, start.elapsed().as_micros());
    // Refuse to continue a batch after unsuccessful lifecycle cleanup.
    if !cleaned { return Err(format!("worker cleanup failed: {report}")); }
    Ok(report)
}

fn worker(kind: &str) -> Result<(), String> {
    let mut input = BufReader::new(io::stdin().lock());
    let mut output = io::stdout().lock();
    let mut exact = ExactPolicy::default();
    let mut current = CurrentOnly;
    let mut next = 1_u64;
    if kind == "hang_reset" { loop { std::thread::sleep(Duration::from_secs(60)); } }
    let reset = transport::read_frame(&mut input).map_err(|f| f.name())?;
    if reset != "RESET 0 v1" { return Err("expected reset".into()); }
    exact.reset(); current.reset();
    writeln!(output, "ACK 0 v1").map_err(|e| e.to_string())?;
    output.flush().map_err(|e| e.to_string())?;
    loop {
        let line = match transport::read_frame(&mut input) { Ok(s) => s, Err(Fault::Eof) => return Ok(()), Err(f) => return Err(f.name().into()) };
        if line.starts_with("FEEDBACK ") {
            let f: Vec<_> = line.split(' ').collect();
            if f.len() != 3 || f[1] != next.to_string() { return Err("bad feedback sequence".into()); }
            bit(f[2])?;
            // Acknowledged but intentionally NOT learned by these diagnostic workers.
            writeln!(output, "ACK {next}").map_err(|e| e.to_string())?;
            output.flush().map_err(|e| e.to_string())?;
            next += 1;
            continue;
        }
        let (seq, o) = decode_observation(&line)?;
        if seq != next { return Err("bad observation sequence".into()); }
        next += 1;
        if kind == "env_probe" && std::env::var_os("ITD_HIDDEN_CANARY").is_some() { return Err("inherited ambient environment".into()); }
        if kind == "pid_probe" && !Path::new(".").exists() { return Err("no cwd".into()); }
        let choice = o.phase == Phase::Choice;
        if choice {
            match kind {
                "hang" => loop { std::thread::sleep(Duration::from_secs(60)); },
                "exit" => std::process::exit(7),
                "truncated" => { write!(output, "ACT {seq} 1").map_err(|e| e.to_string())?; output.flush().map_err(|e| e.to_string())?; return Ok(()); },
                "oversize" => { writeln!(output, "{}", "x".repeat(1024)).map_err(|e| e.to_string())?; output.flush().map_err(|e| e.to_string())?; continue; },
                "stale" => { writeln!(output, "ACT {} 1", seq - 1).map_err(|e| e.to_string())?; output.flush().map_err(|e| e.to_string())?; continue; },
                "invalid" => { writeln!(output, "ACT {seq} banana").map_err(|e| e.to_string())?; output.flush().map_err(|e| e.to_string())?; continue; },
                _ => {},
            }
        }
        let a = if kind == "early" { Action::Door(false) }
            else if kind == "current" { current.act(o) }
            else { exact.act(o) };
        writeln!(output, "ACT {seq} {}", action(a)).map_err(|e| e.to_string())?;
        output.flush().map_err(|e| e.to_string())?;
    }
}

fn run() -> Result<(), String> {
    let args: Vec<_> = std::env::args().skip(1).collect();
    if args.len() == 2 && args[0] == "--worker" { return worker(&args[1]); }
    if args.len() != 4 || !["--batch", "--external"].contains(&args[0].as_str()) {
        return Err("usage: process-game --batch diagnostic-kind deadline-ms empty-worker-directory; or --external absolute-worker-path deadline-ms empty-worker-directory".into());
    }
    let ms: u64 = args[2].parse().map_err(|_| "bad deadline")?;
    if !(1..=5000).contains(&ms) { return Err("deadline must be 1..5000 ms".into()); }
    let cwd = PathBuf::from(&args[3]).canonicalize().map_err(|e| e.to_string())?;
    if !cwd.is_dir() || cwd.read_dir().map_err(|e| e.to_string())?.next().is_some() { return Err("worker directory must exist and be empty".into()); }
    let (executable, worker_args) = if args[0] == "--batch" {
        let kinds = ["exact", "current", "early", "hang", "hang_reset", "exit", "truncated", "oversize", "stale", "invalid", "env_probe", "pid_probe"];
        if !kinds.contains(&args[1].as_str()) { return Err("unknown diagnostic worker".into()); }
        (std::env::current_exe().map_err(|e| e.to_string())?, vec!["--worker".into(), args[1].clone()])
    } else {
        let path = PathBuf::from(&args[1]);
        if !path.is_absolute() { return Err("external executable must be absolute".into()); }
        (path, Vec::new())
    };
    let mut input = BufReader::new(io::stdin().lock());
    let mut output = io::stdout().lock();
    loop {
        let line = match transport::read_frame(&mut input) { Ok(s) => s, Err(Fault::Eof) => break, Err(f) => return Err(f.name().into()) };
        let report = execute(&line, &executable, &worker_args, &cwd, Duration::from_millis(ms))?;
        writeln!(output, "{report}").map_err(|e| e.to_string())?;
        output.flush().map_err(|e| e.to_string())?;
    }
    Ok(())
}
fn main() { if let Err(error) = run() { eprintln!("bridge_error: {error}"); std::process::exit(2); } }

#[cfg(test)]
mod tests {
    use super::*;
    #[test] fn hidden_choice_payload_has_no_past_clues() {
        let o = Observation { condition: Condition::Combined, phase: Phase::Choice, a: None, b: None, rule: Some(true), distractor: None };
        assert_eq!(observation_line(9, o), "OBS 9 combined choice - - 1 -");
        assert_eq!(decode_observation(&observation_line(9,o)).unwrap(), (9,o));
    }
    #[test] fn stale_and_noncanonical_actions_are_rejected() {
        for s in ["ACT 8 1", "ACT 09 1", "ACT +9 1", "ACT 9 1 extra", "ACT 9\t1", "ACT 9 banana"] { assert_eq!(parse_action(s,9),Err(Fault::Protocol)); }
    }
    #[test] fn valid_actions_are_exact() {
        assert_eq!(parse_action("ACT 9 0",9),Ok(Action::Door(false)));
        assert_eq!(parse_action("ACT 9 wait",9),Ok(Action::Wait));
    }
    #[test] fn missing_bit_is_not_false() { assert_eq!(optional("-"),Ok(None)); assert_eq!(optional("0"),Ok(Some(false))); }
    #[test] fn request_roundtrip_all_optional_values() {
        for a in [None,Some(false),Some(true)] { for b in [None,Some(false),Some(true)] {
            let o=Observation { condition:Condition::Logic, phase:Phase::Choice, a,b,rule:Some(false),distractor:None };
            assert_eq!(decode_observation(&observation_line(1,o)).unwrap().1,o);
        } }
    }
}
