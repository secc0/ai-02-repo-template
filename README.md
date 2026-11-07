# ai-02-repo-template

A minimal, reusable starter for small Python AI projects on the [OpenRouter](https://openrouter.ai) API.
It ships with config loading, a single LLM call with model fallbacks, a CLI, offline tests,
a smoke eval, a Dockerfile and CI. Every later project in the series starts from here.

## Problem

Each new AI side project begins with the same work: load an API key, call a model, handle
fallbacks, write tests that don't need the network, lint, containerize and set up CI. Repeating
that every day is slow and error-prone. This template does it once, so a new project starts with
a working, tested skeleton.

## Demo

```console
$ python -m app "What is the capital of France? One word."
Paris
[model: <the model that actually answered>]

$ python -m evals.run
model: <EVAL_MODEL>  cases: 5
PASS  arithmetic   5
PASS  capital      Paris
...
pass rate: 100% (5/5)
```

The answer goes to stdout and the answering model to stderr, so `python -m app ... > out.txt`
captures only the answer.

## Quickstart

Requires Python 3.11+. `make` is optional: every target is a thin wrapper around a plain command.

**Plain commands (work everywhere, including Windows PowerShell):**

```bash
python -m venv .venv
# activate it:  .venv\Scripts\Activate.ps1  (PowerShell)  |  source .venv/bin/activate  (Linux/macOS)
python -m pip install -e ".[dev]"

cp .env.example .env              # PowerShell: Copy-Item .env.example .env
# then edit .env and fill in OPENROUTER_API_KEY and MODEL_PRIMARY

python -m app "Say hello"         # run the CLI
python -m pytest -q               # tests (no network, no key)
python -m ruff check .            # lint
python -m ruff format --check .   # format check
python -m evals.run               # smoke eval (needs .env)
docker build -t app .             # container image
docker run --rm --env-file .env app "Say hello"
```

Docker is optional locally: the CI `docker` job builds the image and checks that the CLI starts
inside it on every push.

**With make** (after creating and activating the venv):

```bash
make setup         # pip install -e ".[dev]"
make run PROMPT="Say hello"
make test
make lint
make eval
make docker-build
```

## How it works

```
src/app/config.py   loads .env (searched from the current directory up) and env vars;
                    fails early naming the missing variable
src/app/llm.py      complete(prompt, settings) -> Completion(text, model)
src/app/cli.py      parses the prompt, calls complete(), prints the answer
evals/cases.yaml    trivial prompts, each with one check (contains / equals / regex)
evals/run.py        runs each case against EVAL_MODEL and prints pass/fail + pass rate
tests/              pytest suite using a fake client: no network, no key
```

- **OpenRouter via the openai SDK.** `llm.py` creates an `OpenAI` client with
  `base_url="https://openrouter.ai/api/v1"` and calls `chat.completions.create`.
- **Fallbacks.** If `MODEL_FALLBACKS` is set, the request includes
  `extra_body={"models": [primary, *fallbacks]}`. OpenRouter tries them in order, and
  `response.model` tells you which one actually answered.
- **Testability.** `complete()` accepts an optional `client`, so tests inject a fake object with
  the same `chat.completions.create` shape instead of mocking HTTP internals.
- **Evals.** The runner uses one model with no fallbacks, so the pass rate measures exactly that
  model. It exits non-zero when the pass rate drops below `--min-pass-rate` (default 0.8).

Configuration (see `.env.example`):

| Variable             | Required | Purpose                                         |
|----------------------|----------|-------------------------------------------------|
| `OPENROUTER_API_KEY` | yes      | OpenRouter API key                              |
| `MODEL_PRIMARY`      | yes      | Model tried first (`provider/model` slug)       |
| `MODEL_FALLBACKS`    | no       | Comma-separated fallback models                 |
| `EVAL_MODEL`         | no       | Model for `evals.run`; defaults to `MODEL_PRIMARY` |

## Results

- **Smoke eval: 5/5 cases passed (100%)** with a free OpenRouter model (measured 2026-11-07).
- The offline test suite runs 24 tests in about 0.1 s locally (Windows, Python 3.14), with no
  network and no API key.

Free models are often rate-limited (HTTP 429). In the same run, the free primary model failed
every eval case with 429, while the CLI still answered through its fallback. Point `EVAL_MODEL`
at a model with available capacity.

## Limits

- Single-turn, text-only calls. No streaming, chat history, tools or structured output.
- No retries or timeouts beyond the SDK defaults and OpenRouter's own fallback routing.
- Eval checks are simple string matches; they suit smoke tests, not quality benchmarks.
- The placeholder package is named `app`; rename it per project if you like.

## Using this template

Create a new project from it with the GitHub CLI:

```bash
gh repo create ai-NN-slug --template <user>/ai-02-repo-template --public --clone
```

Then: update the project name and description in `pyproject.toml`, rewrite this README, copy
`.env.example` to `.env`, and replace the CLI with your project's logic.

### Enable the smoke eval in CI

The `smoke-eval` CI job runs only when the `OPENROUTER_API_KEY` secret exists. Forks and
repositories without it skip the job and stay green.

1. Open the repository on GitHub and go to **Settings > Secrets and variables > Actions**.
2. On the **Secrets** tab, click **New repository secret**. Name: `OPENROUTER_API_KEY`,
   value: your OpenRouter key.
3. On the **Variables** tab, click **New repository variable**. Name: `EVAL_MODEL`,
   value: the model slug to evaluate (for example, a cheap model from
   https://openrouter.ai/models).

If the secret is set but `EVAL_MODEL` is not, the eval fails with a clear message naming the
missing variable.

## License

[MIT](LICENSE)
