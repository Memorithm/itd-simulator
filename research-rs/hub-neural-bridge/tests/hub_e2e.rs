//! Actual HTTP Hub daemon, immutable artifact transfer and actual ITD process.
use itd_hub_neural_bridge::{
    HUB_SHA, ITD_SHA, NEURAL_SHA, Observation, fixture, request_for, sha256,
};
use serde_json::{Value, json};
use std::{
    fs,
    io::{Read, Write},
    net::{TcpListener, TcpStream},
    path::PathBuf,
    process::{Child, Command, Stdio},
    time::{Duration, Instant},
};

struct Daemon {
    child: Child,
    root: PathBuf,
}
impl Drop for Daemon {
    fn drop(&mut self) {
        let _ = self.child.kill();
        let _ = self.child.wait();
        let _ = fs::remove_dir_all(&self.root);
    }
}

fn http(port: u16, method: &str, path: &str, bytes: &[u8]) -> (u16, Value) {
    let mut stream = TcpStream::connect(("127.0.0.1", port)).unwrap();
    stream
        .set_read_timeout(Some(Duration::from_secs(30)))
        .unwrap();
    stream
        .set_write_timeout(Some(Duration::from_secs(30)))
        .unwrap();
    let headers = format!(
        "{method} {path} HTTP/1.0\r\nHost: 127.0.0.1\r\nContent-Type: application/json\r\nx-scirust-artifact-name: development-fields\r\nContent-Length: {}\r\n\r\n",
        bytes.len()
    );
    stream.write_all(headers.as_bytes()).unwrap();
    stream.write_all(bytes).unwrap();
    let mut reply = Vec::new();
    stream.take(1_048_577).read_to_end(&mut reply).unwrap();
    assert!(reply.len() <= 1_048_576);
    let text = String::from_utf8(reply).unwrap();
    let (headers, body) = text.split_once("\r\n\r\n").unwrap();
    let status = headers.split_whitespace().nth(1).unwrap().parse().unwrap();
    (status, serde_json::from_str(body).unwrap())
}

fn call(port: u16, method: &str, path: &str, body: &Value, expected: u16) -> Value {
    let bytes = if method == "GET" {
        vec![]
    } else {
        serde_json::to_vec(body).unwrap()
    };
    let (status, reply) = http(port, method, path, &bytes);
    assert_eq!(status, expected, "{reply}");
    reply
}

fn submit(port: u16, input: &Value, bytes: &[u8]) -> Value {
    let spec = json!({"schema_version":1,"run_spec":{
        "component":"1adbea71-7200-4000-8000-000000000001", "capability":"itd.neural.development",
        "parameters":request_for(bytes), "inputs":[{"name":"fields","artifact":input["id"]}], "timeout_ms":5000}});
    let submitted = call(port, "POST", "/api/v1/runs", &spec, 201);
    let id = submitted["run"]["id"].as_str().unwrap();
    let result = call(port, "POST", "/api/v1/executions", &json!(id), 200);
    assert_eq!(result["state"], "succeeded", "{result}");
    assert_eq!(result["outcome"]["executor_backend"], "process");
    assert_eq!(result["outcome"]["exit_code"], 0);
    assert_eq!(result["outcome"]["inputs"][0]["artifact"], input["id"]);
    assert_eq!(result["outcome"]["inputs"][0]["digest"], input["digest"]);
    result
}

fn observation(port: u16, run: &Value) -> (Value, Value, Vec<u8>) {
    let output = run["outcome"]["outputs"]
        .as_array()
        .unwrap()
        .iter()
        .find(|x| x["name"] == "file:observation")
        .unwrap();
    let id = output["artifact"].as_str().unwrap();
    let artifact = call(
        port,
        "GET",
        &format!("/api/v1/artifacts/{id}?include=content"),
        &Value::Null,
        200,
    );
    let bytes = artifact["content_text"]
        .as_str()
        .unwrap()
        .as_bytes()
        .to_vec();
    let portable = call(
        port,
        "GET",
        &format!("/api/v1/artifacts/{id}/portable-digest"),
        &Value::Null,
        200,
    );
    assert_eq!(portable["raw_sha256"], sha256(&bytes));
    assert_eq!(portable["hub_digest"], output["digest"]);
    assert_ne!(portable["raw_sha256"], portable["hub_digest"]);
    assert_eq!(portable["size"], bytes.len());
    (artifact, portable, bytes)
}

#[test]
#[ignore = "requires exact built ITD_HUB_BINARY; dedicated transport CI executes it"]
fn real_daemon_transfers_development_inputs_executes_both_owners_and_retains_outputs() {
    let hub = PathBuf::from(std::env::var_os("ITD_HUB_BINARY").expect("built exact Hub required"))
        .canonicalize()
        .unwrap();
    let binary = PathBuf::from(env!("CARGO_BIN_EXE_itd-hub-neural-bridge"))
        .canonicalize()
        .unwrap();
    let port = TcpListener::bind("127.0.0.1:0")
        .unwrap()
        .local_addr()
        .unwrap()
        .port();
    let root =
        std::env::temp_dir().join(format!("itd-hub-development-{}-{port}", std::process::id()));
    fs::create_dir(&root).unwrap();
    let child = Command::new(&hub)
        .args([
            "--listen",
            &format!("127.0.0.1:{port}"),
            "--data-dir",
            root.to_str().unwrap(),
        ])
        .env_clear()
        .env("PATH", "/usr/bin:/bin")
        .stdout(Stdio::null())
        .stderr(Stdio::null())
        .spawn()
        .unwrap();
    let _daemon = Daemon { child, root };
    let start = Instant::now();
    while TcpStream::connect(("127.0.0.1", port)).is_err() {
        assert!(
            start.elapsed() < Duration::from_secs(15),
            "Hub did not start"
        );
        std::thread::sleep(Duration::from_millis(20));
    }
    let manifest = json!({"schema_version":1,"manifest":{
        "schema_version":1,"id":"1adbea71-7200-4000-8000-000000000001", "name":"itd-neural-development",
        "version":"1.0.0","kind":"tool","source":{"commit":ITD_SHA,"repository":"Memorithm/itd-simulator","dirty":false},
        "capabilities":[{"name":"itd.neural.development","contract_version":"1.0.0",
            "inputs":[{"name":"fields"}],"outputs":[{"name":"observation"}]}],
        "execution":{"type":"process","program":binary,"args":["{params}","{input:fields}","{output:observation}"],
            "outputs":[{"name":"observation","path":"observation.json","media_type":"application/vnd.itd.hub-neural-development.v1+json","required":true}]}
    }});
    let registration = call(port, "POST", "/api/v1/components", &manifest, 201);
    let mut data = fixture();
    let bytes = serde_json::to_vec(&data).unwrap();
    let (status, input) = http(port, "POST", "/api/v1/artifacts", &bytes);
    assert_eq!(status, 201, "{input}");
    let input_pin = call(
        port,
        "GET",
        &format!(
            "/api/v1/artifacts/{}/portable-digest",
            input["id"].as_str().unwrap()
        ),
        &Value::Null,
        200,
    );
    assert_eq!(input_pin["raw_sha256"], sha256(&bytes));
    let first = submit(port, &input, &bytes);
    let (_, first_pin, first_bytes) = observation(port, &first);
    let observed: Observation = serde_json::from_slice(&first_bytes).unwrap();
    assert_eq!(observed.input_sha256, sha256(&bytes));
    assert_eq!(observed.itd_sha, ITD_SHA);
    assert_eq!(observed.hub_sha, HUB_SHA);
    assert_eq!(observed.neural_operator_sha, NEURAL_SHA);
    assert_eq!(observed.split, "development");
    assert_eq!(
        observed.itd_diagnostic_subset,
        [2.5, 5.0_f64.sqrt(), 63.0 / 25.0 - 1.0, 1.75, 63.0 / 25.0]
    );
    assert_eq!(observed.grid_points, 48);
    assert_eq!(observed.interior_points, 24);
    assert!(observed.darcy_residual.iter().all(|x| *x == -5.0));
    let replay = submit(port, &input, &bytes);
    let (_, replay_pin, replay_bytes) = observation(port, &replay);
    assert_ne!(first["id"], replay["id"]);
    assert_eq!(first_bytes, replay_bytes);
    assert_eq!(first_pin["raw_sha256"], replay_pin["raw_sha256"]);
    data.forcing.fill(2.0);
    let changed_bytes = serde_json::to_vec(&data).unwrap();
    let (status, changed_input) = http(port, "POST", "/api/v1/artifacts", &changed_bytes);
    assert_eq!(status, 201);
    let changed_run = submit(port, &changed_input, &changed_bytes);
    let (_, changed_pin, changed_output) = observation(port, &changed_run);
    let changed: Observation = serde_json::from_slice(&changed_output).unwrap();
    assert!(changed.darcy_residual.iter().all(|x| *x == -6.0));
    assert_ne!(
        observed.numerical_output_sha256,
        changed.numerical_output_sha256
    );
    assert_ne!(first_pin["raw_sha256"], changed_pin["raw_sha256"]);
    // A final split must fail before a nonexistent file can be opened.
    let mut refused = request_for(&bytes);
    refused.split = "final".into();
    let refusal = Command::new(&binary)
        .arg(serde_json::to_string(&refused).unwrap())
        .arg("/nonexistent-final-holdout")
        .arg(_daemon.root.join("must-not-exist.json"))
        .output()
        .unwrap();
    assert!(!refusal.status.success());
    assert!(String::from_utf8_lossy(&refusal.stderr).contains("split"));
    assert!(!_daemon.root.join("must-not-exist.json").exists());
    let evidence = json!({"schema":"itd.hub-neural-development-qualification@1", "sources":{"ITD":ITD_SHA,"Hub":HUB_SHA,"NeuralOperator":NEURAL_SHA},
        "hub_binary_sha256":sha256(&fs::read(&hub).unwrap()),"bridge_binary_sha256":sha256(&fs::read(&binary).unwrap()),
        "registration":registration,"input_artifact":input,"input_portable_digest":input_pin,
        "first":first,"replay":replay,"changed":changed_run,"first_output":first_pin,"replay_output":replay_pin,"changed_output":changed_pin,
        "oracle":{"ITD_periodic_subset":"exact analytical 6x8 u=-y,v=x","NeuralOperator":"isotropic quadratic residual -5 then -6 after forcing change"},
        "negative_controls":"final refused before opening nonexistent input; unit source/digest/shape/schema controls","scientific_promotion":false,"OS_sandbox":false});
    if let Some(path) = std::env::var_os("ITD_BRIDGE_EVIDENCE") {
        let directory = PathBuf::from(path);
        fs::create_dir(&directory).unwrap();
        fs::write(
            directory.join("qualification.json"),
            serde_json::to_vec_pretty(&evidence).unwrap(),
        )
        .unwrap();
        fs::write(directory.join("development-input.json"), bytes).unwrap();
        fs::write(directory.join("first-observation.json"), first_bytes).unwrap();
        fs::write(directory.join("changed-observation.json"), changed_output).unwrap();
    }
    println!(
        "qualified real Hub/ITD/NeuralOperator: exact sources, immutable bytes, Development, two stable replays, causal forcing change, final refusal; no scientific promotion"
    );
}
