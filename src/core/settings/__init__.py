# import os
# from dotenv import load_dotenv

# # load environment variables from .env file
# dotenv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
# load_dotenv(dotenv_path)

# # determine which settings to use based on ENV variable
# ENV = os.getenv('ENV')

# if ENV == 'stage':
#     from .stage import *
#     print('Stage environment is running')
# elif ENV == 'prod':
#     from .prod import *
#     print('Production environment is running')
# else:
#     from .local import *
#     print('Invalid or missing ENV variable in .env file')
#     print('Local environment is running')



