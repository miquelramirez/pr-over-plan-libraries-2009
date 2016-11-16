#! /bin/sh

# Paths to planner components
TRANSLATE="./solvers/LAMA/translate/translate.py"
PREPROCESS="./solvers/LAMA/preprocess"
SEARCH="./solvers/LAMA/release-search"

run_planner() {
    echo "1. Running translator"
    "$TRANSLATE" "$1" "$2"
    echo "2. Running preprocessor"
    "$PREPROCESS" < output.sas
    echo "3. Running search"
    "$SEARCH" "fFlLi" "$3" < output
}

check_input_files() {
    if [ ! -e "$1" ]; then
	echo "Domain file \"$1\" does not exist."
	exit 1
    fi
    if [ ! -e "$2" ]; then
	echo "Problem file \"$2\" does not exist."
	exit 1
    fi
}

# Make sure we have exactly 3 command line arguments
if [ $# -ne 3 ]; then
    echo "Usage: \"plan <domain_file> <problem_file> <result_file>\""
    exit 1
fi

check_input_files "$1" "$2"

# Command line arguments seem to be fine, run planner
run_planner "$1" "$2" "$3"

# We do not clean up temporary files here (not necessary for IPC-2008)
