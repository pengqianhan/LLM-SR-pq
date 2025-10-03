import logging
from argparse import ArgumentParser
from typing import Any, Dict, List

import requests
from flask import Flask, jsonify, request
from flask_cors import CORS


parser = ArgumentParser()
parser.add_argument("--base_url", type=str, default="http://127.0.0.1:11434",
                    help="Base URL for the local Ollama server")
parser.add_argument("--model", type=str, default="qwen2:0.5b",
                    help="Name of the Ollama model to query")
parser.add_argument("--host", type=str, default="0.0.0.0",
                    help="Host interface for the Flask server")
parser.add_argument("--port", type=int, default=5000,
                    help="Port for the Flask server")
parser.add_argument("--request_timeout", type=float, default=300.0,
                    help="Timeout (seconds) when calling the Ollama API")
args = parser.parse_args()

app = Flask(__name__)
CORS(app)
_session = requests.Session()


def _build_options(params: Dict[str, Any]) -> Dict[str, Any]:
    """Translate sampler params to Ollama generation options."""
    options: Dict[str, Any] = {}

    temperature = params.get("temperature")
    if temperature is not None:
        options["temperature"] = temperature

    top_p = params.get("top_p")
    if top_p is not None:
        options["top_p"] = top_p

    top_k = params.get("top_k")
    if top_k is not None:
        options["top_k"] = top_k

    max_new_tokens = params.get("max_new_tokens")
    if max_new_tokens is not None:
        options["num_predict"] = max_new_tokens

    return options


def _call_ollama(prompt: str, params: Dict[str, Any]) -> str:
    payload: Dict[str, Any] = {
        "model": args.model,
        "prompt": prompt,
        "stream": False,
    }

    options = _build_options(params)
    if options:
        payload["options"] = options

    response = _session.post(
        f"{args.base_url}/api/generate",
        json=payload,
        timeout=args.request_timeout,
    )
    response.raise_for_status()
    data = response.json()
    return data.get("response", "")


@app.route("/completions", methods=["POST"])
def completions() -> Any:
    body = request.get_json(force=True, silent=True) or {}
    prompt = body.get("prompt", "")
    repeat_prompt = int(body.get("repeat_prompt", 1))
    params = body.get("params") or {}

    if not isinstance(prompt, str) or not prompt:
        return jsonify({"error": "prompt must be a non-empty string"}), 400

    responses: List[str] = []
    for _ in range(max(repeat_prompt, 1)):
        try:
            responses.append(_call_ollama(prompt, params))
        except requests.RequestException as exc:
            logging.exception("Ollama request failed")
            return jsonify({"error": f"ollama request failed: {exc}"}), 502

    return jsonify({"content": responses})


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    app.run(host=args.host, port=args.port)
