__author__ = 'indieman'

import sys, os, fabtools, random, string
from fabric.api import *
from fabric.contrib import files
from fabtools import require
from fabtools.python import virtualenv, install_pip
from fabtools.files import watch, upload_template
from fabric.contrib.files import comment, uncomment
from fabtools.utils import run_as_root


env.project_name = 'sentry'
env.db_name = env.project_name
env.db_user = env.project_name
env.db_pass = ''
env.project_user = env.project_name

env.shell = '/bin/bash -c'

env.hosts = ['%(project_user)s@95.85.27.119' % env]

env.virtualenv_path = '/usr/local/virtualenvs/%(project_name)s' % env
env.path = '/srv/sites/%(project_name)s' % env
env.manage_path = '/srv/sites/%(project_name)s' % env
env.repository_url = 'https://github.com/indieman/sentry-fab.git'


def create_password(length = 13):
    length = 13
    chars = string.ascii_letters + string.digits + '!@#$%^&*()'
    random.seed = (os.urandom(1024))

    passwd = ''.join(random.choice(chars) for i in range(length))
    return passwd


@task
def host(host_name):
  env.hosts = [host_name]


@task
def setup():
    # require.deb.packages([
    #     'python',
    #     'mercurial',
    #     'subversion',
    #     'git',
    #     'vim',
    #     'sudo',
    #     'python-dev',
    #     'libpq-dev'
    #     ], update=True)

    # # Creating project paths.
    # sudo('mkdir %s -p' % env.path)
    # sudo('chown %(project_user)s %(path)s' % env)
    # sudo('mkdir %s -p' % env.virtualenv_path)
    # sudo('chown %(project_user)s %(virtualenv_path)s' % env)

    # fabtools.git.clone(env.repository_url, path=env.path, use_sudo=False, user=env.project_user)

    # require.python.virtualenv(env.virtualenv_path, use_sudo=False)

    # with virtualenv(env.virtualenv_path):
    #     require.python.requirements(os.path.join(env.path, 'reqs', 'requirements.txt'))

    # env.db_pass = create_password()
    # print 'pass: %s' % env.db_pass
    # upload_template('server_settings.py' % env, '%(path)s/server_settings.py' % env,
    #                 context={'DB_PASSWORD': env.db_pass}, use_jinja=True)

    # print 'pass: %s' % env.db_pass
    # # Require a PostgreSQL server
    # require.postgres.server()
    # require.postgres.user(env.db_user, password=env.db_pass, createdb=False, createrole=True)
    # require.postgres.database(env.db_name, env.db_user)
    # print 'pass: %s' % env.db_pass

    # require.supervisor.process(env.project_name,
    #                            command='%(virtualenv_path)s/bin/sentry --config=%(path)s/sentry.conf.py start' % env,
    #                            directory=env.path,
    #                            user=env.user,
    #                            stdout_logfile='%(path)s/log/sentry_supervisor.log' % env
    # )

    # sentry('migrate')
    with virtualenv(env.virtualenv_path):
        run('sentry --config=/srv/sites/sentry/sentry.conf.py upgrade')

    # Require an nginx server proxying to our app
    require.nginx.proxied_site('sentry',
                               port=80,
                               docroot = '%(path)s/static' % env,
                               proxy_url='http://127.0.0.1:9000')

    remove_default_nginx()


def get_home_dir(username):
    if username == 'root':
        return '/root/'
    return '/home/%s/' % username


@task
def create_project_user(pub_key_file, username=None):
    """
    Creates linux account, setups ssh access.

    Example::

        fab create_linux_account:"/home/indieman/.ssh/id_rsa.pub"

    """
    require.deb.packages(['sudo'])
    with open(os.path.normpath(pub_key_file), 'rt') as f:
        ssh_key = f.read()

    username = username or env.project_user

    with (settings(warn_only=True)):
        sudo('adduser %s --disabled-password --gecos ""' % username)
        # sudo('adduser %s --gecos ""' % username)
    home_dir = get_home_dir(username)
    with cd(home_dir):
        sudo('mkdir -p .ssh')
        files.append('.ssh/authorized_keys', ssh_key, use_sudo=True)
        sudo('chown -R %s:%s .ssh' % (username, username))

    line = '%s ALL=(ALL) NOPASSWD: ALL' % username
    files.append('/etc/sudoers', line)


@task
def sentry(command, noinput=True):
    """
    Run manage command.
    """
    with virtualenv(env.virtualenv_path):
        if noinput:
            run('sentry --config=/srv/sites/sentry/sentry.conf.py ' % env + command + ' --noinput')
        else:
            run('sentry --config=/srv/sites/sentry/sentry.conf.py ' % env + command)


@task
def remove_default_nginx():
    sudo('rm /etc/nginx/sites-enabled/default')
    restart('nginx')

@task
def create_super_user():
    with virtualenv(env.virtualenv_path):
        run('sentry --config=/srv/sites/sentry/sentry.conf.py createsuperuser')
