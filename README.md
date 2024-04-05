pg-monitor
==========

Try to create a slow monitor using PostgreSQL as a test.

## Prepare

Install several python packages.

``` sh
sudo dnf install python3-pip perl-devel perl-FindBin
pip3 install --user -U pip
pip3 install --user -U psycopg pytz lxml html5lib beautifulsoup4 pyepics pyModbusTCP rich
```

Disable Firewall and SELinux.

``` sh
sudo systemctl disable --now firewalld
sudo nano /etc/selinux/config
# SELINUX=disabled
sudo reboot
```

## Install PostgreSQL

``` sh
# Install the repository RPM:
sudo dnf install -y https://download.postgresql.org/pub/repos/yum/reporpms/EL-9-x86_64/pgdg-redhat-repo-latest.noarch.rpm

# Disable the built-in PostgreSQL module:
sudo dnf -qy module disable postgresql

# Install PostgreSQL:
sudo dnf install -y postgresql16-server
```

## Setup PostgreSQL

```sh
# Initialize the database:
sudo /usr/pgsql-16/bin/postgresql-16-setup initdb

# Enable and start the server:
sudo systemctl enable --now postgresql-16
```

Install EPICS base.

```sh
cd epics
./build.sh
```

Add EPICS environment to .bash_profile.

```sh
export EPICS_TOP=/path/to/epics/base
export PATH=$PATH:$EPICS_TOP/bin/linux-x86_64
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$EPICS_TOP/lib/linux-x86_64
export EPICS_CA_AUTO_ADDR_LIST=no
export EPICS_CA_ADDR_LIST=192.153.109.232 # jlandmzcagw01.j-parc.jp
export PYEPICS_LIBCA=$EPICS_TOP/lib/linux-x86_64/libca.so
```