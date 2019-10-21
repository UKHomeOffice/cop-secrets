#!/usr/bin/env python

import datetime
import json
import requests
from common import *
from prettytable import PrettyTable


def getDroneServerUrl():
    drone_server_url = os.environ.get('DRONE_SERVER')
    if drone_server_url is None:
        print('Drone server environment variable not set')
        exit(1)

    return drone_server_url


def getDroneUserToken():
    drone_user_token = os.environ.get('DRONE_TOKEN')
    if drone_user_token is None:
        print('Drone user token environment variable not set')
        exit(1)

    return drone_user_token


def getDroneTokenString(drone_user_token):
    return {'Authorization': "Bearer " + drone_user_token}


def print_repos_build_info(repo, build_list):
    if build_list:
        t = PrettyTable(['Environment', 'Build', 'Date', 'Status', 'Commit'])
        for build in build_list:
            json_str = json.loads(build)
            deploy_env = 'DEV' if json_str['deploy_to'] == '' else json_str['deploy_to'].upper()
            t.add_row([deploy_env, json_str['number'], datetime.datetime.fromtimestamp(json_str['started_at']), json_str['status'], json_str['link_url']])

        print(t)


def print_repo_build_info(build_env, build_list):
    if build_list:
        t = PrettyTable(['Build', 'Date', 'Status', 'Commit', 'Author'])
        print('**' + build_env.upper() + '**')
        for build in build_list:
            json_str = json.loads(build)
            t.add_row([json_str['number'], datetime.datetime.fromtimestamp(json_str['started_at']), json_str['status'], json_str['link_url'], json_str['author']])

        print(t)


def getRepoList(args, header_str, drone_server_url):
    if args.repo is None:
        drone_repos_url = drone_server_url + '/api/user/repos'
        try:
            repos_response = requests.request("GET", drone_repos_url, headers=header_str)
    
            if repos_response.status_code == 200:
                return repos_response.json()
        except Exception as droneError:
            raise(droneError)
    else:
        repo_list = []
        json_dict_obj = { "full_name": args.repo }
        repo_list.append(json_dict_obj)
        return repo_list


def getBuilds(drone_server_url, header_str, repo_name):
    drone_builds_url = drone_server_url + '/api/repos/' + repo_name + '/builds'
        
    try:
        builds_response = requests.request("GET", drone_builds_url, headers=header_str)

        if builds_response.status_code == 200:
            return builds_response.json()
    except Exception as droneError:
        raise(droneError)


def populate_local(yaml_file, drone_server_url, header_str):
    # Validate yaml file
    if not validateFile(yaml_file):
        print('Yaml file is not valid')
        exit(1)

    with open(yaml_file, 'r') as stream:
        var_data = yaml.safe_load(stream)

    repo_list = []
    for entry in var_data:
        repo = var_data[entry]
        if 'gitlab' in repo:
            if ("gitlab" in drone_server_url and repo['gitlab'] == 'true') or (not("gitlab" in drone_server_url) and not(repo['gitlab'] == 'false')):
                build_list = getBuilds(drone_server_url, header_str, repo['drone_repo'])

                for build in build_list:
                    if (build['branch'] == 'master' and (build['event'] == 'push' or build['event'] == 'deployment')):
                        var_data[entry]['tag'] = build['commit'].encode('ascii', 'ignore')
                        break

    print(yaml.dump(var_data))



def buildReport(args, drone_server_url, drone_user_token, header_str):
    repo_list = getRepoList(args, header_str, drone_server_url)
    
    for repo in repo_list:
        dev_builds = []
        secrets_builds = []
        staging_builds = []
        prod_builds = []
                
        build_list = getBuilds(drone_server_url, header_str, repo['full_name'])

        print('**' + repo['full_name'].upper() + '**')

        for build in build_list:
            if (build['deploy_to'] == 'production'):
                prod_builds.append(json.dumps(build))
            elif (build['deploy_to'] == 'staging'):
                staging_builds.append(json.dumps(build))
            elif (build['deploy_to'] == 'secrets'):
                secrets_builds.append(json.dumps(build))
            else:
                if (build['branch'] == 'master' and (build['event'] == 'push' or build['event'] == 'deployment')):
                    dev_builds.append(json.dumps(build))

        if args.reporttype == 'detailed':
            print_repo_build_info('dev', dev_builds)
            print_repo_build_info('secrets', secrets_builds)
            print_repo_build_info('staging', staging_builds)
            print_repo_build_info('production', prod_builds)
        elif args.reporttype == 'summary':
            repo_builds = []
            if dev_builds:
                repo_builds.append(dev_builds[0])

        if secrets_builds:
            repo_builds.append(secrets_builds[0])

        if staging_builds:
            repo_builds.append(staging_builds[0])

        if prod_builds:
            repo_builds.append(prod_builds[0])

        print_repos_build_info(repo['full_name'], repo_builds)

        print('\n')
        
    exit(0)


if __name__ == "__main__":
    parser = getDroneBuildsParser()
    parser.add_argument('-a', '--action', dest='action', default='report', help='Options are report (builds per repo, summary or detailed), and populate (For releases to staging/production)')
    args = parser.parse_args()

    drone_server_url = getDroneServerUrl()
    drone_user_token = getDroneUserToken()
    header_str = getDroneTokenString(drone_user_token)

    if args.action == 'report':
        buildReport(args, drone_server_url, drone_user_token, header_str)
    elif args.action == 'populate':
        populate_local('blocal.yml', drone_server_url, header_str)
    
