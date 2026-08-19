@echo off
echo ========================================================
echo  Paigaldan PlutoF 'seen' CLI tooriista (Windows)...
echo ========================================================

python -m pip install -r requirements.txt

if not exist "%USERPROFILE%\.plutof_env" (
    copy .env.example "%USERPROFILE%\.plutof_env"
    echo Palun ava fail %USERPROFILE%\.plutof_env ja sisesta oma PlutoF volitused.
)

echo.
echo Valmis! Saad tooriista kaivitada käsuga: python seen.py --help
pause
