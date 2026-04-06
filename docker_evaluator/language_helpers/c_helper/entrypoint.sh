#!/bin/sh
if [ -f /cache/main ]; then
  cp /cache/main ./main
else
  compile_output=$(gcc -std=c99 -O2 -o ./main /test_data/target.c 2>&1)
  if [ $? -ne 0 ]; then
    echo "Compilation Error: $compile_output"
    exit 0
  fi
  cp ./main /cache/main 2>/dev/null || true
fi

cp /test_data/target.in ./target.in

start_ms=$(date +%s%3N)
if [ "$INPUT_TYPE" = "file" ]; then
  cp ./target.in ./${FILE_IO_NAME}.in
  if [ -n "$MEMORY_LIMIT_KB" ] && [ "$MEMORY_LIMIT_KB" -gt 0 ] 2>/dev/null; then
    timeout -k 1 ${TIME_LIMIT} sh -c "ulimit -v \"$MEMORY_LIMIT_KB\" && exec ./main"
  else
    timeout -k 1 ${TIME_LIMIT} ./main
  fi
  exit_code=$?
else
  if [ -n "$MEMORY_LIMIT_KB" ] && [ "$MEMORY_LIMIT_KB" -gt 0 ] 2>/dev/null; then
    timeout -k 1 ${TIME_LIMIT} sh -c "ulimit -v \"$MEMORY_LIMIT_KB\" && exec ./main" < ./target.in > ./result.out
  else
    timeout -k 1 ${TIME_LIMIT} ./main < ./target.in > ./result.out
  fi
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
