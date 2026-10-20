@echo off
echo Starting NHL Prop Engine Daily Update...

:: 1. Move into the src folder
cd src

:: 2. Run the pipeline
python -m main gametime

:: 3. Check if the python script actually succeeded
if %ERRORLEVEL% NEQ 0 (
    echo Pipeline failed. Aborting Git push.
    cd ..
    pause
    exit /b
)

:: 4. Move back to the root folder
cd ..

:: 5. Force add the data and push to GitHub
echo Pushing data to GitHub...
git add -f data/built/readytouse.csv
git commit -m "server chunk : updating"
git push

echo Done! Streamlit will update shortly.
pause