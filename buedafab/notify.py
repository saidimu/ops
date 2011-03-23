"""Deploy notification hooks for third party services like Campfire and Hoptoad.
"""
from fabric.api import env, require, local
from fabric.decorators import runs_once
import os

from buedafab import utils

@runs_once
def hoptoad_deploy(deployed=False):
    """Notify Hoptoad of the time and commit SHA of an app deploy.

    Requires the hoppy Python package and the env keys:

        hoptoad_api_key - as it sounds.
        deployment_type - app environment
        release - the commit SHA or git tag of the deployed version
        scm - path to the remote git repository
    """
    require('hoptoad_api_key')
    require('deployment_type')
    require('release')
    require('scm')
    if deployed and env.hoptoad_api_key:
        commit = local('git rev-parse --short %(release)s' % env)
        import hoppy.deploy
        hoppy.api_key = env.hoptoad_api_key
        hoppy.deploy.Deploy().deploy(
            env=env.deployment_type,
            scm_revision=commit,
            scm_repository=env.scm,
            local_username=os.getlogin())
        print ('Hoptoad notified of deploy of %s@%s to %s environment by %s'
                % (env.scm, commit, env.deployment_type, os.getlogin()))

@runs_once
def campfire_notify(deployed=False):
    """Hop in Campfire and notify your developers of the time and commit SHA of
    an app deploy.

    Requires the pinder Python package and the env keys:

        deployment_type - app environment
        release - the commit SHA or git tag of the deployed version
        scm_http_url - path to an HTTP view of the remote git repository
        campfire_subdomain - subdomain of your Campfire account
        campfire_token - API token for Campfire
        campfire_room - the room to join and notify (the string name, e.g.
                        "Developers")
    """
    require('deployment_type')
    require('release')

    if (deployed and env.campfire_subdomain and env.campfire_token
            and env.campfire_room):
        from pinder import Campfire
        deploying = local('git rev-parse --short %(release)s' % env)
        branch = utils.branch(env.release)

        if env.tagged:
            require('release')
            branch = env.release

        name = env.unit
        deployer = os.getlogin()
        deployed = env.deployed_version
        target = env.deployment_type.lower()
        source_repo_url = env.scm_http_url
        compare_url = ('%(source_repo_url)s/compare/%(deployed)s'
                '...%(deploying)s' % locals())

        campfire = Campfire(env.campfire_subdomain, env.campfire_token,
                ssl=True)
        room = campfire.find_room_by_name(env.campfire_room)
        room.join()
        if deployed:
            message = ('%(deployer)s is deploying %(name)s %(branch)s '
                '(%(deployed)s..%(deploying)s) to %(target)s %(compare_url)s'
                % locals())
        else:
            message = ('%(deployer)s is deploying %(name)s %(branch)s to %(target)s'
                % locals())
        room.speak(message)
        print 'Campfire notified that %s' % message

