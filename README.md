# launch-darkly-key-management-tool
This is a Repo dedicated to creating a scheduled key management project that will routinely check if members have used their launch darkly access in a while. The purpose of this is to remove users who have not used LD in awhile in efforts to free seats for LD


1. Configure .env file to include all environment vars. These vars will be used for authenticating into the LD api, database for auditing, and settings for determine who should be deleted.
2. Make sure  3.x.x is installed on your running machine
3. In terminal run pip install -r requirements.txt
3. Once these configurations are made the script will do the following
        1. Query launch darkly and get a list of all users who have not logged in LAUNCH_DARKLY_THRESHOLD of days
        2. Check to see if the user has already been saved in the database previously
        3. If they have previously been in the database then call Launch Darkly again to remove the user from launch darkly then update the database to toggle the has_been_deleted flag
        4. If they did not exist in the database before then add them to the database and set the scheduled delete date. Once this is done then send out an email to the user to prompt them to login or their
4. Run python main.py 
