"""
This file is responsible to manage DM Check clients
"""

'''
Built-in modules
'''
import pdb
import os
import time

'''
User defined modules
'''
from libs.twitter_logging import console_logger as logger
from libs.cypher_store import DMCheckCypherStoreClientIntf as StoreIntf
from libs.cypher_store import ServiceManagementIntf as ServiceIDIntf
from libs.service_manager_client import ServiceManagerClient as ServiceIntf

from libs.service_client_errors import ClientSanityFailed, ServiceNotReady

class DMCheckBucketManagerClient:
    '''
        It uses Facade design pattern
    '''

    def __init__(self, client_id, screen_name, dm_from_id, dm_from_screen_name):
        self.client_id = client_id
        self.screen_name = screen_name
        self.dm_from_id = dm_from_id
        self.dm_from_screen_name = dm_from_screen_name
        self.dataStoreIntf = StoreIntf()
        self.service_id = ServiceIDIntf.ServiceIDs.DMCHECK_SERVICE
        self.service_manager = ServiceIntf(client_id, screen_name, self.service_id)
        
    def register_service(self):
        #tested
        self.service_manager.register_service()

    def assignBuckets(self, bucketscount=1):
        #tested
        logger.info("Assigning {} bucket(s) to the client".format(bucketscount, self.client_id))
        ts = time.perf_counter()
        if not self.__client_sanity_passed():
            return ClientSanityFailed()
        if not self.__service_sanity_passed():
            return ServiceNotReady()       
        #TODO: Threshold the max bucket count

        self.dataStoreIntf.configure(client_id=self.client_id, screen_name=self.screen_name, 
                dm_from_id=self.dm_from_id, dm_from_screen_name=self.dm_from_screen_name)
        buckets = self.dataStoreIntf.assign_buckets(self.client_id, bucketscount)
        print("Assigned {} bucket(s) to the client".format(buckets))
        buckets_for_client = []
        for id in buckets:
            users = self.dataStoreIntf.get_all_entities_for_bucket(id)
            buckets_for_client.append({'bucket_id':id, 'users':users})
        te = time.perf_counter()
        print('perfdata: func:%r took: %2.4f sec' % ('assignBuckets', te-ts))
        return buckets_for_client

    def store_processed_data_for_bucket(self, bucket):
        ts = time.perf_counter()
        if not self.__client_sanity_passed():
            return ClientSanityFailed()
        bucket_id = bucket['bucket_id']
        users = bucket['users']
        self.__store_dmcheck_status_for_bucket(bucket_id, users)
        pdb.set_trace()
        self.__release_bucket(bucket_id)
        print("Successfully processed {} bucket".format(bucket['bucket_id']))
        te = time.perf_counter()
        print('perfdata: func:%r took: %2.4f sec' % ('store_processed_data_for_bucket', te-ts))
        pass

    def __store_dmcheck_status_for_bucket(self, bucket_id, users):
        #tested
        candm_users = [user for user in users if user['candm'].upper()=="DM"]
        cantdm_users = [user for user in users if user['candm'].upper()=="NON_DM"]
        unknown_users = [user for user in users if user['candm'].upper()=="UNKNOWN"]
        bucket_for_db = {'bucket_id': bucket_id, 'candm_users':candm_users, 'cantdm_users':cantdm_users, 'unknown_users':unknown_users}
        #TODO: Try to make atomic for each bucket
        self.dataStoreIntf.store_processed_data_for_bucket(client_id=self.client_id, bucket=bucket_for_db)

    def __client_sanity_passed(self):
        #tested
        if not self.service_manager.valid_client():
            print("Unregistered client {} is trying to get buckets".format(self.client_id))
            return False
        return True

    def __service_sanity_passed(self):
        #tested
        if not self.service_manager.valid_service():
            print("Service with ID {} is not ready".format(self.service_id))
            return False
        return True