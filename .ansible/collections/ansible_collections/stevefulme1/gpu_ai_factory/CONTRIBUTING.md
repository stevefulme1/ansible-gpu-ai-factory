# Contributing to stevefulme1.nvidia_ai_factory

## Development Setup

```bash
git clone https://github.com/stevefulme1/ansible-nvidia-ai-factory.git
cd ansible-nvidia-ai-factory
pip install ansible-core>=2.16 ansible-lint yamllint flake8 pytest requests
```

## Running Tests

```bash
# Linting
flake8 plugins/ --max-line-length=120 --ignore=E402,W503
yamllint -c .yamllint .
ansible-lint --strict

# Unit tests
pytest tests/unit/ -v

# Sanity tests
ansible-test sanity --python 3.12 -v
```

## Module Pattern

All modules follow the pattern established in `plugins/modules/bcm_cluster.py`:

1. Import `NVIDIA_COMMON_ARGS` from `nvidia_common`
2. Define `get_module_args()` merging module-specific args with common args
3. Implement `get_resource()`, `find_resource()`, `create_resource()`,
   `update_resource()`, `delete_resource()`, `needs_update()`
4. Support `check_mode` and idempotent operations
5. Use `call_with_retry()` for all API calls
6. Use `wait_for_resource()` for async operations

## Pull Requests

- Follow conventional commit format for PR titles
- Ensure all linting passes
- Add unit tests for new modules
