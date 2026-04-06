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

## Compilation cache

C and C++ submissions are cached by source hash — repeated evaluations of the same code skip recompilation. To clear the cache:

```python
from docker_evaluator import clear_cache

clear_cache()
```
