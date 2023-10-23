<div align="center">
	<img src="https://github.com/sparrow/design/raw/master/logos/png/snova-logo.png" height="128">
	<h2>Snova</h2>
</div>

Snova is a command-line utility that helps you to install, update, and manage multiple sites for Sparrow/SHOPPER applications on [*nix systems](https://en.wikipedia.org/wiki/Unix-like) for development and production.

<div align="center">
	<a target="_blank" href="https://www.python.org/downloads/" title="Python version">
		<img src="https://img.shields.io/badge/python-%3E=_3.7-green.svg">
	</a>
	<a target="_blank" href="https://app.travis-ci.com/github/sparrow/snova" title="CI Status">
		<img src="https://app.travis-ci.com/sparrow/snova.svg?branch=develop">
	</a>
	<a target="_blank" href="https://pypi.org/project/sparrow-snova" title="PyPI Version">
		<img src="https://badge.fury.io/py/sparrow-snova.svg" alt="PyPI version">
	</a>
	<a target="_blank" title="Platform Compatibility">
		<img src="https://img.shields.io/badge/platform-linux%20%7C%20osx-blue">
	</a>
	<a target="_blank" href="https://app.fossa.com/projects/git%2Bgithub.com%2Fsparrow%2Fsnova?ref=badge_shield" title="FOSSA Status">
		<img src="https://app.fossa.com/api/projects/git%2Bgithub.com%2Fsparrow%2Fsnova.svg?type=shield">
	</a>
	<a target="_blank" href="#LICENSE" title="License: GPLv3">
		<img src="https://img.shields.io/badge/License-GPLv3-blue.svg">
	</a>
</div>

## Table of Contents

- [Table of Contents](#table-of-contents)
- [Installation](#installation)
	- [Containerized Installation](#containerized-installation)
	- [Easy Install Script](#easy-install-script)
		- [Setup](#setup)
		- [Arguments](#arguments)
		- [Troubleshooting](#troubleshooting)
	- [Manual Installation](#manual-installation)
- [Basic Usage](#basic-usage)
- [Custom Snova Commands](#custom-snova-commands)
- [Guides](#guides)
- [Resources](#resources)
- [Development](#development)
- [Releases](#releases)
- [License](#license)


## Installation

A typical snova setup provides two types of environments &mdash; Development and Production.

The setup for each of these installations can be achieved in multiple ways:

 - [Containerized Installation](#containerized-installation)
 - [Manual Installation](#manual-installation)

We recommend using Docker Installation to setup a Production Environment. For Development, you may choose either of the two methods to setup an instance.

Otherwise, if you are looking to evaluate Sparrow apps without hassle of hosting, you can try them [on sparrowcloud.com](https://sparrowcloud.com/).


### Containerized Installation

A Sparrow/SHOPPER instance can be setup and replicated easily using [Docker](https://docker.com). The officially supported Docker installation can be used to setup either of both Development and Production environments.

To setup either of the environments, you will need to clone the official docker repository:

```sh
$ git clone https://github.com/sparrow/sparrow_docker.git
$ cd sparrow_docker
```

A quick setup guide for both the environments can be found below. For more details, check out the [Sparrow/SHOPPER Docker Repository](https://github.com/sparrow/sparrow_docker).

### Easy Install Script

The Easy Install script should get you going with a Sparrow/SHOPPER setup with minimal manual intervention and effort.

This script uses Docker with the [Sparrow/SHOPPER Docker Repository](https://github.com/sparrow/sparrow_docker) and can be used for both Development setup and Production setup.

#### Setup

Download the Easy Install script and execute it:

```sh
$ wget https://raw.githubusercontent.com/sparrow/snova/develop/easy-install.py
$ python3 easy-install.py --prod --email your@email.tld
```

This script will install docker on your system and will fetch the required containers, setup snova and a default SHOPPER instance.

The script will generate MySQL root password and an Administrator password for the Sparrow/SHOPPER instance, which will then be saved under `$HOME/passwords.txt` of the user used to setup the instance.
It will also generate a new compose file under `$HOME/<project-name>-compose.yml`.

When the setup is complete, you will be able to access the system at `http://<your-server-ip>`, wherein you can use the Administrator password to login.

#### Arguments

Here are the arguments for the easy-install script

```txt
usage: easy-install.py [-h] [-p] [-d] [-s SITENAME] [-n PROJECT] [--email EMAIL]

Install Sparrow with Docker

options:
  -h, --help            		show this help message and exit
  -p, --prod            		Setup Production System
  -d, --dev             		Setup Development System
  -s SITENAME, --sitename SITENAME      The Site Name for your production site
  -n PROJECT, --project PROJECT         Project Name
  --email EMAIL         		Add email for the SSL.
```

#### Troubleshooting

In case the setup fails, the log file is saved under `$HOME/easy-install.log`. You may then

- Create an Issue in this repository with the log file attached.

### Manual Installation

Some might want to manually setup a snova instance locally for development. To quickly get started on installing snova the hard way, you can follow the guide on [Installing Snova and the Sparrow Framework](https://sparrow.io/docs/user/en/installation).

You'll have to set up the system dependencies required for setting up a Sparrow Environment. Checkout [docs/installation](https://github.com/sparrow/snova/blob/develop/docs/installation.md) for more information on this. If you've already set up, install snova via pip:


```sh
$ pip install sparrow-snova
```


## Basic Usage

**Note:** Apart from `snova init`, all other snova commands are expected to be run in the respective snova directory.

 * Create a new snova:

	```sh
	$ snova init [snova-name]
	```

 * Add a site under current snova:

	```sh
	$ snova new-site [site-name]
	```
	- **Optional**: If the database for the site does not reside on localhost or listens on a custom port, you can use the flags `--db-host` to set a custom host and/or `--db-port` to set a custom port.

		```sh
		$ snova new-site [site-name] --db-host [custom-db-host-ip] --db-port [custom-db-port]
		```

 * Download and add applications to snova:

	```sh
	$ snova get-app [app-name] [app-link]
	```

 * Install apps on a particular site

	```sh
	$ snova --site [site-name] install-app [app-name]
	```

 * Start snova (only for development)

	```sh
	$ snova start
	```

 * Show snova help:

	```sh
	$ snova --help
	```


For more in-depth information on commands and their usage, follow [Commands and Usage](https://github.com/sparrow/snova/blob/develop/docs/commands_and_usage.md). As for a consolidated list of snova commands, check out [Snova Usage](https://github.com/sparrow/snova/blob/develop/docs/snova_usage.md).


## Custom Snova Commands

If you wish to extend the capabilities of snova with your own custom Sparrow Application, you may follow [Adding Custom Snova Commands](https://github.com/sparrow/snova/blob/develop/docs/snova_custom_cmd.md).


## Guides

- [Configuring HTTPS](https://sparrow.io/docs/user/en/snova/guides/configuring-https.html)
- [Using Let's Encrypt to setup HTTPS](https://sparrow.io/docs/user/en/snova/guides/lets-encrypt-ssl-setup.html)
- [Diagnosing the Scheduler](https://sparrow.io/docs/user/en/snova/guides/diagnosing-the-scheduler.html)
- [Change Hostname](https://sparrow.io/docs/user/en/snova/guides/adding-custom-domains)
- [Manual Setup](https://sparrow.io/docs/user/en/snova/guides/manual-setup.html)
- [Setup Production](https://sparrow.io/docs/user/en/snova/guides/setup-production.html)
- [Setup Multitenancy](https://sparrow.io/docs/user/en/snova/guides/setup-multitenancy.html)
- [Stopping Production](https://github.com/sparrow/snova/wiki/Stopping-Production-and-starting-Development)

For an exhaustive list of guides, check out [Snova Guides](https://sparrow.io/docs/user/en/snova/guides).


## Resources

- [Snova Commands Cheat Sheet](https://sparrow.io/docs/user/en/snova/resources/snova-commands-cheatsheet.html)
- [Background Services](https://sparrow.io/docs/user/en/snova/resources/background-services.html)
- [Snova Procfile](https://sparrow.io/docs/user/en/snova/resources/snova-procfile.html)

For an exhaustive list of resources, check out [Snova Resources](https://sparrow.io/docs/user/en/snova/resources).


## Development

To contribute and develop on the snova CLI tool, clone this repo and create an editable install. In editable mode, you may get the following warning everytime you run a snova command:

	WARN: snova is installed in editable mode!

	This is not the recommended mode of installation for production. Instead, install the package from PyPI with: `pip install sparrow-snova`


```sh
$ git clone https://github.com/sparrow/snova ~/snova-repo
$ pip3 install -e ~/snova-repo
$ snova src
/Users/sparrow/snova-repo
```

To clear up the editable install and switch to a stable version of snova, uninstall via pip and delete the corresponding egg file from the python path.


```sh
# Delete snova installed in editable install
$ rm -r $(find ~ -name '*.egg-info')
$ pip3 uninstall sparrow-snova

# Install latest released version of snova
$ pip3 install -U sparrow-snova
```

To confirm the switch, check the output of `snova src`. It should change from something like `$HOME/snova-repo` to `/usr/local/lib/python3.6/dist-packages` and stop the editable install warnings from getting triggered at every command.


## Releases

Snova's version information can be accessed via `snova.VERSION` in the package's __init__.py file. Eversince the v5.0 release, we've started publishing releases on GitHub, and PyPI.

GitHub: https://github.com/sparrow/snova/releases

PyPI: https://pypi.org/project/sparrow-snova


From v5.3.0, we partially automated the release process using [@semantic-release](.github/workflows/release.yml). Under this new pipeline, we do the following steps to make a release:

1. Merge `develop` into the `staging` branch
1. Merge `staging` into the latest stable branch, which is `v5.x` at this point.

This triggers a GitHub Action job that generates a bump commit, drafts and generates a GitHub release, builds a Python package and publishes it to PyPI.

The intermediate `staging` branch exists to mediate the `snova.VERSION` conflict that would arise while merging `develop` and stable. On develop, the version has to be manually updated (for major release changes). The version tag plays a role in deciding when checks have to be made for new Snova releases.

> Note: We may want to kill the convention of separate branches for different version releases of Snova. We don't need to maintain this the way we do for Sparrow & SHOPPER. A single branch named `stable` would sustain.

## License

This repository has been released under the [GNU GPLv3 License](LICENSE).
