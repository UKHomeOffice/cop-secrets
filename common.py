#!/usr/bin/env python

import argparse
import os
import yaml
from credentials import *

global_exclusion_list = ['api_cop_image', 'api_cop_port', 'api_form_aws_access_key_id', 'api_form_aws_secret_access_key', 'api_form_protocol', 'camunda_aws_access_key_id', 'camunda_aws_secret_access_key', 'cop_ops_sql_clients_aws_access_key_id', 'cop_ops_sql_clients_aws_secret_access_key', 'db_cop_port', 'db_ref_default_username', 'db_ref_governance_anon_username', 'db_ref_governance_authenticator_username', 'db_ref_governance_owner_username', 'db_ref_governance_readonly_username' , 'db_ref_governance_schema', 'db_ref_governance_service_username', 'db_ref_jdbc_options', 'db_ref_options', 'db_ref_port', 'db_ref_private_gitkey', 'db_ref_private_gitrepo', 'db_ref_protocol', 'db_ref_reference_anon_username', 'db_ref_reference_authenticator_username', 'db_ref_reference_dbname', 'db_ref_reference_owner_username', 'db_ref_reference_readonly_username', 'db_ref_reference_schema', 'db_ref_reference_service_username', 'doc_cop_aws_access_key_id', 'doc_cop_aws_secret_access_key', 'doc_training_aws_access_key_id', 'doc_training_aws_secret_access_key', 'docker_credentials', 'docker_password', 'docker_username', 'drone_private_token', 'drone_public_token', 'engine_port', 'engine_private_der_path', 'engine_protocol', 'engine_public_der_path', 'executor_aws_access_key_id', 'executor_aws_secret_access_key', 'flyway_image', 'flyway_tag', 'formbuilder_aws_access_key_id', 'formbuilder_aws_secret_access_key', 'git_repo_private_giturl', 'git_repo_private_port', 'git_repo_private_url', 'log_level_debug', 'log_level_info', 'nginx_image', 'nginx_tag', 'pdf_generator_aws_access_key_id', 'pdf_generator_aws_s3_endpoint', 'pdf_generator_aws_s3_port', 'pdf_generator_aws_s3_protocol', 'pdf_generator_aws_s3_region', 'pdf_generator_aws_secret_access_key', 'translation_private_key_path', 'postgres_image', 'postgres_tag', 'protocol_awbs', 'protocol_https', 'protocol_jdbc', 'protocol_postgres', 'quay_password', 'quay_username', 'report_aws_access_key_id', 'report_aws_secret_access_key', 'slack_webhook', 'translation_image', 'translation_keycloak_client_id', 'translation_name', 'translation_port', 'translation_protocol', 'www_image', 'www_keycloak_access_role', 'www_keycloak_client_id', 'www_name', 'www_port', 'www_protocol', 'www_ref_image', 'www_ref_keycloak_client_id', 'www_ref_name', 'www_ref_port', 'www_ref_protocol', 'www_ui_protocol', 'www_ui_txt_protocol', 'www_ui_version']


env_exclusion_list = ['analytics_site_id', 'analytics_url', 'api_cop_url', 'api_form_url', 'api_ref_port', 'api_ref_protocol', 'api_ref_url', 'db_cop_hostname', 'db_cop_operation_authenticator_password', 'db_cop_operation_authenticator_username', 'db_cop_operation_dbname', 'db_cop_operation_schema', 'db_cop_options', 'db_cop_port', 'db_cop_protocol', 'db_engine_default_dbname', 'db_engine_default_password', 'db_engine_default_username', 'db_engine_driver', 'db_engine_hostname', 'db_engine_jdbc_options', 'db_engine_jdbc_protocol', 'db_engine_options', 'db_engine_type', 'db_engine_port', 'db_engine_protocol', 'db_ref_default_dbname', 'db_ref_default_password', 'db_ref_governance_authenticator_password', 'db_ref_governance_owner_password', 'db_ref_hostname', 'db_ref_reference_authenticator_password', 'db_ref_reference_owner_password', 'drone_aws_access_key_id', 'drone_aws_secret_access_key', 'engine_url', 'environment', 'gov_notify_api_key', 'gov_notify_notification_email_template_id', 'gov_notify_notification_sms_template_id', 'keycloak_protocol', 'keycloak_realm', 'keycloak_url', 'kube_namespace_cop_ops', 'kube_namespace_private_cop', 'kube_namespace_public_cop', 'kube_namespace_refdata', 'kube_server', 'kube_token', 'pdf_generator_aws_s3_access_key', 'pdf_generator_aws_s3_kms_key', 'pdf_generator_aws_s3_pdf_bucketname', 'pdf_generator_aws_s3_secret_key', 'redis_port', 'redis_ssl', 'redis_token', 'redis_url', 'report_protocol', 'report_url', 'translation_url', 'whitelist', 'www_ref_read_only_mode', 'www_ref_url', 'www_ui_environment', 'www_url']


def getCredentials(args):
    if args.authenticate == "Y":
        role_arn = 'arn:aws:iam::' + args.account + ':' + args.rolename
        mfa_arn  = 'arn:aws:iam::' + args.primaryaccount + ':mfa/' + args.mfa
        client = getAssumeRoleCreds(role_arn, mfa_arn)
    else:
        client = getAWSSecretsManagerCreds('eu-west-2')

    return client


def getUserParser():
    parser = argparse.ArgumentParser(description='Secrets management')

    parser.add_argument('-l', '--auth', dest='authenticate', default='N', choices=['Y', 'N'], help='Authentication required Y/N, default N')
    parser.add_argument('-m', '--mfa', dest='mfa', help='MFA device id')
    parser.add_argument('-p', '--primaryaccount', dest='primaryaccount', help='HO primary account')
    parser.add_argument('-a', '--account', dest='account', help='AWS Account number')
    parser.add_argument('-n', '--rolename', dest='rolename', help='AWS role name')

    return parser


def getDroneBuildsParser():
    parser = argparse.ArgumentParser(description='Drone builds')

    parser.add_argument('-a', '--action', dest='action', default='report', help='Options are report (builds per repo, summary or detailed), populate (For releases to staging/production), defaults to report, and deploy')
    parser.add_argument('-d', '--deploy-to', dest='deploy_to', default='staging', choices=['production', 'staging'], help='Environment to deploy to, defaults to staging')
    parser.add_argument('-r', '--repo', dest='repo', help='Drone repository name')
    parser.add_argument('-s', '--store', dest='repo_store', choices=['github', 'gitlab'], help='Github / Gitlab repository store')
    parser.add_argument('-t', '--report-type', dest='reporttype', default='summary', choices=['detailed', 'summary'], help='Type of report, defaults to summary')
    parser.add_argument('-f', '--report-format', dest='reportformat', default='table', choices=['list', 'table'], help='Style of report, defaults to table')

    return parser


def flatten_dict(current, key, result):
    if isinstance(current, dict):
        for k in current:
            new_key = "{0}_{1}".format(key, k) if len(key) > 0 else k
            flatten_dict(current[k], new_key, result)
    else:
        result[key] = current

    return result


def flatten_seed(data):
  seed_list = []
  for key in data['keys']:
    if isinstance(key, dict):
      seed_result = flatten_dict(key, '', {})
      for key_name, key_values in seed_result.items():
        for key_value in key_values.split():
          seed_list.append(key_name + '_' + key_value)
    else:
      seed_list.append(key)

  return seed_list


def summaryStatus(success_list, error_list):
    print ('Successful secrets')
    print ('------------------')
    for success_item in success_list:
        print(success_item)

    print ('\n\nUnsuccessful secrets')
    print ('--------------------')
    for error_item in error_list:
        print(error_item)


def validateFile(src_file):
    try:
        data = yaml.safe_load(open(src_file))
        return True
    except yaml.YAMLError as e:
        print(e)
        return False


def validateArgs(arguments):
    # TODO
    # if logging in, mfa needs to be supplied
    # if update, service, env_deploy needs to be supplied
    return True
