@echo off
SET SERVICE_NAME=DiscordBot
SET BOT_DIRECTORY=C:\Path\To\Your\Bot
SET GIT_PATH=C:\Path\To\Git\bin\git.exe

echo Stopping the NSSM service...
nssm stop %SERVICE_NAME%

echo Navigating to the bot directory...
cd %BOT_DIRECTORY%

echo Pulling the latest changes from Git...
%GIT_PATH% pull

echo Starting the NSSM service...
nssm start %SERVICE_NAME%

echo Update complete!
pause 