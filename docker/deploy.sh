#!/bin/bash

bold_text=$(tput bold)
normal_text=$(tput sgr0)

CWD="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
OLD_PWD=$(pwd)
RSYNC_OPTIONS=""
ZIP_OPTIONS=""

function ask() {
    echo -en "\e[96m"`date "+%Y-%m-%d %H:%M:%S"`"${bold_text} - ${1}\e[39m${normal_text}"
}

function log() {
    echo `date "+%Y-%m-%d %H:%M:%S"`"${bold_text} - ${1}${normal_text}"
}

function err() {
    echo -e "\e[31m"`date "+%Y-%m-%d %H:%M:%S"`"${bold_text} - ${1}\e[39m${normal_text}"
}

function warn() {
    echo -e "\e[33m"`date "+%Y-%m-%d %H:%M:%S"`"${bold_text} - ${1}\e[39m${normal_text}"
}

function succ() {
    echo -e "\e[32m"`date "+%Y-%m-%d %H:%M:%S"`"${bold_text} - ${1}\e[39m${normal_text}"
}

function abort {
  cd $2
  exit $1
}

function main() {
    OPTIONS=${@:1}
    for option in ${OPTIONS[*]}; do
        if [[ "$option" == "--verbose" ]] || [[ "$option" == "-v" ]]; then
            RSYNC_OPTIONS=$RSYNC_OPTIONS"-v "
            ZIP_OPTIONS=$ZIP_OPTIONS"-v "
        elif [[ "$option" == "--help" ]] || [[ "$option" == "-h" ]]; then
            show_help
        else
            show_help "Unknown option $option"
        fi
    done

    log "Generating new version for PySiQ."
    cur_version=$(head -1 $CWD/../VERSION | cut -f1 -d" ")
    log "Current version in VERSION file is ${cur_version}"

    main_dir=$(realpath $CWD/../)
    # Copy the app code to a temporal location
    rm -rf /tmp/pysiq
    log "Copying the app code to temporal directory..."
    mkdir /tmp/pysiq
    rsync -ar $RSYNC_OPTIONS $main_dir/* /tmp/pysiq
    succ "Copying the app code... DONE"

    # Remove unused files
    cd /tmp/pysiq
    rm -rf .idea
    rm -rf .git*
    rm -r venv
    rm -r __pycache__

    log "Compressing server application... "
    cd ..
    zip -rq $ZIP_OPTIONS pysiq pysiq --exclude "*.pyc"
    succ "Compressing server application... DONE"

    cd $CWD

    log "Moving result to docker directory..."
    mv /tmp/pysiq.zip configs/pysiq.zip
    succ "Moving result to docker directory... DONE"

    # Getting pip install script
    log "Getting pip install script..."
    wget --no-check-certificate https://bootstrap.pypa.io/get-pip.py -O /tmp/pysiq/get-pip.py
    check_changes=$(diff configs/get-pip.py /tmp/pysiq/get-pip.py)
    if [[ "$?" != "0" ]]; then
      warn "Pip installator has changed"
      mv /tmp/pysiq/get-pip.py configs/get-pip.py
    fi
    succ "Getting pip install script...DONE"

    log "Cleaning..."
    rm -rf /tmp/pysiq
    succ "Done."

    log "Now you can build the new docker image using the following command"
    log "sudo docker build -t fikipollo/pysiq:${cur_version}  -t fikipollo/pysiq:latest ."

    abort 0 $OLD_PWD
}

main "$@"
