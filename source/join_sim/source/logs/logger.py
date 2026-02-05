import logging


""" FOR TEMPLATE DEBUGGING AS DEBUG WILL CAUSE DISCORDBOT TO STOP WORKING"""
TEMPLATE_LEVEL = 5
logging.addLevelName(TEMPLATE_LEVEL,"TEMPLATE")
def template(self,message,*args,**kwargs):
    if self.isEnabledFor(TEMPLATE_LEVEL):
        self._log(TEMPLATE_LEVEL,message,args,**kwargs)

with open("source/join_sim/source/logs/logs.txt", 'w') as file:
    file.close()
    
logging_level = logging.DEBUG   

logger = logging.getLogger("reconnect")
logging.basicConfig(filename="source/join_sim/source/logs/logs.txt",level=logging_level,format="%(asctime)s - %(levelname)s - %(funcName)s - %(message)s",datefmt="%H:%M:%S")
logger.setLevel(logging_level)