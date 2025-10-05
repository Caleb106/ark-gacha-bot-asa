##Gravity Gacha Bot (Render Bot Version)

  
  #Step One
    
    Open Terminal or PowerShell, change to your preferred folder, then clone with:
      cd C:\YOUR\PREFERRED\FOLDER
      git clone --single-branch --branch Render_Bot https://github.com/AZX-215/ASA-Gravity-Gacha-Bot.git
      cd ASA-Gravity-Gacha-Bot
      git status

  #Step Two

    You need Python 3.11 and 3.13. Run prerequisites_check.bat. It will check and install both versions if necessary. Proceed with the prompts.
    
  #Step Three

    Create the virtual environment and install bot prerequisites. Run setup.bat until it says to press any key (or closes).
  
  #Step Four

    If you received settings.py from @AZX, replace the cloned file with that one.
    If not, create your own Discord bot, update channel IDs, and acquire an API token. Join https://discord.gg/vxzDRgsF if you need help.

  #Step Five

    If you are running Gravity Render Bot, you do not need to edit render_route.json.
    For other setups, edit json_files/render_route.json and replace the teleporters with your TP names:

      {
        "name": "Render #1",
        "teleporter": "Lava Rathole!"   ##must exactly match your in-game teleporter name!
      },


  #Step Six

    Run run.bat. The bot will connect. Use /start in Discord to start the bot.
