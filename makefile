CIRCUITPY = /Volumes/CIRCUITPY
DMX_PIN = D4

circuitpython_tests: microcontroller
	sed -e '/^DMX_PIN/ s/^.*/DMX_PIN = board.${DMX_PIN}/' < examples/circuitpython_tests.py > ${CIRCUITPY}/code.py

microcontroller: ${CIRCUITPY}/lib/dmx_transmitter dmx_transmitter/machine_code.py
	touch ${CIRCUITPY}/lib/dmx_transmitter/__init__.py
	cp dmx_transmitter/dmx_transmitter.py ${CIRCUITPY}/lib/dmx_transmitter
	cp dmx_transmitter/payload_USITT_DMX512_A.py ${CIRCUITPY}/lib/dmx_transmitter
	cp dmx_transmitter/machine_code.py ${CIRCUITPY}/lib/dmx_transmitter

${CIRCUITPY}/lib/dmx_transmitter:
	mkdir /Volumes/CIRCUITPY/lib/dmx_transmitter

dmx_transmitter/machine_code.py:
	python3 assembly_code.py > dmx_transmitter/machine_code.py

cpython_tests:
	python3 -m unittest discover tests_cpython/