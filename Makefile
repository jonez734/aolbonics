# aolbonics (jargon) Makefile. deploytool runs `make -C aolbonics <target>`.

# VENV_DIR defaults to ~/.venv and honors deploytool's --prefix (DEPLOY_PREFIX),
# matching casino and bbsengine6. bbsengine6 requires <3.13, so VENV_PYTHON
# defaults to python3.12 for a new venv.
VENV_DIR ?= $(or $(DEPLOY_PREFIX),$(HOME)/.venv)
VENV_PYTHON ?= python3.12

.PHONY: venv build clean stale-build version

# Move aside any build/dist/egg-info directory the project holds before a build.
# A tree left by another user cannot be deleted, but renaming it needs only write
# access to this project directory. The stale tree is kept under *.stale.<timestamp>.
# Same pattern as casino's Makefile (stale-build -> clean -> build).
stale-build:
	@ts=$$(date +%Y%m%d%H%M%S); \
	for d in build dist src/*.egg-info src/jargon/*.egg-info *.egg-info; do \
		for x in $$d; do \
			[ -e "$$x" ] || continue; \
			mv "$$x" "$$x.stale.$$ts" && echo "stale-build: moved $$x -> $$x.stale.$$ts"; \
		done; \
	done

clean: stale-build
	-rm -rf build dist
	-rm -rf *.egg-info src/*.egg-info src/jargon/*.egg-info
	-find . -type d -name __pycache__ -exec rm -rf {} +
	-find . -type d -name .pytest_cache -exec rm -rf {} +
	-find . -type d -name .ruff_cache -exec rm -rf {} +
	-find . -type d -name .mypy_cache -exec rm -rf {} +

# Wheel version is pyproject's static name/version; no stamp file to write.
version:
	@true

# Make sure build/ exists with mode 1775 (sticky, not setgid) before invoking `python -m build`.
# Same rule as casino's Makefile: a setgid build/ breaks bdist_wheel's dist-info rename under
# NoNewPrivs. A build/ owned by another user is renamed aside first.
PREPARE_BUILD = \
	if [ -d $(1)/build ] && [ ! -O $(1)/build ]; then \
		mv $(1)/build $(1)/build.stale.$$ 2>/dev/null || true; \
	fi; \
	mkdir -p $(1)/build && chmod g-s,+t $(1)/build

# Build the wheel in place. clean (stale-build first) runs before every build.
build: clean version
	$(call PREPARE_BUILD,$(CURDIR))
	python3 -m build --wheel --outdir dist .

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
