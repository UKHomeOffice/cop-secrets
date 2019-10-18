#!/usr/bin/env python

import datetime
import json
import requests
from common import *
from prettytable import PrettyTable


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


def buildReport(args):
    drone_server_url = os.environ.get('DRONE_SERVER')
    if drone_server_url is None:
        print('Drone server environment variable not set')
        exit(1)

    drone_user_token = os.environ.get('DRONE_TOKEN')
    if drone_user_token is None:
        print('Drone user token environment variable not set')
        exit(1)

    header_str = {'Authorization': "Bearer " + drone_user_token}

    repo_list = getRepoList(args, header_str, drone_server_url)
    
    for repo in repo_list:
        drone_builds_url = drone_server_url + '/api/repos/' + repo['full_name'] + '/builds'
        
        dev_builds = []
        secrets_builds = []
        staging_builds = []
        prod_builds = []
                
        try:
            builds_response = requests.request("GET", drone_builds_url, headers=header_str)

            if builds_response.status_code == 200:
                build_list = builds_response.json()
            else:
                continue

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
            else:
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
        
        except Exception as droneError:
            raise(droneError)

    exit(0)


if __name__ == "__main__":
    parser = getDroneBuildsParser()
    args = parser.parse_args()

    buildReport(args)
