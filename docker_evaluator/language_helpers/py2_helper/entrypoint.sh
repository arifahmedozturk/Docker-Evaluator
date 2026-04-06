#!/bin/sh

cp /test_data/target.py ./target.py
cp /test_data/target.in ./target.in

start_ms=$(date +%s%3N)
if [ "$INPUT_TYPE" = "file" ]; then
  cp ./target.in ./${FILE_IO_NAME}.in
  timeout -k 1 ${TIME_LIMIT} python2 ./target.py
  exit_code=$?
else
  timeout -k 1 ${TIME_LIMIT} python2 ./target.py < ./target.in > ./result.out
  exit_code=$?
fi
end_ms=$(date +%s%3N)
elapsed_ms=$((end_ms - start_ms))

if [ $exit_code -eq 124 ]; then
  echo "Time Limit Exceeded"
  exit 0
fi

if [ $exit_code -eq 137 ]; then
  echo "Memory Limit Exceeded"
  exit 0
fi

if [ $exit_code -ne 0 ]; then
  echo "Runtime Error (exit code $exit_code)"
  exit 0
fi

if [ "$INPUT_TYPE" = "file" ]; then
  cat ./${FILE_IO_NAME}.out 2>/dev/null
else
  cat ./result.out
fi
printf '\n__TIME__:%sms\n' "${elapsed_ms}"
exit 0
