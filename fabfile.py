__author__ = 'indieman'

import sys, os, fabtools
from fabric.api import *
from fabtools import require
from fabtools.python import virtualenv, install_pip
from fabtools.files import watch
from fabric.contrib.files import comment, uncomment
from fabtools.utils import run_as_root

env.hosts = ['root@10.88.12.1']
env.project_name = 'reeliner'
env.virtualenv_path = '/usr/local/virtualenvs/%(project_name)s' % env
env.path = '/srv/sites/%(project_name)s' % env
env.repository_url = 'https://indieman@bitbucket.org/indieman/reeliner.com'
env.database_name = env.project_name
env.user = env.project_name
env.shell = '/bin/bash -c'
env.rabbit_user = 'rabbit_user'
env.rabbit_pass = 'rabbit_pass'


@task
def setup():
    require.deb.packages([
        'python2.6',
        'libxml2-dev',
        'mercurial',
        'subversion',
        'git',
        'vim',
        'sudo',
        'libpq-dev',
        'libxml2-dev',
        'libxslt1-dev',
        'python2.6-dev'
    ])

    clone_repo()
    with cd(env.path):
        run_as_root('chmod ogu+x manage.py')

    require.python.virtualenv(env.virtualenv_path, use_sudo=False)

    with virtualenv(env.virtualenv_path):
        require.python.requirements(os.path.join(env.path, 'reqs', 'all.txt'))

    # # Require a PostgreSQL server
    require.postgres.server()
    require.postgres.user(env.user, 'mu#^73U#P_o$JWf')
    require.postgres.database(env.database_name, env.user)


    # Require a supervisor process for our app
    require.supervisor.process(env.project_name,
                               command='%(virtualenv_path)s/bin/gunicorn -c %(path)s/_deploy/gunicorn.conf.py reeliner.wsgi:application' % env,
                               directory=env.path,
                               user=env.user,
                               stdout_logfile='%(path)s/log/gunicorn_supervisor.log' % env
    )

    # Require an nginx server proxying to our app
    require.nginx.proxied_site('reeliner.com',
                               docroot='%(path)s/media' % env,
                               proxy_url='http://127.0.0.1:8888'
    )
    # create_dirs()


@task
def sentry_setup():
    require.deb.packages([
        'python2.6',
        'mercurial',
        'subversion',
        'git',
        'vim',
        'sudo',
        'python2.6-dev',
        ])

    require.python.virtualenv(env.virtualenv_path, use_sudo=False)

    with virtualenv(env.virtualenv_path):
        require.python.requirements(os.path.join(env.path, 'reqs', 'all.txt'))

    require.postgres.server()
    require.postgres.user(env.user, 'mu#^73U#P_o$JWf')
    require.postgres.database(env.database_name, env.user)


    require.supervisor.process(env.project_name,
                               command='%(virtualenv_path)s/bin/gunicorn -c %(path)s/_deploy/gunicorn.conf.py reeliner.wsgi:application' % env,
                               directory=env.path,
                               user=env.user,
                               stdout_logfile='%(path)s/log/gunicorn_supervisor.log' % env
    )

    require.nginx.proxied_site('reeliner.com',
                               docroot='%(path)s/media' % env,
                               proxy_url='http://127.0.0.1:8888'
    )


@task
def update():
    run('hg pull')


def set_rabbitmq():
    run('rabbitmqctl add_user %(rabbit_user)s %(rabbit_pass)s' % env)
    run("rabbitmqctl add_vhost 'reeliner'")
    run('rabbitmqctl set_permissions -p "reeliner" %(rabbit_user)s ".*" ".*" ".*"' % env)


def manage(command):
    with virtualenv(env.virtualenv_path):
        # run_as_root('manage.py ' + command + ' --noinput')
        run('manage.py ' + command + ' --noinput')


def setup_supervisor():
    run('pip install supervisor')
    supervisord = os.path.join(env.path, 'vf/configs/production/settings/supervisord')
    run('ln -s %s /etc/init.d/supervisord' % supervisord)
    supervisord_conf = os.path.join(env.path, 'vf/configs/production/settings/supervisord.conf')
    run('ln -s %s /etc/supervisord.conf' % supervisord_conf)

    # run('chown www-data:www-data /etc/supervisord.conf')
    # run('chown www-data:www-data /etc/init.d/supervisord')
    run('/etc/init.d/supervisord start')


def create_dirs():
    celery_dir = os.path.join(env.path, 'celery')
    run('mkdir %s' % celery_dir)
    run('chown www-data:www-data %s' % celery_dir)


def create_dirs_media():
    run('mkdir %s' % '/data')
    run('chown nginx:nginx %s' % '/data')


def create_users():
    require.user('www-data', create_home=False, shell='/bin/false')
    require.user('deploy')


"""
Branches
"""


def branch(branch_name):
    """
    Work on any specified branch.
    """
    env.branch = branch_name


def clone_repo():
    """
    Do initial clone of the git repository.
    """
    run('hg clone %(repository_url)s %(path)s' % env)


# @task
def checkout_latest():
    """
    Pull the latest code on the specified branch.
    """
    run('cd %(path)s; git checkout %(branch)s; git pull origin %(branch)s' % env)

