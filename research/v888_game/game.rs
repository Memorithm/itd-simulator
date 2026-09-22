//! Two-door environment reference, not a V888 learner or a neural simulation.
//! The policy sees only Observation, never Episode, target, trial ID or RNG state.
//! Batch stdin is an administrator/test surface, NOT the future learner interface.
#![forbid(unsafe_code)]

use std::io::{self, BufRead, Write};

const MAX_DELAY: usize = 64;

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Condition { Memory, Logic, Combined }
impl Condition {
    fn name(self) -> &'static str {
        match self { Self::Memory => "memory", Self::Logic => "logic", Self::Combined => "combined" }
    }
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Phase { CueA, Distractor, CueB, Choice }
impl Phase {
    fn name(self) -> &'static str {
        match self { Self::CueA => "cue_a", Self::Distractor => "distractor", Self::CueB => "cue_b", Self::Choice => "choice" }
    }
}

/// Entire candidate-visible payload. None is distinct from a visible false bit.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct Observation {
    pub condition: Condition,
    pub phase: Phase,
    pub a: Option<bool>,
    pub b: Option<bool>,
    pub rule: Option<bool>,
    pub distractor: Option<bool>,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Action { Wait, Door(bool), Missing, Invalid, Timeout }
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Mode { Training, Evaluation }
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Reason { Correct, Wrong, EarlyAction, MissingAction, InvalidAction, Timeout }
impl Reason {
    fn name(self) -> &'static str {
        match self {
            Self::Correct => "correct", Self::Wrong => "wrong", Self::EarlyAction => "early_action",
            Self::MissingAction => "missing_action", Self::InvalidAction => "invalid_action", Self::Timeout => "timeout",
        }
    }
}
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct Outcome {
    pub success: bool,
    pub reason: Reason,
    /// Post-action feedback only. Standard evaluation never exposes feedback.
    pub training_feedback: Option<bool>,
}

/// Private environment state. No getter exposes the target or future clues.
pub struct Episode {
    condition: Condition,
    a: bool,
    b: bool,
    rule: bool,
    distractors: Vec<bool>,
    mode: Mode,
    step: usize,
    finished: bool,
}
impl Episode {
    pub fn new(condition: Condition, a: bool, b: bool, rule: bool, distractors: Vec<bool>, mode: Mode) -> Result<Self, &'static str> {
        if distractors.len() > MAX_DELAY { return Err("delay exceeds the 64-update environment limit"); }
        Ok(Self { condition, a, b, rule, distractors, mode, step: 0, finished: false })
    }
    pub fn observe(&self) -> Result<Observation, &'static str> {
        if self.finished { return Err("episode already terminated"); }
        let delay = self.distractors.len();
        let phase = if self.step == 0 { Phase::CueA }
            else if self.step <= delay { Phase::Distractor }
            else if self.step == delay + 1 { Phase::CueB }
            else { Phase::Choice };
        let mut o = Observation { condition: self.condition, phase, a: None, b: None, rule: None, distractor: None };
        match phase {
            Phase::CueA if self.condition != Condition::Logic => o.a = Some(self.a),
            Phase::Distractor => o.distractor = Some(self.distractors[self.step - 1]),
            Phase::CueB if self.condition == Condition::Combined => o.b = Some(self.b),
            Phase::Choice => match self.condition {
                Condition::Memory => {},
                Condition::Logic => { o.a = Some(self.a); o.b = Some(self.b); o.rule = Some(self.rule); },
                Condition::Combined => o.rule = Some(self.rule),
            },
            _ => {},
        }
        Ok(o)
    }
    fn target(&self) -> bool {
        match self.condition {
            Condition::Memory => self.a,
            // Conditional definition, independent of the control policy's XOR spelling.
            _ => if self.a == self.b { self.rule } else { !self.rule },
        }
    }
    fn finish(&mut self, reason: Reason) -> Outcome {
        self.finished = true;
        let success = reason == Reason::Correct;
        Outcome { success, reason, training_feedback: (self.mode == Mode::Training).then_some(success) }
    }
    /// One observation is followed by one action. No retry can replace a failure.
    pub fn apply(&mut self, action: Action) -> Result<Option<Outcome>, &'static str> {
        let o = self.observe()?;
        if o.phase != Phase::Choice {
            return match action {
                Action::Wait => { self.step += 1; Ok(None) },
                Action::Door(_) => Ok(Some(self.finish(Reason::EarlyAction))),
                Action::Missing => Ok(Some(self.finish(Reason::MissingAction))),
                Action::Invalid => Ok(Some(self.finish(Reason::InvalidAction))),
                Action::Timeout => Ok(Some(self.finish(Reason::Timeout))),
            };
        }
        let reason = match action {
            Action::Door(value) => if value == self.target() { Reason::Correct } else { Reason::Wrong },
            Action::Wait | Action::Missing => Reason::MissingAction,
            Action::Invalid => Reason::InvalidAction,
            Action::Timeout => Reason::Timeout,
        };
        Ok(Some(self.finish(reason)))
    }
}

/// Interface deliberately excludes environment state and feedback during an episode.
pub trait Policy {
    fn reset(&mut self);
    fn act(&mut self, observation: Observation) -> Action;
    fn persistent_state_bytes(&self) -> usize;
}

/// Hand-written exact reference, NOT learned behavior. Stores two optional bits.
#[derive(Default)]
pub struct ExactPolicy { a: Option<bool>, b: Option<bool> }
impl Policy for ExactPolicy {
    fn reset(&mut self) { self.a = None; self.b = None; }
    fn act(&mut self, o: Observation) -> Action {
        if let Some(a) = o.a { self.a = Some(a); }
        if let Some(b) = o.b { self.b = Some(b); }
        if o.phase != Phase::Choice { return Action::Wait; }
        match o.condition {
            Condition::Memory => self.a.map_or(Action::Missing, Action::Door),
            _ => match (self.a, self.b, o.rule) {
                (Some(a), Some(b), Some(r)) => Action::Door(a ^ b ^ r),
                _ => Action::Missing,
            },
        }
    }
    fn persistent_state_bytes(&self) -> usize { std::mem::size_of::<Self>() }
}

/// Zero-state diagnostic. Solves simultaneous logic but cannot remember hidden clues.
pub struct CurrentOnly;
impl Policy for CurrentOnly {
    fn reset(&mut self) {}
    fn act(&mut self, o: Observation) -> Action {
        if o.phase != Phase::Choice { return Action::Wait; }
        match (o.a, o.b, o.rule) {
            (Some(a), Some(b), Some(r)) => Action::Door(a ^ b ^ r),
            _ => Action::Door(false),
        }
    }
    fn persistent_state_bytes(&self) -> usize { 0 }
}

struct ForcedPolicy { name: String }
impl Policy for ForcedPolicy {
    fn reset(&mut self) {}
    fn act(&mut self, o: Observation) -> Action {
        if self.name == "early" { return Action::Door(false); }
        if o.phase != Phase::Choice { return Action::Wait; }
        match self.name.as_str() {
            "left" => Action::Door(false), "right" => Action::Door(true),
            "missing" => Action::Missing, "invalid" => Action::Invalid,
            "timeout" => Action::Timeout, _ => Action::Invalid,
        }
    }
    fn persistent_state_bytes(&self) -> usize { 0 }
}

fn bit(text: &str) -> Result<bool, &'static str> {
    match text { "0" => Ok(false), "1" => Ok(true), _ => Err("expected an exact 0/1 bit") }
}
fn maybe(value: Option<bool>) -> &'static str {
    match value { Some(false) => "0", Some(true) => "1", None => "null" }
}
fn observation_json(o: Observation) -> String {
    format!("{{\"condition\":\"{}\",\"phase\":\"{}\",\"a\":{},\"b\":{},\"rule\":{},\"distractor\":{}}}",
        o.condition.name(), o.phase.name(), maybe(o.a), maybe(o.b), maybe(o.rule), maybe(o.distractor))
}
fn action_json(action: Action) -> String {
    match action {
        Action::Door(value) => format!("\"door_{}\"", u8::from(value)),
        Action::Wait => "\"wait\"".into(), Action::Missing => "\"missing\"".into(),
        Action::Invalid => "\"invalid\"".into(), Action::Timeout => "\"timeout\"".into(),
    }
}

/// Audit batch record: condition A B R distractor-bits-or-dash policy train|eval.
/// This fixture surface must not be forwarded to a learner.
fn execute_record(line: &str) -> Result<String, &'static str> {
    let fields: Vec<_> = line.split_whitespace().collect();
    if fields.len() != 7 { return Err("expected exactly seven administrative fixture fields"); }
    let condition = match fields[0] { "memory" => Condition::Memory, "logic" => Condition::Logic,
        "combined" => Condition::Combined, _ => return Err("unknown condition") };
    let mode = match fields[6] { "train" => Mode::Training, "eval" => Mode::Evaluation, _ => return Err("unknown feedback mode") };
    let noise = if fields[4] == "-" { Vec::new() } else {
        if fields[4].len() > MAX_DELAY { return Err("delay exceeds limit"); }
        fields[4].chars().map(|c| match c { '0' => Ok(false), '1' => Ok(true), _ => Err("invalid distractor bit") }).collect::<Result<Vec<_>, _>>()?
    };
    let mut episode = Episode::new(condition, bit(fields[1])?, bit(fields[2])?, bit(fields[3])?, noise, mode)?;
    let mut policy: Box<dyn Policy> = match fields[5] {
        "exact" => Box::<ExactPolicy>::default(), "current" => Box::new(CurrentOnly),
        "left" | "right" | "missing" | "invalid" | "timeout" | "early" => Box::new(ForcedPolicy { name: fields[5].into() }),
        _ => return Err("unknown diagnostic policy"),
    };
    policy.reset();
    let state_bytes = policy.persistent_state_bytes();
    let mut steps = Vec::new();
    let mut choice_attempts = 0;
    let outcome = loop {
        let observation = episode.observe()?;
        let action = policy.act(observation);
        if observation.phase == Phase::Choice { choice_attempts += 1; }
        steps.push(format!("{{\"observation\":{},\"action\":{}}}", observation_json(observation), action_json(action)));
        if let Some(outcome) = episode.apply(action)? { break outcome; }
    };
    Ok(format!("{{\"schema\":\"itd-two-doors-trace-v1\",\"steps\":[{}],\"success\":{},\"reason\":\"{}\",\"training_feedback\":{},\"observation_count\":{},\"choice_attempts\":{},\"policy_state_bytes\":{},\"learning_performed\":false}}",
        steps.join(","), outcome.success, outcome.reason.name(), maybe(outcome.training_feedback), steps.len(), choice_attempts, state_bytes))
}
fn run() -> Result<(), String> {
    if std::env::args().skip(1).collect::<Vec<_>>() != ["--batch"] { return Err("usage: two-doors --batch (administrative diagnostic fixture stream)".into()); }
    let stdin = io::stdin();
    let mut input = stdin.lock();
    let stdout = io::stdout();
    let mut output = io::BufWriter::new(stdout.lock());
    loop {
        let mut bytes = Vec::with_capacity(128);
        // Bound malformed administrative records without allocating an arbitrary line.
        loop {
            let available = input.fill_buf().map_err(|e| e.to_string())?;
            if available.is_empty() { break; }
            let count = available.iter().position(|&b| b == b'\n').map_or(available.len(), |i| i + 1);
            if bytes.len() + count > 256 { return Err("administrative record exceeds 256 bytes".into()); }
            bytes.extend_from_slice(&available[..count]);
            let newline = available[count - 1] == b'\n';
            input.consume(count);
            if newline { break; }
        }
        if bytes.is_empty() { break; }
        let text = std::str::from_utf8(&bytes).map_err(|_| "non-UTF8 administrative record")?;
        let record = execute_record(text).map_err(str::to_owned)?;
        writeln!(output, "{record}").map_err(|e| e.to_string())?;
        output.flush().map_err(|e| e.to_string())?;
    }
    Ok(())
}
fn main() {
    if let Err(error) = run() { eprintln!("protocol_error: {error}"); std::process::exit(2); }
}

#[cfg(test)]
mod tests {
    use super::*;
    fn game(c: Condition, a: bool, b: bool, r: bool, d: usize, m: Mode) -> Episode {
        Episode::new(c, a, b, r, vec![true; d], m).unwrap()
    }
    fn finish(g: &mut Episode, p: &mut dyn Policy) -> Outcome {
        p.reset();
        loop { let o = g.observe().unwrap(); if let Some(end) = g.apply(p.act(o)).unwrap() { return end; } }
    }
    #[test]
    fn exact_control_covers_all_bits_and_delays() {
        let mut p = ExactPolicy::default();
        for c in [Condition::Memory, Condition::Logic, Condition::Combined] {
            for bits in 0..8 { for d in [0, 1, 2, 4, 16, 32, 64] {
                assert!(finish(&mut game(c, bits & 1 != 0, bits & 2 != 0, bits & 4 != 0, d, Mode::Evaluation), &mut p).success);
            } }
        }
    }
    #[test]
    fn combined_choice_hides_both_clues() {
        let mut g = game(Condition::Combined, true, false, true, 2, Mode::Evaluation);
        for _ in 0..4 { assert_eq!(g.apply(Action::Wait).unwrap(), None); }
        let o = g.observe().unwrap();
        assert_eq!((o.phase, o.a, o.b, o.rule, o.distractor), (Phase::Choice, None, None, Some(true), None));
    }
    #[test]
    fn future_clues_do_not_change_prefix() {
        let mut left = game(Condition::Combined, true, false, false, 3, Mode::Evaluation);
        let mut right = game(Condition::Combined, true, true, true, 3, Mode::Evaluation);
        for _ in 0..4 { assert_eq!(left.observe(), right.observe()); left.apply(Action::Wait).unwrap(); right.apply(Action::Wait).unwrap(); }
    }
    #[test]
    fn false_cue_is_not_missing() {
        assert_eq!(game(Condition::Memory, false, false, false, 0, Mode::Evaluation).observe().unwrap().a, Some(false));
    }
    #[test]
    fn premature_door_terminates_episode() {
        let mut g = game(Condition::Combined, false, false, false, 0, Mode::Training);
        let end = g.apply(Action::Door(false)).unwrap().unwrap();
        assert_eq!(end.reason, Reason::EarlyAction); assert!(!end.success);
        assert!(g.observe().is_err()); assert!(g.apply(Action::Door(false)).is_err());
    }
    #[test]
    fn evaluation_has_no_feedback() {
        let end = finish(&mut game(Condition::Memory, true, false, false, 0, Mode::Evaluation), &mut ExactPolicy::default());
        assert_eq!(end.training_feedback, None);
    }
    #[test]
    fn training_feedback_arrives_only_after_action() {
        let mut g = game(Condition::Memory, true, false, false, 0, Mode::Training);
        assert_eq!(g.apply(Action::Wait).unwrap(), None); assert_eq!(g.apply(Action::Wait).unwrap(), None);
        assert_eq!(g.apply(Action::Door(true)).unwrap().unwrap().training_feedback, Some(true));
    }
    #[test]
    fn missing_invalid_timeout_are_failed_attempts() {
        for (a, expected) in [(Action::Missing, Reason::MissingAction), (Action::Invalid, Reason::InvalidAction), (Action::Timeout, Reason::Timeout), (Action::Wait, Reason::MissingAction)] {
            let mut g = game(Condition::Memory, false, false, false, 0, Mode::Evaluation);
            g.apply(Action::Wait).unwrap(); g.apply(Action::Wait).unwrap();
            let end = g.apply(a).unwrap().unwrap(); assert_eq!(end.reason, expected); assert!(!end.success);
        }
    }
    #[test]
    fn reset_erases_transient_reference_memory() {
        let mut p = ExactPolicy::default(); let g = game(Condition::Memory, true, false, false, 0, Mode::Evaluation);
        p.act(g.observe().unwrap()); p.reset();
        assert_eq!(p.act(Observation { condition: Condition::Memory, phase: Phase::Choice, a: None, b: None, rule: None, distractor: None }), Action::Missing);
    }
    #[test]
    fn bounded_environment_and_strict_fixture_parser() {
        assert!(Episode::new(Condition::Memory, false, false, false, vec![false; 65], Mode::Evaluation).is_err());
        for bad in ["memory 2 0 0 - exact eval", "memory 0 0 0 01x exact eval", "memory 0 0 0 - unknown eval", "memory 0 0 0 - exact final", "memory 0 0 0 - exact eval extra"] { assert!(execute_record(bad).is_err()); }
    }
    #[test]
    fn stateless_control_is_balanced_on_hidden_clue_tasks() {
        for c in [Condition::Memory, Condition::Combined] {
            let mut correct = 0;
            for bits in 0..8 { correct += usize::from(finish(&mut game(c, bits & 1 != 0, bits & 2 != 0, bits & 4 != 0, 2, Mode::Evaluation), &mut CurrentOnly).success); }
            assert_eq!(correct, 4);
        }
    }
    #[test]
    fn terminal_outcome_cannot_be_replaced() {
        let mut g = game(Condition::Memory, false, false, false, 0, Mode::Evaluation);
        g.apply(Action::Wait).unwrap(); g.apply(Action::Wait).unwrap();
        assert_eq!(g.apply(Action::Door(true)).unwrap().unwrap().reason, Reason::Wrong);
        assert!(g.apply(Action::Door(false)).is_err());
    }
}
