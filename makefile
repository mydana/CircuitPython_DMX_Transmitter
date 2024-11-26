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


install:
	python3 -m venv .venv; \
	source .venv/bin/activate; \
	pip install -Ur requirements.txt; \
	pip install -Ur requirements/dev.txt;

.PHONY: docs
docs:
	source .venv/bin/activate; \
	cd docs; \
	sphinx-build -E -W -b html . _build/html;

check:
	source .venv/bin/activate; \
	pre-commit run --all-files;

dmx_transmitter/machine_code.py: $(MACHINE_CODE_DEPS)
	# TODO source .venv/bin/activate;
	python3 assembly_code/reformat_pioasm.py \
	--sideset-pins -1 \
	--python assembly_code/assembly_code.txt \
	--out dmx_transmitter/machine_code.py

deploy: deploy.py examples/fireworks.py $(LIBRARY_FILES)
	# TODO source .venv/bin/activate;
	python3 deploy.py --code=examples/fireworks.py \
	--var DMX_PIN=board.D4 \
	dmx_transmitter/dmx_transmitter.py \
	dmx_transmitter/payload_USITT_DMX512_A.py \
	dmx_transmitter/machine_code.py

clean: FORCE
	rm -rf .venv
	find -iname "*.pyc" -delete
	rm -rf docs/_build/html

FORCE: ;