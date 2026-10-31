Automated gacha bot for ark survival ascended
Automate Element Dust and other resources

if you have come across this and need any help the community discord is https://discord.gg/KAZtg7hDXS and someone might be able to help you out
 and a youtube video of bot install and setup till it runs https://www.youtube.com/watch?v=uz5wbqzQ6I8

To Setup -> being able to run the bot 
preferably using python 3.11 (other versions will work if you download the right dependencies however the build script is for 3.11)
Running the setup.bat file will automatically download python if you dont already have it installed Make sure to check for adding python to path 
and will install the dependencies required to a venv folder in the project
you can then either run main.py or run the run.bat which will also pull(check for updates) from github if you have cloned the project

Some clarification on the settings
in main settings Ledger Gacha Wait determines how long the bot will wait before regoing to the gachas this setting only matters with the cargo ledger option 
as it is dependent on your gachas weight stats 
Replenish interval is the amount of time between the bot going to pickup from the central station For berry bot it goes to feeding troughs
if you have a cargo ledger bot it will go to the cargo ledger 

You can also increase the default amount of vaults and dedi boxs in the respected json_files/*.json 
recommended if you do not know what you are doing to paste the files into AI 
For dedis change the active Flag under the dedi locations name from "false" to "true" and add or remove box positions
For vaults when adding more vaults you will need to change side to "custom" and enter in yaw and pitch values into the respected areas 

If you would like to collect reasources from a gacha for instanance if you have a silica or paste set up you can change the Resource type to "collect" 
you can also add in another argument called depo_tp which will deposit the gachas collectables in a seperate location comapared to your main deposit section 