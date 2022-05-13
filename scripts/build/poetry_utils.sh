#!/usr/bin/env bash

init_poetry () {
  echo "Initializing poetry:"
  export LC_ALL=C.UTF-8
  "$POETRY_BIN" env use "$PYTHON_BIN"
  "$POETRY_BIN" install
}

request_install_poetry () {
  install_command="cat get-poetry.py | python3 -"
  curl -sSL -o get-poetry.py https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py
  sed -i 's/allowed_executables = \["python", "python3"\]/allowed_executables = ["python3", "python"]/'  get-poetry.py 
  if [ "$POETRY_INSTALL" = YES ]
  then
    ANSWER=yes
  else
    echo "Do you want to install poetry local to the user using '$install_command'"
    echo -n "yes/no: "
    read -r ANSWER
  fi
  if [ "$ANSWER" == "yes" ]
  then
    echo "Installing poetry"
    if ! bash -c "$install_command"
    then
      echo "The automatic installation of Poetry failed please install in manually."
      echo "To install it manually, you can use the command 'cat get-poetry.py | python3 -'."
      echo "Aborting"
      exit 1
    fi
    rm get-poetry.py
  else
      echo "Please install poetry manually or set the environment variable POETRY_BIN."
      echo "To install it manually you can use 'cat get-poetry.py | python3 -'."
      echo "Aborting"
      exit 1
  fi
}

check_poetry() {
  echo -n "Poetry available? "
  if [ -z "$POETRY_BIN" ]
  then
    POETRY_BIN=$(command -v poetry)
    if [ -z "$POETRY_BIN" ]
    then
      POETRY_BIN_HOME="$HOME/.poetry/bin/poetry"
      if [ -e "$POETRY_BIN_HOME" ]
      then
        POETRY_BIN=$POETRY_BIN_HOME
      else
        echo "[Not found]"
        request_install_poetry
        POETRY_BIN=$POETRY_BIN_HOME
        echo -n "Poetry available? "
      fi
    fi
  fi
  echo "[OK] ($POETRY_BIN)"
}

check_python_version(){
  echo -n "Python available? "
  if [ -z "$PYTHON_BIN" ]
  then
    ACCEPTABLE_PYTHON_EXECUTABLES=("python3.8" "python3.9" "python3.10")
    for python_executable in "${ACCEPTABLE_PYTHON_EXECUTABLES[@]}"
    do
      PYTHON_BIN=$(command -v "$python_executable")
      if [ -n "$PYTHON_BIN" ]
      then
        break
      fi
    done
    if [ -z "$PYTHON_BIN" ]
    then
      echo "[Not found]"
      echo "Found no compatible Python executable, please install Python 3.8+ or set the environment variable PYTHON_BIN to the path of the Python executable."
      echo "Aborting"
      exit 1
    fi
  fi 
  echo "[OK] ($PYTHON_BIN)"
  #echo "Found the following Python executable: $PYTHON_BIN"
}

check_distutils(){
  echo -n "Distutils available? "
  if ! $PYTHON_BIN -c "import distutils.util" &> /dev/null 
  then
    echo "[Not found]"
    echo "The python package 'distutils' is not installed, please install the package 'distutils' either via your package manager or by installing 'setuptools', for more information, please refer to https://packaging.python.org/guides/installing-using-linux-tools/"
    echo "Aborting"
    exit 1
  else
    echo "[OK]"
  fi
}

check_requirements() {
  echo "Checking Requirements:"
  check_python_version
  check_distutils
  check_poetry
}
