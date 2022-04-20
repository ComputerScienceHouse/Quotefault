# Quotefault
Quote-submission system for members of CSH.  Utilizes a CSH Bootsrap framework for the front-end webpages and a Flask app backend to send/retrieve quotes in a MySQL database.

## Dev Setup
This project is built in Python 3, and all of its dependencies are accesible via pip.  **Before getting started, please be aware that the LDAP dependency has been known to have issues on Windows operating systems, and it is HIGHLY reccomended that you work on a distribution of the Linux operating system to circumvent this problem.**

### Installing Python
[This guide](https://docs.python-guide.org/starting/installation/#installation-guides) should cover installing python
then you need to make sure you [have pip installed](https://packaging.python.org/tutorials/installing-packages/#ensure-you-can-run-pip-from-the-command-line).

### Installing Docker
[This guide](https://docs.docker.com/get-docker/) should cover installing docker
This will only work on Mac/Linux, so Windows users will still have to use the python method.

### Recommended setup
From inside your repository directory run
```
docker build -t "quotefault" .
docker run -p 8080:8080 --name "quotefault" --rm quotefault:latest
```

### Alternate setup (Without Docker)
From inside your repository directory run
```
python -m virtualenv venv # Sets up virtualenve in the venv directory in your working directory
source venv/bin/activate # Activates the virtual environment
pip install -r requirements.txt # Installs all of the dependencies listed in the requirements to the virtualenv
```

### Accessing the DB locally
At this point all the dependencies are installed, so the next step would be to copy `config.env.py` to `config.py` and fill in fields (you probably also need to set `SERVER_NAME = 127.0.0.1:5000`, which is where flask will put local applications).  Since we can't freely distribute the keys for the config file, there's a few options available to access the database.  The first is to simply contact any CSH RTP or Webmaster for the keys; if they approve you can proceed with the original course of action to get your local dev up and running (just make sure you aren't putting those keys back up publicly when you push!).  Alternatively, they could ask you to make a branch on this repo so they could make a dev instance online that you could then access to see your changes.  Finally, you could make your own MySQL database with test data to work off of.  For this, usage of a [Docker](https://www.docker.com/get-started) container is reccomended (MySQL specific docs can be found [here](https://docs.docker.com/samples/library/mysql/)).  To learn more about MySQL, check [this link](https://dev.mysql.com/doc/mysql-getting-started/en/), and to format your table so it mimics ours simply refer to the init.py file for all the necessary columns.

### Running the app
All that's left is running it with `flask run`. Flask should automatically find `app.py`, though you may want to set debug mode with `export FLASK_ENV=development` before you run it.
