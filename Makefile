PYTHON=python
PYTHON_VENV=venv/bin/python
COMPILER=gcc
LINKER=gcc

CLEAN_EXT=*.o *.c *.so
EXTENSION_FOLDER=octobot_trading
CFLAGS=-O9

PYTHON=$(PYTHON_VENV)

# export PYTHONPATH=$PYTHONPATH:../OctoBot-Commons

help:
	@echo "OctoBot-Trading Cython Makefile.  Available tasks:"
	@echo "build -> build the Cython extension module."
	@echo "clean -> clean the Cython extension module."
	@echo "debug -> debug the Cython extension module."
	@echo "run -> run the Cython extension module."

all: build

.PHONY: build
build: clean
	$(PYTHON) setup.py build_ext --inplace

.PHONY: clean
clean:
	rm -rf build
	rm -rf auditwheel
	rm -rf dist
	rm -rf .eggs
	rm -rf *.egg-info
	for i in $(CLEAN_EXT); do find $(EXTENSION_FOLDER) -name "$$i" -delete; done

.PHONY: debug
debug:
	gdb -ex r --args $(PYTHON) demo.py

.PHONY: run
run: build
	$(PYTHON) demo.py

# Suffix rules
.PRECIOUS: %.c
%: %.o
	$(LINKER) -o $@ -L$(LIBRARY_DIR) -l$(PYTHON_LIB) $(SYSLIBS) $<

%.o: %.c
	$(COMPILER) $(CFLAGS) -I$(INCLUDE_DIR) -c $< -o $@

%.c: %.py
	cython -a --embed $<

%.c: %.pyx
	cython -a --embed $<
