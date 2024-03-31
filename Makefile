.ONESHELL:

#################################################################################
# GLOBALS                                                                       #
#################################################################################

PYTHON_INTERPRETER = python

PYTHON_ENV = ./venv/Scripts/python
PIP_ENV = ./venv/Scripts/pip

## Check if Python interpreter exists
ifeq (,$(shell where $(PYTHON_INTERPRETER) 2> nul))
HAS_PYTHON=False
else
HAS_PYTHON=True
endif

#################################################################################
# COMMANDS (Windows OS only)                                                                      #
#################################################################################


## Install Python Dependencies
requirements: test_environment
	$(PYTHON_ENV) -m pip install -r requirements.txt

## Delete all compiled Python files
clean:
	del /S /Q *.pyc
	del /S /Q *.pyo
	rmdir /S /Q __pycache__
	
## Lint using flake8
lint:
	flake8 src

## Set up python interpreter environment
create_environment:
ifeq (True,$(HAS_PYTHON))
	$(PYTHON_INTERPRETER) -m venv venv
	@echo ">>> New virtualenv created. Activate with:\nmake activate_environment"
else
	@echo ">>> Python interpreter not found. Please install Python version 3.11.3 or above."
endif

## Activate the virtual environment
activate_environment:
ifeq (True,$(shell if exist venv (echo True) else (echo False)))
	@echo ">>> Activating virtual environment.."
	.\\venv\\Scripts\\activate
else
	@echo ">>> Virtual environment not found. Please create it first by running:\nmake create_environment"
endif

## Test python environment is setup correctly
test_environment:
ifeq (True,$(shell if exist venv (echo True)))
	$(PYTHON_ENV) test_environment.py
else
	@echo ">>> Virtual environment not found. Please create it first by running:\nmake create_environment"
endif