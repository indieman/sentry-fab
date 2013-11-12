__author__ = 'indieman'

import sys, os, fabtools
from fabric.api import *
from fabtools import require
from fabtools.python import virtualenv, install_pip
from fabtools.files import watch
from fabric.contrib.files import comment, uncomment
from fabtools.utils import run_as_root

env.hosts = ['root@lookido']
env.project_name = 'sentry'
env.virtualenv_path = '/usr/local/virtualenvs/%(project_name)s' % env
env.path = '/srv/sites/%(project_name)s' % env
env.repository_url = 'https://github.com/indieman/sentry-fab.git'
env.database_name = env.project_name
env.user = env.project_name
env.shell = '/bin/bash -c'


@task
def setup():
    # require.deb.packages([
    #     'python',
    #     'mercurial',
    #     'subversion',
    #     'git',
    #     'vim',
    #     'sudo'
    #     ], update=True)

    clone_repo()

    require.python.virtualenv(env.virtualenv_path, use_sudo=False)

    with virtualenv(env.virtualenv_path):
        require.python.requirements(os.path.join(env.path, 'reqs', 'requirements.txt'))

    require.postgres.server()
    require.postgres.user(env.user, 'mu#^73U#P_o$JWf')
    require.postgres.database(env.database_name, env.user)


    require.supervisor.process(env.project_name,
                               command='%(virtualenv_path)s/sentry --config=%(path)s/sentry.conf.py start' % env,
                               directory=env.path,
                               user=env.user,
                               stdout_logfile='%(path)s/log/sentry_supervisor.log' % env
    )

    with virtualenv(env.virtualenv_path):
        run('sentry --config=/srv/sites/sentry/sentry.conf.py upgrade')

def clone_repo():
    """
    Do initial clone of the git repository.
    """
    run('git clone %(repository_url)s %(path)s' % env)