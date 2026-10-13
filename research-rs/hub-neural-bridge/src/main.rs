use itd_hub_neural_bridge::{INPUT_LIMIT, Request, execute};
use std::{
    fs::{self, File, OpenOptions},
    io::{Read, Write},
    path::Path,
};

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let args = std::env::args().skip(1).collect::<Vec<_>>();
    if args.len() != 3 || args[0].len() > 2048 {
        return Err(
            "expected bounded params JSON, Hub materialized input path and declared output path"
                .into(),
        );
    }
    let request: Request = serde_json::from_str(&args[0])?;
    // Refuse final/validation requests before even opening their input path.
    request.validate()?;
    let path = Path::new(&args[1]);
    let meta = fs::symlink_metadata(path)?;
    if !meta.is_file() || meta.len() > INPUT_LIMIT as u64 {
        return Err("bounded regular input required".into());
    }
    let mut bytes = Vec::new();
    File::open(path)?
        .take(INPUT_LIMIT as u64 + 1)
        .read_to_end(&mut bytes)?;
    let result = execute(&request, &bytes)?;
    let output = serde_json::to_vec(&result)?;
    let mut file = OpenOptions::new()
        .write(true)
        .create_new(true)
        .open(&args[2])?;
    file.write_all(&output)?;
    println!("Development observation emitted; no scientific or isolation promotion");
    Ok(())
}
