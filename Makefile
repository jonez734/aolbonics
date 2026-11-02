# aolbonics (jargon) Makefile. deploytool runs `make -C aolbonics <target>`.

# VENV_DIR defaults to ~/.venv and honors deploytool's --prefix (DEPLOY_PREFIX),
# matching casino and bbsengine6. bbsengine6 requires <3.13, so VENV_PYTHON
# defaults to python3.12 for a new venv.
VENV_DIR ?= $(or $(DEPLOY_PREFIX),$(HOME)/.venv)
VENV_PYTHON ?= python3.12

.PHONY: venv

# Local venv install (no remote). Installs jargon into VENV_DIR so the
# `jargon` command is on that venv's PATH. The package depends on bed,
# bbsengine6 and zoid6, which must already be installed in the same venv.
venv:
	@if [ ! -x "$(VENV_DIR)/bin/python" ]; then \
		command -v "$(VENV_PYTHON)" >/dev/null 2>&1 || { echo "venv: $(VENV_PYTHON) not found; install it or set VENV_PYTHON" >&2; exit 1; }; \
		"$(VENV_PYTHON)" -m venv "$(VENV_DIR)" || { echo "venv: could not create $(VENV_DIR)" >&2; exit 1; }; \
	fi
	"$(VENV_DIR)/bin/python" -m pip install --upgrade pip
	"$(VENV_DIR)/bin/python" -m pip install --upgrade build
	@work="$$(mktemp -d)" && \
	trap 'rm -rf "$$work"' EXIT && \
	mkdir "$$work/src" && \
	tar -C . --exclude=./build --exclude=./dist --exclude='*.egg-info' --exclude=__pycache__ --exclude=.git -cf - . | tar -C "$$work/src" -xf - && \
	wheels="$$work/out" && \
	"$(VENV_DIR)/bin/python" -m build --wheel --outdir "$$wheels" "$$work/src" && \
	whl="$$(ls "$$wheels"/*.whl)" && \
	"$(VENV_DIR)/bin/python" -m pip install --upgrade --force-reinstall --no-deps "$$whl"
	@echo "installed jargon into $(VENV_DIR)"
