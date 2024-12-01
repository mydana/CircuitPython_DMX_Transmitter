# SPDX-FileCopyrightText: Copyright (c) 2024 Dana Runge
#
# SPDX-License-Identifier: Unlicense
MACHINE_CODE_DEPS = \
  assembly_code/reformat_pioasm.py \
  assembly_code/assembly_code.txt

LIBRARY_FILES = \
  dmx_transmitter/machine_code.py \
  dmx_transmitter/payload_USITT_DMX512_A.py \
  dmx_transmitter/machine_code.py


##Build the development environment and embed the RP2040 PIO machine code.
##
##This project features a pipeline that converts RP2040 PIO assembly code into
##hex codes in Python code. This makefile is used for working this pipeline.
##
##1. The assembly code and timings are generated in a LibreOffice Calc spreadsheet.
##2. The spreadsheet is converted to a tab-separated file.
##3a. The tab-separated file is converted to machine code and timings.
##3b. Then these are embedded into a Python library.
##4. Finally The Python library imports the embedded code.
##
##The follwing commands set up the enviroment, run the pipeline, and test the project.
##
##======================================================================================
##

.PHONY: help
help: ## Show this help message.
	@sed -E -ne 's/^##//p' -e 's/^([a-z/.-]+:)[^:]*##(.*)/\1\t\t\2/p' $(MAKEFILE_LIST)

.PHONY: install
install:  ## Install the development environment.
	python3 -m venv .venv; \
	source .venv/bin/activate; \
	python3 -m pip install --upgrade pip; \
	pip install -Ur requirements.txt; \
	pip install -Ur requirements/dev.txt;

.PHONY: deploy
deploy: deploy.py examples/fireworks.py $(LIBRARY_FILES)  ## Deploy libary to the CircuitPython board.
	source .venv/bin/activate; \
	python3 deploy.py --code=examples/fireworks.py \
	--var DMX_PIN=board.D4 \
	dmx_transmitter/dmx_transmitter.py \
	dmx_transmitter/payload_USITT_DMX512_A.py \
	dmx_transmitter/machine_code.py

dmx_transmitter/machine_code.py: $(MACHINE_CODE_DEPS)  ## Convert assembly code to a python library.
	source .venv/bin/activate; \
	python3 assembly_code/reformat_pioasm.py \
	--sideset-pins -2 \
	--python assembly_code/assembly_code.txt \
	--out dmx_transmitter/machine_code.py

.PHONY: docs
docs:  ## Construct the documentation.
	source .venv/bin/activate; \
	cd docs; \
	sphinx-build -E -W -b html . _build/html;

.PHONY: c-test
c-test:  ## Run tests that can be checked using C python.
	source .venv/bin/activate; \
	python3 -m unittest discover

.PHONY: check
check:  ## Check if this project is ready for publishing.
	source .venv/bin/activate; \
	pre-commit run --all-files

.PHONY: clean
clean: FORCE  ## Clean up the development environment.
	rm -rf .venv
	find -iname "*.pyc" -delete
	rm -rf docs/_build/html

FORCE: ;
