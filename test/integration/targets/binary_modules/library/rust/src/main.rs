extern crate serde;
extern crate serde_json;

use std::env;
use std::fs::File;
use std::io::prelude::*;
use std::process;

#[macro_use]
extern crate serde_derive;

use serde_json::Error;


fn default_name_arg() -> String {
    String::from("World")
}


#[derive(Serialize, Deserialize)]
struct ModuleArgs {
    #[serde(default = "default_name_arg")]
    name: String,
}


#[derive(Clone, Serialize, Deserialize)]
struct Response {
	msg: String,
	changed: bool,
	failed: bool,
}


fn exit_json(response_body: Response) {
	return_response(response_body)
}


fn fail_json(response_body: Response) {
    let failed_response = &mut response_body.clone();
	failed_response.failed = true;
	return_response(failed_response.clone())
}


fn return_response(resp: Response) {
    println!("{}", serde_json::to_string(&resp).unwrap());
    process::exit(resp.failed as i32);
}


fn read_file_contents(file_name: &str) -> Result<String, Box<std::io::Error>> {
    let mut json_string = String::new();
    File::open(file_name)?.read_to_string(&mut json_string)?;
    Ok(json_string)
}


fn parse_module_args(json_input: String) -> Result<ModuleArgs, Error> {
    Ok(
        ModuleArgs::from(
            serde_json::from_str(
                json_input.as_str()
            )?
        )
    )
}


fn main() {
    let args: Vec<String> = env::args().collect();
    let program = &args[0];
    let input_file_name = match args.len() {
        2 => &args[1],
        _ => {
            eprintln!("module '{}' expects exactly one argument!", program);
            fail_json(Response {
                msg: "No module arguments file provided".to_owned(),
                changed: false,
                failed: true,
            });
            ""
        }
    };
    let json_input = read_file_contents(input_file_name).map_err(|err| {
        eprintln!("Could not read file '{}': {}", input_file_name, err);
        fail_json(Response {
            msg: format!("Could not read input JSON file '{}': {}", input_file_name, err),
            changed: false,
            failed: true,
        })
    }).unwrap();
    let module_args = parse_module_args(json_input).map_err(|err| {
        eprintln!("Error during parsing JSON module arguments: {}", err);
        fail_json(Response {
            msg: format!("Malformed input JSON module arguments: {}", err),
            changed: false,
            failed: true,
        })
    }).unwrap();
    exit_json(Response {
        msg: format!("Hello, {}!", module_args.name.as_str()),
        changed: true,
        failed: false,
    });
}
