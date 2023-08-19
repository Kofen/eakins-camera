#!/bin/sh

# Default values
BYTES=""
HEX=""
PID=""

# Parse command-line arguments
while getopts "p:s:x" opt; do
  case $opt in
    p)
      PID="$OPTARG"
      ;;
    s)
      BYTES="$OPTARG"
      ;;
    x)
      HEX="true"
      ;;
    \?)
      echo "Usage: $0 -p <PID> [-s <bytes>] [-x]"
      exit 1
      ;;
  esac
done

# Check if PID is provided
if [ -z "$PID" ]; then
  echo "PID is required."
  exit 1
fi

# Construct the strace command
strace_cmd="strace"
if [ -n "$HEX" ]; then
  strace_cmd="$strace_cmd -x"
fi
if [ -n "$BYTES" ]; then
  strace_cmd="$strace_cmd -s $BYTES"
fi
strace_cmd="$strace_cmd -p $PID 2>&1 | grep \"write\" | awk -F '\\\\x' '{for(i=2; i<=NF; i++) printf(\"pos %d, byte 0x%s\\n\", i-2, \$i);}'"

# Execute the strace command
eval "$strace_cmd"

