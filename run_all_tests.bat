@echo off
setlocal enabledelayedexpansion

set OSI_DIR=C:\Users\Mayukh Jain\osdag-core\Column to Column Cover Plate Bolted
set OUTPUT_DIR=C:\Users\Mayukh Jain\Documents\osdag_test_output
set LOG_FILE=%OUTPUT_DIR%\test_results.log

mkdir "%OUTPUT_DIR%" 2>nul
echo. > "%LOG_FILE%"
echo ========================================== >> "%LOG_FILE%"
echo Osdag CLI Test Run - %date% %time% >> "%LOG_FILE%"
echo ========================================== >> "%LOG_FILE%"

set PASS=0
set FAIL=0

for %%f in ("%OSI_DIR%\*.osi") do (
    echo Testing: %%~nf
    echo ---------------------------------------- >> "%LOG_FILE%"
    echo Testing: %%f >> "%LOG_FILE%"

    osdag-cli run module -i "%%f" -t generate_report -o "%OUTPUT_DIR%\%%~nf" >> "%LOG_FILE%" 2>&1

    if !errorlevel! == 0 (
        echo PASS: %%~nf >> "%LOG_FILE%"
        set /a PASS+=1
    ) else (
        echo FAIL: %%~nf >> "%LOG_FILE%"
        set /a FAIL+=1
    )
)

echo ========================================== >> "%LOG_FILE%"
echo Results: !PASS! passed, !FAIL! failed >> "%LOG_FILE%"
echo ========================================== >> "%LOG_FILE%"

echo.
echo Done. Results saved to %LOG_FILE%
echo Passed: !PASS!
echo Failed: !FAIL!