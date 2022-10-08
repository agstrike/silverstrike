# SilverStrike
[![Actions Status](https://github.com/agstrike/silverstrike/workflows/Test%20and%20Lint/badge.svg)](https://github.com/agstrike/silverstrike/actions)
[![codecov](https://codecov.io/gh/agstrike/silverstrike/branch/master/graph/badge.svg)](https://codecov.io/gh/agstrike/silverstrike)

Webapp based on Django to manage personal finances

## Demo
There is a [demo](https://demo.silverstrike.org/) available.
It is regularly updated from the master branch.

## Get SilverStrike running on your machine

The easiest way to deploy SilverStrike is to clone this repository and use the provided docker-compose file. Check out you own branch so you can persist your configuration. 
You need to set a SECRET_KEY and should update the domain names and then you can start it up. 
You can generate yourself a random secrety key by running `python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'`

After starting the container, you should create yourself a user account
`docker-compose exec -it ags python manage.py createsuperuser`

To update SilverStrike simply fetch the changes from GitHub and rebuild your container.

By default sqlite is used which should be enough for a local installation. If you'd rather use postgresdb or mariadb you can uncomment the relevant parts in the docker-compose.

In the deploy directory you can find a couple of files:
- **nginx.conf** minimal nginx configuration for a reverse proxy setup
- **local_settings.py** Use this file to override any of the settings found in `settings.py`
- **demo_middleware.py** If you want to use some kind of external authentication you could use this as a starting point

## Contributing

You can contribute in several ways. If you know how to code or are a designer, you are welcome to contribute using pull requests.  
If you speak languages other than english, you are welcome to help translate SilverStrike.

If nothing of the above suits you, you can still contribute by opening issues about defects and things that could be improved or request entirely new features that you think would help others.

More information can be found [here](https://github.com/agstrike/silverstrike/blob/master/CONTRIBUTING.md).

## Branding

SilverStrike is derived from the German name Silberschlag. Silberschlag is the name of a crater on the moon which is named after a German Scientist.

SilverStrike is abbreviated as AgStrike or simply AgS. SilverStrike is pronounced AgS or SilverStrike.
An alternative way of writing SilverStrike is `silverstrike` with no capital letters. Abbreviations have to be written as mentioned here.
