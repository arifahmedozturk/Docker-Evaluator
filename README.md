# docker-evaluator

A code evaluation backend for competitive programming judges. Runs untrusted submissions in isolated Docker containers, enforces time and memory limits, and checks output against expected results — similar to how Codeforces/CodeChef judge submissions.

Supports Python 2/3, C, and C++.

## Requirements

- Docker (running and accessible to the current user)
- Python 3.9+

## Installation

```bash
pip install docker-evaluator
```

## Usage

```python
from docker_evaluator import DockerEvaluator

evaluator = DockerEvaluator()

result = evaluator.evaluate(
    code='n = int(input()); print(n * 2)',
    input="21",
    expected_output="42",
    language="py3",
    time_limit=1,
    memory_limit=256 * 1024,  # 256 MB in KB
)

print(result)
# {'correct': True, 'details': 'OK (8ms)'}

evaluator.close()
```

### Parameters

| Parameter | Type | Default | Description |
|---|---|---|---|
| `code` | `str` | — | Submission source code |
| `input` | `str` | — | Problem input (stdin or file content) |
| `expected_output` | `str` | — | Correct output to compare against |
| `language` | `str` | — | `"py3"`, `"py2"`, `"c"`, or `"cpp"` |
| `time_limit` | `int` | — | Time limit in seconds |
| `input_type` | `str` | `"stdin"` | `"stdin"` or `"file"` |
| `file_io_name` | `str` | `""` | File name when using file I/O (e.g. `"input.txt"`) |
| `memory_limit` | `int` | `1024` | Memory limit in KB (minimum enforced: 256 MB) |

### Return value

```python
{"correct": bool, "details": str}
```

`details` is one of:

- `OK (Xms)` — accepted
- `Wrong Answer`
- `Time Limit Exceeded`
- `Memory Limit Exceeded`
- `Runtime Error (exit code N)`
- `Compilation Error`

## Supported languages

| Key | Language |
|---|---|
| `py3` | Python 3 |
| `py2` | Python 2 |
| `c` | C |
| `cpp` | C++ |

Docker images are built automatically on first use and cached for subsequent runs.

## File I/O

For problems that read/write files instead of stdin/stdout:

```python
result = evaluator.evaluate(
    code=open("solution.cpp").read(),
    input="5\n1 2 3 4 5",
    expected_output="15",
    language="cpp",
    time_limit=2,
    input_type="file",
    file_io_name="input.txt",
)
```

## Configuration

Create a `.env` file in your working directory:

| Variable | Default | Description |
|---|---|---|
| `KEEP_EVAL_CONTAINERS` | `0` | Set to `1` to keep containers after a run (useful for debugging) |
| `ENVIRONMENT` | — | If set, also loads `.env.<ENVIRONMENT>` |

## How It Works

1. The submission is written to a temporary directory
2. A language-specific Docker image is built (once) and cached for subsequent runs
3. A container is started with the submission mounted read-only
4. Resource limits (CPU, memory, PID count) are applied before execution
5. The code is compiled (if needed) and executed inside the container with no network access
6. Output is captured and compared against expected output
7. The container is removed after execution

## Security Model

- Code runs inside isolated Docker containers with no network access
- No access to the host filesystem outside the mounted read-only workspace
- Containers are ephemeral and removed after execution
- Resource limits prevent abuse (memory exhaustion, fork bombs, infinite loops)
- PID limit (64) restricts process spawning inside the container

**Note:** This is not a fully hardened sandbox and should not be exposed directly to the internet without additional isolation (e.g. VM-level sandboxing). Docker isolation has known escape vectors in misconfigured environments.

## Design Decisions

**Why Docker?**
Provides portable, language-agnostic process isolation without requiring a VM. Adding a new language is as simple as writing a Dockerfile and entrypoint script.

**Why cache compilation?**
Compiled languages (C, C++) are recompiled only when the source changes. Repeated evaluations of the same submission skip compilation entirely, reducing latency significantly in judge workloads.

**Why a synchronous API?**
Keeps integration simple. The library can be wrapped in an async worker or job queue by the caller without imposing an execution model.

## Limitations

- Not a fully secure sandbox — Docker isolation has known escape risks in misconfigured environments
- No distributed execution (single-machine only)
- No built-in concurrency control or request queuing
- Memory limit enforcement has a minimum floor of 256 MB (Docker constraint)

## Compilation cache

C and C++ submissions are cached by source hash — repeated evaluations of the same code skip recompilation. To clear the cache:

```python
from docker_evaluator import clear_cache

clear_cache()
```
