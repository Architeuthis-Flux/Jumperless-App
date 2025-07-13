.PHONY: clean packager_env Packager/constraints.txt app app_env package
# Base python interpreter
BASE_PYTHON=python3
# Packager venv vars
PACKAGER_BUILDDST=./Packager/build
PACKAGER_ENV=$(PACKAGER_BUILDDST)/.packager_env
PACKAGER_PYTHON=$(PACKAGER_ENV)/bin/python
PACKAGER_REQUIREMENTS=Packager/packagerRequirements.txt
PACKAGER_CONSTRAINTS=Packager/constraints.txt
# Constraints venv vars
PACKAGER_CONST_ENV=$(PACKAGER_BUILDDST)/.constraints_env
PACKAGER_CONST_PYTHON=$(PACKAGER_CONST_ENV)/bin/python
# App venv vars
APP_ENV=.env
APP_PYTHON=$(APP_ENV)/bin/python
APP_REQUIREMENTS=requirements.txt
APP_CONSTRAINTS=constraints.txt

# Separate requirements and constraints files
# This allows for easier management of dependencies
# and ensures reproducible builds
# requirements.txt should only list versions if absolutely necessary
# constraints.txt is auto-generated and pins exact versions


app: app_env
	$(APP_PYTHON) JumperlessWokwiBridge.py

app_env: $(APP_ENV)/bin/activate
$(APP_ENV)/bin/activate: $(APP_REQUIREMENTS)
	$(BASE_PYTHON) -m venv $(APP_ENV)
	$(APP_PYTHON) -m pip install --upgrade pip
	$(APP_PYTHON) -m pip install -r $(APP_REQUIREMENTS)

# Target to create and set up the virtual environment
# Dependencies: requirements.txt and constraints.txt
packager_env: $(PACKAGER_ENV)/bin/activate
$(PACKAGER_ENV)/bin/activate: $(PACKAGER_REQUIREMENTS) $(PACKAGER_CONSTRAINTS)
	$(BASE_PYTHON) -m venv $(PACKAGER_ENV)
	$(PACKAGER_PYTHON) -m pip install --upgrade pip
	$(PACKAGER_PYTHON) -m pip install -r $(PACKAGER_REQUIREMENTS) -c $(PACKAGER_CONSTRAINTS)

# Target to create constraints file
# Dependencies: requirements.txt
# Run `make constraints.txt` to update the versions of packages
# that will be used in the build environment
# This is useful when adding new packages or updating existing ones
$(PACKAGER_CONSTRAINTS): $(PACKAGER_REQUIREMENTS)
	rm -rf $(PACKAGER_CONST_ENV)
	$(BASE_PYTHON) -m venv $(PACKAGER_CONST_ENV)
	$(PACKAGER_CONST_PYTHON) -m pip install --upgrade pip
	$(PACKAGER_CONST_PYTHON) -m pip install --no-input -U -r $(PACKAGER_REQUIREMENTS)
	$(PACKAGER_CONST_PYTHON) -m pip freeze > $(PACKAGER_CONSTRAINTS)
	rm -rf $(PACKAGER_CONST_ENV)

# Target to build the application
# Dependencies: env and constraints
package: packager_env
	$(PACKAGER_PYTHON) Packager/JumperlessAppPackagerLinux.py

# Target to clean up build artifacts
clean:
	rm -rf $(PACKAGER_BUILDDST)
	rm -rf $(APP_ENV)
	rm -rf builds
