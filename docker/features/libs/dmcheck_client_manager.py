"""
This file is responsible to manage client registration management
"""

'''
Built-in modules
'''
import pdb
import os
from libs.twitter_logging import console_logger as logger

'''
User defined modules
'''
store_type = os.getenv("DB_STORE_TYPE", "file_store")
if store_type.lower() == "file_store":
    from libs.file_store import DMFileStoreIntf as DMStoreIntf
else:
    from libs.cypher_store import DMCypherStoreIntf as DMStoreIntf

#TODO: Make it singleton
class DMCheckClientManager:
    def __init__(self):
        self.dataStoreIntf = DMStoreIntf()
    """
    client_id : Twitter UID
    client_screen_name: Twitter screen name of user
    """
    def register_client(self, client_id, client_screen_name):
        logger.info("Processing registeration request for client with ID={} and screen_name={}".format(client_id, client_screen_name))
        valid_client = self.dataStoreIntf.dmcheck_client_valid(client_id)
        if not valid_client:
            self.dataStoreIntf.add_dmcheck_client(client_id, client_screen_name)
        else:
            logger.info("client with ID={} and screen_name={} has registered earlier as well".format(client_id, client_screen_name))
        self.dataStoreIntf.change_state_dmcheck_client(client_id, "ACTIVE")
        logger.info("Successfully registered client with ID={} and screen_name={}".format(client_id, client_screen_name))
        return True

    """
    client_id : Twitter UID
    client_screen_name: Twitter screen name of user
    """
    def unregister_client(self, client_id, client_screen_name):
        logger.info("Processing registeration request for client with ID={} and screen_name={}".format(client_id, client_screen_name))
        valid_client = self.dataStoreIntf.dmcheck_client_valid(client_id)
        if not valid_client:
            logger.error("Ignoring as {} is not a registered DM check user".format(client_id))
            return False
        self.dataStoreIntf.change_state_dmcheck_client(client_id, "DEACTIVE")
        logger.info("Successfully unregistered client with ID={} and screen_name={}".format(client_id, client_screen_name))
        return True

