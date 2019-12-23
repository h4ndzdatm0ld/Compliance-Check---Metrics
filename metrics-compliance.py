# /usr/bin/python3
''''
This program is used to SSH across all 7750/7450 platform and extract the TE-Metric of each MPLS interface.
Once the information is extracted via custom NTC-Template/Regex, the ISIS interface Level-2 metric
is updated to match the TE-Metric.
Version 1 - Hugo Tinoco - htinoco@lsnetworks.net - 12/19/2019
'''
#########################################################################
# Imported packages
import sys
import os
from netmiko import Netmiko
from operator import itemgetter
from types import SimpleNamespace
from pymongo import MongoClient
from getpass import getpass
from datetime import datetime
import time
import threading
import logging

#########################################################################
#################### Time Traveler
start_time = datetime.now ()
localtime = time.asctime (time.localtime (time.time ()))
########################################################################
#################### Logging
L = open ('metrics-logz.log', "w+")
logging.basicConfig (filename = ('metrics-logz.log'), level = logging.DEBUG)
logger = logging.getLogger ("netmiko")
#########################################################################

# Extract routers IP by tags from
Client = MongoClient('172.17.25.236')
db = Client["network"] #This is the Database we want to use out of all available in MongoDB.
cx = db['routers'] # This is a collection within the Network Database.

# Create the file from std.output | this was used when the scripts were in two files
# sys.stdout = open('a4routers.txt','wt')

# # # # Loop through all 7750 Tags and extract from MongoDB
for x in cx.find({'tags': '7750'}): #
         my_dict = dict(x) # create a dictionary
         # Print out the two values that matter.
         # print(x['name'], x['address'])
         print(x['address'], file = open("routers.txt", "a"))

# # # # Loop through all 7450 Tags and extract from MongoDB
for y in cx.find({'tags': '7450'}): #
         my_dict = dict(y) # create a dictionary
         # Print out the two values that matter.
         # print(x['name'], x['address'])
         print(y['address'], file = open("routers.txt", "a"))

with open ('routers.txt') as f:
    content = f.read ().splitlines ()
    all_devices = list (content)  # We use this var with a list of IP's and sort through it below  # print (all_devices)
# #
# # Use getpass
username = input ("Username: ")
password = getpass ()
#
#
def mpls_metrics(a_device):
    '''
    Examine 'show router mpls interface results - Extract Interface Name/TE-Metric
    with regex / NTC-Templates.
    '''
    global dict_mplsInt, dict_IsisInt
    try:
        net_connect = Netmiko (host = a_device, username = username, password = password,
                               device_type = 'alcatel_sros')  # Home Sandbox
        # net_connect = Netmiko(host='192.168.253.136', username=username,password=password, device_type='alcatel_sros') # Work Sandbox
        mplsInt = net_connect.send_command ("show router mpls interface", use_textfsm = True)
        sortedListMpls = sorted (mplsInt, key = itemgetter ('port'))

        for dict_mplsInt in sortedListMpls:
            n = SimpleNamespace (**dict_mplsInt)
            cmd = "/configure router isis interface " + n.interface + " level 2 metric " + n.te_metric
            net_connect.send_command (cmd)  # Update the IS-IS Metrics with the extraced TE-Metric value.
            mpls_pre_int = n.interface
            mpls_pre_metric = n.te_metric
        # except Exception as e:
        # print ("There was an error", e)

        # def isis_interface(a_device):
        # try:
        time.sleep (2) # Ensure the ISIS interface has been configured.
        # net_connect = Netmiko(host=a_device, username=username,password=password, device_type='alcatel_sros') # Home Sandbox
        sysname = net_connect.send_command ('show system information | match Name')
        isisInt = net_connect.send_command ("show router isis interface", use_textfsm = True)

        sortedListIsis = sorted (isisInt, key = itemgetter ('interface'))
        print (sysname)

        for dict_IsisInt in sortedListIsis:
            print ('Updated ISIS Interface: ' + dict_IsisInt["interface"] + " with new metrics: " + dict_IsisInt[
                "l2_metric"])

        if dict_IsisInt["l2_metric"] != mpls_pre_metric:
            print ("ISIS Metric: "+ (dict_IsisInt["l2_metric"]+ " on interface: "+ (dict_IsisInt["interface"]) +
                                     " Mismatch to MPLS Metric: " + (mpls_pre_metric)))
    except Exception as er:
        print ("Error Encountered: ", er)


def main():
    '''
     Use threads and Netmiko to connect to each of the devices.
    '''
    # Time Traveler
    start_time = datetime.now ()
    localtime = time.asctime (time.localtime (time.time ()))

    for a_device in all_devices:
        my_thread = threading.Thread (target = mpls_metrics, args = (a_device,))
        # my_other_thread = threading.Thread(target=isis_interface, args=(a_device,))
        my_thread.start ()  # my_other_thread.start()
    main_thread = threading.currentThread ()
    for some_thread in threading.enumerate ():
        if some_thread != main_thread:
            some_thread.join ()

    # Tell me how long it took to run this script!
    end_time = datetime.now ()
    total_time = end_time - start_time
    print ("It took the following amount of time to automate this task:")
    print (total_time)


if __name__ == "__main__":
    main ()
