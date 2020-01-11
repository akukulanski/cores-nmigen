


.phony: test clean

test:
	python3 -m pytest -v cores/test

clean:
	rm -rf *.vcd sim_build/ .pytest_cache/ ./**/__pycache__/ ./*/**/__pycache__/