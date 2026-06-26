#!/bin/bash

OSI_DIR="/mnt/c/Users/Mayukh Jain/osdag-core/Column to Column Cover Plate Bolted"
OUTPUT_DIR="${HOME}/osdag_test_output"
LOG_FILE="${OUTPUT_DIR}/test_results.log"

mkdir -p "$OUTPUT_DIR"
echo "" > "$LOG_FILE"
echo "==========================================" >> "$LOG_FILE"
echo "Osdag CLI Test Run - $(date)" >> "$LOG_FILE"
echo "==========================================" >> "$LOG_FILE"

PASS=0
FAIL=0

for osi_file in "$OSI_DIR"/*.osi; do
    [ -f "$osi_file" ] || continue
    filename=$(basename "$osi_file" .osi)
    echo "Testing: $filename"
    echo "----------------------------------------" >> "$LOG_FILE"
    echo "Testing: $osi_file" >> "$LOG_FILE"

    osdag-cli run module -i "$osi_file" -t generate_report -o "$OUTPUT_DIR/$filename" >> "$LOG_FILE" 2>&1

    if [ $? -eq 0 ]; then
        echo "PASS: $filename" >> "$LOG_FILE"
        ((PASS++))
    else
        echo "FAIL: $filename" >> "$LOG_FILE"
        ((FAIL++))
    fi
done

echo "==========================================" >> "$LOG_FILE"
echo "Results: $PASS passed, $FAIL failed" >> "$LOG_FILE"
echo "==========================================" >> "$LOG_FILE"

echo ""
echo "Done. Results saved to $LOG_FILE"
echo "Passed: $PASS"
echo "Failed: $FAIL"