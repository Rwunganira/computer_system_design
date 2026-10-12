#!/usr/bin/env bash
# Run every module page through test_lesson.js and fail on JS errors, overflow at phone
# width, or an exercise whose own solution does not pass. Python errors are only reported,
# because a few cells demonstrate an error on purpose.
#   cd web && npm install --no-save playwright skulpt@1.2.0 && bash tools/check_all.sh
set -u
shopt -s nullglob
cd "$(dirname "$0")/.."
status=0
for page in m*.html; do
  id="${page%.html}"
  out="$(node tools/test_lesson.js "$id")"
  echo "$out" | grep -E "^m[0-9]+:|quizzes|scrollWidth|errors:|exercise .*solution"
  if echo "$out" | grep -q "<<< OVERFLOW"; then echo "FAIL $id: overflow at 390px"; status=1; fi
  if ! echo "$out" | grep -q "errors: none"; then echo "FAIL $id: page errors"; status=1; fi
  if echo "$out" | grep "solution ->" | grep -vq "pass"; then echo "FAIL $id: an exercise solution does not pass"; status=1; fi
done
exit $status
